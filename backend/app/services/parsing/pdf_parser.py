import fitz  # PyMuPDF
from app.services.parsing.base_parser import BaseParser
from app.schemas.unified_document import UnifiedDocument, Page, Section, Paragraph
from app.utils.constants import FileType
from app.core.exceptions import DocumentProcessingError
from app.core.logger import logger

class PDFParser(BaseParser):
    def parse(self, file_content: bytes, document_id: str, filename: str) -> UnifiedDocument:
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF '{filename}': {str(e)}")
            raise DocumentProcessingError(f"Corrupted or unreadable PDF document: {str(e)}")

        if doc.page_count == 0:
            raise DocumentProcessingError(f"PDF '{filename}' contains no pages.")

        pages = []
        full_text_blocks = []
        total_chars = 0

        pdf_title = doc.metadata.get("title", filename) if doc.metadata else filename

        for page_idx in range(doc.page_count):
            page = doc.load_page(page_idx)
            page_text = page.get_text("text") or ""

            if page_text.strip():
                full_text_blocks.append(page_text)
                total_chars += len(page_text)

            paragraphs = []
            raw_blocks = page.get_text("blocks")
            for b_idx, block in enumerate(raw_blocks):
                # block[4] is the text content of the block
                block_text = block[4].strip()
                if block_text:
                    paragraphs.append(Paragraph(
                        paragraph_index=b_idx,
                        text=block_text,
                        section_title=f"Page {page_idx + 1}",
                        page_number=page_idx + 1,
                        character_count=len(block_text)
                    ))

            section = Section(
                section_index=0,
                title=f"Page {page_idx + 1} Content",
                paragraphs=paragraphs
            )

            pages.append(Page(
                page_number=page_idx + 1,
                text=page_text,
                sections=[section]
            ))

        raw_text = "\n\n".join(full_text_blocks)
        if not raw_text.strip():
            raise DocumentProcessingError(f"PDF '{filename}' contains no extractable text.")

        estimated_tokens = len(raw_text.split())

        logger.info(f"Successfully parsed PDF '{filename}': {doc.page_count} pages, {total_chars} chars.")

        return UnifiedDocument(
            document_id=document_id,
            original_filename=filename,
            file_type=FileType.PDF,
            raw_text=raw_text,
            normalized_text="",  # Will be populated by normalizer
            pages=pages,
            sections=[],
            metadata={
                "pdf_title": pdf_title,
                "page_count": doc.page_count,
                "author": doc.metadata.get("author", "") if doc.metadata else ""
            },
            character_count=total_chars,
            estimated_tokens=estimated_tokens
        )
