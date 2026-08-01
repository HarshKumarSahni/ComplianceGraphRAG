import time
import json
from typing import List, Dict, Any, Optional

from app.core.config import Settings
from app.core.logger import logger
from app.core.exceptions import GraphRAGRetrievalError, ExternalAPIError, QueryTimeoutError
from app.repositories.graph_reader_repository import GraphReaderRepository
from app.services.openrouter_client import OpenRouterClient
from app.services.graphrag.embedding_service import EmbeddingService
from app.services.graphrag.entity_extractor import EntityExtractor
from app.services.graphrag.query_prompt_builder import QueryPromptBuilder
from app.schemas.rag import (
    QueryRequest,
    QueryResponse,
    Citation,
    SubGraphPath,
    RetrievalStats,
)


class GraphRAGQueryEngine:
    """Orchestrates the complete GraphRAG retrieval-augmented generation pipeline.

    Flow:
        Question → Entity Extraction → Embedding → Graph Retrieval
        → Chunk Retrieval → Evidence Ranking → Prompt Building
        → LLM Answer → Citation Assembly → QueryResponse
    """

    def __init__(
        self,
        graph_reader: GraphReaderRepository,
        openrouter_client: OpenRouterClient,
        settings: Settings,
    ):
        self.graph_reader = graph_reader
        self.openrouter = openrouter_client
        self.settings = settings
        self.embedding_service = EmbeddingService(settings)
        self.entity_extractor = EntityExtractor(openrouter_client)
        self.prompt_builder = QueryPromptBuilder()

    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        """Execute the full GraphRAG pipeline and return a grounded answer."""
        pipeline_start = time.time()

        question = request.question
        top_k = request.top_k

        logger.info(f"GraphRAG query received: '{question[:80]}...' (top_k={top_k})",
                     extra={"request_id": "graphrag"})

        # ------------------------------------------------------------------
        # 1. Extract entities and keywords from the question
        # ------------------------------------------------------------------
        extraction_result = await self.entity_extractor.extract(question)
        entities = extraction_result.get("entities", [])
        keywords = extraction_result.get("keywords", [])
        all_search_terms = list(set(entities + keywords))

        logger.info(f"Extracted entities={entities}, keywords={keywords}",
                     extra={"request_id": "graphrag"})

        # ------------------------------------------------------------------
        # 2. Generate question embedding
        # ------------------------------------------------------------------
        try:
            question_embedding = self.embedding_service.encode(question)
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}. Proceeding with keyword-only retrieval.",
                           extra={"request_id": "graphrag"})
            question_embedding = None

        # ------------------------------------------------------------------
        # 3. Retrieve from Neo4j
        # ------------------------------------------------------------------
        retrieval_start = time.time()

        # 3a. Entity search (vector + keyword)
        entity_results = []
        if question_embedding:
            entity_results = self.graph_reader.search_entities_by_embedding(
                question_embedding, top_k=top_k
            )
        if not entity_results and all_search_terms:
            entity_results = self.graph_reader.search_entities_by_name(
                all_search_terms, limit=top_k
            )

        # 3b. Subgraph neighborhood around matched entities
        matched_entity_names = [e.get("name") for e in entity_results if e.get("name")]
        subgraph = {"nodes": [], "edges": []}
        if matched_entity_names:
            subgraph = self.graph_reader.get_entity_neighborhood(
                matched_entity_names[:5], depth=1
            )

        # 3c. Chunk search (vector + keyword)
        chunk_results = []
        if question_embedding:
            chunk_results = self.graph_reader.search_chunks_by_embedding(
                question_embedding, top_k=top_k
            )
        if not chunk_results and all_search_terms:
            chunk_results = self.graph_reader.search_chunks_by_keywords(
                all_search_terms, top_k=top_k
            )

        retrieval_time_ms = (time.time() - retrieval_start) * 1000

        logger.info(
            f"Retrieval complete: {len(entity_results)} entities, "
            f"{len(subgraph.get('edges', []))} relationships, "
            f"{len(chunk_results)} chunks ({retrieval_time_ms:.0f}ms)",
            extra={"request_id": "graphrag"},
        )

        # ------------------------------------------------------------------
        # 4. Combine evidence for prompt
        # ------------------------------------------------------------------
        graph_facts = self._build_graph_facts(entity_results, subgraph)

        # If absolutely nothing was retrieved, return a helpful no-data response
        if not graph_facts and not chunk_results:
            total_time_ms = (time.time() - pipeline_start) * 1000
            return QueryResponse(
                question=question,
                answer="The knowledge graph does not contain information relevant to this question. Please ensure documents have been uploaded and processed.",
                confidence=0.0,
                citations=[],
                sources=[],
                subgraph=SubGraphPath(),
                retrieval_stats=RetrievalStats(
                    node_count=0,
                    chunk_count=0,
                    relationship_count=0,
                    retrieval_time_ms=retrieval_time_ms,
                    llm_time_ms=0.0,
                    total_time_ms=total_time_ms,
                ),
            )

        # ------------------------------------------------------------------
        # 5. Build prompt and call LLM
        # ------------------------------------------------------------------
        system_prompt = self.prompt_builder.get_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(
            question=question,
            graph_facts=graph_facts,
            chunks=chunk_results,
        )

        llm_start = time.time()
        try:
            llm_response = await self.openrouter.generate_json(
                prompt=user_prompt,
                system_prompt=system_prompt,
            )
        except Exception as e:
            logger.error(f"LLM call failed: {e}", extra={"request_id": "graphrag"})
            raise ExternalAPIError(f"Failed to generate answer: {e}")
        llm_time_ms = (time.time() - llm_start) * 1000

        # ------------------------------------------------------------------
        # 6. Parse LLM response and assemble citations
        # ------------------------------------------------------------------
        answer_text = llm_response.get("answer", "Unable to generate an answer from the provided evidence.")
        confidence = float(llm_response.get("confidence", 0.5))
        cited_chunk_ids = llm_response.get("cited_chunks", [])

        # Build citation objects from the chunks the LLM cited
        citations = self._build_citations(chunk_results, cited_chunk_ids)

        # Collect unique source document names
        sources = list(set(
            c.get("document_name", "Unknown")
            for c in chunk_results
            if c.get("document_name")
        ))

        # Build subgraph response
        subgraph_response = SubGraphPath(
            nodes=subgraph.get("nodes", []),
            edges=subgraph.get("edges", []),
        )

        total_time_ms = (time.time() - pipeline_start) * 1000

        logger.info(
            f"GraphRAG pipeline complete: confidence={confidence:.2f}, "
            f"citations={len(citations)}, total_time={total_time_ms:.0f}ms",
            extra={"request_id": "graphrag"},
        )

        return QueryResponse(
            question=question,
            answer=answer_text,
            confidence=confidence,
            citations=citations,
            sources=sources,
            subgraph=subgraph_response,
            retrieval_stats=RetrievalStats(
                node_count=len(entity_results),
                chunk_count=len(chunk_results),
                relationship_count=len(subgraph.get("edges", [])),
                retrieval_time_ms=round(retrieval_time_ms, 2),
                llm_time_ms=round(llm_time_ms, 2),
                total_time_ms=round(total_time_ms, 2),
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_graph_facts(
        self,
        entity_results: List[Dict[str, Any]],
        subgraph: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Combine entity results and subgraph into a flat list of facts for prompting."""
        facts: List[Dict[str, Any]] = []

        # Add entity nodes
        for entity in entity_results:
            facts.append({
                "name": entity.get("name", ""),
                "type": entity.get("type", "Entity"),
                "description": entity.get("description", ""),
            })

        # Add subgraph nodes (dedup by name)
        seen_names = {f.get("name", "").lower() for f in facts}
        for node in subgraph.get("nodes", []):
            name = node.get("name", "")
            if name.lower() not in seen_names:
                seen_names.add(name.lower())
                facts.append(node)

        # Add edges as relationship facts
        for edge in subgraph.get("edges", []):
            facts.append(edge)

        return facts

    def _build_citations(
        self,
        chunk_results: List[Dict[str, Any]],
        cited_chunk_ids: List[str],
    ) -> List[Citation]:
        """Map LLM-cited chunk IDs back to full Citation objects."""
        # Create a lookup by chunk_id
        chunk_lookup = {c.get("chunk_id", ""): c for c in chunk_results}

        citations = []

        if cited_chunk_ids:
            # Use only LLM-cited chunks
            for cid in cited_chunk_ids:
                chunk = chunk_lookup.get(cid)
                if chunk:
                    citations.append(self._chunk_to_citation(chunk, score=chunk.get("score")))
        else:
            # LLM didn't cite specific chunks — use all retrieved chunks
            for chunk in chunk_results:
                citations.append(self._chunk_to_citation(chunk, score=chunk.get("score")))

        return citations

    @staticmethod
    def _chunk_to_citation(chunk: Dict[str, Any], score: Optional[float] = None) -> Citation:
        """Convert a raw chunk dict to a Citation schema."""
        return Citation(
            chunk_id=chunk.get("chunk_id", "unknown"),
            document_id=chunk.get("document_id", "unknown"),
            document_name=chunk.get("document_name", "Unknown Document"),
            snippet=chunk.get("text", "")[:500],  # Truncate long snippets
            confidence_score=min(max(score or 0.5, 0.0), 1.0),
            page_number=chunk.get("page_number"),
            section_title=chunk.get("section_title"),
        )
