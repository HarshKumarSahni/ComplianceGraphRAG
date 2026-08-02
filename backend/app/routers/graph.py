from fastapi import APIRouter, Depends, status, HTTPException
from app.schemas.response import ApiResponse
from app.schemas.knowledge_extraction import ExtractionPipelineResult
from app.services.extraction.knowledge_extraction_pipeline import KnowledgeExtractionPipeline
from app.services.processing.document_processor import DocumentProcessor
from app.services.cloudinary_service import CloudinaryService
from app.repositories.graph_repository import GraphRepository
from app.dependencies.clients import Neo4jClient
from app.routers.documents import _json_repo
from app.core.config import get_settings, Settings
from app.dependencies.auth_deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/graph", tags=["Graph Explorer & Builder"])


def get_graph_repo(settings: Settings = Depends(get_settings)) -> GraphRepository:
    client = Neo4jClient(settings)
    client.connect()
    return GraphRepository(client)


def get_extraction_pipeline(settings: Settings = Depends(get_settings)) -> KnowledgeExtractionPipeline:
    return KnowledgeExtractionPipeline(doc_repo=_json_repo, settings=settings)


def get_document_processor(settings: Settings = Depends(get_settings)) -> DocumentProcessor:
    cloudinary_service = CloudinaryService(settings)
    return DocumentProcessor(doc_repo=_json_repo, cloudinary_service=cloudinary_service)


@router.get("", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
async def get_graph(
    graph_repo: GraphRepository = Depends(get_graph_repo),
    current_user: User = Depends(get_current_user),
):
    graph_data = await graph_repo.get_graph(user_id=str(current_user.id))
    return ApiResponse(
        success=True,
        message="Knowledge Graph retrieved successfully",
        data=graph_data
    )


@router.get("/stats", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
async def get_graph_stats(
    graph_repo: GraphRepository = Depends(get_graph_repo),
    current_user: User = Depends(get_current_user),
):
    user_id = str(current_user.id)
    graph_data = await graph_repo.get_graph(user_id=user_id)
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    chunk_count = await graph_repo.get_chunk_count(user_id=user_id)
    return ApiResponse(
        success=True,
        message="Graph stats retrieved successfully",
        data={
            "entity_count": len(nodes),
            "relationship_count": len(edges),
            "chunk_count": chunk_count,
        }
    )


@router.delete("", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
async def clear_graph(
    graph_repo: GraphRepository = Depends(get_graph_repo),
    current_user: User = Depends(get_current_user),
):
    cleared = await graph_repo.clear_graph(user_id=str(current_user.id))
    return ApiResponse(
        success=cleared,
        message="Knowledge Graph reset successfully" if cleared else "Failed to reset Knowledge Graph",
        data={"cleared": cleared}
    )


@router.post("/build/{document_id}", response_model=ApiResponse[ExtractionPipelineResult], status_code=status.HTTP_200_OK)
async def build_graph_for_document(
    document_id: str,
    pipeline: KnowledgeExtractionPipeline = Depends(get_extraction_pipeline),
    processor: DocumentProcessor = Depends(get_document_processor),
    current_user: User = Depends(get_current_user),
):
    proc_result = await processor.process(document_id)
    if not proc_result.chunks:
        raise HTTPException(status_code=400, detail="Document produced no chunks for graph building.")

    result = await pipeline.process_chunks(document_id, proc_result.chunks, user_id=str(current_user.id))
    return ApiResponse(
        success=True,
        message=f"Graph building completed for document ID {document_id}.",
        data=result,
    )
