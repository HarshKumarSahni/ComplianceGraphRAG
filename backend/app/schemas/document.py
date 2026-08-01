from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from app.utils.constants import FileType, DocumentStatus

class DocumentMetadata(BaseModel):
    document_id: str
    original_filename: str
    cloudinary_url: str
    public_id: str
    upload_timestamp: datetime
    file_size_bytes: int
    file_type: FileType
    mime_type: str
    status: DocumentStatus = DocumentStatus.UPLOADED
    error_message: Optional[str] = None

class FileUploadStatus(BaseModel):
    filename: str
    success: bool
    metadata: Optional[DocumentMetadata] = None
    error: Optional[str] = None

class MultiUploadResponse(BaseModel):
    total_files: int
    successful_uploads: int
    failed_uploads: int
    files: List[FileUploadStatus]
