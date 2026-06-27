import logging
import time
from typing import Any, Dict, List, Optional

from .search_models import SearchQuery, SearchResult, SearchResultItem, SearchStatistics
from .query_parser import QueryParser
from .query_analyzer import QueryAnalyzer
from .semantic_search import SemanticSearch
from .keyword_search import KeywordSearch
from .hybrid_ranker import HybridRanker
from .citation_builder import CitationBuilder
from .retrieval_metrics import RetrievalMetrics

logger = logging.getLogger(__name__)


class SearchEngine:
    def __init__(
        self,
        semantic_search: SemanticSearch,
        keyword_search: KeywordSearch,
        hybrid_ranker: HybridRanker,
        query_analyzer: Optional[QueryAnalyzer] = None,
        citation_builder: Optional[CitationBuilder] = None,
        metrics: Optional[RetrievalMetrics] = None,
        top_k: int = 10,
        min_score: float = 0.0,
    ):
        self._semantic_search = semantic_search
        self._keyword_search = keyword_search
        self._hybrid_ranker = hybrid_ranker
        self._query_analyzer = query_analyzer or QueryAnalyzer()
        self._citation_builder = citation_builder or CitationBuilder()
        self._metrics = metrics or RetrievalMetrics()
        self._parser = QueryParser()
        self._top_k = top_k
        self._min_score = min_score

    def search(self, query: SearchQuery) -> SearchResult:
        total_start = time.time()

        if not query.text or not query.text.strip():
            logger.warning("Empty search query rejected")
            return SearchResult(
                query=query.text or "",
                processing_time_ms=0.0,
            )

        logger.info(
            "Search request: query='%s', workspace=%s, top_k=%d, filters=%s",
            query.text[:80], query.workspace_id, query.top_k, query.filters,
        )

        parsed = self._parser.parse(query.text)

        query_analysis = self._query_analyzer.analyze(query.text)
        logger.debug(
            "Query analysis: lang=%s, intent=%s, complexity=%s",
            query_analysis.get("language"), query_analysis.get("intent"),
            query_analysis.get("complexity"),
        )

        search_filters: Dict[str, Any] = {}

        if query.workspace_id and query.workspace_id != "default":
            search_filters["workspace_id"] = query.workspace_id

        for fk, fv in (query.filters or {}).items():
            search_filters[fk] = fv

        parsed_filters = parsed.get("filters", {})
        for fk, fv in parsed_filters.items():
            search_filters[fk] = fv

        if query.language:
            search_filters["language"] = query.language
        if query.document_type:
            search_filters["document_type"] = query.document_type
        if query.document_ids:
            search_filters["document_id"] = query.document_ids

        estimated_top_k = query.top_k or self._top_k
        semantic_extra = estimated_top_k * 3

        semantic_start = time.time()
        semantic_results = self._semantic_search.search(
            query=query.text,
            top_k=semantic_extra,
            min_score=query.min_score or self._min_score,
            filters=search_filters if search_filters else None,
        )
        semantic_latency = (time.time() - semantic_start) * 1000

        keyword_start = time.time()
        keyword_results = self._keyword_search.score(
            query=parsed.get("clean_query", query.text),
            candidates=semantic_results,
        )
        keyword_latency = (time.time() - keyword_start) * 1000

        ranking_start = time.time()
        final_results = self._hybrid_ranker.rank(
            candidates=keyword_results,
            query=query.text,
            top_k=estimated_top_k,
            query_analysis=query_analysis,
        )
        ranking_latency = (time.time() - ranking_start) * 1000

        items = []
        for r in final_results:
            items.append(SearchResultItem(
                chunk_id=r.get("chunk_id", ""),
                document_id=r.get("document_id", ""),
                text=r.get("text", ""),
                title=r.get("title", ""),
                section=r.get("section", ""),
                page=r.get("page", 0),
                score=r.get("final_score", r.get("score", 0.0)),
                semantic_score=r.get("semantic_score", 0.0),
                keyword_score=r.get("keyword_score", 0.0),
                metadata_score=r.get("metadata_score", 0.0),
                language=r.get("language", ""),
                document_type=r.get("document_type", ""),
                workspace_id=r.get("workspace_id", "default"),
                chunk_index=r.get("chunk_index", 0),
                word_count=r.get("word_count", 0),
                keywords=r.get("keywords", []),
            ))

        citations = self._citation_builder.build_citations(final_results)

        total_latency = (time.time() - total_start) * 1000

        avg_sem = 0.0
        avg_key = 0.0
        avg_final = 0.0
        if items:
            avg_sem = sum(i.semantic_score for i in items) / len(items)
            avg_key = sum(i.keyword_score for i in items) / len(items)
            avg_final = sum(i.score for i in items) / len(items)

        stats = SearchStatistics(
            total_chunks_searched=len(semantic_results),
            semantic_chunks_retrieved=len(semantic_results),
            keyword_chunks_scored=len(keyword_results),
            final_chunks_returned=len(items),
            avg_semantic_score=round(avg_sem, 4),
            avg_keyword_score=round(avg_key, 4),
            avg_final_score=round(avg_final, 4),
            semantic_latency_ms=round(semantic_latency, 2),
            keyword_latency_ms=round(keyword_latency, 2),
            ranking_latency_ms=round(ranking_latency, 2),
            total_latency_ms=round(total_latency, 2),
        )

        self._metrics.record_query(
            query=query.text,
            latency_ms=total_latency,
            chunks_searched=len(semantic_results),
            chunks_returned=len(items),
            avg_score=avg_final,
            semantic_latency_ms=semantic_latency,
            keyword_latency_ms=keyword_latency,
            ranking_latency_ms=ranking_latency,
        )

        logger.info(
            "Search result: query='%s', semantic=%d, keyword=%d, final=%d, top_score=%.4f, latency=%.2fms",
            query.text[:50], len(semantic_results), len(keyword_results), len(items),
            items[0].score if items else 0.0, total_latency,
        )

        return SearchResult(
            query=query.text,
            results=items,
            citations=citations,
            statistics=stats,
            processing_time_ms=round(total_latency, 2),
            query_analysis=query_analysis,
        )

    def health(self) -> Dict[str, Any]:
        semantic_health = self._semantic_search.health()
        stats = self._metrics.get_statistics()

        return {
            "ready": semantic_health.get("ready", False),
            "embedding_model_loaded": semantic_health.get("embedding_model_loaded", False),
            "vector_store_healthy": semantic_health.get("vector_store_healthy", False),
            "keyword_backend": "BM25" if self._keyword_search._use_bm25 else "TF-IDF",
            "ranking_weights": self._hybrid_ranker.get_weights(),
            "statistics": stats,
        }

    def get_metrics(self) -> RetrievalMetrics:
        return self._metrics

    @property
    def query_analyzer(self) -> QueryAnalyzer:
        return self._query_analyzer
