import pandas as pd
import io
from app.services.parsing.base_parser import BaseParser
from app.schemas.unified_document import UnifiedDocument, Section, Paragraph
from app.utils.constants import FileType
from app.core.exceptions import DocumentProcessingError
from app.core.logger import logger

class CSVParser(BaseParser):
    def parse(self, file_content: bytes, document_id: str, filename: str) -> UnifiedDocument:
        try:
            df = pd.read_csv(io.BytesIO(file_content))
        except Exception as e:
            logger.error(f"Failed to parse CSV '{filename}': {str(e)}")
            raise DocumentProcessingError(f"Invalid or corrupted CSV file: {str(e)}")

        if df.empty:
            raise DocumentProcessingError(f"CSV document '{filename}' is empty.")

        paragraphs = []
        structured_lines = []

        headers = [str(col).strip() for col in df.columns]

        for row_idx, row in df.iterrows():
            row_parts = []
            for header in headers:
                val = row.get(header)
                if pd.notna(val):
                    row_parts.append(f"{header}: {val}")

            row_text = f"Record Row {row_idx + 1}: " + ", ".join(row_parts) + "."
            structured_lines.append(row_text)

            paragraphs.append(Paragraph(
                paragraph_index=row_idx,
                text=row_text,
                section_title="CSV Data Records",
                page_number=1,
                character_count=len(row_text)
            ))

        raw_text = "\n".join(structured_lines)
        total_chars = len(raw_text)
        estimated_tokens = len(raw_text.split())

        section = Section(
            section_index=0,
            title="CSV Records Summary",
            paragraphs=paragraphs
        )

        logger.info(f"Successfully parsed CSV '{filename}': {len(df)} rows, {total_chars} chars.")

        return UnifiedDocument(
            document_id=document_id,
            original_filename=filename,
            file_type=FileType.CSV,
            raw_text=raw_text,
            normalized_text="",
            pages=[],
            sections=[section],
            metadata={
                "row_count": len(df),
                "column_count": len(headers),
                "columns": headers
            },
            character_count=total_chars,
            estimated_tokens=estimated_tokens
        )
