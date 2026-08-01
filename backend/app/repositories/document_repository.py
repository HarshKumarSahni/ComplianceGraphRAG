from abc import ABC, abstractmethod
from typing import List, Optional
from app.schemas.document import DocumentMetadata

class IDocumentRepository(ABC):
    @abstractmethod
    async def create_document(self, document: DocumentMetadata) -> DocumentMetadata:
        pass

    @abstractmethod
    async def get_document_by_id(self, document_id: str) -> Optional[DocumentMetadata]:
        pass

    @abstractmethod
    async def list_documents(self) -> List[DocumentMetadata]:
        pass

class DocumentRepository(IDocumentRepository):
    def __init__(self):
        self._in_memory_store = {}

    async def create_document(self, document: DocumentMetadata) -> DocumentMetadata:
        self._in_memory_store[document.document_id] = document
        return document

    async def get_document_by_id(self, document_id: str) -> Optional[DocumentMetadata]:
        return self._in_memory_store.get(document_id)

    async def list_documents(self) -> List[DocumentMetadata]:
        return list(self._in_memory_store.values())
