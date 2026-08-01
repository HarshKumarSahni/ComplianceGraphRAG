"""Tests for the GraphRAG query engine pipeline.

Covers:
- Unit tests for QueryPromptBuilder
- Unit tests for EntityExtractor (heuristic mode)
- Integration tests for GraphRAGQueryEngine with mocked dependencies
- API tests for POST /api/v1/query
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.schemas.rag import QueryRequest, QueryResponse, RetrievalStats
from app.services.graphrag.query_prompt_builder import QueryPromptBuilder
from app.services.graphrag.entity_extractor import EntityExtractor
from app.services.graphrag.query_engine import GraphRAGQueryEngine
from app.repositories.graph_reader_repository import GraphReaderRepository


# ======================================================================
# Fixtures
# ======================================================================

@pytest.fixture
def settings():
    """Provide a test Settings instance with mock values."""
    return Settings(
        NEO4J_URI="",
        NEO4J_USERNAME="neo4j",
        NEO4J_PASSWORD="",
        NEO4J_DATABASE="neo4j",
        OPENROUTER_API_KEY="",
        OPENROUTER_PRIMARY_MODEL="anthropic/claude-sonnet-5",
        EMBEDDING_MODEL="BAAI/bge-small-en-v1.5",
    )


@pytest.fixture
def mock_graph_reader():
    """Provide a mocked GraphReaderRepository."""
    reader = MagicMock(spec=GraphReaderRepository)
    reader.search_entities_by_embedding.return_value = []
    reader.search_entities_by_name.return_value = [
        {"name": "GDPR Article 32", "type": "Regulation", "description": "Data protection security measures"},
        {"name": "Customer Data Bucket", "type": "Storage", "description": "S3 bucket for PII"},
    ]
    reader.get_entity_neighborhood.return_value = {
        "nodes": [
            {"name": "GDPR Article 32", "type": "Regulation", "description": "Data protection security measures"},
            {"name": "Customer Data Bucket", "type": "Storage", "description": "S3 bucket for PII"},
        ],
        "edges": [
            {"source": "GDPR Article 32", "target": "Customer Data Bucket", "type": "GOVERNS", "confidence": 0.95},
        ],
    }
    reader.search_chunks_by_embedding.return_value = []
    reader.search_chunks_by_keywords.return_value = [
        {
            "chunk_id": "chunk-001",
            "document_id": "doc-001",
            "document_name": "GDPR_Policy.pdf",
            "text": "Article 32 requires appropriate technical and organizational measures to ensure data security.",
            "page_number": 5,
            "section_title": "Security Measures",
        },
    ]
    reader.get_graph_stats.return_value = {"entity_count": 10, "relationship_count": 15, "chunk_count": 20}
    return reader


@pytest.fixture
def mock_openrouter():
    """Provide a mocked OpenRouterClient."""
    client = MagicMock()
    client.api_key = ""  # No API key → heuristic entity extraction
    client.generate_json = AsyncMock(return_value={
        "answer": "GDPR Article 32 requires technical and organizational measures for data security.",
        "confidence": 0.92,
        "cited_chunks": ["chunk-001"],
    })
    return client


@pytest.fixture
def query_engine(mock_graph_reader, mock_openrouter, settings):
    """Provide a GraphRAGQueryEngine with mocked dependencies."""
    engine = GraphRAGQueryEngine(
        graph_reader=mock_graph_reader,
        openrouter_client=mock_openrouter,
        settings=settings,
    )
    # Mock the embedding service to avoid loading the model
    engine.embedding_service = MagicMock()
    engine.embedding_service.encode.return_value = [0.1] * 384
    return engine


# ======================================================================
# QueryPromptBuilder tests
# ======================================================================

class TestQueryPromptBuilder:
    def test_system_prompt_contains_rules(self):
        prompt = QueryPromptBuilder.get_system_prompt()
        assert "GraphGuard AI" in prompt
        assert "ONLY" in prompt
        assert "cited_chunks" in prompt
        assert "confidence" in prompt

    def test_user_prompt_with_facts_and_chunks(self):
        graph_facts = [
            {"name": "GDPR", "type": "Regulation", "description": "EU data protection regulation"},
            {"source": "GDPR", "target": "S3 Bucket", "type": "GOVERNS"},
        ]
        chunks = [
            {"chunk_id": "c1", "document_name": "policy.pdf", "text": "GDPR governs data storage.", "page_number": 1},
        ]

        prompt = QueryPromptBuilder.build_user_prompt("What does GDPR govern?", graph_facts, chunks)

        assert "QUESTION:" in prompt
        assert "GRAPH FACTS:" in prompt
        assert "DOCUMENT CHUNKS:" in prompt
        assert "GDPR" in prompt
        assert "c1" in prompt
        assert "policy.pdf" in prompt

    def test_user_prompt_empty_evidence(self):
        prompt = QueryPromptBuilder.build_user_prompt("Test question?", [], [])
        assert "No relevant graph facts" in prompt
        assert "No relevant document chunks" in prompt

    def test_format_graph_facts_edges(self):
        facts = [{"source": "A", "target": "B", "type": "USES", "confidence": 0.9}]
        text = QueryPromptBuilder._format_graph_facts(facts)
        assert "A --[USES]--> B" in text
        assert "0.9" in text

    def test_format_graph_facts_nodes(self):
        facts = [{"name": "HIPAA", "type": "Regulation", "description": "Healthcare privacy"}]
        text = QueryPromptBuilder._format_graph_facts(facts)
        assert "[Regulation] HIPAA" in text
        assert "Healthcare privacy" in text


# ======================================================================
# EntityExtractor tests (heuristic mode)
# ======================================================================

class TestEntityExtractor:
    @pytest.fixture
    def extractor(self, mock_openrouter):
        mock_openrouter.api_key = ""  # Force heuristic mode
        return EntityExtractor(mock_openrouter)

    def test_heuristic_extracts_capitalized_phrases(self, extractor):
        result = extractor._extract_heuristic("What does GDPR Article 32 require for Cloud Storage?")
        assert any("GDPR" in e for e in result["entities"])
        assert any("Cloud" in e or "Storage" in e for e in result["entities"])

    def test_heuristic_extracts_keywords(self, extractor):
        result = extractor._extract_heuristic("What are the compliance requirements for data encryption?")
        assert "compliance" in result["keywords"]
        assert "requirements" in result["keywords"]
        assert "encryption" in result["keywords"]

    def test_heuristic_removes_stop_words(self, extractor):
        result = extractor._extract_heuristic("What is the policy for data storage?")
        assert "the" not in result["keywords"]
        assert "for" not in result["keywords"]
        assert "is" not in result["keywords"]

    def test_heuristic_deduplicates(self, extractor):
        result = extractor._extract_heuristic("GDPR GDPR compliance compliance")
        # Should not have duplicate keywords
        assert len(result["keywords"]) == len(set(result["keywords"]))

    @pytest.mark.asyncio
    async def test_extract_falls_back_to_heuristic(self, extractor):
        result = await extractor.extract("What does GDPR require?")
        # Should return heuristic results since api_key is empty
        assert isinstance(result, dict)
        assert "entities" in result
        assert "keywords" in result


# ======================================================================
# GraphRAGQueryEngine integration tests
# ======================================================================

class TestGraphRAGQueryEngine:
    @pytest.mark.asyncio
    async def test_execute_query_returns_valid_response(self, query_engine):
        request = QueryRequest(question="What does GDPR Article 32 require?")
        response = await query_engine.execute_query(request)

        assert isinstance(response, QueryResponse)
        assert response.question == "What does GDPR Article 32 require?"
        assert response.answer != ""
        assert 0.0 <= response.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_execute_query_returns_citations(self, query_engine):
        request = QueryRequest(question="What does GDPR Article 32 require?")
        response = await query_engine.execute_query(request)

        assert len(response.citations) > 0
        citation = response.citations[0]
        assert citation.chunk_id == "chunk-001"
        assert citation.document_name == "GDPR_Policy.pdf"

    @pytest.mark.asyncio
    async def test_execute_query_returns_sources(self, query_engine):
        request = QueryRequest(question="What does GDPR Article 32 require?")
        response = await query_engine.execute_query(request)

        assert "GDPR_Policy.pdf" in response.sources

    @pytest.mark.asyncio
    async def test_execute_query_returns_retrieval_stats(self, query_engine):
        request = QueryRequest(question="What does GDPR Article 32 require?")
        response = await query_engine.execute_query(request)

        stats = response.retrieval_stats
        assert isinstance(stats, RetrievalStats)
        assert stats.total_time_ms > 0
        assert stats.node_count >= 0
        assert stats.chunk_count >= 0

    @pytest.mark.asyncio
    async def test_execute_query_returns_subgraph(self, query_engine):
        request = QueryRequest(question="What does GDPR Article 32 require?")
        response = await query_engine.execute_query(request)

        assert len(response.subgraph.nodes) > 0
        assert len(response.subgraph.edges) > 0

    @pytest.mark.asyncio
    async def test_empty_graph_returns_no_data_response(self, query_engine, mock_graph_reader):
        # Override mocks to return empty results
        mock_graph_reader.search_entities_by_name.return_value = []
        mock_graph_reader.search_entities_by_embedding.return_value = []
        mock_graph_reader.get_entity_neighborhood.return_value = {"nodes": [], "edges": []}
        mock_graph_reader.search_chunks_by_keywords.return_value = []
        mock_graph_reader.search_chunks_by_embedding.return_value = []

        request = QueryRequest(question="Tell me about quantum computing")
        response = await query_engine.execute_query(request)

        assert response.confidence == 0.0
        assert "does not contain" in response.answer.lower()

    @pytest.mark.asyncio
    async def test_llm_failure_raises_external_api_error(self, query_engine, mock_openrouter):
        from app.core.exceptions import ExternalAPIError

        mock_openrouter.generate_json = AsyncMock(side_effect=Exception("API timeout"))
        request = QueryRequest(question="What does GDPR require?")

        with pytest.raises(ExternalAPIError):
            await query_engine.execute_query(request)


# ======================================================================
# API endpoint tests
# ======================================================================

class TestQueryAPI:
    @pytest.fixture
    def client(self):
        from app.main import create_application
        app = create_application()
        return TestClient(app)

    def test_query_endpoint_rejects_empty_question(self, client):
        response = client.post("/api/v1/query", json={"question": ""})
        assert response.status_code == 422

    def test_query_endpoint_rejects_short_question(self, client):
        response = client.post("/api/v1/query", json={"question": "ab"})
        assert response.status_code == 422

    def test_query_request_schema_validation(self):
        # Valid request
        req = QueryRequest(question="What is GDPR?")
        assert req.question == "What is GDPR?"
        assert req.top_k == 5

        # Custom top_k
        req2 = QueryRequest(question="Tell me about compliance", top_k=10)
        assert req2.top_k == 10

    def test_query_request_rejects_invalid_top_k(self):
        with pytest.raises(Exception):
            QueryRequest(question="Test", top_k=0)

        with pytest.raises(Exception):
            QueryRequest(question="Test", top_k=25)
