from typing import List, Dict, Any, Optional
from app.dependencies.clients import Neo4jClient
from app.core.logger import logger


class GraphReaderRepository:
    """Read-only Neo4j repository for GraphRAG retrieval queries.

    Separates query-time reads from the write-path GraphRepository.
    All methods use explicit read transactions for optimal routing
    on Neo4j Aura clusters.
    """

    def __init__(self, neo4j_client: Neo4jClient):
        self.client = neo4j_client

    # ------------------------------------------------------------------
    # Entity search
    # ------------------------------------------------------------------

    def search_entities_by_name(self, keywords: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """Search entity nodes by name using case-insensitive CONTAINS matching.

        Falls back gracefully to an empty list when no entities match.
        """
        if not keywords:
            return []

        conditions = " OR ".join(
            [f"toLower(e.name) CONTAINS toLower($kw{i})" for i in range(len(keywords))]
        )
        params: Dict[str, Any] = {f"kw{i}": kw for i, kw in enumerate(keywords)}
        params["limit"] = limit

        query = f"""
        MATCH (e:Entity)
        WHERE {conditions}
        RETURN e.name AS name,
               e.type AS type,
               e.description AS description,
               labels(e) AS labels,
               id(e) AS node_id
        ORDER BY e.name
        LIMIT $limit
        """

        try:
            return self.client.execute_read(query, params)
        except Exception as e:
            logger.error(f"Entity keyword search failed: {e}")
            return []

    def search_entities_by_embedding(
        self, embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Vector similarity search on entity embeddings.

        Uses Neo4j vector index if available, otherwise falls back
        to brute-force cosine similarity on the `embedding` property.
        """
        query = """
        CALL db.index.vector.queryNodes('entity_embedding_index', $top_k, $embedding)
        YIELD node, score
        RETURN node.name AS name,
               node.type AS type,
               node.description AS description,
               score
        ORDER BY score DESC
        """

        try:
            results = self.client.execute_read(query, {"embedding": embedding, "top_k": top_k})
            if results:
                return results
        except Exception as e:
            logger.warning(f"Vector index query failed (may not exist): {e}. Falling back to keyword search.")

        return []

    # ------------------------------------------------------------------
    # Subgraph neighborhood
    # ------------------------------------------------------------------

    def get_entity_neighborhood(
        self, entity_names: List[str], depth: int = 1
    ) -> Dict[str, Any]:
        """Fetch the 1–2 hop subgraph around the given entity names.

        Returns nodes and edges as serializable dicts for prompt building.
        """
        if not entity_names:
            return {"nodes": [], "edges": []}

        query = """
        UNWIND $names AS entity_name
        MATCH (e:Entity)
        WHERE toLower(e.name) = toLower(entity_name)
        CALL apoc.path.subgraphAll(e, {maxLevel: $depth})
        YIELD nodes, relationships
        UNWIND nodes AS n
        WITH COLLECT(DISTINCT {
            name: n.name,
            type: COALESCE(n.type, head(labels(n))),
            description: n.description
        }) AS node_list, relationships
        UNWIND relationships AS r
        RETURN node_list AS nodes,
               COLLECT(DISTINCT {
                   source: startNode(r).name,
                   target: endNode(r).name,
                   type: type(r),
                   confidence: r.confidence
               }) AS edges
        """

        try:
            results = self.client.execute_read(
                query, {"names": entity_names, "depth": depth}
            )
            if results:
                return {"nodes": results[0].get("nodes", []), "edges": results[0].get("edges", [])}
        except Exception as e:
            logger.warning(f"APOC subgraph query failed: {e}. Using simple expansion.")

        # Fallback: simple variable-length path without APOC
        return self._get_neighborhood_simple(entity_names, depth)

    def _get_neighborhood_simple(
        self, entity_names: List[str], depth: int = 1
    ) -> Dict[str, Any]:
        """Simple neighborhood expansion without APOC dependency."""
        query = """
        UNWIND $names AS entity_name
        MATCH (e:Entity)
        WHERE toLower(e.name) = toLower(entity_name)
        OPTIONAL MATCH path = (e)-[r*1..2]-(neighbor:Entity)
        WITH e, neighbor, relationships(path) AS rels
        WITH COLLECT(DISTINCT {
            name: e.name,
            type: COALESCE(e.type, 'Entity'),
            description: e.description
        }) + COLLECT(DISTINCT {
            name: neighbor.name,
            type: COALESCE(neighbor.type, 'Entity'),
            description: neighbor.description
        }) AS all_nodes,
        COLLECT(DISTINCT rels) AS all_rels_nested
        UNWIND all_rels_nested AS rel_list
        UNWIND rel_list AS r
        RETURN all_nodes AS nodes,
               COLLECT(DISTINCT {
                   source: startNode(r).name,
                   target: endNode(r).name,
                   type: type(r),
                   confidence: r.confidence
               }) AS edges
        """
        try:
            results = self.client.execute_read(query, {"names": entity_names})
            if results:
                nodes = results[0].get("nodes", [])
                # Deduplicate nodes by name
                seen = set()
                unique_nodes = []
                for n in nodes:
                    if n and n.get("name") and n["name"] not in seen:
                        seen.add(n["name"])
                        unique_nodes.append(n)
                return {"nodes": unique_nodes, "edges": results[0].get("edges", [])}
        except Exception as e:
            logger.error(f"Simple neighborhood query failed: {e}")

        return {"nodes": [], "edges": []}

    # ------------------------------------------------------------------
    # Chunk search
    # ------------------------------------------------------------------

    def search_chunks_by_embedding(
        self, embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Vector similarity search on chunk embeddings."""
        query = """
        CALL db.index.vector.queryNodes('chunk_embedding_index', $top_k, $embedding)
        YIELD node, score
        RETURN node.chunk_id AS chunk_id,
               node.document_id AS document_id,
               node.document_name AS document_name,
               node.text AS text,
               node.page_number AS page_number,
               node.section_title AS section_title,
               score
        ORDER BY score DESC
        """

        try:
            results = self.client.execute_read(query, {"embedding": embedding, "top_k": top_k})
            if results:
                return results
        except Exception as e:
            logger.warning(f"Chunk vector search failed: {e}. Falling back to keyword search.")

        return []

    def search_chunks_by_keywords(
        self, keywords: List[str], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Keyword-based chunk retrieval using CONTAINS matching."""
        if not keywords:
            return []

        conditions = " OR ".join(
            [f"toLower(c.text) CONTAINS toLower($kw{i})" for i in range(len(keywords))]
        )
        params: Dict[str, Any] = {f"kw{i}": kw for i, kw in enumerate(keywords)}
        params["limit"] = top_k

        query = f"""
        MATCH (c:Chunk)
        WHERE {conditions}
        RETURN c.chunk_id AS chunk_id,
               c.document_id AS document_id,
               c.document_name AS document_name,
               c.text AS text,
               c.page_number AS page_number,
               c.section_title AS section_title
        LIMIT $limit
        """

        try:
            return self.client.execute_read(query, params)
        except Exception as e:
            logger.error(f"Chunk keyword search failed: {e}")
            return []

    # ------------------------------------------------------------------
    # Graph stats (for health checks and diagnostics)
    # ------------------------------------------------------------------

    def get_graph_stats(self) -> Dict[str, int]:
        """Return counts of entities, relationships, and chunks in the graph."""
        query = """
        OPTIONAL MATCH (e:Entity)
        WITH count(e) AS entity_count
        OPTIONAL MATCH ()-[r]->()
        WITH entity_count, count(r) AS rel_count
        OPTIONAL MATCH (c:Chunk)
        RETURN entity_count, rel_count, count(c) AS chunk_count
        """

        try:
            results = self.client.execute_read(query)
            if results:
                return {
                    "entity_count": results[0].get("entity_count", 0),
                    "relationship_count": results[0].get("rel_count", 0),
                    "chunk_count": results[0].get("chunk_count", 0),
                }
        except Exception as e:
            logger.error(f"Graph stats query failed: {e}")

        return {"entity_count": 0, "relationship_count": 0, "chunk_count": 0}
