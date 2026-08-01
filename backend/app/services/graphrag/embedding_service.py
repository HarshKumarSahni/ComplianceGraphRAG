import httpx
import hashlib
from typing import List, Optional
from app.core.config import Settings
from app.core.logger import logger


class EmbeddingService:
    """API-first lightweight Embedding Service for GraphGuard AI.

    Uses OpenRouter / OpenAI API for dense vector generation.
    Does NOT load PyTorch or SentenceTransformers into RAM, keeping memory usage
    under 60 MB and completely preventing Render Free Tier OOM restarts.
    """

    def __init__(self, settings: Settings):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model_name = "text-embedding-3-small"
        self.api_url = "https://openrouter.ai/api/v1/embeddings"
        self.dimension_val = 384

    def encode(self, text: str) -> List[float]:
        """Encode a single text string into a dense vector via API."""
        if not text:
            return [0.0] * self.dimension_val

        if not self.api_key:
            return self._generate_mock_vector(text)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://graphguard.ai",
            "X-Title": "GraphGuard AI",
        }
        payload = {
            "model": self.model_name,
            "input": text,
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(self.api_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["data"][0]["embedding"]
                else:
                    logger.warning(f"Embedding API returned HTTP {resp.status_code}. Using fallback vector.")
                    return self._generate_mock_vector(text)
        except Exception as e:
            logger.warning(f"Embedding API request failed: {e}. Using fallback vector.")
            return self._generate_mock_vector(text)

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into dense vectors."""
        return [self.encode(text) for text in texts]

    @property
    def dimension(self) -> int:
        """Return the vector embedding dimension."""
        return self.dimension_val

    def _generate_mock_vector(self, text: str) -> List[float]:
        """Generate a deterministic normalized vector based on SHA-256 text hash."""
        seed_hash = hashlib.sha256(text.encode("utf-8")).digest()
        raw_vals = [(b / 255.0) - 0.5 for b in (seed_hash * 12)[:self.dimension_val]]
        norm = (sum(v ** 2 for v in raw_vals) ** 0.5) or 1.0
        return [v / norm for v in raw_vals]
