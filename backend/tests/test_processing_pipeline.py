import pytest
from app.services.parsing.pdf_parser import PDFParser
from app.services.parsing.csv_parser import CSVParser
from app.services.parsing.audio_parser import AudioParser
from app.services.processing.normalizer import DocumentNormalizer
from app.services.processing.semantic_chunker import SemanticChunker
from app.schemas.unified_document import UnifiedDocument
from app.utils.constants import FileType

def test_csv_parser():
    parser = CSVParser()
    csv_bytes = b"Employee,Department,Policy\nJohn Doe,Finance,GDPR Passed\nJane Smith,Security,ISO27001 Active"
    unified_doc = parser.parse(csv_bytes, "doc-csv-1", "test.csv")

    assert unified_doc.file_type == FileType.CSV
    assert "Record Row 1: Employee: John Doe" in unified_doc.raw_text
    assert len(unified_doc.sections[0].paragraphs) == 2

def test_document_normalizer():
    raw_doc = UnifiedDocument(
        document_id="doc-norm-1",
        original_filename="raw.txt",
        file_type=FileType.PDF,
        raw_text="Header   Text  \n\n\n\nSection  com-\npliance  details.",
        normalized_text="",
        pages=[],
        sections=[],
        metadata={},
        character_count=50,
        estimated_tokens=8
    )

    normalized_doc = DocumentNormalizer.normalize(raw_doc)
    assert "compliance details." in normalized_doc.normalized_text
    assert "\n\n\n" not in normalized_doc.normalized_text

def test_semantic_chunker():
    chunker = SemanticChunker(target_chunk_size=100, overlap_sentences=1)
    doc = UnifiedDocument(
        document_id="doc-chunk-1",
        original_filename="test.pdf",
        file_type=FileType.PDF,
        raw_text="",
        normalized_text="First sentence for testing chunking. Second sentence expanding semantic content. Third sentence completing paragraph context.",
        pages=[],
        sections=[],
        metadata={},
        character_count=135,
        estimated_tokens=20
    )

    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 0
    assert chunks[0].document_id == "doc-chunk-1"
    assert chunks[0].chunk_id == "doc-chunk-1-chunk-0"
