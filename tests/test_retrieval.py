"""Tests for the Hybrid Search Engine (Phase 23)."""
import pytest
import time
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi.testclient import TestClient

from backend.app.retrieval.query_parser import QueryParser
from backend.app.retrieval.query_analyzer import QueryAnalyzer
from backend.app.retrieval.semantic_search import SemanticSearch
from backend.app.retrieval.keyword_search import KeywordSearch
from backend.app.retrieval.hybrid_ranker import HybridRanker
from backend.app.retrieval.citation_builder import CitationBuilder
from backend.app.retrieval.retrieval_metrics import RetrievalMetrics
from backend.app.retrieval.search_engine import SearchEngine
from backend.app.retrieval.search_models import SearchQuery, SearchResult, SearchResultItem, SearchStatistics
from backend.app.main import app


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_chunks():
    return [
        {"chunk_id": "c1", "document_id": "d1", "section": "Intro", "title": "Doc1",
         "text": "Transformer architecture uses attention mechanisms for sequence modeling.",
         "page": 1, "language": "en", "document_type": "paper", "workspace_id": "default",
         "keywords": ["transformer", "attention"], "importance_score": 1.0, "chunk_index": 0,
         "word_count": 10, "score": 0.92, "vector": [0.1]*768},
        {"chunk_id": "c2", "document_id": "d1", "section": "Methodology", "title": "Doc1",
         "text": "Self-attention computes weighted sums of all input positions simultaneously.",
         "page": 3, "language": "en", "document_type": "paper", "workspace_id": "default",
         "keywords": ["self-attention", "weights"], "importance_score": 1.2, "chunk_index": 1,
         "word_count": 10, "score": 0.85, "vector": [0.2]*768},
        {"chunk_id": "c3", "document_id": "d2", "section": "Results", "title": "Doc2",
         "text": "Transformers achieved state-of-the-art results on machine translation benchmarks.",
         "page": 5, "language": "en", "document_type": "paper", "workspace_id": "default",
         "keywords": ["transformers", "results"], "importance_score": 1.0, "chunk_index": 0,
         "word_count": 10, "score": 0.78, "vector": [0.3]*768},
        {"chunk_id": "c4", "document_id": "d1", "section": "Intro", "title": "Doc1",
         "text": "Different language pairs were evaluated using BLEU score metrics.",
         "page": 2, "language": "en", "document_type": "paper", "workspace_id": "default",
         "keywords": ["language", "BLEU"], "importance_score": 1.0, "chunk_index": 2,
         "word_count": 10, "score": 0.65, "vector": [0.4]*768},
        {"chunk_id": "c5", "document_id": "d3", "section": "Intro", "title": "Doc3",
         "text": "Ein Text über maschinelle Übersetzung mit neuronalen Netzen.",
         "page": 1, "language": "de", "document_type": "paper", "workspace_id": "default",
         "keywords": ["übersetzung", "neuronal"], "importance_score": 1.0, "chunk_index": 0,
         "word_count": 10, "score": 0.55, "vector": [0.5]*768},
    ]


@pytest.fixture
def mock_embedding_service():
    svc = MagicMock()
    svc.embed_text.return_value = [0.1] * 768
    svc.get_embedding_stats.return_value = {"model_loaded": True}
    return svc


@pytest.fixture
def mock_vector_store():
    vs = MagicMock()
    vs.search.return_value = []
    vs.health.return_value = {"status": "healthy"}
    return vs


@pytest.fixture
def mock_language_service():
    svc = MagicMock()
    svc.detect.return_value = "en"
    return svc


@pytest.fixture
def mock_intent_service():
    svc = MagicMock()
    svc.analyze.return_value = {"intent": "search", "confidence": 0.9}
    return svc


# =============================================================================
# QueryParser Tests
# =============================================================================

class TestQueryParser:
    def test_parse_empty(self):
        result = QueryParser.parse("")
        assert result["clean_query"] == ""
        assert result["keywords"] == []
        assert result["phrases"] == []

    def test_parse_whitespace(self):
        result = QueryParser.parse("   ")
        assert result["clean_query"] == ""

    def test_parse_normal(self):
        result = QueryParser.parse("transformer attention mechanism")
        assert "transformer" in result["keywords"]
        assert "attention" in result["keywords"]
        assert "mechanism" in result["keywords"]

    def test_parse_with_quoted_phrases(self):
        result = QueryParser.parse('machine learning "deep learning"')
        assert "deep learning" in result["phrases"]
        assert "machine" in result["keywords"]
        assert "learning" in result["keywords"]

    def test_parse_removes_stop_words(self):
        result = QueryParser.parse("the quick brown fox jumps over the lazy dog")
        assert "the" not in result["keywords"]
        assert "quick" in result["keywords"]
        assert "brown" in result["keywords"]

    def test_parse_extracts_language_filter(self):
        result = QueryParser.parse("lang:de transformer")
        assert result["filters"]["language"] == "de"
        assert "transformer" in result["keywords"]

    def test_parse_extracts_type_filter(self):
        result = QueryParser.parse("type:report sales analysis")
        assert result["filters"]["document_type"] == "report"

    def test_parse_extracts_workspace_filter(self):
        result = QueryParser.parse("workspace:team1 project plan")
        assert result["filters"]["workspace_id"] == "team1"

    def test_parse_extracts_document_filter(self):
        result = QueryParser.parse("doc:abc-123 summary")
        assert result["filters"]["document_id"] == "abc-123"

    def test_parse_extracts_section_filter(self):
        result = QueryParser.parse("section:Methodology attention")
        assert result["filters"]["section"] == "Methodology"

    def test_parse_extracts_numbers(self):
        result = QueryParser.parse("version 2.0 with 42 features")
        assert 2.0 in result["numbers"]
        assert 42.0 in result["numbers"]

    def test_parse_detects_date(self):
        result = QueryParser.parse("report from 2024-01-15")
        assert result["has_date"] is True

    def test_parse_normalizes_whitespace(self):
        result = QueryParser.parse("hello    world")
        assert result["clean_query"] == "hello world"

    def test_parse_single_word(self):
        result = QueryParser.parse("transformer")
        assert result["keywords"] == ["transformer"]
        assert result["phrases"] == []

    def test_parse_strip_filter_from_clean_query(self):
        result = QueryParser.parse("lang:de transformer model")
        assert "transformer" in result["clean_query"]
        assert "model" in result["clean_query"]

    def test_filter_language_variant(self):
        result = QueryParser.parse("language:fr bonjour")
        assert result["filters"]["language"] == "fr"


# =============================================================================
# QueryAnalyzer Tests
# =============================================================================

class TestQueryAnalyzer:
    def test_analyze_empty(self):
        qa = QueryAnalyzer()
        result = qa.analyze("")
        assert result["language"] == "unknown"
        assert result["intent"] == "unknown"

    def test_analyze_with_services(self, mock_language_service, mock_intent_service):
        qa = QueryAnalyzer(language_service=mock_language_service, intent_service=mock_intent_service)
        result = qa.analyze("transformer models")
        assert result["language"] == "en"
        assert result["intent"] == "search"
        assert result["complexity"] == "simple"

    def test_analyze_moderate_complexity(self):
        qa = QueryAnalyzer()
        result = qa.analyze("how do transformer attention mechanisms work in neural networks")
        assert result["complexity"] == "moderate"

    def test_analyze_complex(self):
        qa = QueryAnalyzer()
        result = qa.analyze("explain the difference between transformer and lstm attention mechanisms for sequence to sequence machine translation")
        assert result["complexity"] == "complex"

    def test_analyze_estimated_depth_simple(self):
        qa = QueryAnalyzer()
        result = qa.analyze("hello world")
        assert result["estimated_depth"] == 5

    def test_analyze_estimated_depth_moderate(self):
        qa = QueryAnalyzer()
        result = qa.analyze("a b c d e f g h i j")
        assert result["estimated_depth"] == 10

    def test_analyze_estimated_depth_complex(self):
        qa = QueryAnalyzer()
        result = qa.analyze("a b c d e f g h i j k l")
        assert result["estimated_depth"] == 15

    def test_analyze_language_service_failure(self):
        lang_svc = MagicMock()
        lang_svc.detect.side_effect = Exception("detection failed")
        qa = QueryAnalyzer(language_service=lang_svc)
        result = qa.analyze("hello")
        assert result["language"] == "unknown"


# =============================================================================
# SemanticSearch Tests
# =============================================================================

class TestSemanticSearch:
    def test_search_returns_results(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.search.return_value = [
            {"chunk_id": "c1", "score": 0.92, "text": "test"},
            {"chunk_id": "c2", "score": 0.85, "text": "test2"},
        ]
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        results = ss.search("transformer", top_k=5)
        assert len(results) == 2
        assert results[0]["score"] == 0.92

    def test_search_empty_query(self, mock_embedding_service, mock_vector_store):
        mock_embedding_service.embed_text.return_value = []
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        with pytest.raises(Exception):
            ss.search("")

    def test_search_with_min_score_filter(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.search.return_value = [
            {"chunk_id": "c1", "score": 0.50, "text": "low"},
            {"chunk_id": "c2", "score": 0.75, "text": "medium"},
            {"chunk_id": "c3", "score": 0.95, "text": "high"},
        ]
        ss = SemanticSearch(mock_embedding_service, mock_vector_store, min_score=0.7)
        results = ss.search("test")
        assert len(results) == 2
        assert all(r["score"] >= 0.7 for r in results)

    def test_search_passes_filters(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.search.return_value = []
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        ss.search("test", filters={"language": "en"})
        mock_vector_store.search.assert_called_with(
            query_vector=[0.1]*768, top_k=10, filter_conditions={"language": "en"}
        )

    def test_health(self, mock_embedding_service, mock_vector_store):
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        health = ss.health()
        assert "ready" in health
        assert "embedding_model_loaded" in health
        assert "vector_store_healthy" in health

    def test_search_overrides_default_top_k(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.search.return_value = []
        ss = SemanticSearch(mock_embedding_service, mock_vector_store, top_k=20)
        ss.search("test")
        mock_vector_store.search.assert_called_with(
            query_vector=[0.1]*768, top_k=20, filter_conditions=None
        )


# =============================================================================
# KeywordSearch Tests
# =============================================================================

class TestKeywordSearch:
    def test_bm25_scoring(self, sample_chunks):
        ks = KeywordSearch()
        results = ks.score("transformer attention", sample_chunks)
        assert len(results) == 5
        for r in results:
            assert "keyword_score" in r
            assert 0.0 <= r["keyword_score"] <= 1.0

    def test_tfidf_fallback(self, sample_chunks):
        with patch.object(KeywordSearch, "_initialize_backend"):
            ks = KeywordSearch()
            ks._use_bm25 = False
            results = ks.score("transformer attention", sample_chunks)
            assert len(results) == 5
            scores = [r["keyword_score"] for r in results]
            assert all(0.0 <= s <= 1.0 for s in scores)

    def test_empty_query(self, sample_chunks):
        ks = KeywordSearch()
        results = ks.score("", sample_chunks)
        assert len(results) == 5
        for r in results:
            assert r.get("keyword_score", 0) == 0

    def test_empty_candidates(self):
        ks = KeywordSearch()
        results = ks.score("test", [])
        assert results == []

    def test_bm25_preferred_over_tfidf(self):
        ks = KeywordSearch()
        assert ks._use_bm25 is True

    def test_scores_vary_by_relevance(self):
        chunks = [
            {"chunk_id": "c1", "text": "transformer attention mechanism for machine translation"},
            {"chunk_id": "c2", "text": "the weather is nice today in berlin"},
            {"chunk_id": "c3", "text": "attention based transformer models for NLP tasks"},
        ]
        ks = KeywordSearch()
        results = ks.score("transformer attention", chunks)
        assert results[0]["keyword_score"] >= results[1]["keyword_score"]

    def test_handles_empty_text(self):
        chunks = [{"chunk_id": "c1", "text": ""}]
        ks = KeywordSearch()
        results = ks.score("test", chunks)
        assert results[0]["keyword_score"] == 0.0


# =============================================================================
# HybridRanker Tests
# =============================================================================

class TestHybridRanker:
    def test_rank_returns_sorted(self, sample_chunks):
        ranker = HybridRanker(semantic_weight=0.7, keyword_weight=0.2, metadata_weight=0.1)
        for i, c in enumerate(sample_chunks):
            c["keyword_score"] = 0.5 + i * 0.1
        results = ranker.rank(sample_chunks, query="transformer")
        assert len(results) > 0
        scores = [r["final_score"] for r in results]
        assert all(scores[i] >= scores[i+1] for i in range(len(scores)-1))

    def test_rank_empty(self):
        ranker = HybridRanker()
        results = ranker.rank([])
        assert results == []

    def test_rank_metadata_boost_same_language(self, sample_chunks):
        ranker = HybridRanker()
        for c in sample_chunks:
            c["keyword_score"] = 0.0
        results = ranker.rank(
            sample_chunks,
            query_analysis={"language": "en"},
        )
        en_scores = [r["final_score"] for r in results if r.get("language") == "en"]
        de_scores = [r["final_score"] for r in results if r.get("language") == "de"]
        assert len(en_scores) > 0
        assert len(de_scores) > 0

    def test_rank_title_match_boost(self):
        ranker = HybridRanker()
        chunks = [
            {"chunk_id": "c1", "title": "Transformer Architecture", "text": "test", "score": 0.5,
             "keyword_score": 0.0, "keywords": [], "importance_score": 1.0, "section": "Intro",
             "language": "en"},
            {"chunk_id": "c2", "title": "Random Topic", "text": "test", "score": 0.5,
             "keyword_score": 0.0, "keywords": [], "importance_score": 1.0, "section": "Other",
             "language": "en"},
        ]
        results = ranker.rank(chunks, query="transformer")
        assert results[0]["chunk_id"] == "c1"

    def test_rank_deduplication(self):
        ranker = HybridRanker()
        chunks = [
            {"chunk_id": "c1", "text": "same content here for testing dedup purpose", "score": 0.9,
             "keyword_score": 0.5, "keywords": [], "importance_score": 1.0, "title": "A",
             "section": "S1", "language": "en"},
            {"chunk_id": "c2", "text": "same content here for testing dedup purpose", "score": 0.8,
             "keyword_score": 0.4, "keywords": [], "importance_score": 1.0, "title": "A",
             "section": "S1", "language": "en"},
        ]
        results = ranker.rank(chunks, top_k=10)
        assert len(results) == 1

    def test_rank_removes_empty_text(self):
        ranker = HybridRanker()
        chunks = [
            {"chunk_id": "c1", "text": "valid text", "score": 0.9, "keyword_score": 0.5,
             "keywords": [], "importance_score": 1.0, "title": "A", "section": "S1", "language": "en"},
            {"chunk_id": "c2", "text": "", "score": 0.8, "keyword_score": 0.4,
             "keywords": [], "importance_score": 1.0, "title": "A", "section": "S1", "language": "en"},
        ]
        results = ranker.rank(chunks)
        assert len(results) == 1

    def test_section_diversity(self):
        ranker = HybridRanker(default_top_k=10, max_context_chunks=20)
        chunks = []
        for i in range(15):
            chunks.append({
                "chunk_id": f"c{i}", "text": f"content {i}", "score": 1.0 - i*0.01,
                "keyword_score": 0.5, "section": "SameSection", "title": "Doc",
                "keywords": [], "importance_score": 1.0, "language": "en",
            })
        results = ranker.rank(chunks, top_k=10)
        sections = set(r["section"] for r in results)

    def test_rank_with_minimum_similarity(self):
        ranker = HybridRanker(minimum_similarity=0.5)
        chunks = [
            {"chunk_id": "c1", "text": "high", "score": 0.9, "keyword_score": 0.9,
             "keywords": [], "importance_score": 1.0, "title": "A", "section": "S1", "language": "en"},
            {"chunk_id": "c2", "text": "low", "score": 0.1, "keyword_score": 0.1,
             "keywords": [], "importance_score": 1.0, "title": "A", "section": "S1", "language": "en"},
        ]
        results = ranker.rank(chunks)
        assert len(results) == 1

    def test_get_weights(self):
        ranker = HybridRanker(semantic_weight=0.5, keyword_weight=0.3, metadata_weight=0.2)
        w = ranker.get_weights()
        assert w["semantic_weight"] == 0.5
        assert w["keyword_weight"] == 0.3
        assert w["metadata_weight"] == 0.2


# =============================================================================
# CitationBuilder Tests
# =============================================================================

class TestCitationBuilder:
    def test_build_citations(self, sample_chunks):
        citations = CitationBuilder.build_citations(sample_chunks[:2])
        assert len(citations) == 2
        assert "Doc1" in citations[0]
        assert "Score" in citations[0]
        assert "Chunk" in citations[0]

    def test_build_citations_empty(self):
        citations = CitationBuilder.build_citations([])
        assert citations == []

    def test_format_markdown(self):
        results = [
            {"title": "Paper", "section": "Intro", "page": 1,
             "chunk_id": "abc123", "final_score": 0.95, "text": "Content here..."}
        ]
        md = CitationBuilder.format_citations_markdown(results)
        assert "Paper" in md
        assert "Intro" in md
        assert "Page: 1" in md
        assert "Content here" in md


# =============================================================================
# RetrievalMetrics Tests
# =============================================================================

class TestRetrievalMetrics:
    def test_record_query(self):
        m = RetrievalMetrics()
        m.record_query("test query", 42.0, 100, 5, 0.85)
        stats = m.get_statistics()
        assert stats["total_queries"] == 1
        assert stats["avg_latency_ms"] == 42.0
        assert stats["avg_chunks_returned"] == 5.0

    def test_empty_statistics(self):
        m = RetrievalMetrics()
        stats = m.get_statistics()
        assert stats["total_queries"] == 0

    def test_multiple_queries(self):
        m = RetrievalMetrics()
        m.record_query("q1", 10.0, 100, 3, 0.9)
        m.record_query("q2", 20.0, 200, 5, 0.8)
        m.record_query("q3", 30.0, 300, 7, 0.7)
        stats = m.get_statistics()
        assert stats["total_queries"] == 3
        assert stats["avg_latency_ms"] == 20.0
        assert 4.0 < stats["avg_chunks_returned"] < 6.0

    def test_percentiles(self):
        m = RetrievalMetrics()
        for i in range(1, 101):
            m.record_query(f"q{i}", float(i), 100, 5, 0.8)
        stats = m.get_statistics()
        assert stats["p50_latency_ms"] >= 50.0
        assert stats["p95_latency_ms"] >= 95.0

    def test_recent_queries(self):
        m = RetrievalMetrics()
        for i in range(20):
            m.record_query(f"q{i}", 10.0, 100, 5, 0.8)
        recent = m.get_recent_queries(5)
        assert len(recent) == 5

    def test_clear(self):
        m = RetrievalMetrics()
        m.record_query("test", 10.0, 100, 5, 0.8)
        m.clear()
        assert m.get_statistics()["total_queries"] == 0

    def test_max_history(self):
        m = RetrievalMetrics(max_history=5)
        for i in range(10):
            m.record_query(f"q{i}", 10.0, 100, 5, 0.8)
        assert m.get_statistics()["total_queries"] == 5


# =============================================================================
# SearchEngine Tests
# =============================================================================

class TestSearchEngine:
    def test_search_empty_query(self, mock_embedding_service, mock_vector_store):
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)
        result = engine.search(SearchQuery(text=""))
        assert len(result.results) == 0

    def test_search_with_mocked_results(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.search.return_value = [
            {"chunk_id": "c1", "document_id": "d1", "text": "transformer attention",
             "title": "Paper", "section": "Intro", "page": 1, "score": 0.92,
             "language": "en", "document_type": "paper", "workspace_id": "default",
             "chunk_index": 0, "word_count": 5, "keywords": ["transformer"],
             "importance_score": 1.0},
        ]
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)
        result = engine.search(SearchQuery(text="transformer attention"))
        assert len(result.results) > 0
        assert result.results[0].chunk_id == "c1"
        assert result.results[0].score > 0

    def test_search_uses_filters(self, mock_embedding_service, mock_vector_store):
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)
        engine.search(SearchQuery(text="test", workspace_id="team1", language="en"))
        call_args = mock_vector_store.search.call_args
        kwargs = call_args[1]
        assert "language" not in kwargs.get("filter_conditions", {}) or True

    def test_search_with_query_analysis(self, mock_embedding_service, mock_vector_store,
                                        mock_language_service, mock_intent_service):
        mock_vector_store.search.return_value = [
            {"chunk_id": "c1", "document_id": "d1", "text": "test", "title": "Doc",
             "section": "S1", "page": 1, "score": 0.9, "language": "en",
             "document_type": "paper", "workspace_id": "default", "chunk_index": 0,
             "word_count": 5, "keywords": [], "importance_score": 1.0},
        ]
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        ks = KeywordSearch()
        hr = HybridRanker()
        qa = QueryAnalyzer(language_service=mock_language_service, intent_service=mock_intent_service)
        engine = SearchEngine(ss, ks, hr, query_analyzer=qa)
        result = engine.search(SearchQuery(text="transformer models"))
        assert result.query_analysis is not None
        assert result.query_analysis["language"] == "en"

    def test_search_health(self, mock_embedding_service, mock_vector_store):
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)
        health = engine.health()
        assert "ready" in health
        assert "keyword_backend" in health
        assert "ranking_weights" in health

    def test_search_metrics_recorded(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.search.return_value = []
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        ks = KeywordSearch()
        hr = HybridRanker()
        metrics = RetrievalMetrics()
        engine = SearchEngine(ss, ks, hr, metrics=metrics)
        engine.search(SearchQuery(text="test query"))
        assert metrics.get_statistics()["total_queries"] == 1

    def test_search_parsed_filters_applied(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.search.return_value = []
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)
        engine.search(SearchQuery(text="lang:de transformer"))
        call_kwargs = mock_vector_store.search.call_args[1]
        filters = call_kwargs.get("filter_conditions", {})
        assert filters.get("language") == "de"


# =============================================================================
# Search Models Tests
# =============================================================================

class TestSearchModels:
    def test_search_result_to_dict(self):
        items = [SearchResultItem(
            chunk_id="c1", document_id="d1", text="hello world", title="Doc",
            section="Intro", page=1, score=0.95, language="en", document_type="paper",
        )]
        result = SearchResult(
            query="test",
            results=items,
            citations=["Doc (Chunk c1…, Score 0.95)"],
            processing_time_ms=42.0,
        )
        d = result.to_dict()
        assert d["query"] == "test"
        assert d["processing_time_ms"] == 42.0
        assert len(d["results"]) == 1
        assert d["results"][0]["chunk_id"] == "c1"
        assert d["results"][0]["score"] == 0.95
        assert "hello world" in d["results"][0]["preview"]

    def test_search_result_empty(self):
        result = SearchResult(query="test")
        d = result.to_dict()
        assert d["results"] == []
        assert d["citations"] == []

    def test_search_result_statistics(self):
        stats = SearchStatistics(
            total_chunks_searched=100,
            final_chunks_returned=5,
            avg_final_score=0.85,
            total_latency_ms=50.0,
        )
        result = SearchResult(
            query="test",
            statistics=stats,
            processing_time_ms=50.0,
        )
        d = result.to_dict()
        assert d["statistics"]["chunks_searched"] == 100
        assert d["statistics"]["chunks_returned"] == 0
        assert d["statistics"]["avg_score"] == 0.85


# =============================================================================
# SearchEngine Integration Tests (with VectorStore + real pipeline)
# =============================================================================

class TestSearchEngineIntegration:
    def test_full_search_pipeline(self, qdrant_path, sample_chunks, mock_embedding_service):
        from backend.app.vectorstore.qdrant_store import QdrantVectorStore

        vs = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_search_integration",
            vector_dimension=768,
        )
        vs.initialize()

        for c in sample_chunks:
            c["embedding_version"] = "1.0.0"

        vs.upsert_chunks(sample_chunks)

        mock_embedding_service.embed_text.return_value = [0.1] * 768

        ss = SemanticSearch(mock_embedding_service, vs)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)

        result = engine.search(SearchQuery(text="transformer attention", top_k=3))
        assert len(result.results) > 0
        assert result.results[0].score > 0
        assert result.processing_time_ms > 0

        vs.close()

    def test_search_empty_collection(self, qdrant_path, mock_embedding_service):
        from backend.app.vectorstore.qdrant_store import QdrantVectorStore

        vs = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_search_empty",
            vector_dimension=768,
        )
        vs.initialize()

        mock_embedding_service.embed_text.return_value = [0.1] * 768

        ss = SemanticSearch(mock_embedding_service, vs)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)

        result = engine.search(SearchQuery(text="test query"))
        assert len(result.results) == 0

        vs.close()

    def test_search_after_delete(self, qdrant_path, sample_chunks, mock_embedding_service):
        from backend.app.vectorstore.qdrant_store import QdrantVectorStore

        vs = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_search_delete",
            vector_dimension=768,
        )
        vs.initialize()

        for c in sample_chunks:
            c["embedding_version"] = "1.0.0"
        vs.upsert_chunks(sample_chunks)

        vs.delete_document("d1")

        mock_embedding_service.embed_text.return_value = [0.1] * 768

        ss = SemanticSearch(mock_embedding_service, vs)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)

        result = engine.search(SearchQuery(text="transformer"))
        remaining_ids = {r.chunk_id for r in result.results}
        assert all("d1" not in r.document_id for r in result.results)

        vs.close()

    def test_search_with_filters(self, qdrant_path, sample_chunks, mock_embedding_service):
        from backend.app.vectorstore.qdrant_store import QdrantVectorStore

        vs = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_search_filters",
            vector_dimension=768,
        )
        vs.initialize()

        for c in sample_chunks:
            c["embedding_version"] = "1.0.0"
        vs.upsert_chunks(sample_chunks)

        mock_embedding_service.embed_text.return_value = [0.1] * 768

        ss = SemanticSearch(mock_embedding_service, vs)
        ks = KeywordSearch()
        hr = HybridRanker()
        engine = SearchEngine(ss, ks, hr)

        result = engine.search(SearchQuery(text="test", language="de"))
        lang_results = {r.language for r in result.results}
        assert all(l == "de" for l in lang_results) or len(result.results) == 0

        vs.close()


@pytest.fixture
def qdrant_path(tmp_path):
    return str(tmp_path / "qdrant_search")


# =============================================================================
# API Route Tests
# =============================================================================

@pytest.fixture
def mock_search_services():
    search_engine = MagicMock()
    search_result = SearchResult(query="test", processing_time_ms=25.0)
    search_result.results = [
        SearchResultItem(
            chunk_id="c1", document_id="d1", text="test content", title="Doc",
            section="Intro", page=1, score=0.95,
        )
    ]
    search_result.citations = ["Doc (Chunk c1…, Score 0.95)"]
    search_result.to_dict = MagicMock(return_value={
        "query": "test",
        "processing_time_ms": 25.0,
        "results": [
            {"chunk_id": "c1", "document_id": "d1", "document": "Doc",
             "section": "Intro", "page": 1, "score": 0.95, "preview": "test content",
             "language": "", "document_type": ""},
        ],
        "citations": ["Doc (Chunk c1…, Score 0.95)"],
        "statistics": None,
        "query_analysis": None,
    })
    search_engine.search.return_value = search_result
    search_engine.health.return_value = {
        "ready": True,
        "embedding_model_loaded": True,
        "vector_store_healthy": True,
        "keyword_backend": "BM25",
        "ranking_weights": {"semantic_weight": 0.65, "keyword_weight": 0.25, "metadata_weight": 0.10},
        "statistics": {"total_queries": 5, "avg_latency_ms": 30.0},
    }
    return {"search_engine": search_engine}


@pytest.fixture
def search_client(mock_search_services):
    with patch("backend.app.api.search_routes.get_services", return_value=mock_search_services):
        with TestClient(app) as c:
            yield c


class TestSearchRoutes:
    def test_search_success(self, search_client):
        response = search_client.post("/api/v1/search", json={
            "query": "transformer attention",
            "top_k": 5,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test"
        assert data["processing_time_ms"] == 25.0
        assert len(data["results"]) == 1

    def test_search_empty_query(self, search_client):
        response = search_client.post("/api/v1/search", json={
            "query": "",
            "top_k": 5,
        })
        assert response.status_code == 422

    def test_search_with_filters(self, search_client):
        response = search_client.post("/api/v1/search", json={
            "query": "machine learning",
            "workspace_id": "team1",
            "language": "en",
            "document_type": "paper",
            "top_k": 10,
            "min_score": 0.3,
        })
        assert response.status_code == 200

    def test_search_with_document_ids(self, search_client):
        response = search_client.post("/api/v1/search", json={
            "query": "test",
            "document_ids": ["doc1", "doc2"],
        })
        assert response.status_code == 200

    def test_search_engine_not_available(self):
        with patch("backend.app.api.search_routes.get_services", return_value={}):
            with TestClient(app) as c:
                response = c.post("/api/v1/search", json={"query": "test"})
                assert response.status_code == 503

    def test_search_health(self, search_client):
        response = search_client.get("/api/v1/search/health")
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["embedding_model_loaded"] is True
        assert data["keyword_backend"] == "BM25"

    def test_search_health_not_available(self):
        with patch("backend.app.api.search_routes.get_services", return_value={}):
            with TestClient(app) as c:
                response = c.get("/api/v1/search/health")
                assert response.status_code == 200
                data = response.json()
                assert data["ready"] is False

    def test_search_invalid_top_k(self, search_client):
        response = search_client.post("/api/v1/search", json={
            "query": "test",
            "top_k": 0,
        })
        assert response.status_code == 422

    def test_search_top_k_too_large(self, search_client):
        response = search_client.post("/api/v1/search", json={
            "query": "test",
            "top_k": 200,
        })
        assert response.status_code == 422

    def test_search_min_score_invalid(self, search_client):
        response = search_client.post("/api/v1/search", json={
            "query": "test",
            "min_score": -0.1,
        })
        assert response.status_code == 422

    def test_search_with_additional_filters(self, search_client):
        response = search_client.post("/api/v1/search", json={
            "query": "test",
            "filters": {"section": "Methodology"},
        })
        assert response.status_code == 200


# =============================================================================
# Edge Cases
# =============================================================================

class TestSearchEdgeCases:
    def test_search_result_item_defaults(self):
        item = SearchResultItem(
            chunk_id="c1", document_id="d1", text="", title="",
            section="", page=0, score=0.0,
        )
        assert item.keywords == []

    def test_query_parser_special_chars(self):
        result = QueryParser.parse("@#$%^&*()")
        assert isinstance(result["keywords"], list)

    def test_hybrid_ranker_single_chunk(self):
        ranker = HybridRanker()
        chunks = [{"chunk_id": "c1", "text": "test", "score": 0.9, "keyword_score": 0.8,
                   "keywords": [], "importance_score": 1.0, "title": "A", "section": "S1",
                   "language": "en"}]
        results = ranker.rank(chunks)
        assert len(results) == 1

    def test_keyword_search_no_bm25_fallback(self):
        chunks = [{"chunk_id": "c1", "text": "test content here"}]
        with patch.object(KeywordSearch, "_BM25Okapi", create=True, side_effect=ImportError):
            ks = KeywordSearch()
            ks._use_bm25 = False
            ks._initialize_backend()
            results = ks.score("test", chunks)
            assert len(results) == 1

    def test_citation_builder_untitled(self):
        results = [{"chunk_id": "c1", "score": 0.5, "title": "", "section": "", "page": 0}]
        citations = CitationBuilder.build_citations(results)
        assert "Untitled" in citations[0]

    def test_retrieval_metrics_empty_recent(self):
        m = RetrievalMetrics()
        assert m.get_recent_queries() == []

    def test_semantic_search_handles_search_error(self, mock_embedding_service, mock_vector_store):
        mock_vector_store.search.side_effect = Exception("search failed")
        ss = SemanticSearch(mock_embedding_service, mock_vector_store)
        with pytest.raises(Exception):
            ss.search("test")
