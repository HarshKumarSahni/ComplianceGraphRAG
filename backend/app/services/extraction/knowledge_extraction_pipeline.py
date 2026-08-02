import time
from typing import List, Optional
from app.core.config import Settings
from app.core.logger import logger
from app.core.exceptions import BaseAppException
from app.utils.constants import DocumentStatus
from app.utils.helpers import utc_now
from app.schemas.unified_document import Chunk
from app.schemas.knowledge_extraction import (
    KnowledgeObject,
    ExtractionPipelineResult,
    ExtractionLLMOutput
)
from app.services.openrouter_client import OpenRouterClient
from app.services.extraction.prompt_builder import PromptBuilder
from app.services.extraction.json_validator import JSONValidator
from app.services.extraction.entity_resolver import EntityResolver
from app.repositories.document_repository import IDocumentRepository
from app.services.graphrag.embedding_service import EmbeddingService
from app.repositories.graph_repository import GraphRepository, IGraphRepository
from app.dependencies.clients import Neo4jClient

class KnowledgeExtractionPipeline:
    def __init__(self, doc_repo: IDocumentRepository, settings: Settings, graph_repo: Optional[IGraphRepository] = None):
        self.doc_repo = doc_repo
        self.settings = settings
        self.openrouter_client = OpenRouterClient(settings)
        self.embedding_service = EmbeddingService(settings)
        if graph_repo:
            self.graph_repo = graph_repo
        else:
            client = Neo4jClient(settings)
            client.connect()
            self.graph_repo = GraphRepository(client)

    async def process_chunks(self, document_id: str, chunks: List[Chunk], user_id: str = None) -> ExtractionPipelineResult:
        if not user_id:
            raise ValueError("user_id is required for knowledge extraction. Never extract without an authenticated user.")
        start_time = time.time()
        doc_meta = await self.doc_repo.get_document_by_id(document_id)
        if not doc_meta:
            raise BaseAppException(f"Document with ID '{document_id}' not found.", status_code=404)

        logger.info(f"Starting Knowledge Extraction Pipeline for Document ID: {document_id} ({len(chunks)} chunks)")

        # 1. Update Status: ENTITY_EXTRACTION
        doc_meta.status = DocumentStatus.ENTITY_EXTRACTION
        await self.doc_repo.create_document(doc_meta)

        knowledge_objects: List[KnowledgeObject] = []
        total_entities = 0
        total_relationships = 0
        validation_errors = 0
        confidences = []

        system_prompt = PromptBuilder.get_system_prompt()

        for chunk in chunks:
            prompt = PromptBuilder.build_extraction_prompt(chunk.text, doc_meta.original_filename)

            try:
                raw_json = await self.openrouter_client.generate_json(prompt, system_prompt)
                is_valid, validated_output, err_msg = JSONValidator.validate_llm_json(raw_json)

                if not is_valid:
                    validation_errors += 1
                    logger.warning(f"Validation failure on chunk {chunk.chunk_id}: {err_msg}")

                # Deduplicate entities for chunk
                deduped_entities = EntityResolver.deduplicate_entities(validated_output.entities)

                chunk_conf = 1.0
                if deduped_entities:
                    chunk_conf = sum(e.confidence for e in deduped_entities) / len(deduped_entities)
                confidences.append(chunk_conf)

                k_obj = KnowledgeObject(
                    document_id=document_id,
                    chunk_id=chunk.chunk_id,
                    page_number=chunk.page_number or 1,
                    chunk_text=chunk.text,
                    entities=deduped_entities,
                    relationships=validated_output.relationships,
                    confidence_score=chunk_conf,
                    source_metadata=chunk.metadata,
                    processing_timestamp=utc_now()
                )

                knowledge_objects.append(k_obj)
                total_entities += len(deduped_entities)
                total_relationships += len(validated_output.relationships)

            except Exception as e:
                logger.error(f"Error processing chunk {chunk.chunk_id}: {str(e)}")
                validation_errors += 1

        # 2. Persist Entities, Edges & Chunks into Neo4j Graph & Vector Store
        all_nodes = []
        all_edges = []
        chunk_data_list = []

        for k_obj in knowledge_objects:
            for entity in k_obj.entities:
                all_nodes.append({
                    "name": entity.name,
                    "type": entity.type,
                    "description": entity.description,
                    "document_id": document_id,
                    "user_id": user_id or "anonymous",
                })
            for rel in k_obj.relationships:
                all_edges.append({
                    "source_entity": rel.source_entity,
                    "relationship_type": rel.relationship_type,
                    "target_entity": rel.target_entity,
                    "confidence": rel.confidence,
                    "evidence": rel.evidence,
                    "user_id": user_id,
                })

        for chunk in chunks:
            sec_title = chunk.metadata.get("section_title", "") if isinstance(chunk.metadata, dict) else ""
            chunk_data_list.append({
                "chunk_id": chunk.chunk_id,
                "document_id": document_id,
                "document_name": doc_meta.original_filename,
                "text": chunk.text,
                "page_number": chunk.page_number or 1,
                "section_title": sec_title,
                "embedding": self.embedding_service.encode(chunk.text),
                "user_id": user_id,
            })

        await self.graph_repo.upsert_nodes_and_edges(all_nodes, all_edges)
        await self.graph_repo.upsert_chunks(chunk_data_list)

        # 3. Update Status: READY_FOR_GRAPH_BUILDING
        doc_meta.status = DocumentStatus.READY_FOR_GRAPH_BUILDING
        doc_meta.entity_count = total_entities
        doc_meta.relation_count = total_relationships
        await self.doc_repo.create_document(doc_meta)

        processing_time = round(time.time() - start_time, 2)
        avg_confidence = round(sum(confidences) / len(confidences), 2) if confidences else 1.0

        logger.info(
            f"Completed Knowledge Extraction Pipeline for Document ID: {document_id}. "
            f"Extracted {total_entities} entities and {total_relationships} relationships in {processing_time}s."
        )

        return ExtractionPipelineResult(
            document_id=document_id,
            status=DocumentStatus.READY_FOR_GRAPH_BUILDING.value,
            chunk_count=len(chunks),
            entity_count=total_entities,
            relationship_count=total_relationships,
            validation_errors=validation_errors,
            average_confidence=avg_confidence,
            processing_time_seconds=processing_time,
            knowledge_objects=knowledge_objects
        )
