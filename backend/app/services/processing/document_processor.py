import httpx
from app.services.parsing.pdf_parser import PDFParser
from app.services.parsing.csv_parser import CSVParser
from app.services.parsing.audio_parser import AudioParser
from app.services.processing.normalizer import DocumentNormalizer
from app.services.processing.semantic_chunker import SemanticChunker

from app.schemas.unified_document import ProcessingResult, UnifiedDocument
from app.schemas.document import DocumentMetadata
from app.utils.constants import FileType, DocumentStatus
from app.core.exceptions import DocumentProcessingError, BaseAppException
from app.core.logger import logger
from app.repositories.document_repository import IDocumentRepository

class DocumentProcessor:
    def __init__(self, doc_repo: IDocumentRepository):
        self.doc_repo = doc_repo
        self.pdf_parser = PDFParser()
        self.csv_parser = CSVParser()
        self.audio_parser = AudioParser()
        self.chunker = SemanticChunker()

    async def _fetch_file_content(self, url: str) -> bytes:
        if url.startswith("https://res.cloudinary.com/mock-cloud"):
            logger.info("Mock Cloudinary URL detected. Returning sample file content.")
            return b"Sample Compliance Document Content for testing processing pipeline."

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=30.0)
                resp.raise_for_status()
                return resp.content
        except Exception as e:
            logger.error(f"Failed to download file from Cloudinary URL ({url}): {str(e)}")
            raise DocumentProcessingError(f"File retrieval from cloud storage failed: {str(e)}")

    async def process(self, document_id: str) -> ProcessingResult:
        doc_meta: DocumentMetadata = await self.doc_repo.get_document_by_id(document_id)
        if not doc_meta:
            raise BaseAppException(message=f"Document with ID '{document_id}' not found.", status_code=404)

        logger.info(f"Starting processing pipeline for Document ID: {document_id} ({doc_meta.original_filename})")

        # 1. Update Status: PARSING
        doc_meta.status = DocumentStatus.PARSING
        await self.doc_repo.create_document(doc_meta)

        file_content = await self._fetch_file_content(doc_meta.cloudinary_url)

        # 2. Select Parser
        if doc_meta.file_type == FileType.PDF:
            parsed_doc = self.pdf_parser.parse(file_content, document_id, doc_meta.original_filename)
        elif doc_meta.file_type == FileType.CSV:
            parsed_doc = self.csv_parser.parse(file_content, document_id, doc_meta.original_filename)
        else:
            parsed_doc = self.audio_parser.parse(file_content, document_id, doc_meta.original_filename)

        # 3. Update Status: NORMALIZING
        doc_meta.status = DocumentStatus.NORMALIZING
        await self.doc_repo.create_document(doc_meta)

        normalized_doc = DocumentNormalizer.normalize(parsed_doc)

        # 4. Update Status: CHUNKING
        doc_meta.status = DocumentStatus.CHUNKING
        await self.doc_repo.create_document(doc_meta)

        chunks = self.chunker.chunk_document(normalized_doc)

        # 5. Update Status: READY_FOR_ENTITY_EXTRACTION
        doc_meta.status = DocumentStatus.READY_FOR_ENTITY_EXTRACTION
        doc_meta.chunk_count = len(chunks)
        await self.doc_repo.create_document(doc_meta)

        logger.info(f"Completed processing pipeline for Document ID: {document_id}. Chunks: {len(chunks)}.")

        return ProcessingResult(
            document_id=document_id,
            status=DocumentStatus.READY_FOR_ENTITY_EXTRACTION.value,
            page_count=len(normalized_doc.pages) if normalized_doc.pages else 1,
            chunk_count=len(chunks),
            character_count=normalized_doc.character_count,
            estimated_tokens=normalized_doc.estimated_tokens,
            chunks=chunks,
            metadata=normalized_doc.metadata
        )
