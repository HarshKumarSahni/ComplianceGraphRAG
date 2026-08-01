import pytest
from app.utils.constants import FileType
from app.services.upload_service import UploadService
from app.repositories.json_document_repository import JSONDocumentRepository
from app.services.cloudinary_service import CloudinaryService
from app.core.config import Settings
from app.core.exceptions import DocumentProcessingError
from fastapi import UploadFile
import io

@pytest.fixture
def mock_settings():
    return Settings(MAX_UPLOAD_SIZE_MB=5)

@pytest.fixture
def mock_upload_service(mock_settings):
    repo = JSONDocumentRepository("test_docs.json")
    cloudinary_svc = CloudinaryService(mock_settings)
    return UploadService(doc_repo=repo, cloudinary_service=cloudinary_svc, settings=mock_settings)

def test_validate_allowed_extensions(mock_upload_service):
    pdf_file = UploadFile(filename="test.pdf", file=io.BytesIO(b"dummy pdf content"))
    csv_file = UploadFile(filename="test.csv", file=io.BytesIO(b"dummy csv content"))
    mp3_file = UploadFile(filename="test.mp3", file=io.BytesIO(b"dummy mp3 content"))

    assert mock_upload_service.validate_file(pdf_file, b"dummy pdf content") == FileType.PDF
    assert mock_upload_service.validate_file(csv_file, b"dummy csv content") == FileType.CSV
    assert mock_upload_service.validate_file(mp3_file, b"dummy mp3 content") == FileType.AUDIO

def test_validate_disallowed_extension(mock_upload_service):
    exe_file = UploadFile(filename="virus.exe", file=io.BytesIO(b"malware"))
    with pytest.raises(DocumentProcessingError):
        mock_upload_service.validate_file(exe_file, b"malware")
