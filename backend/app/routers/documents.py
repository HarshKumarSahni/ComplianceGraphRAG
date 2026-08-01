from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from app.schemas.response import ApiResponse
from app.schemas.document import MultiUploadResponse, DocumentListResponse
from app.services.upload_service import UploadService
from app.services.cloudinary_service import CloudinaryService
from app.repositories.json_document_repository import JSONDocumentRepository
from app.core.config import get_settings, Settings

router = APIRouter(prefix="/documents", tags=["Documents"])

_json_repo = JSONDocumentRepository()

def get_upload_service(settings: Settings = Depends(get_settings)) -> UploadService:
    cloudinary_service = CloudinaryService(settings)
    return UploadService(
        doc_repo=_json_repo,
        cloudinary_service=cloudinary_service,
        settings=settings
    )

@router.post("/upload", response_model=ApiResponse[MultiUploadResponse], status_code=status.HTTP_207_MULTI_STATUS)
async def upload_documents(
    files: List[UploadFile] = File(...),
    upload_service: UploadService = Depends(get_upload_service)
):
    if not files or len(files) == 0:
        raise HTTPException(status_code=400, detail="At least one file must be provided")

    result = await upload_service.process_multiple_uploads(files)
    
    status_code = status.HTTP_201_CREATED if result.failed_uploads == 0 else status.HTTP_207_MULTI_STATUS

    return ApiResponse(
        success=result.successful_uploads > 0,
        message=f"Uploaded {result.successful_uploads}/{result.total_files} files successfully",
        data=result
    )

@router.get("", response_model=ApiResponse[DocumentListResponse])
async def list_documents(
    upload_service: UploadService = Depends(get_upload_service)
):
    result = await upload_service.list_documents()
    return ApiResponse(
        success=True,
        message="Documents retrieved successfully",
        data=result
    )
