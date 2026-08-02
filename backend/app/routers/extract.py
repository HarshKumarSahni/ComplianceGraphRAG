from fastapi import APIRouter, Depends, status, HTTPException, Query
from app.schemas.response import ApiResponse
from app.schemas.knowledge_extraction import ExtractionPipelineResult
from app.services.extraction.knowledge_extraction_pipeline import KnowledgeExtractionPipeline
from app.services.processing.document_processor import DocumentProcessor
from app.services.cloudinary_service import CloudinaryService
from app.routers.documents import _json_repo
from app.core.config import get_settings, Settings
from app.dependencies.auth_deps import get_current_user
from app.models.user import User
from app.utils.constants import DocumentStatus

router = APIRouter(prefix="/documents", tags=["AI Knowledge Extraction"])


def get_extraction_pipeline(settings: Settings = Depends(get_settings)) -> KnowledgeExtractionPipeline:
    return KnowledgeExtractionPipeline(doc_repo=_json_repo, settings=settings)


def get_document_processor(settings: Settings = Depends(get_settings)) -> DocumentProcessor:
    cloudinary_service = CloudinaryService(settings)
    return DocumentProcessor(doc_repo=_json_repo, cloudinary_service=cloudinary_service)


@router.post("/extract/{document_id}", response_model=ApiResponse[ExtractionPipelineResult], status_code=status.HTTP_200_OK)
async def extract_knowledge(
    document_id: str,
    force: bool = Query(default=False, description="Set to true to re-extract even if already completed."),
    pipeline: KnowledgeExtractionPipeline = Depends(get_extraction_pipeline),
    processor: DocumentProcessor = Depends(get_document_processor),
    current_user: User = Depends(get_current_user),
):
    """
    Run entity and relationship extraction for a document.

    Idempotency guard: if the document is already being extracted or already
    completed, return 409 Conflict unless `?force=true` is passed.
    """
    # --- Idempotency / status guard ---
    doc_meta = await _json_repo.get_document_by_id(document_id)
    if doc_meta:
        blocked_statuses = {
            DocumentStatus.ENTITY_EXTRACTION,
            DocumentStatus.RELATIONSHIP_EXTRACTION,
            DocumentStatus.VALIDATION,
            DocumentStatus.READY_FOR_GRAPH_BUILDING,
            DocumentStatus.GRAPH_BUILT,
        }
        if doc_meta.status in blocked_statuses and not force:
            return ApiResponse(
                success=True,
                message=(
                    f"Document '{document_id}' is already in status '{doc_meta.status.value}'. "
                    "Extraction is not re-run. Use ?force=true to override."
                ),
                data=None,
            )

    # 1. Ensure document has been processed into chunks
    proc_result = await processor.process(document_id)
    if not proc_result.chunks:
        raise HTTPException(status_code=400, detail="Document produced no chunks for entity extraction.")

    # 2. Execute extraction pipeline on extracted chunks
    result = await pipeline.process_chunks(document_id, proc_result.chunks, user_id=str(current_user.id))

    return ApiResponse(
        success=True,
        message=f"Knowledge extraction completed. Extracted {result.entity_count} entities, {result.relationship_count} relationships.",
        data=result,
    )
