from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Citation(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    snippet: str
    confidence_score: float

class SubGraphPath(BaseModel):
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Compliance query text")
    top_k: int = Field(default=5, ge=1, le=20)

class QueryResponse(BaseModel):
    query: str
    answer: str
    confidence_score: float
    citations: List[Citation] = Field(default_factory=list)
    subgraph: SubGraphPath = Field(default_factory=SubGraphPath)
