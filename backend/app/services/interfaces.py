from abc import ABC, abstractmethod
from fastapi import UploadFile
from app.schemas.document import UploadResponse, DocumentListResponse
from app.schemas.rag import QueryRequest, QueryResponse

class ICloudinaryService(ABC):
    @abstractmethod
    async def upload_file(self, file: UploadFile) -> str:
        pass

class IParserService(ABC):
    @abstractmethod
    async def parse(self, file: UploadFile, file_type: str) -> str:
        pass

class IEntityExtractionService(ABC):
    @abstractmethod
    async def extract_entities(self, text: str) -> list:
        pass

class IRelationshipExtractionService(ABC):
    @abstractmethod
    async def extract_relationships(self, text: str, entities: list) -> list:
        pass

class IGraphService(ABC):
    @abstractmethod
    async def build_graph(self, nodes: list, edges: list) -> bool:
        pass

class IUploadService(ABC):
    @abstractmethod
    async def process_upload(self, file: UploadFile) -> UploadResponse:
        pass

    @abstractmethod
    async def list_documents(self) -> DocumentListResponse:
        pass

class IGraphRAGService(ABC):
    @abstractmethod
    async def execute_query(self, request: QueryRequest) -> QueryResponse:
        pass
