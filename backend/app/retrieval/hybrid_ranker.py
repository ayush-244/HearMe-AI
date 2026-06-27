import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class HybridRanker:
    def __init__(
        self,
        semantic_weight: float = 0.65,
        keyword_weight: float = 0.25,
        metadata_weight: float = 0.10,
        default_top_k: int = 10,
        max_context_chunks: int = 20,
        minimum_similarity: float = 0.0,
    ):
        self._semantic_weight = semantic_weight
        self._keyword_weight = keyword_weight
        self._metadata_weight = metadata_weight
        self._default_top_k = default_top_k
        self._max_context_chunks = max_context_chunks
        self._minimum_similarity = minimum_similarity

    def rank(
        self,
        candidates: List[Dict[str, Any]],
        query: str = "",
        top_k: Optional[int] = None,
        query_analysis: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        if not candidates:
            return []

        start = time.time()
        k = top_k if top_k is not None else self._default_top_k

        scored = []
        for chunk in candidates:
            semantic_score = chunk.get("score", 0.0)
            keyword_score = chunk.get("keyword_score", 0.0)

            metadata_score = self._compute_metadata_score(chunk, query, query_analysis)

            combined = (
                self._semantic_weight * semantic_score
                + self._keyword_weight * keyword_score
                + self._metadata_weight * metadata_score
            )

            chunk["semantic_score"] = semantic_score
            chunk["metadata_score"] = metadata_score

            if combined >= self._minimum_similarity:
                chunk["final_score"] = combined
                scored.append(chunk)

        scored.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)

        deduplicated = self._deduplicate(scored)

        diverse = self._ensure_section_diversity(deduplicated, k)

        top_n = diverse[: min(k, self._max_context_chunks)]

        elapsed = time.time() - start
        logger.info(
            "Hybrid ranker: candidates=%d, after_dedup=%d, after_diversity=%d, final=%d, elapsed=%.2fms",
            len(candidates), len(deduplicated), len(diverse), len(top_n), elapsed * 1000,
        )

        return top_n

    def _compute_metadata_score(
        self,
        chunk: Dict[str, Any],
        query: str,
        query_analysis: Optional[Dict[str, Any]],
    ) -> float:
        score = 0.0
        boosts = 0

        if query_analysis:
            query_lang = query_analysis.get("language", "")
            chunk_lang = chunk.get("language", "")
            if query_lang and chunk_lang and query_lang == chunk_lang:
                score += 0.3
                boosts += 1

            query_type = query_analysis.get("document_type", "")
            chunk_type = chunk.get("document_type", "")
            if query_type and chunk_type and query_type == chunk_type:
                score += 0.2
                boosts += 1

        query_lower = query.lower()
        chunk_title = (chunk.get("title", "") or "").lower()
        if chunk_title and any(word in chunk_title for word in query_lower.split()):
            score += 0.25
            boosts += 1

        section = (chunk.get("section", "") or "").lower()
        if section and any(word in section for word in query_lower.split()):
            score += 0.15
            boosts += 1

        importance = chunk.get("importance_score", 1.0)
        if importance > 1.0:
            score += 0.1 * (importance - 1.0)
            boosts += 1

        chunk_keywords = chunk.get("keywords", []) or []
        query_keywords = [w for w in query_lower.split() if len(w) > 2]
        if chunk_keywords and query_keywords:
            overlap = sum(1 for kw in query_keywords if kw in [k.lower() for k in chunk_keywords])
            if overlap > 0:
                score += 0.1 * min(overlap / len(query_keywords), 1.0)
                boosts += 1

        return score / max(boosts, 1)

    def _deduplicate(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "")
            text = (chunk.get("text", "") or "").strip()
            if not text:
                continue
            if chunk_id in seen:
                continue
            text_key = text[:100].lower()
            is_dup = False
            for existing in unique:
                existing_text = (existing.get("text", "") or "")[:100].lower()
                if self._texts_are_near_identical(text_key, existing_text):
                    is_dup = True
                    break
            if not is_dup:
                seen.add(chunk_id)
                unique.append(chunk)
        return unique

    def _texts_are_near_identical(self, a: str, b: str) -> bool:
        if not a or not b:
            return False
        if len(a) < 20 or len(b) < 20:
            return a == b
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio() > 0.85

    def _ensure_section_diversity(self, chunks: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        if not chunks:
            return []

        max_per_section = max(1, top_k // 3)

        section_counts: Dict[str, int] = {}
        diverse = []
        for chunk in chunks:
            section = chunk.get("section", "") or "general"
            if section_counts.get(section, 0) < max_per_section:
                diverse.append(chunk)
                section_counts[section] = section_counts.get(section, 0) + 1
            elif len(diverse) < top_k:
                diverse.append(chunk)

        return diverse

    def get_weights(self) -> Dict[str, float]:
        return {
            "semantic_weight": self._semantic_weight,
            "keyword_weight": self._keyword_weight,
            "metadata_weight": self._metadata_weight,
        }
