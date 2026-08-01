from fastapi import APIRouter, Depends, status
from app.schemas.response import ApiResponse
from app.schemas.unified_document import ProcessingResult
from app.services.processing.document_processor import DocumentProcessor
from app.services.cloudinary_service import CloudinaryService
from app.routers.documents import _json_repo
from app.core.config import get_settings, Settings

router = APIRouter(prefix="/documents", tags=["Processing Pipeline"])


def get_document_processor(settings: Settings = Depends(get_settings)) -> DocumentProcessor:
    cloudinary_service = CloudinaryService(settings)
    return DocumentProcessor(doc_repo=_json_repo, cloudinary_service=cloudinary_service)


@router.post("/process/{document_id}", response_model=ApiResponse[ProcessingResult], status_code=status.HTTP_200_OK)
async def process_document(
    document_id: str,
    processor: DocumentProcessor = Depends(get_document_processor),
):
    result = await processor.process(document_id)
    return ApiResponse(
        success=True,
        message=f"Document processed successfully. Status: {result.status}",
        data=result,
    )
