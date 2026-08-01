import pytest
import asyncio
from app.services.extraction.prompt_builder import PromptBuilder
from app.services.extraction.json_validator import JSONValidator
from app.services.extraction.entity_resolver import EntityResolver
from app.schemas.knowledge_extraction import ExtractedEntity

def test_prompt_builder():
    prompt = PromptBuilder.build_extraction_prompt("GDPR Article 32 governs cloud security.", "policy.pdf")
    assert "GDPR Article 32 governs cloud security." in prompt
    assert "policy.pdf" in prompt

def test_json_validator():
    valid_raw_json = {
        "entities": [
            {
                "name": "AWS S3",
                "type": "Storage",
                "description": "Cloud bucket",
                "aliases": ["s3-bucket"],
                "confidence": 0.95
            }
        ],
        "relationships": [
            {
                "source_entity": "AWS S3",
                "relationship_type": "STORES",
                "target_entity": "Customer Data",
                "confidence": 0.90,
                "evidence": "AWS S3 stores customer data."
            }
        ]
    }

    is_valid, output, err = JSONValidator.validate_llm_json(valid_raw_json)
    assert is_valid is True
    assert len(output.entities) == 1
    assert output.entities[0].name == "AWS S3"

def test_entity_resolver_deduplication():
    entities = [
        ExtractedEntity(name="  AWS S3  ", type="Storage", description="Short desc", aliases=["s3-1"], confidence=0.8),
        ExtractedEntity(name="aws s3", type="Storage", description="Long detailed description", aliases=["s3-2"], confidence=0.95)
    ]

    deduped = EntityResolver.deduplicate_entities(entities)
    assert len(deduped) == 1
    assert deduped[0].name.strip().lower() == "aws s3"
    assert deduped[0].confidence == 0.95
    assert set(deduped[0].aliases) == {"s3-1", "s3-2"}
