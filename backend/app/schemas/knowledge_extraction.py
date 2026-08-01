from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

class ExtractedEntity(BaseModel):
    name: str = Field(..., description="Canonical entity name")
    type: str = Field(..., description="Entity type: Policy, Regulation, Application, Cloud Service, Storage, Data Asset, Compliance Rule, Risk, Department, Employee, Meeting, Audit, Document")
    description: str = Field(default="", description="Detailed description extracted from context")
    aliases: List[str] = Field(default_factory=list, description="Known alternate names or codes")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("name", mode="after")
    def sanitize_name(cls, v):
        return v.strip()

class ExtractedRelationship(BaseModel):
    source_entity: str = Field(..., description="Source entity name")
    relationship_type: str = Field(..., description="Relationship verb: STORES, USES, BELONGS_TO, VIOLATES, GOVERNS, REFERENCES, OWNS, CONNECTED_TO, DEPENDS_ON")
    target_entity: str = Field(..., description="Target entity name")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: str = Field(default="", description="Verbatim textual evidence supporting the relationship")

class ExtractionLLMOutput(BaseModel):
    entities: List[ExtractedEntity] = Field(default_factory=list)
    relationships: List[ExtractedRelationship] = Field(default_factory=list)

class KnowledgeObject(BaseModel):
    document_id: str
    chunk_id: str
    page_number: Optional[int] = 1
    chunk_text: str
    entities: List[ExtractedEntity] = Field(default_factory=list)
    relationships: List[ExtractedRelationship] = Field(default_factory=list)
    confidence_score: float = 1.0
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_timestamp: datetime

class ExtractionPipelineResult(BaseModel):
    document_id: str
    status: str
    chunk_count: int
    entity_count: int
    relationship_count: int
    validation_errors: int = 0
    average_confidence: float = 1.0
    processing_time_seconds: float
    knowledge_objects: List[KnowledgeObject] = Field(default_factory=list)
