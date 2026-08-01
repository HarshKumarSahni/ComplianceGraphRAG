from abc import ABC, abstractmethod
from app.schemas.unified_document import UnifiedDocument

class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_content: bytes, document_id: str, filename: str) -> UnifiedDocument:
        pass
