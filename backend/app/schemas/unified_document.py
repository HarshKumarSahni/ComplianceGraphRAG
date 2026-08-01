from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.utils.constants import FileType

class Paragraph(BaseModel):
    paragraph_index: int
    text: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    character_count: int

class Section(BaseModel):
    section_index: int
    title: str
    paragraphs: List[Paragraph] = Field(default_factory=list)

class Page(BaseModel):
    page_number: int
    text: str
    sections: List[Section] = Field(default_factory=list)

class UnifiedDocument(BaseModel):
    document_id: str
    original_filename: str
    file_type: FileType
    raw_text: str
    normalized_text: str
    pages: List[Page] = Field(default_factory=list)
    sections: List[Section] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    character_count: int
    estimated_tokens: int

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    character_count: int
    estimated_tokens: int

class ProcessingResult(BaseModel):
    document_id: str
    status: str
    page_count: int
    chunk_count: int
    character_count: int
    estimated_tokens: int
    chunks: List[Chunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
