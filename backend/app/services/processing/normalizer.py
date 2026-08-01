import re
import unicodedata
from app.schemas.unified_document import UnifiedDocument
from app.core.logger import logger

class DocumentNormalizer:
    @staticmethod
    def normalize(doc: UnifiedDocument) -> UnifiedDocument:
        text = doc.raw_text

        # 1. Unicode Normalization
        text = unicodedata.normalize("NFKC", text)

        # 2. Control Characters Removal (preserve newlines and tabs)
        text = "".join(ch for ch in text if ch in ("\n", "\r", "\t") or unicodedata.category(ch)[0] != "C")

        # 3. Fix broken hyphenated line breaks (e.g. "com- \n pliance" -> "compliance")
        text = re.sub(r"(\w+)-\s*[\r\n]+\s*(\w+)", r"\1\2", text)

        # 4. Replace 3+ consecutive newlines with exactly 2 newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # 5. Remove excessive horizontal spaces while keeping line breaks
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        normalized_text = "\n".join(lines).strip()

        doc.normalized_text = normalized_text
        doc.character_count = len(normalized_text)
        doc.estimated_tokens = len(normalized_text.split())

        logger.info(f"Normalized document '{doc.original_filename}': clean char count = {doc.character_count}.")
        return doc
