from typing import List
from fastapi import APIRouter, UploadFile, File, Depends
from app.schemas.response import ApiResponse
from app.schemas.document import MultiUploadResponse
from app.routers.documents import upload_documents, get_upload_service
from app.services.upload_service import UploadService

# Alias /upload to /documents/upload for direct API route compatibility
router = APIRouter(tags=["Upload Alias"])

@router.post("/upload", response_model=ApiResponse[MultiUploadResponse], include_in_schema=True)
async def upload_alias(
    files: List[UploadFile] = File(...),
    upload_service: UploadService = Depends(get_upload_service)
):
    return await upload_documents(files=files, upload_service=upload_service)

