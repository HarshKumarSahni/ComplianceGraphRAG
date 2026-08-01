from typing import List, Optional
from app.core.config import Settings
from app.core.logger import logger


class EmbeddingService:
    """Lazy-loaded sentence-transformers wrapper for query-time embedding.

    The model is loaded on first call and cached for subsequent uses.
    This avoids startup latency when the service is not needed.
    """

    def __init__(self, settings: Settings):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self._model = None

    def _load_model(self):
        """Load the sentence-transformer model on first use."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading embedding model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Embedding model loaded: {self.model_name} (dim={self._model.get_sentence_embedding_dimension()})")
            except Exception as e:
                logger.error(f"Failed to load embedding model '{self.model_name}': {e}")
                raise

    def encode(self, text: str) -> List[float]:
        """Encode a single text string into a dense vector."""
        self._load_model()
        embedding = self._model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Encode multiple texts into dense vectors."""
        if not texts:
            return []
        self._load_model()
        embeddings = self._model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [emb.tolist() for emb in embeddings]

    @property
    def dimension(self) -> int:
        """Return the embedding dimension of the loaded model."""
        self._load_model()
        return self._model.get_sentence_embedding_dimension()
