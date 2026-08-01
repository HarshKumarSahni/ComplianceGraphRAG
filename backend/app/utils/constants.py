from enum import Enum

class FileType(str, Enum):
    PDF = "pdf"
    CSV = "csv"
    AUDIO = "audio"

class DocumentStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PARSING = "PARSING"
    NORMALIZING = "NORMALIZING"
    CHUNKING = "CHUNKING"
    READY_FOR_ENTITY_EXTRACTION = "READY_FOR_ENTITY_EXTRACTION"
    ENTITY_EXTRACTION = "ENTITY_EXTRACTION"
    RELATIONSHIP_EXTRACTION = "RELATIONSHIP_EXTRACTION"
    VALIDATION = "VALIDATION"
    READY_FOR_GRAPH_BUILDING = "READY_FOR_GRAPH_BUILDING"
    PARSED = "PARSED"
    GRAPH_BUILT = "GRAPH_BUILT"
    READY = "READY"
    FAILED = "FAILED"

ALLOWED_EXTENSIONS = {
    FileType.PDF: [".pdf"],
    FileType.CSV: [".csv"],
    FileType.AUDIO: [".mp3"]
}

ALLOWED_MIME_TYPES = {
    "application/pdf": FileType.PDF,
    "text/csv": FileType.CSV,
    "application/vnd.ms-excel": FileType.CSV,
    "audio/mpeg": FileType.AUDIO,
    "audio/mp3": FileType.AUDIO
}
