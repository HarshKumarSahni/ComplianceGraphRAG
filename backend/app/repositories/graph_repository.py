from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.core.logger import logger


class IGraphRepository(ABC):
    @abstractmethod
    async def ensure_indexes(self) -> bool:
        pass

    @abstractmethod
    async def upsert_nodes_and_edges(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
        pass

    @abstractmethod
    async def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        pass

    @abstractmethod
    async def get_graph(self, user_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_chunk_count(self, user_id: str) -> int:
        pass

    @abstractmethod
    async def clear_graph(self, user_id: str) -> bool:
        pass


class GraphRepository(IGraphRepository):
    # In-memory store for local testing when physical Neo4j driver is inactive
    _mock_store: Dict[str, Dict[str, Any]] = {}

    def __init__(self, neo4j_client):
        self.client = neo4j_client

    async def ensure_indexes(self) -> bool:
        """Create composite indexes and vector indexes in Neo4j if driver is active."""
        if not getattr(self.client, "_driver", None):
            return False

        cypher_statements = [
            # Drop old single-property constraint if present
            "DROP CONSTRAINT entity_name_unique IF EXISTS",
            "DROP CONSTRAINT chunk_id_unique IF EXISTS",
            # Indexes for composite lookup on user_id + name / chunk_id
            "CREATE INDEX entity_user_name_idx IF NOT EXISTS FOR (e:Entity) ON (e.user_id, e.name)",
            "CREATE INDEX chunk_user_chunk_idx IF NOT EXISTS FOR (c:Chunk) ON (c.user_id, c.chunk_id)",
            """
            CREATE VECTOR INDEX entity_embedding_index IF NOT EXISTS
            FOR (e:Entity) ON (e.embedding)
            OPTIONS {indexConfig: {`vector.similarity_function`: 'cosine', `vector.dimensions`: 384}}
            """,
            """
            CREATE VECTOR INDEX chunk_embedding_index IF NOT EXISTS
            FOR (c:Chunk) ON (c.embedding)
            OPTIONS {indexConfig: {`vector.similarity_function`: 'cosine', `vector.dimensions`: 384}}
            """
        ]

        for stmt in cypher_statements:
            try:
                self.client.execute_write(stmt)
            except Exception as e:
                logger.warning(f"Neo4j schema index init statement ({stmt[:60]}...): {e}")

        return True

    async def upsert_nodes_and_edges(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
        """Upsert extracted entity nodes and relationship edges into Neo4j, strictly scoped by user_id."""
        if not getattr(self.client, "_driver", None):
            logger.info("Neo4j driver inactive (mock mode). Saving nodes/edges to mock memory store.")
            for node in nodes:
                u_id = node.get("user_id", "anonymous")
                if u_id not in GraphRepository._mock_store:
                    GraphRepository._mock_store[u_id] = {"nodes": {}, "edges": [], "chunks": []}
                
                name = node.get("name")
                if name:
                    GraphRepository._mock_store[u_id]["nodes"][name] = {
                        "id": name,
                        "label": name,
                        "name": name,
                        "type": node.get("type") or "Entity",
                        "description": node.get("description") or ""
                    }

            for edge in edges:
                u_id = edge.get("user_id", "anonymous")
                if u_id not in GraphRepository._mock_store:
                    GraphRepository._mock_store[u_id] = {"nodes": {}, "edges": [], "chunks": []}

                rel_type = edge.get("relationship_type") or "RELATED_TO"
                GraphRepository._mock_store[u_id]["edges"].append({
                    "source": edge.get("source_entity"),
                    "target": edge.get("target_entity"),
                    "type": rel_type,
                    "relationship_type": rel_type,
                    "confidence": edge.get("confidence") or 0.9
                })
            return True

        # 1. Ensure schema indexes
        await self.ensure_indexes()

        # 2. Upsert Entity Nodes — composite key (user_id, name)
        if nodes:
            cypher_nodes = """
            UNWIND $nodes AS node
            MERGE (e:Entity {user_id: node.user_id, name: node.name})
            SET e.type = COALESCE(node.type, 'Entity'),
                e.description = COALESCE(node.description, ''),
                e.document_id = node.document_id,
                e.user_id = node.user_id
            """
            self.client.execute_write(cypher_nodes, {"nodes": nodes})
            logger.info(f"Upserted {len(nodes)} entity nodes for user {nodes[0].get('user_id')}")

        # 3. Upsert Relationships
        if edges:
            cypher_edges = """
            UNWIND $edges AS rel
            MATCH (source:Entity {user_id: rel.user_id, name: rel.source_entity})
            MATCH (target:Entity {user_id: rel.user_id, name: rel.target_entity})
            MERGE (source)-[r:RELATES_TO {relationship_type: rel.relationship_type, user_id: rel.user_id}]->(target)
            SET r.confidence = rel.confidence,
                r.evidence = rel.evidence,
                r.relationship_type = rel.relationship_type,
                r.user_id = rel.user_id
            """
            self.client.execute_write(cypher_edges, {"edges": edges})
            logger.info(f"Upserted {len(edges)} relationships for user {edges[0].get('user_id')}")

        return True

    async def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Upsert document text chunks with vectors into Neo4j, scoped by user_id."""
        if not chunks:
            return True

        if not getattr(self.client, "_driver", None):
            for chunk in chunks:
                u_id = chunk.get("user_id", "anonymous")
                if u_id not in GraphRepository._mock_store:
                    GraphRepository._mock_store[u_id] = {"nodes": {}, "edges": [], "chunks": []}
                GraphRepository._mock_store[u_id]["chunks"].append(chunk)
            return True

        cypher_chunks = """
        UNWIND $chunks AS chunk
        MERGE (c:Chunk {user_id: chunk.user_id, chunk_id: chunk.chunk_id})
        SET c.document_id = chunk.document_id,
            c.document_name = chunk.document_name,
            c.text = chunk.text,
            c.page_number = chunk.page_number,
            c.section_title = chunk.section_title,
            c.embedding = chunk.embedding,
            c.user_id = chunk.user_id
        """
        self.client.execute_write(cypher_chunks, {"chunks": chunks})
        logger.info(f"Upserted {len(chunks)} chunk nodes for user {chunks[0].get('user_id')}")
        return True

    async def get_graph(self, user_id: str) -> Dict[str, Any]:
        """Retrieve ONLY entity nodes and relationships belonging to user_id."""
        if not getattr(self.client, "_driver", None):
            user_data = GraphRepository._mock_store.get(user_id, {"nodes": {}, "edges": [], "chunks": []})
            return {
                "nodes": list(user_data["nodes"].values()),
                "edges": user_data["edges"]
            }

        query = """
        MATCH (n:Entity {user_id: $user_id})
        OPTIONAL MATCH (n)-[r]->(m:Entity {user_id: $user_id})
        WHERE r.user_id = $user_id
        RETURN n.name AS source_name,
               n.type AS source_type,
               n.description AS source_desc,
               m.name AS target_name,
               m.type AS target_type,
               m.description AS target_desc,
               r.relationship_type AS rel_label,
               r.confidence AS confidence
        LIMIT 500
        """
        try:
            records = self.client.execute_read(query, {"user_id": user_id})
            nodes_dict = {}
            edges_list = []

            for row in records:
                s_name = row.get("source_name")
                if s_name and s_name not in nodes_dict:
                    nodes_dict[s_name] = {
                        "id": s_name,
                        "label": s_name,
                        "name": s_name,
                        "type": row.get("source_type") or "Entity",
                        "description": row.get("source_desc") or ""
                    }

                t_name = row.get("target_name")
                if t_name and t_name not in nodes_dict:
                    nodes_dict[t_name] = {
                        "id": t_name,
                        "label": t_name,
                        "name": t_name,
                        "type": row.get("target_type") or "Entity",
                        "description": row.get("target_desc") or ""
                    }

                if s_name and t_name and row.get("rel_label"):
                    edges_list.append({
                        "source": s_name,
                        "target": t_name,
                        "type": row.get("rel_label"),
                        "relationship_type": row.get("rel_label"),
                        "confidence": row.get("confidence") or 0.9
                    })

            return {
                "nodes": list(nodes_dict.values()),
                "edges": edges_list
            }
        except Exception as e:
            logger.error(f"Failed to fetch graph from Neo4j: {e}")
            return {"nodes": [], "edges": []}

    async def get_chunk_count(self, user_id: str) -> int:
        """Return the actual count of Chunk nodes belonging to this user."""
        if not getattr(self.client, "_driver", None):
            user_data = GraphRepository._mock_store.get(user_id, {"nodes": {}, "edges": [], "chunks": []})
            return len(user_data["chunks"])

        try:
            query = "MATCH (c:Chunk {user_id: $user_id}) RETURN count(c) AS cnt"
            records = self.client.execute_read(query, {"user_id": user_id})
            return records[0].get("cnt", 0) if records else 0
        except Exception as e:
            logger.error(f"Failed to get chunk count: {e}")
            return 0

    async def clear_graph(self, user_id: str) -> bool:
        """Delete ONLY this user's Entity AND Chunk nodes."""
        if not getattr(self.client, "_driver", None):
            if user_id in GraphRepository._mock_store:
                GraphRepository._mock_store[user_id] = {"nodes": {}, "edges": [], "chunks": []}
            return True

        try:
            self.client.execute_write(
                "MATCH (n:Entity {user_id: $user_id}) DETACH DELETE n",
                {"user_id": user_id}
            )
            self.client.execute_write(
                "MATCH (c:Chunk {user_id: $user_id}) DETACH DELETE c",
                {"user_id": user_id}
            )
            logger.info(f"Cleared graph and chunks for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear Neo4j graph for user {user_id}: {e}")
            return False
