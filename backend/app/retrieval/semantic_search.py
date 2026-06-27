import logging
import time
from typing import Any, Dict, List, Optional

from ..vectorstore.base import VectorStore
from ..services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class SemanticSearch:
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        top_k: int = 10,
        min_score: float = 0.0,
    ):
        self._embedding_service = embedding_service
        self._vector_store = vector_store
        self._top_k = top_k
        self._min_score = min_score

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        k = top_k if top_k is not None else self._top_k
        score_threshold = min_score if min_score is not None else self._min_score

        start = time.time()

        query_vector = self._embedding_service.embed_text(query)

        embed_latency = time.time() - start
        logger.debug("Query embedding: dimension=%d, latency=%.2fms", len(query_vector), embed_latency * 1000)

        search_start = time.time()
        results = self._vector_store.search(
            query_vector=query_vector,
            top_k=k,
            filter_conditions=filters,
        )
        search_latency = time.time() - search_start

        filtered = []
        for r in results:
            score = r.get("score", 0.0)
            if score >= score_threshold:
                filtered.append(r)

        elapsed = time.time() - start
        logger.info(
            "Semantic search: query='%s', top_k=%d, candidates=%d, passed_threshold=%d, latency=%.2fms",
            query[:50], k, len(results), len(filtered), elapsed * 1000,
        )

        return filtered

    def health(self) -> Dict[str, Any]:
        model_loaded = False
        try:
            stats = self._embedding_service.get_embedding_stats()
            model_loaded = stats.get("model_loaded", False)
        except Exception:
            pass
        vs_healthy = False
        try:
            h = self._vector_store.health()
            vs_healthy = h.get("status") == "healthy"
        except Exception:
            pass
        return {
            "ready": model_loaded and vs_healthy,
            "embedding_model_loaded": model_loaded,
            "vector_store_healthy": vs_healthy,
        }
