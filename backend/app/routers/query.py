from fastapi import APIRouter, Depends, status
from app.schemas.response import ApiResponse
from app.schemas.rag import QueryRequest, QueryResponse
from app.services.rag_service import GraphRAGService

router = APIRouter(tags=["GraphRAG"])

def get_rag_service() -> GraphRAGService:
    return GraphRAGService()

@router.post("/query", response_model=ApiResponse[QueryResponse], status_code=status.HTTP_200_OK)
async def query_compliance_graph(
    request: QueryRequest,
    rag_service: GraphRAGService = Depends(get_rag_service)
):
    result = await rag_service.execute_query(request)
    return ApiResponse(
        success=True,
        message="Query processed successfully",
        data=result
    )
