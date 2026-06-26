import logging
import time
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class EmbeddingModel:
    def __init__(
        self,
        model_name: str = "BAAI/bge-base-en-v1.5",
        batch_size: int = 32,
        max_seq_length: int = 512,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.batch_size = batch_size
        self.max_seq_length = max_seq_length
        self._device = device
        self._model = None
        self._dimension = 0
        self._loaded = False

    def initialize(self) -> None:
        if self._loaded:
            logger.debug("Embedding model already loaded: %s", self.model_name)
            return

        logger.info("Loading embedding model: %s", self.model_name)
        start = time.time()

        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                self.model_name,
                device=self._device,
            )
            if self.max_seq_length:
                self._model.max_seq_length = self.max_seq_length

            self._dimension = self._model.get_sentence_embedding_dimension()
            self._loaded = True

            elapsed = time.time() - start
            logger.info(
                "Embedding model loaded: name=%s, dimension=%d, device=%s, duration=%.2fs",
                self.model_name, self._dimension, self._device or "auto", elapsed,
            )
        except Exception as e:
            logger.error("Failed to load embedding model '%s': %s", self.model_name, e)
            raise

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def embed(self, text: str) -> List[float]:
        self._ensure_initialized()
        if not text or not text.strip():
            return [0.0] * self._dimension
        vector = self._model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        self._ensure_initialized()
        if not texts:
            return []

        valid_texts = [t if t and t.strip() else "" for t in texts]
        vectors = self._model.encode(
            valid_texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [v.tolist() if v is not None else [0.0] * self._dimension for v in vectors]

    def get_model_info(self) -> dict:
        self._ensure_initialized()
        return {
            "model_name": self.model_name,
            "dimension": self._dimension,
            "max_seq_length": self.max_seq_length,
            "batch_size": self.batch_size,
            "device": str(self._model.device) if self._model else "unknown",
        }

    def _ensure_initialized(self) -> None:
        if not self._loaded:
            self.initialize()
