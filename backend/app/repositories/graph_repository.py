from abc import ABC, abstractmethod
from typing import List, Dict, Any
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
    async def get_graph(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def clear_graph(self) -> bool:
        pass


class GraphRepository(IGraphRepository):
    def __init__(self, neo4j_client):
        self.client = neo4j_client

    async def ensure_indexes(self) -> bool:
        """Create constraints and vector indexes in Neo4j if driver is active."""
        if not getattr(self.client, "_driver", None):
            return False

        cypher_statements = [
            "CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE",
            "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
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
                logger.warning(f"Neo4j schema index init statement ({stmt[:50]}...): {e}")

        return True

    async def upsert_nodes_and_edges(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> bool:
        """Upsert extracted entity nodes and relationship edges into Neo4j."""
        if not getattr(self.client, "_driver", None):
            logger.info("Neo4j driver inactive (mock mode). Skipping physical Cypher writes.")
            return True

        # 1. Ensure schema indexes
        await self.ensure_indexes()

        # 2. Upsert Entity Nodes
        if nodes:
            cypher_nodes = """
            UNWIND $nodes AS node
            MERGE (e:Entity {name: node.name, user_id: node.user_id})
            SET e.type = COALESCE(node.type, 'Entity'),
                e.description = COALESCE(node.description, ''),
                e.document_id = node.document_id,
                e.user_id = node.user_id
            """
            try:
                self.client.execute_write(cypher_nodes, {"nodes": nodes})
            except Exception as e:
                logger.error(f"Failed to upsert Entity nodes to Neo4j: {e}")

        # 3. Upsert Relationships
        if edges:
            cypher_edges_standard = """
            UNWIND $edges AS rel
            MATCH (source:Entity {name: rel.source_entity})
            MATCH (target:Entity {name: rel.target_entity})
            MERGE (source)-[r:GOVERNS]->(target)
            SET r.confidence = rel.confidence,
                r.evidence = rel.evidence,
                r.relationship_type = rel.relationship_type
            """
            try:
                self.client.execute_write(cypher_edges_standard, {"edges": edges})
            except Exception as e:
                logger.error(f"Failed to upsert relationships to Neo4j: {e}")

        return True

    async def upsert_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """Upsert document text chunks with vectors into Neo4j."""
        if not getattr(self.client, "_driver", None) or not chunks:
            return True

        cypher_chunks = """
        UNWIND $chunks AS chunk
        MERGE (c:Chunk {chunk_id: chunk.chunk_id})
        SET c.document_id = chunk.document_id,
            c.document_name = chunk.document_name,
            c.text = chunk.text,
            c.page_number = chunk.page_number,
            c.section_title = chunk.section_title,
            c.embedding = chunk.embedding
        """
        try:
            self.client.execute_write(cypher_chunks, {"chunks": chunks})
        except Exception as e:
            logger.error(f"Failed to upsert Chunk nodes to Neo4j: {e}")

        return True

    async def get_graph(self, user_id: str = None) -> Dict[str, Any]:
        """Retrieve entity nodes and relationships filtered strictly by user_id."""
        if not getattr(self.client, "_driver", None):
            return {"nodes": [], "edges": []}

        if user_id:
            query = """
            MATCH (n:Entity {user_id: $user_id})
            OPTIONAL MATCH (n)-[r]->(m:Entity {user_id: $user_id})
            RETURN n.name AS source_name,
                   n.type AS source_type,
                   n.description AS source_desc,
                   m.name AS target_name,
                   m.type AS target_type,
                   m.description AS target_desc,
                   type(r) AS rel_type,
                   r.confidence AS confidence
            LIMIT 200
            """
            params = {"user_id": user_id}
        else:
            query = """
            MATCH (n:Entity)
            OPTIONAL MATCH (n)-[r]->(m:Entity)
            RETURN n.name AS source_name,
                   n.type AS source_type,
                   n.description AS source_desc,
                   m.name AS target_name,
                   m.type AS target_type,
                   m.description AS target_desc,
                   type(r) AS rel_type,
                   r.confidence AS confidence
            LIMIT 200
            """
            params = {}

        try:
            records = self.client.execute_read(query, params)
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

                if s_name and t_name and row.get("rel_type"):
                    edges_list.append({
                        "source": s_name,
                        "target": t_name,
                        "type": row.get("rel_type"),
                        "relationship_type": row.get("rel_type"),
                        "confidence": row.get("confidence") or 0.9
                    })

            return {
                "nodes": list(nodes_dict.values()),
                "edges": edges_list
            }
        except Exception as e:
            logger.error(f"Failed to fetch graph from Neo4j: {e}")
            return {"nodes": [], "edges": []}

    async def clear_graph(self, user_id: str = None) -> bool:
        """Delete Entity/Chunk nodes for a specific user from Neo4j."""
        if not getattr(self.client, "_driver", None):
            return True

        if user_id:
            query = "MATCH (n:Entity {user_id: $user_id}) DETACH DELETE n"
            params = {"user_id": user_id}
        else:
            query = "MATCH (n) DETACH DELETE n"
            params = {}

        try:
            self.client.execute_write(query, params)
            logger.info("Cleared nodes and relationships from Neo4j Knowledge Graph.")
            return True
        except Exception as e:
            logger.error(f"Failed to clear Neo4j graph: {e}")
            return False
