import re
from typing import List
from app.schemas.unified_document import UnifiedDocument, Chunk
from app.core.logger import logger

class SemanticChunker:
    def __init__(self, target_chunk_size: int = 500, overlap_sentences: int = 1):
        self.target_chunk_size = target_chunk_size
        self.overlap_sentences = overlap_sentences

    def _split_into_sentences(self, text: str) -> List[str]:
        # Sentence splitting regex preserving punctuation
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_document(self, doc: UnifiedDocument) -> List[Chunk]:
        text_to_chunk = doc.normalized_text or doc.raw_text
        sentences = self._split_into_sentences(text_to_chunk)

        chunks: List[Chunk] = []
        current_sentences: List[str] = []
        current_length = 0
        chunk_idx = 0

        for sentence in sentences:
            sentence_len = len(sentence)
            if current_length + sentence_len > self.target_chunk_size and current_sentences:
                chunk_text = " ".join(current_sentences)
                chunks.append(Chunk(
                    chunk_id=f"{doc.document_id}-chunk-{chunk_idx}",
                    document_id=doc.document_id,
                    chunk_index=chunk_idx,
                    text=chunk_text,
                    page_number=1,
                    section_title=f"Chunk {chunk_idx + 1}",
                    metadata={"source_file": doc.original_filename, "file_type": doc.file_type.value},
                    character_count=len(chunk_text),
                    estimated_tokens=len(chunk_text.split())
                ))
                chunk_idx += 1

                # Keep overlap sentences for context preservation
                current_sentences = current_sentences[-self.overlap_sentences:] if self.overlap_sentences > 0 else []
                current_length = sum(len(s) for s in current_sentences)

            current_sentences.append(sentence)
            current_length += sentence_len

        # Flush final chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append(Chunk(
                chunk_id=f"{doc.document_id}-chunk-{chunk_idx}",
                document_id=doc.document_id,
                chunk_index=chunk_idx,
                text=chunk_text,
                page_number=1,
                section_title=f"Chunk {chunk_idx + 1}",
                metadata={"source_file": doc.original_filename, "file_type": doc.file_type.value},
                character_count=len(chunk_text),
                estimated_tokens=len(chunk_text.split())
            ))

        logger.info(f"Generated {len(chunks)} semantic chunks for document '{doc.original_filename}'.")
        return chunks
