import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .memory_models import MemoryEntry, MemoryQuery, MemoryType

logger = logging.getLogger(__name__)


class MemoryRetriever:
    def __init__(self, top_k: int = 10):
        self._top_k = top_k
        logger.info("MemoryRetriever initialized: top_k=%d", top_k)

    def retrieve(
        self,
        query: MemoryQuery,
        entries: List[MemoryEntry],
    ) -> List[MemoryEntry]:
        start = time.time()

        if not entries:
            logger.debug("MemoryRetriever: no entries to search")
            return []

        filtered = self._apply_filters(query, entries)

        if not filtered:
            logger.debug("MemoryRetriever: no entries after filters")
            return []

        scored = self._score_relevance(query, filtered)

        scored.sort(key=lambda x: x[1], reverse=True)

        top_k = query.top_k or self._top_k
        query_words = set(self._tokenize(query.query))
        results = []
        for entry, score in scored[:top_k]:
            if query_words:
                entry_words = set(self._tokenize(entry.content)) | set(self._tokenize(entry.summary))
                has_match = bool(query_words & entry_words)
                if not has_match and score <= (entry.importance * 0.4 + 0.1):
                    continue
            results.append(entry)

        for entry in results:
            entry.touch()

        elapsed = (time.time() - start) * 1000
        logger.debug(
            "MemoryRetriever: query='%s', filtered=%d, results=%d, time=%.2fms",
            query.query[:40], len(filtered), len(results), elapsed,
        )

        return results

    def _apply_filters(
        self, query: MemoryQuery, entries: List[MemoryEntry]
    ) -> List[MemoryEntry]:
        result = entries

        if not query.include_working:
            result = [e for e in result if e.type != MemoryType.WORKING]

        if query.memory_types:
            result = [e for e in result if e.type in query.memory_types]

        if query.user_id:
            result = [e for e in result if e.user_id == query.user_id]

        if query.workspace_id:
            result = [e for e in result if e.workspace_id == query.workspace_id]

        if query.min_importance > 0:
            result = [e for e in result if e.importance >= query.min_importance]

        return result

    def _score_relevance(
        self, query: MemoryQuery, entries: List[MemoryEntry]
    ) -> List[Tuple[MemoryEntry, float]]:
        query_words = set(self._tokenize(query.query))
        if not query_words:
            return [(e, e.importance) for e in entries]

        scored: List[Tuple[MemoryEntry, float]] = []
        for entry in entries:
            lexical = self._lexical_score(query_words, entry)
            importance = entry.importance * 0.4
            recency = self._recency_weight(entry) * 0.1
            total = lexical + importance + recency
            scored.append((entry, round(total, 4)))

        return scored

    def _lexical_score(self, query_words: set, entry: MemoryEntry) -> float:
        content_words = set(self._tokenize(entry.content))
        summary_words = set(self._tokenize(entry.summary))
        all_words = content_words | summary_words

        if not all_words:
            return 0.0

        overlap = query_words & all_words
        if not overlap:
            return 0.0

        raw_score = len(overlap) / len(query_words)
        exact_matches = sum(1 for w in overlap if len(w) > 3)
        bonus = min(exact_matches * 0.05, 0.2)

        return round(min(raw_score + bonus, 1.0), 4)

    def _recency_weight(self, entry: MemoryEntry) -> float:
        try:
            from datetime import datetime, timezone
            accessed = datetime.fromisoformat(entry.last_accessed)
            now = datetime.now(timezone.utc)
            delta_days = (now - accessed).total_seconds() / 86400
            if delta_days < 1:
                return 1.0
            elif delta_days < 7:
                return 0.8
            elif delta_days < 30:
                return 0.5
            elif delta_days < 90:
                return 0.3
            else:
                return 0.1
        except (ValueError, TypeError):
            return 0.5

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r"[a-zA-Z0-9_]+", text)
        return [t for t in tokens if len(t) > 1]
