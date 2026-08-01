import re
from typing import List
from app.schemas.knowledge_extraction import ExtractedEntity
from app.core.logger import logger

class EntityResolver:
    @staticmethod
    def normalize_name(name: str) -> str:
        name_clean = name.strip().lower()
        name_clean = re.sub(r"\s+", " ", name_clean)
        return name_clean

    @classmethod
    def deduplicate_entities(cls, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        seen: dict[str, ExtractedEntity] = {}

        for entity in entities:
            norm_key = cls.normalize_name(entity.name)
            if norm_key not in seen:
                seen[norm_key] = entity
            else:
                existing = seen[norm_key]
                # Merge aliases & take max confidence
                combined_aliases = list(set(existing.aliases + entity.aliases))
                existing.aliases = combined_aliases
                existing.confidence = max(existing.confidence, entity.confidence)
                if len(entity.description) > len(existing.description):
                    existing.description = entity.description

        deduped = list(seen.values())
        logger.info(f"EntityResolver: Reduced {len(entities)} raw entities -> {len(deduped)} deduplicated entities.")
        return deduped
