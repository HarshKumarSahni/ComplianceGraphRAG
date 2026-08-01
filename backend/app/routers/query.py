from fastapi import APIRouter, Depends, status
from app.core.config import get_settings, Settings
from app.dependencies.clients import Neo4jClient
from app.repositories.graph_reader_repository import GraphReaderRepository
from app.services.extraction.openrouter_client import OpenRouterClient
from app.services.graphrag.query_engine import GraphRAGQueryEngine
from app.services.rag_service import GraphRAGService
from app.schemas.response import ApiResponse
from app.schemas.rag import QueryRequest, QueryResponse

router = APIRouter(tags=["GraphRAG"])


def get_rag_service() -> GraphRAGService:
    """Wire the full GraphRAG dependency chain."""
    settings = get_settings()

    # Neo4j client
    neo4j_client = Neo4jClient(settings)
    neo4j_client.connect()

    # OpenRouter client (extraction-layer client with retries)
    openrouter_client = OpenRouterClient(settings)

    # Graph reader repository
    graph_reader = GraphReaderRepository(neo4j_client)

    # Query engine
    engine = GraphRAGQueryEngine(
        graph_reader=graph_reader,
        openrouter_client=openrouter_client,
        settings=settings,
    )

    return GraphRAGService(engine)


@router.post(
    "/query",
    response_model=ApiResponse[QueryResponse],
    status_code=status.HTTP_200_OK,
    summary="Query the compliance knowledge graph",
    description="Accepts a natural language question and returns a grounded answer with citations from the knowledge graph.",
)
async def query_compliance_graph(
    request: QueryRequest,
    rag_service: GraphRAGService = Depends(get_rag_service),
):
    result = await rag_service.execute_query(request)
    return ApiResponse(
        success=True,
        message="Query processed successfully",
        data=result,
    )
