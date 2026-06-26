import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from ai.embeddings.embedding_model import EmbeddingModel
from ai.embeddings.embedding_cache import EmbeddingCache

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    def __init__(self, message: str, status_code: int = 422):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EmbeddingService:
    def __init__(
        self,
        embeddings_dir: Path,
        model_name: str = "BAAI/bge-base-en-v1.5",
        batch_size: int = 32,
        embedding_version: str = "1.0.0",
        max_seq_length: int = 512,
    ):
        self._embeddings_dir = Path(embeddings_dir)
        self._model_name = model_name
        self._batch_size = batch_size
        self._embedding_version = embedding_version
        self._max_seq_length = max_seq_length
        self._model: Optional[EmbeddingModel] = None
        self._cache = EmbeddingCache()
        self._embeddings_dir.mkdir(parents=True, exist_ok=True)

    def initialize(self) -> None:
        if self._model is not None and self._model.is_loaded:
            logger.debug("EmbeddingService already initialized")
            return

        logger.info(
            "Initializing EmbeddingService: model=%s, batch_size=%d, version=%s",
            self._model_name, self._batch_size, self._embedding_version,
        )
        self._model = EmbeddingModel(
            model_name=self._model_name,
            batch_size=self._batch_size,
            max_seq_length=self._max_seq_length,
        )
        self._model.initialize()
        logger.info(
            "EmbeddingService initialized: dimension=%d", self._model.dimension,
        )

    def embed_text(self, text: str) -> List[float]:
        self._ensure_initialized()
        start = time.time()
        vector = self._model.embed(text)
        elapsed = time.time() - start
        logger.debug("Embedded single text: dimension=%d, duration=%.3fs", len(vector), elapsed)
        return vector

    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        self._ensure_initialized()
        if not chunks:
            return []

        texts = [c.get("text", "") for c in chunks]
        start = time.time()

        vectors, checksums = self._cache.process_batch(texts, self._model.embed_batch)

        elapsed = time.time() - start
        logger.info(
            "Batch embedded: chunks=%d, dimension=%d, cache_hits=%d, cache_misses=%d, duration=%.2fs",
            len(chunks), self._model.dimension,
            len(chunks) - sum(1 for c in checksums if c is None),
            sum(1 for c in checksums if c is not None),
            elapsed,
        )

        results = []
        for chunk, vector, ck in zip(chunks, vectors, checksums):
            results.append({
                "chunk_id": chunk["chunk_id"],
                "checksum": ck,
                "vector": vector,
            })

        return results

    def embed_document(self, document_id: str, chunks_data: list) -> dict:
        self._ensure_initialized()

        chunks_list = chunks_data if isinstance(chunks_data, list) else chunks_data.get("chunks", [])

        if not chunks_list:
            logger.warning("No chunks to embed for document %s", document_id)
            return self._empty_result(document_id)

        logger.info(
            "Document embedding started: id=%s, chunks=%d, model=%s",
            document_id, len(chunks_list), self._model_name,
        )
        start = time.time()

        embedded = self.embed_chunks(chunks_list)

        result = {
            "document_id": document_id,
            "embedding_model": self._model_name,
            "embedding_version": self._embedding_version,
            "dimension": self._model.dimension,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "chunks": embedded,
        }

        self._save_embeddings(document_id, result)

        elapsed = time.time() - start
        logger.info(
            "Document embedding completed: id=%s, chunks=%d, duration=%.2fs",
            document_id, len(embedded), elapsed,
        )

        return result

    def get_embedding(self, document_id: str, chunk_id: str) -> Optional[dict]:
        data = self._load_embeddings(document_id)
        if data is None:
            return None

        for c in data.get("chunks", []):
            if c["chunk_id"] == chunk_id:
                return {
                    "chunk_id": c["chunk_id"],
                    "checksum": c["checksum"],
                    "dimension": data["dimension"],
                    "model": data["embedding_model"],
                    "vector": c["vector"],
                }

        return None

    def get_embedding_list(self, document_id: str) -> Optional[dict]:
        data = self._load_embeddings(document_id)
        if data is None:
            return None

        return {
            "document_id": data["document_id"],
            "embedding_model": data["embedding_model"],
            "embedding_version": data["embedding_version"],
            "dimension": data["dimension"],
            "created_at": data["created_at"],
            "chunks": [
                {
                    "chunk_id": c["chunk_id"],
                    "checksum": c["checksum"],
                    "dimension": data["dimension"],
                }
                for c in data.get("chunks", [])
            ],
        }

    def get_embedding_stats(self) -> dict:
        return {
            "model_name": self._model_name,
            "dimension": self._model.dimension if self._model else 0,
            "batch_size": self._batch_size,
            "embedding_version": self._embedding_version,
            "cache_size": self._cache.size(),
            "model_loaded": self._model is not None and self._model.is_loaded,
        }

    def is_embedded(self, document_id: str) -> bool:
        return self._embeddings_path(document_id).exists()

    def delete_embeddings(self, document_id: str) -> None:
        path = self._embeddings_path(document_id)
        if path.exists():
            try:
                path.unlink()
                logger.info("Deleted embeddings: id=%s", document_id)
            except OSError as e:
                logger.error("Failed to delete embeddings: id=%s — %s", document_id, e)

    def _embeddings_path(self, document_id: str) -> Path:
        return self._embeddings_dir / f"{document_id}.json"

    def _save_embeddings(self, document_id: str, data: dict) -> None:
        path = self._embeddings_path(document_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save embeddings: %s", e)
            raise EmbeddingError("Failed to save embeddings", status_code=500)

    def _load_embeddings(self, document_id: str) -> Optional[dict]:
        path = self._embeddings_path(document_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load embeddings: %s", e)
            return None

    def _ensure_initialized(self) -> None:
        if self._model is None or not self._model.is_loaded:
            self.initialize()

    def _empty_result(self, document_id: str) -> dict:
        dim = self._model.dimension if self._model else 0
        return {
            "document_id": document_id,
            "embedding_model": self._model_name,
            "embedding_version": self._embedding_version,
            "dimension": dim,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "chunks": [],
        }
