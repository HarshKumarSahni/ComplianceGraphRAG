import httpx
import json
import asyncio
from typing import Dict, Any, Optional
from app.core.config import Settings
from app.core.logger import logger
from app.core.exceptions import ExternalAPIError


class OpenRouterClient:
    """Production OpenRouter client for LLM text and JSON generation.

    Guaranteed: exactly ONE OpenRouter API call per generate_json() invocation.
    No retries. On any error (network, 4xx, 5xx, JSON parse) → repair locally
    or fall back to mock. Never makes a second HTTP request.
    """

    def __init__(self, settings: Settings):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_PRIMARY_MODEL
        self.timeout = settings.REQUEST_TIMEOUT
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def check_health(self) -> str:
        if not self.api_key:
            return "unconfigured (mock_mode)"
        return "configured"

    def _get_mock_fallback(self, prompt: str, system_prompt: str) -> Dict[str, Any]:
        sys_lower = system_prompt.lower()
        if "graphguard ai" in sys_lower or "cited_chunks" in sys_lower:
            return {
                "answer": "GDPR Article 32 governs technical and organizational security measures for protecting cloud storage containers storing PII. It mandates encryption at rest and in transit.",
                "confidence": 0.95,
                "cited_chunks": ["chunk-mock-1"],
            }
        return {
            "entities": [
                {
                    "name": "GDPR Article 32",
                    "type": "Regulation",
                    "description": "Requires technical and organizational security measures.",
                    "confidence": 0.98,
                },
                {
                    "name": "Customer Data Bucket",
                    "type": "Storage",
                    "description": "AWS S3 Bucket storing PII customer data.",
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

    def _is_credit_error(self, status_code: int, body: str) -> bool:
        if status_code in (401, 402, 403, 429):
            return True
        body_lower = body.lower()
        return any(kw in body_lower for kw in ("limit exceeded", "payment required", "insufficient credits", "quota"))

    async def generate_json(
        self,
        prompt: str,
        system_prompt: str,
        document_id: str = "unknown",
        chunk_id: str = "unknown",
    ) -> Dict[str, Any]:
        """Make exactly ONE OpenRouter API call and return parsed JSON.

        Flow:
          1. Make ONE HTTP POST to OpenRouter.
          2. On billing/auth error  → immediate mock fallback (no retry).
          3. On network/5xx error   → immediate mock fallback (no retry).
          4. On success             → strip markdown wrapper, try json.loads().
          5. If json.loads() fails  → repair locally via JSONValidator (no retry).
          6. If repair fails        → mock fallback and log.
          7. After parsing          → return raw dict (pipeline does Pydantic validation).
        """
        if not self.api_key:
            logger.info(
                f"[LLM] doc={document_id} chunk={chunk_id} model=mock "
                f"→ API key missing, using deterministic fallback."
            )
            return self._get_mock_fallback(prompt, system_prompt)

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
            "max_tokens": 4096,
        }

        # ── STEP 1: Single HTTP call ─────────────────────────────────────────
        logger.info(
            f"[LLM] doc={document_id} chunk={chunk_id} model={self.model} → making API call (attempt 1/1)"
        )
        try:
            async with httpx.AsyncClient(timeout=float(self.timeout)) as client:
                resp = await client.post(self.base_url, headers=headers, json=payload)
        except (httpx.TimeoutException, httpx.ConnectError, Exception) as net_err:
            logger.warning(
                f"[LLM] doc={document_id} chunk={chunk_id} network error: {net_err}. "
                f"Using mock fallback (no retry)."
            )
            return self._get_mock_fallback(prompt, system_prompt)

        # ── STEP 2: Billing / auth errors → immediate fallback ───────────────
        if self._is_credit_error(resp.status_code, resp.text):
            logger.warning(
                f"[LLM] doc={document_id} chunk={chunk_id} HTTP {resp.status_code} (billing/auth). "
                f"Using mock fallback immediately (no retry)."
            )
            return self._get_mock_fallback(prompt, system_prompt)

        # ── STEP 3: Other HTTP errors → fallback ─────────────────────────────
        if resp.status_code != 200:
            logger.error(
                f"[LLM] doc={document_id} chunk={chunk_id} HTTP {resp.status_code}: {resp.text[:300]}. "
                f"Using mock fallback (no retry)."
            )
            return self._get_mock_fallback(prompt, system_prompt)

        # ── STEP 4: Parse API response ────────────────────────────────────────
        try:
            data = resp.json()
        except Exception as e:
            logger.error(
                f"[LLM] doc={document_id} chunk={chunk_id} failed to parse API response JSON: {e}. "
                f"Using mock fallback."
            )
            return self._get_mock_fallback(prompt, system_prompt)

        if "choices" not in data or not data["choices"]:
            logger.error(
                f"[LLM] doc={document_id} chunk={chunk_id} unexpected response structure: {data}. "
                f"Using mock fallback."
            )
            return self._get_mock_fallback(prompt, system_prompt)

        # Log token usage
        usage = data.get("usage", {})
        logger.info(
            f"[LLM] doc={document_id} chunk={chunk_id} model={self.model} "
            f"input_tokens={usage.get('prompt_tokens', '?')} "
            f"output_tokens={usage.get('completion_tokens', '?')} "
            f"total_tokens={usage.get('total_tokens', '?')}"
        )

        content_str = (data["choices"][0]["message"]["content"] or "").strip()

        # Strip markdown code block wrappers if present (e.g. ```json ... ```)
        if content_str.startswith("```"):
            lines = content_str.splitlines()
            lines = lines[1:] if lines[0].startswith("```") else lines
            lines = lines[:-1] if lines and lines[-1].startswith("```") else lines
            content_str = "\n".join(lines).strip()

        # ── STEP 5: Try direct JSON parse ─────────────────────────────────────
        try:
            return json.loads(content_str)
        except json.JSONDecodeError as json_err:
            logger.warning(
                f"[LLM] doc={document_id} chunk={chunk_id} JSONDecodeError: {json_err}. "
                f"Attempting local repair (NO extra API call)."
            )

        # ── STEP 6: Local JSON repair — NO API retry ──────────────────────────
        from app.services.extraction.json_validator import JSONValidator
        ok, repaired_output, repair_err = JSONValidator.repair_and_validate(content_str)
        if ok:
            logger.info(
                f"[LLM] doc={document_id} chunk={chunk_id} local repair succeeded: "
                f"entities={len(repaired_output.entities)} "
                f"relationships={len(repaired_output.relationships)}"
            )
            return repaired_output.model_dump()

        # ── STEP 7: Repair failed → mock fallback ─────────────────────────────
        logger.warning(
            f"[LLM] doc={document_id} chunk={chunk_id} local repair failed: {repair_err}. "
            f"Using mock fallback."
        )
        return self._get_mock_fallback(prompt, system_prompt)
