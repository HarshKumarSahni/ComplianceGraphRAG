import httpx
import json
import asyncio
from typing import Dict, Any, Optional
from app.core.config import Settings
from app.core.logger import logger
from app.core.exceptions import ExternalAPIError


class OpenRouterClient:
    """Production OpenRouter client for LLM text and JSON generation.

    Single source of truth for all LLM calls in GraphGuard AI (Knowledge Extraction,
    GraphRAG Query Answering, Entity Extraction, etc.).
    """

    def __init__(self, settings: Settings):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_PRIMARY_MODEL
        self.timeout = settings.REQUEST_TIMEOUT
        self.max_retries = settings.MAX_RETRIES
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def check_health(self) -> str:
        """Check if OpenRouter client is configured with an API key."""
        if not self.api_key:
            return "unconfigured (mock_mode)"
        return "configured"

    async def generate_json(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        """Generate structured JSON output from OpenRouter LLM.

        Falls back to a deterministic mock response if API key is missing.
        """
        if not self.api_key:
            logger.info("OpenRouter API key missing. Operating in deterministic mock LLM mode.")
            sys_lower = system_prompt.lower()
            if "graphguard ai" in sys_lower or "cited_chunks" in sys_lower:
                return {
                    "answer": "GDPR Article 32 governs technical and organizational security measures for protecting cloud storage containers (such as AWS S3 buckets) storing personal identifiable information (PII). It mandates encryption at rest and in transit.",
                    "confidence": 0.95,
                    "cited_chunks": ["chunk-mock-1"]
                }

            return {
                "entities": [
                    {
                        "name": "GDPR Article 32",
                        "type": "Regulation",
                        "description": "Requires technical and organizational security measures.",
                        "aliases": ["GDPR Art 32"],
                        "confidence": 0.98,
                    },
                    {
                        "name": "Customer Data Bucket",
                        "type": "Storage",
                        "description": "AWS S3 Bucket storing PII customer data.",
                        "aliases": ["s3-customer-pii"],
                        "confidence": 0.95,
                    },
                ],
                "relationships": [
                    {
                        "source_entity": "GDPR Article 32",
                        "relationship_type": "GOVERNS",
                        "target_entity": "Customer Data Bucket",
                        "confidence": 0.94,
                        "evidence": "GDPR Article 32 governs cloud storage containers storing personal data.",
                    }
                ],
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://graphguard.ai",
            "X-Title": "GraphGuard AI",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1,
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                    resp = await client.post(self.base_url, headers=headers, json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    content_str = data["choices"][0]["message"]["content"]
                    return json.loads(content_str)
            except Exception as e:
                logger.warning(f"OpenRouter API request attempt {attempt}/{self.max_retries} failed: {str(e)}")
                if attempt == self.max_retries:
                    logger.error(f"OpenRouter call failed after {self.max_retries} retries.")
                    raise ExternalAPIError(f"OpenRouter LLM extraction failed: {str(e)}")
                await asyncio.sleep(2**attempt)
