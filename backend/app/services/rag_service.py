from app.services.interfaces import IGraphRAGService
from app.schemas.rag import QueryRequest, QueryResponse
from app.services.graphrag.query_engine import GraphRAGQueryEngine


class GraphRAGService(IGraphRAGService):
    """Thin wrapper that delegates to GraphRAGQueryEngine.

    Preserves the IGraphRAGService interface contract so existing
    consumers (routers, tests) continue to work unchanged.
    """

    def __init__(self, query_engine: GraphRAGQueryEngine):
        self.engine = query_engine

    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        return await self.engine.execute_query(request)
