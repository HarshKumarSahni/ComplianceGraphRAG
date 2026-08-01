import pytest
import asyncio
import fitz
from app.core.config import Settings
from app.utils.constants import FileType, DocumentStatus
from app.utils.helpers import utc_now
from app.schemas.document import DocumentMetadata
from app.repositories.json_document_repository import JSONDocumentRepository
from app.services.processing.document_processor import DocumentProcessor
from app.services.extraction.knowledge_extraction_pipeline import KnowledgeExtractionPipeline


def create_sample_pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "GDPR Article 32 Security Policy.\n"
        "Technical and organizational measures must be implemented for cloud storage buckets.\n"
        "All customer PII stored in AWS S3 buckets requires encryption at rest and in transit."
    )
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


@pytest.mark.asyncio
async def test_full_ingestion_pipeline_end_to_end(tmp_path, monkeypatch):
    repo_file = str(tmp_path / "documents.json")
    doc_repo = JSONDocumentRepository(storage_file=repo_file)

    pdf_bytes = create_sample_pdf_bytes()

    # 1. Create initial document metadata simulating upload
    doc_id = "doc-e2e-test-123"
    doc_meta = DocumentMetadata(
        document_id=doc_id,
        original_filename="compliance_policy.pdf",
        file_type=FileType.PDF,
        mime_type="application/pdf",
        file_size_bytes=len(pdf_bytes),
        upload_timestamp=utc_now(),
        status=DocumentStatus.UPLOADED,
        cloudinary_url="https://res.cloudinary.com/mock-cloud/raw/upload/v1234567890/compliance_policy.pdf",
        public_id="graphguard/compliance_policy.pdf",
    )
    await doc_repo.create_document(doc_meta)

    # 2. Mock _fetch_file_content to return real PDF bytes
    processor = DocumentProcessor(doc_repo=doc_repo)
    monkeypatch.setattr(processor, "_fetch_file_content", lambda *args, **kwargs: asyncio.sleep(0, result=pdf_bytes))

    proc_result = await processor.process(doc_id)

    assert proc_result.document_id == doc_id
    assert proc_result.status == DocumentStatus.READY_FOR_ENTITY_EXTRACTION
    assert proc_result.chunk_count > 0
    assert len(proc_result.chunks) > 0

    # 3. Execute AI Knowledge Extraction (LLM Entity & Relationship extraction)
    settings = Settings(
        ENVIRONMENT="development",
        NEO4J_URI="",
        NEO4J_USERNAME="",
        NEO4J_PASSWORD="",
        NEO4J_DATABASE="neo4j",
        OPENROUTER_API_KEY="",
        OPENROUTER_PRIMARY_MODEL="anthropic/claude-sonnet-5",
    )

    extraction_pipeline = KnowledgeExtractionPipeline(doc_repo=doc_repo, settings=settings)
    extract_result = await extraction_pipeline.process_chunks(doc_id, proc_result.chunks)

    assert extract_result.document_id == doc_id
    assert extract_result.status == DocumentStatus.READY_FOR_GRAPH_BUILDING.value
    assert extract_result.entity_count > 0
    assert extract_result.relationship_count > 0
    assert len(extract_result.knowledge_objects) > 0

    # 4. Verify Document Repository updated status
    updated_doc = await doc_repo.get_document_by_id(doc_id)
    assert updated_doc.status == DocumentStatus.READY_FOR_GRAPH_BUILDING
    assert updated_doc.entity_count == extract_result.entity_count
    assert updated_doc.relation_count == extract_result.relationship_count
