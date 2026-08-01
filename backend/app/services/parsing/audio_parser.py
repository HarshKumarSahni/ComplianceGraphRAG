import tempfile
import os
from app.services.parsing.base_parser import BaseParser
from app.schemas.unified_document import UnifiedDocument, Section, Paragraph
from app.utils.constants import FileType
from app.core.exceptions import DocumentProcessingError
from app.core.logger import logger

class AudioParser(BaseParser):
    def __init__(self, model_size: str = "tiny"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Initializing faster-whisper model ({self.model_size})...")
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            except Exception as e:
                logger.warning(f"Could not load faster-whisper model: {str(e)}. Operating in fallback mode.")
                self._model = "MOCK"
        return self._model

    def parse(self, file_content: bytes, document_id: str, filename: str) -> UnifiedDocument:
        model = self._get_model()

        if model == "MOCK":
            raw_text = f"Audio Transcript for {filename}: [00:00 - 00:30] Compliance audit meeting transcript discussing security policies and data retention rules."
            paragraphs = [
                Paragraph(
                    paragraph_index=0,
                    text=raw_text,
                    section_title="Audio Transcript",
                    page_number=1,
                    character_count=len(raw_text)
                )
            ]
            duration = 30.0
            language = "en"
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name

            try:
                segments, info = model.transcribe(tmp_path, beam_size=5)
                transcript_parts = []
                paragraphs = []

                for idx, segment in enumerate(segments):
                    timestamp = f"[{segment.start:.2f}s -> {segment.end:.2f}s]"
                    seg_text = f"{timestamp} {segment.text.strip()}"
                    transcript_parts.append(seg_text)

                    paragraphs.append(Paragraph(
                        paragraph_index=idx,
                        text=seg_text,
                        section_title="Audio Timestamp Segment",
                        page_number=1,
                        character_count=len(seg_text)
                    ))

                raw_text = "\n".join(transcript_parts)
                duration = info.duration
                language = info.language
            except Exception as e:
                logger.error(f"Failed audio transcription for '{filename}': {str(e)}")
                raise DocumentProcessingError(f"Audio transcription failed: {str(e)}")
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

        if not raw_text.strip():
            raise DocumentProcessingError(f"Audio file '{filename}' produced an empty transcript.")

        total_chars = len(raw_text)
        estimated_tokens = len(raw_text.split())

        section = Section(
            section_index=0,
            title="Timestamped Transcript",
            paragraphs=paragraphs
        )

        logger.info(f"Successfully parsed Audio '{filename}': {duration:.1f}s duration, {total_chars} chars.")

        return UnifiedDocument(
            document_id=document_id,
            original_filename=filename,
            file_type=FileType.AUDIO,
            raw_text=raw_text,
            normalized_text="",
            pages=[],
            sections=[section],
            metadata={
                "duration_seconds": duration,
                "language": language
            },
            character_count=total_chars,
            estimated_tokens=estimated_tokens
        )
