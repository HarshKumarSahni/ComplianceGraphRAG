import httpx
import hashlib
from typing import List
from app.core.config import Settings
from app.core.logger import logger


class EmbeddingService:
    """API-first lightweight Embedding Service for GraphGuard AI.

    Uses OpenRouter / OpenAI compatible API for dense vector generation.
    Does NOT load PyTorch or SentenceTransformers into RAM.

    Embedding model: text-embedding-3-small with dimensions=384
    This matches the Neo4j vector index dimension (384).
    The `dimensions` parameter is supported by OpenAI-compatible models and
    truncates the output embedding to the specified size, keeping it consistent
    with stored vectors and Neo4j indexes.
    """

    DIMENSION = 384

    def __init__(self, settings: Settings):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model_name = "text-embedding-3-small"
        self.api_url = "https://openrouter.ai/api/v1/embeddings"

    def encode(self, text: str) -> List[float]:
        """Encode a single text string into a 384-dimensional dense vector via API."""
        if not text:
            return [0.0] * self.DIMENSION

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
            # Force exactly 384 dimensions — matches Neo4j vector index.
            # text-embedding-3-small natively supports dimension reduction via this parameter.
            "dimensions": self.DIMENSION,
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(self.api_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    embedding = data["data"][0]["embedding"]
                    if len(embedding) != self.DIMENSION:
                        logger.warning(
                            f"Embedding API returned {len(embedding)} dims instead of {self.DIMENSION}. "
                            f"Truncating/padding to {self.DIMENSION}."
                        )
                        # Truncate or pad to ensure consistent dimension
                        embedding = (embedding + [0.0] * self.DIMENSION)[: self.DIMENSION]
                    return embedding
                else:
                    logger.warning(
                        f"Embedding API returned HTTP {resp.status_code}. Using deterministic fallback vector."
                    )
                    return self._generate_mock_vector(text)
        except Exception as e:
            logger.warning(f"Embedding API request failed: {e}. Using deterministic fallback vector.")
            return self._generate_mock_vector(text)

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into 384-dimensional dense vectors."""
        return [self.encode(text) for text in texts]

    @property
    def dimension(self) -> int:
        """Return the vector embedding dimension (always 384)."""
        return self.DIMENSION

    def _generate_mock_vector(self, text: str) -> List[float]:
        """Generate a deterministic normalized 384-dimensional vector based on SHA-256 text hash."""
        seed_hash = hashlib.sha256(text.encode("utf-8")).digest()
        raw_vals = [(b / 255.0) - 0.5 for b in (seed_hash * 12)[: self.DIMENSION]]
        norm = (sum(v**2 for v in raw_vals) ** 0.5) or 1.0
        return [v / norm for v in raw_vals]
