import httpx
from typing import Optional
from app.services.parsing.pdf_parser import PDFParser
from app.services.parsing.csv_parser import CSVParser
from app.services.parsing.audio_parser import AudioParser
from app.services.processing.normalizer import DocumentNormalizer
from app.services.processing.semantic_chunker import SemanticChunker
from app.services.cloudinary_service import CloudinaryService

from app.schemas.unified_document import ProcessingResult, UnifiedDocument
from app.schemas.document import DocumentMetadata
from app.utils.constants import FileType, DocumentStatus
from app.core.exceptions import DocumentProcessingError, BaseAppException
from app.core.logger import logger
from app.repositories.document_repository import IDocumentRepository


class DocumentProcessor:
    def __init__(
        self,
        doc_repo: IDocumentRepository,
        cloudinary_service: Optional[CloudinaryService] = None,
    ):
        self.doc_repo = doc_repo
        self.cloudinary_service = cloudinary_service
        self.pdf_parser = PDFParser()
        self.csv_parser = CSVParser()
        self.audio_parser = AudioParser()
        self.chunker = SemanticChunker()

    async def _fetch_file_content(
        self,
        url: str,
        public_id: Optional[str] = None,
        resource_type: str = "raw",
    ) -> bytes:
        if url.startswith("https://res.cloudinary.com/mock-cloud"):
            logger.info("Mock Cloudinary URL detected. Returning sample file content.")
            if url.endswith(".pdf"):
                return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 12 Tf 50 750 Td (Sample Compliance Document) Tj ET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000125 00000 n \n0000000260 00000 n \n0000000364 00000 n \ntrailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n443\n%%EOF"
            if url.endswith(".csv"):
                return b"Dataset,Department,Classification,Owner\nCustomer_PII_DB,Engineering,Restricted,Jane Doe\nEmployee_Audit_Logs,HR,Internal,John Smith\n"
            return b"Sample Compliance Document Content for testing processing pipeline."

        # Build candidate URL list: primary URL ➔ signed URL ➔ private download URL
        urls_to_try = [url]

        if public_id and self.cloudinary_service:
            signed_url = self.cloudinary_service.get_signed_url(public_id, resource_type)
            if signed_url and signed_url not in urls_to_try:
                urls_to_try.append(signed_url)

            private_url = self.cloudinary_service.get_private_download_url(public_id, resource_type)
            if private_url and private_url not in urls_to_try:
                urls_to_try.append(private_url)

        last_exception = None

        for attempt_idx, attempt_url in enumerate(urls_to_try, 1):
            try:
                logger.info(f"[Fetch Attempt {attempt_idx}/{len(urls_to_try)}] Downloading from URL: {attempt_url}")

                async with httpx.AsyncClient(follow_redirects=True) as client:
                    resp = await client.get(
                        attempt_url,
                        timeout=45.0,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                            "Accept": "*/*",
                        },
                    )

                    logger.info(f"Cloudinary Download Response Status: {resp.status_code}")
                    logger.info(f"Cloudinary Response Headers: {dict(resp.headers)}")
                    if resp.history:
                        logger.info(f"Redirect Chain: {[(r.status_code, str(r.url)) for r in resp.history]}")
                    else:
                        logger.info("Redirect Chain: Direct response (No redirects)")

                    if resp.status_code != 200:
                        logger.warning(
                            f"Cloudinary fetch attempt {attempt_idx} returned HTTP {resp.status_code}. "
                            f"Body snippet (first 500 chars): {resp.text[:500]}"
                        )

                    resp.raise_for_status()
                    logger.info(f"Successfully downloaded {len(resp.content)} bytes from cloud storage.")
                    return resp.content

            except Exception as e:
                logger.error(f"Fetch attempt {attempt_idx} failed for URL ({attempt_url}): {str(e)}")
                last_exception = e

        raise DocumentProcessingError(
            f"File retrieval from cloud storage failed for all attempted URLs. Last error: {str(last_exception)}"
        )

    async def process(self, document_id: str) -> ProcessingResult:
        doc_meta: DocumentMetadata = await self.doc_repo.get_document_by_id(document_id)
        if not doc_meta:
            raise BaseAppException(message=f"Document with ID '{document_id}' not found.", status_code=404)

        logger.info(f"Starting processing pipeline for Document ID: {document_id} ({doc_meta.original_filename})")

        # 1. Update Status: PARSING
        doc_meta.status = DocumentStatus.PARSING
        await self.doc_repo.create_document(doc_meta)

        # Determine Cloudinary resource_type
        resource_type = "video" if doc_meta.file_type == FileType.AUDIO else "raw"

        # 2. Fetch File Content from Cloudinary
        file_content = await self._fetch_file_content(
            url=doc_meta.cloudinary_url,
            public_id=doc_meta.public_id,
            resource_type=resource_type,
        )

        # 3. Parse File into a UnifiedDocument object
        if doc_meta.file_type == FileType.PDF:
            unified_doc: UnifiedDocument = self.pdf_parser.parse(
                file_content=file_content,
                document_id=document_id,
                filename=doc_meta.original_filename,
            )
        elif doc_meta.file_type == FileType.CSV:
            unified_doc: UnifiedDocument = self.csv_parser.parse(
                file_content=file_content,
                document_id=document_id,
                filename=doc_meta.original_filename,
            )
        elif doc_meta.file_type == FileType.AUDIO:
            unified_doc: UnifiedDocument = self.audio_parser.parse(
                file_content=file_content,
                document_id=document_id,
                filename=doc_meta.original_filename,
            )
        else:
            raise DocumentProcessingError(f"Unsupported file type: {doc_meta.file_type}")

        # 4. Normalize Document
        doc_meta.status = DocumentStatus.NORMALIZING
        await self.doc_repo.create_document(doc_meta)

        unified_doc = DocumentNormalizer.normalize(unified_doc)

        # 5. Semantic Chunking
        doc_meta.status = DocumentStatus.CHUNKING
        await self.doc_repo.create_document(doc_meta)

        chunks = self.chunker.chunk_document(unified_doc)

        # 6. Update Status: READY_FOR_ENTITY_EXTRACTION
        doc_meta.status = DocumentStatus.READY_FOR_ENTITY_EXTRACTION
        await self.doc_repo.create_document(doc_meta)

        logger.info(
            f"Successfully processed document ID '{document_id}'. "
            f"Extracted {len(unified_doc.normalized_text or unified_doc.raw_text)} chars into {len(chunks)} semantic chunks."
        )

        return ProcessingResult(
            document_id=document_id,
            status=doc_meta.status,
            page_count=len(unified_doc.pages) or 1,
            chunk_count=len(chunks),
            character_count=unified_doc.character_count,
            estimated_tokens=unified_doc.estimated_tokens,
            chunks=chunks,
            metadata=unified_doc.metadata,
        )
