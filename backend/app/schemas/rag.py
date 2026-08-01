from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RetrievalStats(BaseModel):
    """Metrics from the GraphRAG retrieval pipeline."""
    node_count: int = 0
    chunk_count: int = 0
    relationship_count: int = 0
    retrieval_time_ms: float = 0.0
    llm_time_ms: float = 0.0
    total_time_ms: float = 0.0


class Citation(BaseModel):
    """A single piece of evidence supporting the answer."""
    chunk_id: str
    document_id: str
    document_name: str
    snippet: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    page_number: Optional[int] = None
    section_title: Optional[str] = None


class SubGraphPath(BaseModel):
    """A subgraph of nodes and edges related to the query."""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class QueryRequest(BaseModel):
    """Incoming compliance question."""
    question: str = Field(..., min_length=3, description="Natural language compliance question")
    top_k: int = Field(default=5, ge=1, le=20, description="Max chunks/nodes to retrieve")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Optional retrieval filters")


class QueryResponse(BaseModel):
    """Complete GraphRAG answer with citations and provenance."""
    question: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    citations: List[Citation] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list, description="Unique source document names")
    subgraph: SubGraphPath = Field(default_factory=SubGraphPath)
    retrieval_stats: RetrievalStats = Field(default_factory=RetrievalStats)
