import os
import json
from typing import List, Optional
from app.schemas.document import DocumentMetadata
from app.repositories.document_repository import IDocumentRepository
from app.core.logger import logger

class JSONDocumentRepository(IDocumentRepository):
    def __init__(self, storage_file: str = "documents_store.json"):
        self.storage_file = storage_file
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        if not os.path.exists(self.storage_file):
            with open(self.storage_file, "w") as f:
                json.dump({}, f)

    def _read_data(self) -> dict:
        try:
            with open(self.storage_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read from JSON storage file {self.storage_file}: {str(e)}")
            return {}

    def _write_data(self, data: dict):
        try:
            with open(self.storage_file, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to write to JSON storage file {self.storage_file}: {str(e)}")

    async def create_document(self, document: DocumentMetadata) -> DocumentMetadata:
        data = self._read_data()
        data[document.document_id] = document.model_dump(mode="json")
        self._write_data(data)
        logger.info(f"Persisted document metadata to JSON repository: {document.document_id}")
        return document

    async def get_document_by_id(self, document_id: str) -> Optional[DocumentMetadata]:
        data = self._read_data()
        doc_dict = data.get(document_id)
        if doc_dict:
            return DocumentMetadata(**doc_dict)
        return None

    async def list_documents(self) -> List[DocumentMetadata]:
        data = self._read_data()
        return [DocumentMetadata(**doc) for doc in data.values()]

    async def delete_user_documents(self, user_id: str) -> List[DocumentMetadata]:
        """Delete all document records belonging to user_id. Returns the deleted docs so callers can clean Cloudinary."""
        data = self._read_data()
        to_keep = {}
        deleted = []
        for doc_id, doc_dict in data.items():
            if doc_dict.get("user_id") == user_id:
                try:
                    deleted.append(DocumentMetadata(**doc_dict))
                except Exception:
                    pass
            else:
                to_keep[doc_id] = doc_dict
        self._write_data(to_keep)
        logger.info(f"Deleted {len(deleted)} document records for user {user_id}")
        return deleted

