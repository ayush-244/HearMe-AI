import logging
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RetrievalMetrics:
    def __init__(self, max_history: int = 1000):
        self._max_history = max_history
        self._queries: deque = deque(maxlen=max_history)

    def record_query(
        self,
        query: str,
        latency_ms: float,
        chunks_searched: int,
        chunks_returned: int,
        avg_score: float,
        semantic_latency_ms: float = 0.0,
        keyword_latency_ms: float = 0.0,
        ranking_latency_ms: float = 0.0,
    ) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query[:100],
            "latency_ms": round(latency_ms, 2),
            "chunks_searched": chunks_searched,
            "chunks_returned": chunks_returned,
            "avg_score": round(avg_score, 4),
            "semantic_latency_ms": round(semantic_latency_ms, 2),
            "keyword_latency_ms": round(keyword_latency_ms, 2),
            "ranking_latency_ms": round(ranking_latency_ms, 2),
        }
        self._queries.append(record)

    def get_statistics(self) -> Dict[str, Any]:
        if not self._queries:
            return {
                "total_queries": 0,
                "avg_latency_ms": 0.0,
                "avg_chunks_returned": 0.0,
                "avg_score": 0.0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
            }

        latencies = [q["latency_ms"] for q in self._queries]
        scores = [q["avg_score"] for q in self._queries if q["avg_score"] > 0]
        returned = [q["chunks_returned"] for q in self._queries]

        sorted_lat = sorted(latencies)

        def percentile(data, p):
            if not data:
                return 0.0
            idx = max(0, min(len(data) - 1, int(len(data) * p / 100)))
            return data[idx]

        return {
            "total_queries": len(self._queries),
            "avg_latency_ms": round(sum(latencies) / len(latencies), 2),
            "avg_chunks_returned": round(sum(returned) / len(returned), 2) if returned else 0.0,
            "avg_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
            "p50_latency_ms": round(percentile(sorted_lat, 50), 2),
            "p95_latency_ms": round(percentile(sorted_lat, 95), 2),
            "p99_latency_ms": round(percentile(sorted_lat, 99), 2),
            "min_latency_ms": round(sorted_lat[0], 2) if sorted_lat else 0.0,
            "max_latency_ms": round(sorted_lat[-1], 2) if sorted_lat else 0.0,
        }

    def get_recent_queries(self, n: int = 10) -> List[Dict[str, Any]]:
        return list(self._queries)[-n:]

    def clear(self) -> None:
        self._queries.clear()
        logger.info("Retrieval metrics cleared")
