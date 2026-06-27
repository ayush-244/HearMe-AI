import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KeywordSearch:
    def __init__(self, bm25_k1: float = 1.5, bm25_b: float = 0.75):
        self._bm25_k1 = bm25_k1
        self._bm25_b = bm25_b
        self._use_bm25 = False
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        try:
            from rank_bm25 import BM25Okapi
            self._BM25Okapi = BM25Okapi
            self._use_bm25 = True
            logger.info("KeywordSearch using BM25Okapi backend")
        except ImportError:
            self._use_bm25 = False
            logger.info("KeywordSearch using TF-IDF fallback backend")

    def score(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if not query or not query.strip() or not candidates:
            return candidates

        start = time.time()

        tokenized_query = query.lower().split()

        texts = [c.get("text", "") or "" for c in candidates]
        tokenized_corpus = [t.lower().split() for t in texts]

        if self._use_bm25:
            scores = self._bm25_score(tokenized_query, tokenized_corpus)
        else:
            scores = self._tfidf_score(tokenized_query, tokenized_corpus)

        if scores is None or len(scores) == 0:
            max_score = 1.0
        else:
            max_score = max(scores)
        normalized = [s / max_score if max_score > 0 else 0.0 for s in scores]

        for i, chunk in enumerate(candidates):
            chunk["keyword_score"] = normalized[i]

        elapsed = time.time() - start
        logger.debug(
            "Keyword scoring: candidates=%d, backend=%s, latency=%.2fms",
            len(candidates), "BM25" if self._use_bm25 else "TF-IDF", elapsed * 1000,
        )

        return candidates

    def _bm25_score(self, tokenized_query: List[str], tokenized_corpus: List[List[str]]) -> List[float]:
        if not tokenized_corpus or all(len(doc) == 0 for doc in tokenized_corpus):
            return [0.0] * len(tokenized_corpus)
        bm25 = self._BM25Okapi(tokenized_corpus, k1=self._bm25_k1, b=self._bm25_b)
        return bm25.get_scores(tokenized_query).tolist()

    def _tfidf_score(self, tokenized_query: List[str], tokenized_corpus: List[List[str]]) -> List[float]:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        corpus = [" ".join(tokens) for tokens in tokenized_corpus]
        if not corpus or all(not doc for doc in corpus):
            return [0.0] * len(tokenized_corpus)

        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            return [0.0] * len(tokenized_corpus)

        query_str = " ".join(tokenized_query)
        try:
            query_vec = vectorizer.transform([query_str])
        except ValueError:
            return [0.0] * len(tokenized_corpus)

        similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
        return similarities.tolist()
