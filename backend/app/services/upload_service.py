import uuid
import os
from typing import List, Optional
from fastapi import UploadFile

from app.core.config import Settings
from app.core.logger import logger
from app.core.exceptions import DocumentProcessingError
from app.schemas.document import DocumentMetadata, FileUploadStatus, MultiUploadResponse, DocumentListResponse
from app.utils.constants import FileType, DocumentStatus, ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES
from app.utils.helpers import utc_now, sanitize_filename
from app.services.cloudinary_service import CloudinaryService
from app.repositories.document_repository import IDocumentRepository

class UploadService:
    def __init__(self, doc_repo: IDocumentRepository, cloudinary_service: CloudinaryService, settings: Settings):
        self.doc_repo = doc_repo
        self.cloudinary_service = cloudinary_service
        self.max_upload_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    def validate_file(self, file: UploadFile, content: bytes) -> FileType:
        if not file.filename:
            raise DocumentProcessingError("Filename cannot be empty")

        filename = sanitize_filename(file.filename)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        # 1. Validate File Extension
        matched_type: Optional[FileType] = None
        for ftype, valid_exts in ALLOWED_EXTENSIONS.items():
            if ext in valid_exts:
                matched_type = ftype
                break

        if not matched_type:
            raise DocumentProcessingError(
                f"File extension '{ext}' is not supported. Allowed extensions: .pdf, .csv, .mp3"
            )

        # 2. Validate File Size
        file_size = len(content)
        if file_size == 0:
            raise DocumentProcessingError(f"File '{filename}' is empty")
        
        if file_size > self.max_upload_size_bytes:
            raise DocumentProcessingError(
                f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit ({self.max_upload_size_bytes / (1024*1024):.2f} MB)"
            )

        return matched_type

    async def process_single_file(self, file: UploadFile, user_id: Optional[str] = None) -> FileUploadStatus:
        filename = sanitize_filename(file.filename or "unnamed_file")
        try:
            content = await file.read()
            file_type = self.validate_file(file, content)

            document_id = str(uuid.uuid4())
            unique_remote_filename = f"{document_id}_{filename}"

            resource_type = "video" if file_type == FileType.AUDIO else "raw"

            cloudinary_resp = await self.cloudinary_service.upload_file_content(
                file_content=content,
                filename=unique_remote_filename,
                resource_type=resource_type
            )

            metadata = DocumentMetadata(
                document_id=document_id,
                original_filename=filename,
                cloudinary_url=cloudinary_resp.get("secure_url", ""),
                public_id=cloudinary_resp.get("public_id", f"graphguard/{unique_remote_filename}"),
                upload_timestamp=utc_now(),
                file_size_bytes=len(content),
                file_type=file_type,
                mime_type=file.content_type or "application/octet-stream",
                status=DocumentStatus.UPLOADED,
                user_id=user_id
            )

            await self.doc_repo.create_document(metadata)
            logger.info(f"File upload completed successfully for: {filename} (ID: {document_id}, User: {user_id})")

            return FileUploadStatus(
                filename=filename,
                success=True,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Upload failed for file '{filename}': {str(e)}")
            return FileUploadStatus(
                filename=filename,
                success=False,
                error=str(e)
            )

    async def process_multiple_uploads(self, files: List[UploadFile], user_id: Optional[str] = None) -> MultiUploadResponse:
        statuses: List[FileUploadStatus] = []
        successful_count = 0
        failed_count = 0

        for file in files:
            status = await self.process_single_file(file, user_id=user_id)
            statuses.append(status)
            if status.success:
                successful_count += 1
            else:
                failed_count += 1

        return MultiUploadResponse(
            total_files=len(files),
            successful_uploads=successful_count,
            failed_uploads=failed_count,
            files=statuses
        )

    async def list_documents(self, user_id: Optional[str] = None) -> DocumentListResponse:
        all_docs = await self.doc_repo.list_documents()
        if user_id:
            docs = [d for d in all_docs if d.user_id == user_id]
        else:
            docs = all_docs
        return DocumentListResponse(documents=docs, total=len(docs))
