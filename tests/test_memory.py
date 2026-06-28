import pytest
import json
import time
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime, timezone
import tempfile
import shutil

from backend.app.memory.memory_models import MemoryEntry, MemoryQuery, MemoryType
from backend.app.memory.memory_extractor import MemoryExtractor
from backend.app.memory.memory_classifier import MemoryClassifier
from backend.app.memory.importance_scorer import ImportanceScorer
from backend.app.memory.memory_store import MemoryStore
from backend.app.memory.memory_retriever import MemoryRetriever
from backend.app.memory.consolidation import ConsolidationEngine
from backend.app.memory.forgetting import ForgettingEngine


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_storage_dir(tmp_path):
    d = tmp_path / "uploads"
    d.mkdir()
    return str(d)


@pytest.fixture
def sample_entry():
    return MemoryEntry(
        content="My name is Ayush.",
        type=MemoryType.SEMANTIC,
        user_id="user1",
        workspace_id="default",
        importance=0.8,
        confidence=0.9,
    )


@pytest.fixture
def sample_entries():
    return [
        MemoryEntry(content="I study Computer Science.", type=MemoryType.SEMANTIC, importance=0.7),
        MemoryEntry(content="I love Python.", type=MemoryType.PREFERENCE, importance=0.6),
        MemoryEntry(content="I uploaded my resume yesterday.", type=MemoryType.EPISODIC, importance=0.5),
        MemoryEntry(content="I prefer dark mode.", type=MemoryType.PREFERENCE, importance=0.4),
    ]


@pytest.fixture
def memory_store(temp_storage_dir):
    store = MemoryStore(storage_dir=temp_storage_dir)
    yield store
    shutil.rmtree(Path(temp_storage_dir) / "memory", ignore_errors=True)


# =============================================================================
# Memory Models Tests
# =============================================================================

class TestMemoryModels:
    def test_memory_entry_defaults(self):
        entry = MemoryEntry(content="test memory")
        assert entry.memory_id
        assert entry.type == MemoryType.EPISODIC
        assert entry.importance == 0.0
        assert entry.checksum
        assert entry.created_at
        assert entry.last_accessed

    def test_memory_entry_with_values(self):
        entry = MemoryEntry(
            content="I like Python.",
            type=MemoryType.PREFERENCE,
            user_id="u1",
            workspace_id="w1",
            importance=0.9,
            confidence=0.95,
            pinned=True,
        )
        assert entry.content == "I like Python."
        assert entry.type == "preference"
        assert entry.user_id == "u1"
        assert entry.pinned

    def test_touch_updates_access(self):
        entry = MemoryEntry(content="test")
        old = entry.last_accessed
        time.sleep(0.01)
        entry.touch()
        assert entry.access_count == 1
        assert entry.last_accessed != old

    def test_update_content(self):
        entry = MemoryEntry(content="original")
        old_checksum = entry.checksum
        entry.update_content("updated content")
        assert entry.content == "updated content"
        assert entry.checksum != old_checksum

    def test_to_dict(self):
        entry = MemoryEntry(content="test", type=MemoryType.SEMANTIC)
        d = entry.to_dict()
        assert d["content"] == "test"
        assert d["type"] == "semantic"
        assert "memory_id" in d

    def test_serialize_roundtrip(self):
        entries = [
            MemoryEntry(content="first", type=MemoryType.SEMANTIC),
            MemoryEntry(content="second", type=MemoryType.PREFERENCE),
        ]
        raw = MemoryEntry.serialize_all(entries)
        loaded = MemoryEntry.deserialize_all(raw)
        assert len(loaded) == 2
        assert loaded[0].content == "first"

    def test_memory_query_defaults(self):
        q = MemoryQuery(query="test query")
        assert q.query == "test query"
        assert q.workspace_id == "default"
        assert q.top_k == 10

    def test_memory_type_constants(self):
        assert MemoryType.EPISODIC == "episodic"
        assert MemoryType.SEMANTIC == "semantic"
        assert MemoryType.PREFERENCE == "preference"
        assert MemoryType.WORKING == "working"
        assert len(MemoryType.ALL) == 4


# =============================================================================
# Memory Extractor Tests
# =============================================================================

class TestMemoryExtractor:
    def test_extract_empty_text(self):
        extractor = MemoryExtractor()
        assert extractor.extract("") == []
        assert extractor.extract("   ") == []
        assert extractor.extract("hi") == []

    def test_extract_short_text(self):
        extractor = MemoryExtractor(min_content_length=10)
        assert extractor.extract("short") == []

    def test_extract_greeting_filtered(self):
        extractor = MemoryExtractor()
        assert extractor.extract("Hello! How are you?") == []

    def test_extract_farewell_filtered(self):
        extractor = MemoryExtractor()
        assert extractor.extract("Goodbye, see you later!") == []

    def test_extract_small_talk_filtered(self):
        extractor = MemoryExtractor()
        assert extractor.extract("How are you doing today?") == []

    def test_extract_acknowledgment_noise(self):
        extractor = MemoryExtractor()
        results = extractor.extract("ok thanks")
        # "ok thanks" is 2 words, filtered by length
        assert len(results) == 0

    def test_extract_semantic_fact(self):
        extractor = MemoryExtractor()
        results = extractor.extract("I am a Computer Science student at Stanford.")
        assert len(results) == 1
        assert results[0].type == MemoryType.SEMANTIC

    def test_extract_semantic_my_name(self):
        extractor = MemoryExtractor()
        results = extractor.extract("My name is Ayush and I study AI.")
        assert len(results) == 1
        assert results[0].type == MemoryType.SEMANTIC

    def test_extract_preference_like(self):
        extractor = MemoryExtractor()
        results = extractor.extract("I really like Python for data science.")
        assert len(results) == 1
        assert results[0].type == MemoryType.PREFERENCE

    def test_extract_preference_prefer(self):
        extractor = MemoryExtractor()
        results = extractor.extract("I prefer concise answers to long ones.")
        assert len(results) == 1
        assert results[0].type == MemoryType.PREFERENCE

    def test_extract_episodic_action(self):
        extractor = MemoryExtractor()
        results = extractor.extract("I uploaded my resume yesterday afternoon.")
        assert len(results) == 1
        assert results[0].type == MemoryType.EPISODIC

    def test_extract_episodic_completed(self):
        extractor = MemoryExtractor()
        results = extractor.extract("I just finished reading the research paper.")
        assert len(results) == 1
        assert results[0].type == MemoryType.EPISODIC

    def test_extract_working_memory(self):
        extractor = MemoryExtractor()
        result = extractor.extract_working("I am currently working on my project.")
        assert result is not None
        assert result.type == MemoryType.WORKING

    def test_extract_working_short(self):
        extractor = MemoryExtractor(min_content_length=5)
        result = extractor.extract_working("no")
        assert result is None

    def test_extract_noise_rejection(self):
        extractor = MemoryExtractor()
        assert extractor._is_noise("Hi there!") is True
        assert extractor._is_noise("Thanks for your help!") is True
        assert extractor._is_noise("ok") is True

    def test_extract_confidence_scoring(self):
        extractor = MemoryExtractor()
        assert extractor._estimate_confidence("My name is Ayush.") > 0.5
        low_conf = extractor._estimate_confidence("hello")
        high_conf = extractor._estimate_confidence(
            "My name is Ayush and I study Computer Science at Stanford University! I use Python."
        )
        assert high_conf > low_conf

    def test_extract_source_field(self):
        extractor = MemoryExtractor()
        results = extractor.extract("I am a developer.")
        if results:
            assert results[0].source == "conversation"

    def test_extract_multiple_candidates(self):
        extractor = MemoryExtractor()
        results = extractor.extract(
            "I am a Python developer. I really like FastAPI. I built a chatbot last week."
        )
        # Each sentence may be extracted separately - at least one should be found
        assert len(results) >= 1

    def test_extract_noise_long_greeting(self):
        extractor = MemoryExtractor()
        assert extractor._is_noise("Hey there, how are you?") is True

    def test_extract_non_noise(self):
        extractor = MemoryExtractor()
        assert extractor._is_noise("I use Linux and Python for my daily work.") is False

    def test_extract_assistant_text_ignored(self):
        extractor = MemoryExtractor()
        results = extractor.extract(
            user_text="My name is Ayush.",
            assistant_text="Nice to meet you!",
        )
        assert len(results) == 1


# =============================================================================
# Memory Classifier Tests
# =============================================================================

class TestMemoryClassifier:
    def test_classify_semantic(self):
        classifier = MemoryClassifier()
        entry = MemoryEntry(content="I study Computer Science at university.", type="unknown")
        result = classifier.classify(entry)
        assert result == MemoryType.SEMANTIC

    def test_classify_preference(self):
        classifier = MemoryClassifier()
        entry = MemoryEntry(content="I love programming in Python.", type="unknown")
        result = classifier.classify(entry)
        assert result == MemoryType.PREFERENCE

    def test_classify_episodic(self):
        classifier = MemoryClassifier()
        entry = MemoryEntry(content="I uploaded a document yesterday.", type="unknown")
        result = classifier.classify(entry)
        assert result == MemoryType.EPISODIC

    def test_classify_working_unchanged(self):
        classifier = MemoryClassifier()
        entry = MemoryEntry(content="current task", type=MemoryType.WORKING)
        result = classifier.classify(entry)
        assert result == MemoryType.WORKING

    def test_classify_already_set(self):
        classifier = MemoryClassifier()
        entry = MemoryEntry(content="I like Python.", type=MemoryType.PREFERENCE)
        result = classifier.classify(entry)
        assert result == MemoryType.PREFERENCE

    def test_batch_classify(self):
        classifier = MemoryClassifier()
        entries = [
            MemoryEntry(content="I study AI.", type="unknown"),
            MemoryEntry(content="I love cats.", type="unknown"),
            MemoryEntry(content="I uploaded my file.", type="unknown"),
        ]
        results = classifier.batch_classify(entries)
        assert len(results) == 3
        assert results[0].type == MemoryType.SEMANTIC
        assert results[1].type == MemoryType.PREFERENCE
        assert results[2].type == MemoryType.EPISODIC

    def test_classify_empty_text_fallback(self):
        classifier = MemoryClassifier()
        entry = MemoryEntry(content="", type="unknown")
        result = classifier.classify(entry)
        assert result == MemoryType.EPISODIC

    def test_detect_type_none_match(self):
        classifier = MemoryClassifier()
        result = classifier._detect_type("The sky is blue.")
        assert result == MemoryType.EPISODIC


# =============================================================================
# Importance Scorer Tests
# =============================================================================

class TestImportanceScorer:
    def test_base_importance_semantic(self):
        scorer = ImportanceScorer()
        entry = MemoryEntry(content="I study CS.", type=MemoryType.SEMANTIC)
        assert scorer._base_importance(entry) == 0.85

    def test_base_importance_preference(self):
        scorer = ImportanceScorer()
        entry = MemoryEntry(content="I like Python.", type=MemoryType.PREFERENCE)
        assert scorer._base_importance(entry) == 0.6

    def test_base_importance_episodic(self):
        scorer = ImportanceScorer()
        entry = MemoryEntry(content="I did something.", type=MemoryType.EPISODIC)
        assert scorer._base_importance(entry) == 0.4

    def test_base_importance_working(self):
        scorer = ImportanceScorer()
        entry = MemoryEntry(content="working", type=MemoryType.WORKING)
        assert scorer._base_importance(entry) == 0.1

    def test_specificity_with_proper_nouns(self):
        scorer = ImportanceScorer()
        score = scorer._specificity_score("I study at Stanford University in California.")
        assert score > 0.3

    def test_specificity_with_numbers(self):
        scorer = ImportanceScorer()
        score = scorer._specificity_score("I have 5 years of experience with Python 3.")
        assert score > 0.1

    def test_emphasis_with_exclamation(self):
        scorer = ImportanceScorer()
        score = scorer._emphasis_score("I LOVE PYTHON!")
        assert score > 0.2

    def test_frequency_bonus(self):
        scorer = ImportanceScorer()
        entry = MemoryEntry(content="I love Python.")
        existing = [MemoryEntry(content="Python is my favorite language.")]
        bonus = scorer._frequency_bonus(entry, existing)
        assert bonus > 0

    def test_frequency_bonus_no_match(self):
        scorer = ImportanceScorer()
        entry = MemoryEntry(content="I love Python.")
        existing = [MemoryEntry(content="I use Java at work.")]
        bonus = scorer._frequency_bonus(entry, existing)
        assert bonus == 0.0

    def test_future_usefulness(self):
        scorer = ImportanceScorer()
        score = scorer._future_usefulness("I use Python for data science and machine learning.")
        assert score > 0

    def test_is_important_above_threshold(self):
        scorer = ImportanceScorer(threshold=0.3)
        entry = MemoryEntry(content="I study Computer Science at Stanford University using Python.", type=MemoryType.SEMANTIC)
        assert scorer.is_important(entry) is True

    def test_is_important_below_threshold(self):
        scorer = ImportanceScorer(threshold=0.9)
        entry = MemoryEntry(content="I did a thing.", type=MemoryType.EPISODIC)
        assert scorer.is_important(entry) is False

    def test_score_normalized_range(self):
        scorer = ImportanceScorer()
        entry = MemoryEntry(content="I am a Python developer at Google for 5 years.", type=MemoryType.SEMANTIC)
        score = scorer.score(entry)
        assert 0.0 <= score <= 1.0

    def test_threshold_property(self):
        scorer = ImportanceScorer(threshold=0.5)
        assert scorer.threshold == 0.5
        scorer.threshold = 0.7
        assert scorer.threshold == 0.7

    def test_recency_bonus_recent(self):
        scorer = ImportanceScorer(recency_hours=24)
        entry = MemoryEntry(content="test", created_at=datetime.now(timezone.utc).isoformat())
        bonus = scorer._recency_bonus(entry)
        assert bonus == 0.2

    def test_recency_bonus_old(self):
        scorer = ImportanceScorer(recency_hours=24)
        from datetime import timedelta
        old = datetime.now(timezone.utc) - timedelta(days=30)
        entry = MemoryEntry(content="test", created_at=old.isoformat())
        bonus = scorer._recency_bonus(entry)
        assert bonus == 0.0


# =============================================================================
# Memory Store Tests
# =============================================================================

class TestMemoryStore:
    def test_save_and_get(self, memory_store, sample_entry):
        memory_store.save(sample_entry)
        retrieved = memory_store.get(sample_entry.memory_id)
        assert retrieved is not None
        assert retrieved.content == sample_entry.content

    def test_get_nonexistent(self, memory_store):
        assert memory_store.get("nonexistent") is None

    def test_delete(self, memory_store, sample_entry):
        memory_store.save(sample_entry)
        assert memory_store.delete(sample_entry.memory_id) is True
        assert memory_store.get(sample_entry.memory_id) is None

    def test_delete_nonexistent(self, memory_store):
        assert memory_store.delete("nonexistent") is False

    def test_list_all(self, memory_store, sample_entries):
        for e in sample_entries:
            memory_store.save(e)
        entries = memory_store.list()
        assert len(entries) == 4

    def test_list_by_type(self, memory_store, sample_entries):
        for e in sample_entries:
            memory_store.save(e)
        semantic = memory_store.list(memory_type=MemoryType.SEMANTIC)
        assert len(semantic) == 1
        assert semantic[0].type == MemoryType.SEMANTIC

    def test_list_by_user(self, memory_store, sample_entry):
        sample_entry.user_id = "user1"
        memory_store.save(sample_entry)
        entries = memory_store.list(user_id="user1")
        assert len(entries) == 1
        entries = memory_store.list(user_id="user2")
        assert len(entries) == 0

    def test_list_excludes_working_by_default(self, memory_store):
        memory_store.save(MemoryEntry(content="fact", type=MemoryType.SEMANTIC))
        memory_store.save(MemoryEntry(content="temp", type=MemoryType.WORKING))
        entries = memory_store.list()
        assert len(entries) == 1

    def test_list_includes_working_when_requested(self, memory_store):
        memory_store.save(MemoryEntry(content="fact", type=MemoryType.SEMANTIC))
        memory_store.save(MemoryEntry(content="temp", type=MemoryType.WORKING))
        entries = memory_store.list(include_working=True)
        assert len(entries) == 2

    def test_get_by_type(self, memory_store, sample_entries):
        for e in sample_entries:
            memory_store.save(e)
        prefs = memory_store.get_by_type(MemoryType.PREFERENCE)
        assert len(prefs) == 2

    def test_clear_working(self, memory_store):
        memory_store.save(MemoryEntry(content="working1", type=MemoryType.WORKING))
        memory_store.save(MemoryEntry(content="working2", type=MemoryType.WORKING))
        memory_store.save(MemoryEntry(content="fact", type=MemoryType.SEMANTIC))
        assert memory_store.clear_working() == 2
        entries = memory_store.list(include_working=True)
        assert len(entries) == 1

    def test_count(self, memory_store, sample_entries):
        for e in sample_entries:
            memory_store.save(e)
        counts = memory_store.count()
        assert counts["total"] == 4
        assert counts.get(MemoryType.SEMANTIC) == 1

    def test_persists_to_disk(self, memory_store, sample_entry):
        memory_store.save(sample_entry)
        memory_store.flush()
        file_path = Path(memory_store.storage_dir) / "semantic.json"
        assert file_path.exists()
        raw = file_path.read_text(encoding="utf-8")
        loaded = MemoryEntry.deserialize_all(raw)
        assert len(loaded) >= 1

    def test_loads_from_disk(self, temp_storage_dir, sample_entry):
        store1 = MemoryStore(storage_dir=temp_storage_dir)
        store1.save(sample_entry)
        store1.flush()
        store2 = MemoryStore(storage_dir=temp_storage_dir)
        retrieved = store2.get(sample_entry.memory_id)
        assert retrieved is not None
        assert retrieved.content == sample_entry.content
        shutil.rmtree(Path(temp_storage_dir) / "memory", ignore_errors=True)

    def test_save_all(self, memory_store, sample_entries):
        memory_store.save_all(sample_entries)
        assert memory_store.total_entries == 4

    def test_total_entries_property(self, memory_store):
        assert memory_store.total_entries == 0
        memory_store.save(MemoryEntry(content="test"))
        assert memory_store.total_entries == 1


# =============================================================================
# Memory Retriever Tests
# =============================================================================

class TestMemoryRetriever:
    def test_retrieve_empty(self):
        retriever = MemoryRetriever()
        query = MemoryQuery(query="test")
        results = retriever.retrieve(query, [])
        assert results == []

    def test_retrieve_exact_match(self, sample_entries):
        retriever = MemoryRetriever()
        query = MemoryQuery(query="Python")
        results = retriever.retrieve(query, sample_entries)
        assert len(results) >= 1

    def test_retrieve_top_k(self, sample_entries):
        retriever = MemoryRetriever(top_k=2)
        query = MemoryQuery(query="Python", top_k=2)
        results = retriever.retrieve(query, sample_entries)
        assert len(results) <= 2

    def test_retrieve_filter_by_type(self, sample_entries):
        retriever = MemoryRetriever()
        query = MemoryQuery(query="study", memory_types=[MemoryType.SEMANTIC])
        results = retriever.retrieve(query, sample_entries)
        for r in results:
            assert r.type == MemoryType.SEMANTIC

    def test_retrieve_min_importance(self, sample_entries):
        retriever = MemoryRetriever()
        query = MemoryQuery(query="test", min_importance=0.6)
        results = retriever.retrieve(query, sample_entries)
        for r in results:
            assert r.importance >= 0.6

    def test_retrieve_excludes_working_by_default(self, sample_entries):
        retriever = MemoryRetriever()
        entries = sample_entries + [MemoryEntry(content="working", type=MemoryType.WORKING)]
        query = MemoryQuery(query="test")
        results = retriever.retrieve(query, entries)
        for r in results:
            assert r.type != MemoryType.WORKING

    def test_retrieve_includes_working(self, sample_entries):
        retriever = MemoryRetriever()
        entries = sample_entries + [MemoryEntry(content="working test", type=MemoryType.WORKING)]
        query = MemoryQuery(query="test", include_working=True)
        results = retriever.retrieve(query, entries)
        has_working = any(r.type == MemoryType.WORKING for r in results)
        assert has_working

    def test_retrieve_lexical_scoring(self):
        retriever = MemoryRetriever()
        entry = MemoryEntry(content="Python is my favorite programming language.", importance=0.5)
        query = MemoryQuery(query="Python programming")
        results = retriever.retrieve(query, [entry])
        assert len(results) == 1

    def test_retrieve_no_match(self):
        retriever = MemoryRetriever()
        entry = MemoryEntry(content="I like cats.", importance=0.5)
        query = MemoryQuery(query="quantum physics")
        results = retriever.retrieve(query, [entry])
        assert len(results) == 0

    def test_apply_filters_user(self):
        retriever = MemoryRetriever()
        entries = [
            MemoryEntry(content="a", user_id="u1"),
            MemoryEntry(content="b", user_id="u2"),
        ]
        query = MemoryQuery(query="test", user_id="u1")
        filtered = retriever._apply_filters(query, entries)
        assert len(filtered) == 1

    def test_recency_weight(self):
        retriever = MemoryRetriever()
        recent = MemoryEntry(content="test", last_accessed=datetime.now(timezone.utc).isoformat())
        assert retriever._recency_weight(recent) == 1.0

    def test_tokenize(self):
        retriever = MemoryRetriever()
        tokens = retriever._tokenize("Hello World! I use Python3.")
        assert "hello" in tokens
        assert "python3" in tokens
        assert "i" not in tokens  # single char filtered


# =============================================================================
# Consolidation Engine Tests
# =============================================================================

class TestConsolidation:
    def test_consolidate_empty(self):
        engine = ConsolidationEngine()
        assert engine.consolidate([]) == []

    def test_consolidate_no_merges(self):
        engine = ConsolidationEngine()
        entries = [
            MemoryEntry(content="I am a student.", type=MemoryType.SEMANTIC),
            MemoryEntry(content="I uploaded a file yesterday.", type=MemoryType.EPISODIC),
        ]
        result = engine.consolidate(entries)
        assert len(result) == 2

    def test_consolidate_merges_semantic(self):
        engine = ConsolidationEngine()
        entries = [
            MemoryEntry(content="I know Python.", type=MemoryType.SEMANTIC),
            MemoryEntry(content="I use FastAPI.", type=MemoryType.SEMANTIC),
            MemoryEntry(content="I build AI systems.", type=MemoryType.SEMANTIC),
        ]
        result = engine.consolidate(entries)
        assert len(result) >= 1

    def test_consolidate_merges_preferences(self):
        engine = ConsolidationEngine()
        entries = [
            MemoryEntry(content="I like Python.", type=MemoryType.PREFERENCE),
            MemoryEntry(content="I love FastAPI.", type=MemoryType.PREFERENCE),
        ]
        result = engine.consolidate(entries)
        assert len(result) >= 1

    def test_consolidate_preserves_non_factual(self):
        engine = ConsolidationEngine()
        entries = [
            MemoryEntry(content="I know Python.", type=MemoryType.SEMANTIC),
            MemoryEntry(content="I uploaded a file.", type=MemoryType.EPISODIC),
        ]
        result = engine.consolidate(entries)
        assert len(result) == 2

    def test_cluster_by_topic(self):
        engine = ConsolidationEngine()
        entries = [
            MemoryEntry(content="I use Python for AI.", type=MemoryType.SEMANTIC),
            MemoryEntry(content="I love Python.", type=MemoryType.PREFERENCE),
            MemoryEntry(content="I prefer Java.", type=MemoryType.PREFERENCE),
        ]
        clusters = engine._cluster_by_topic(entries, max_cluster=10)
        assert len(clusters) >= 1

    def test_merge_cluster(self):
        engine = ConsolidationEngine()
        entries = [
            MemoryEntry(content="I know Python.", importance=0.7, type=MemoryType.SEMANTIC),
            MemoryEntry(content="I use FastAPI.", importance=0.6, type=MemoryType.SEMANTIC),
        ]
        merged = engine._merge_cluster(entries)
        assert merged is not None
        assert merged.importance >= 0.7
        assert "Python" in merged.content

    def test_merge_updates_importance(self):
        engine = ConsolidationEngine()
        entries = [
            MemoryEntry(content="a", importance=0.5, type=MemoryType.SEMANTIC),
            MemoryEntry(content="b", importance=0.8, type=MemoryType.SEMANTIC),
        ]
        merged = engine._merge_cluster(entries)
        assert merged.importance == 0.9  # max(0.8) + 0.1 = 0.9

    def test_consolidate_different_topics(self):
        engine = ConsolidationEngine()
        entries = [
            MemoryEntry(content="I use Python.", type=MemoryType.SEMANTIC),
            MemoryEntry(content="My cat is fluffy.", type=MemoryType.SEMANTIC),
        ]
        result = engine.consolidate(entries)
        assert len(result) == 2


# =============================================================================
# Forgetting Engine Tests
# =============================================================================

class TestForgetting:
    def test_apply_empty(self):
        engine = ForgettingEngine()
        assert engine.apply_forgetting([]) == []

    def test_protect_pinned(self):
        engine = ForgettingEngine()
        entry = MemoryEntry(content="important", pinned=True, importance=0.1)
        assert engine._should_protect(entry) is True

    def test_protect_high_importance(self):
        engine = ForgettingEngine()
        entry = MemoryEntry(content="important", importance=0.8)
        assert engine._should_protect(entry) is True

    def test_protect_frequently_accessed(self):
        engine = ForgettingEngine()
        entry = MemoryEntry(content="important", importance=0.3, access_count=25)
        assert engine._should_protect(entry) is True

    def test_no_protect_low_importance(self):
        engine = ForgettingEngine()
        entry = MemoryEntry(content="trivial", importance=0.1, access_count=1)
        assert engine._should_protect(entry) is False

    def test_decay_importance_recent(self):
        engine = ForgettingEngine()
        entry = MemoryEntry(content="test", importance=0.5,
                           last_accessed=datetime.now(timezone.utc).isoformat())
        decayed = engine._decay_importance(entry)
        assert decayed.importance == 0.5  # no decay for recent

    def test_should_forget_low_importance_old(self):
        engine = ForgettingEngine(max_age_days=1)
        from datetime import timedelta
        old = datetime.now(timezone.utc) - timedelta(days=2)
        entry = MemoryEntry(content="old", importance=0.1,
                           last_accessed=old.isoformat())
        assert engine._should_forget(entry) is True

    def test_should_not_forget_pinned(self):
        engine = ForgettingEngine()
        entry = MemoryEntry(content="pinned", importance=0.1, pinned=True)
        assert engine._should_forget(entry) is False

    def test_apply_forgetting_preserves_important(self):
        engine = ForgettingEngine(forgetting_rate=0.5, importance_decay=0.1)
        from datetime import timedelta
        old = datetime.now(timezone.utc) - timedelta(days=30)
        entries = [
            MemoryEntry(content="important", importance=0.8, last_accessed=old.isoformat()),
            MemoryEntry(content="trivial", importance=0.05, last_accessed=old.isoformat()),
        ]
        survivors = engine.apply_forgetting(entries)
        survivor_ids = [e.memory_id for e in survivors]
        assert entries[0].memory_id in survivor_ids

    def test_high_preference_protected(self):
        engine = ForgettingEngine()
        entry = MemoryEntry(content="preference", type=MemoryType.PREFERENCE, importance=0.6)
        assert engine._should_protect(entry) is True


# =============================================================================
# Memory Engine Integration Tests
# =============================================================================

class TestMemoryEngine:
    @pytest.fixture
    def memory_engine(self, temp_storage_dir):
        from backend.app.memory.memory_engine import MemoryEngine
        from backend.app.config.settings import Settings
        extractor = MemoryExtractor()
        classifier = MemoryClassifier()
        store = MemoryStore(storage_dir=temp_storage_dir)
        retriever = MemoryRetriever(top_k=10)
        scorer = ImportanceScorer(threshold=0.2)
        consolidation = ConsolidationEngine()
        forgetting = ForgettingEngine()
        settings = Settings()
        engine = MemoryEngine(
            extractor=extractor,
            classifier=classifier,
            store=store,
            retriever=retriever,
            scorer=scorer,
            consolidation=consolidation,
            forgetting=forgetting,
            settings=settings,
        )
        yield engine
        shutil.rmtree(Path(temp_storage_dir) / "memory", ignore_errors=True)

    def test_process_conversation_turn_semantic(self, memory_engine):
        result = memory_engine.process_conversation_turn(
            user_text="My name is Ayush and I study Computer Science.",
            user_id="user1",
            workspace_id="default",
        )
        assert result["extracted_count"] >= 1
        assert result["stored_count"] >= 1

    def test_process_conversation_turn_preference(self, memory_engine):
        result = memory_engine.process_conversation_turn(
            user_text="I really prefer concise answers to long explanations.",
            user_id="user1",
        )
        assert result["extracted_count"] >= 1

    def test_process_conversation_turn_noise(self, memory_engine):
        result = memory_engine.process_conversation_turn(
            user_text="Hello!",
            user_id="user1",
        )
        assert result["extracted_count"] == 0
        assert result["stored_count"] == 0

    def test_process_conversation_turn_working_memory(self, memory_engine):
        result = memory_engine.process_conversation_turn(
            user_text="I am currently working on my new project.",
            user_id="user1",
        )
        assert result["working_memory_id"] is not None

    def test_retrieve_for_query(self, memory_engine):
        memory_engine.process_conversation_turn(
            user_text="My name is Ayush and I study Computer Science.",
            user_id="user1",
        )
        result = memory_engine.retrieve_memories(
            query="Ayush",
            user_id="user1",
        )
        assert result["count"] >= 1
        memories = result["memories"]
        assert any("Ayush" in m["content"] for m in memories)

    def test_retrieve_empty(self, memory_engine):
        result = memory_engine.retrieve_memories(
            query="nothing here",
            user_id="nonexistent",
        )
        assert result["count"] == 0

    def test_delete_memory(self, memory_engine):
        result = memory_engine.process_conversation_turn(
            user_text="My name is Test User.",
            user_id="user1",
        )
        memories = memory_engine.get_memories(user_id="user1")
        assert len(memories) >= 1
        mid = memories[0]["memory_id"]
        assert memory_engine.delete_memory(mid) is True
        assert memory_engine.delete_memory(mid) is False

    def test_get_memories_by_type(self, memory_engine):
        memory_engine.process_conversation_turn(
            user_text="I love Python programming.", user_id="user1",
        )
        memory_engine.process_conversation_turn(
            user_text="I uploaded my resume to Google Drive yesterday at 3 PM.", user_id="user1",
        )
        prefs = memory_engine.get_memories(user_id="user1", memory_type=MemoryType.PREFERENCE)
        episodics = memory_engine.get_memories(user_id="user1", memory_type=MemoryType.EPISODIC)
        assert len(prefs) >= 1
        assert len(episodics) >= 1

    def test_clear_working_memory(self, memory_engine):
        memory_engine.process_conversation_turn(
            user_text="Working on my project now.", user_id="user1",
        )
        cleared = memory_engine.clear_working_memory()
        assert cleared >= 1

    def test_health(self, memory_engine):
        health = memory_engine.health()
        assert health["ready"] is True
        assert "memory_count" in health

    def test_consolidate(self, memory_engine):
        memory_engine.process_conversation_turn(
            user_text="I know Python programming language.", user_id="user1",
        )
        memory_engine.process_conversation_turn(
            user_text="I use Python for data science.", user_id="user1",
        )
        result = memory_engine.consolidate(user_id="user1")
        assert "consolidated_count" in result

    def test_deduplication_on_update(self, memory_engine):
        r1 = memory_engine.process_conversation_turn(
            user_text="My name is Ayush.", user_id="user1",
        )
        r2 = memory_engine.process_conversation_turn(
            user_text="My name is Ayush.", user_id="user1",
        )
        # Second occurrence should update, not create new
        assert r2["updated_count"] >= 1


# =============================================================================
# Reasoning Engine + Memory Integration
# =============================================================================

class TestReasoningMemoryIntegration:
    @pytest.fixture
    def setup(self, temp_storage_dir):
        from backend.app.reasoning.reasoning_engine import ReasoningEngine
        from backend.app.reasoning.context_builder import ContextBuilder
        from backend.app.reasoning.prompt_builder import PromptBuilder
        from backend.app.reasoning.citation_manager import CitationManager
        from backend.app.reasoning.response_validator import ResponseValidator
        from backend.app.reasoning.guardrails import Guardrails
        from backend.app.memory.memory_engine import MemoryEngine
        from backend.app.config.settings import Settings

        settings = Settings()
        search_engine = MagicMock()
        search_engine.search.return_value = MagicMock(
            results=[
                MagicMock(
                    chunk_id="c1", document_id="d1", text="Python is a programming language.",
                    title="Doc", section="Intro", page=1, score=0.95,
                    chunk_index=0, language="en", document_type="doc",
                    workspace_id="default", keywords=["python"],
                )
            ]
        )
        search_engine.health.return_value = {"ready": True}

        chat_service = MagicMock()
        chat_service.invoke_llm.return_value = "Python is a great programming language."

        context_builder = ContextBuilder()
        prompt_dir = Path(temp_storage_dir).parent / "prompts"
        prompt_dir.mkdir(parents=True, exist_ok=True)
        (prompt_dir / "knowledge_system.txt").write_text("test system {guardrails}")
        (prompt_dir / "knowledge_user.txt").write_text("test user {context} {conversation_history} {question} {language} {token_estimate} {chunk_count}")
        (prompt_dir / "knowledge_guardrails.txt").write_text("test guardrails {external_knowledge}")
        prompt_builder = PromptBuilder(prompts_dir=prompt_dir)

        memory_extractor = MemoryExtractor()
        memory_classifier = MemoryClassifier()
        memory_store = MemoryStore(storage_dir=temp_storage_dir)
        memory_retriever = MemoryRetriever()
        scorer = ImportanceScorer(threshold=0.1)
        consolidation = ConsolidationEngine()
        forgetting = ForgettingEngine()

        memory_engine = MemoryEngine(
            extractor=memory_extractor,
            classifier=memory_classifier,
            store=memory_store,
            retriever=memory_retriever,
            scorer=scorer,
            consolidation=consolidation,
            forgetting=forgetting,
            settings=settings,
        )

        reasoning = ReasoningEngine(
            search_engine=search_engine,
            chat_service=chat_service,
            context_builder=context_builder,
            prompt_builder=prompt_builder,
            citation_manager=CitationManager(),
            response_validator=ResponseValidator(),
            guardrails=Guardrails(),
            settings=settings,
            memory_engine=memory_engine,
        )

        yield {
            "reasoning": reasoning,
            "memory_engine": memory_engine,
            "search_engine": search_engine,
            "chat_service": chat_service,
        }
        shutil.rmtree(Path(temp_storage_dir) / "memory", ignore_errors=True)

    def test_memory_engine_passed_to_reasoning(self, setup):
        assert setup["reasoning"]._memory_engine is not None

    def test_reasoning_answer_without_memory(self, setup):
        from backend.app.reasoning.answer_models import KnowledgeQuery
        query = KnowledgeQuery(question="What is Python?", workspace_id="default")
        answer = setup["reasoning"].answer(query)
        assert answer.answer
        assert "Python" in answer.answer

    def test_memory_integrated_in_answer_flow(self, setup):
        setup["memory_engine"].process_conversation_turn(
            user_text="My name is Ayush.", user_id="user1", workspace_id="default",
        )
        from backend.app.reasoning.answer_models import KnowledgeQuery
        query = KnowledgeQuery(question="What is my name?", workspace_id="default")
        answer = setup["reasoning"].answer(query)
        assert answer.answer

    def test_memory_engine_none_when_not_provided(self):
        from backend.app.reasoning.reasoning_engine import ReasoningEngine
        from backend.app.config.settings import Settings
        engine = ReasoningEngine(
            search_engine=MagicMock(),
            chat_service=MagicMock(),
            context_builder=MagicMock(),
            prompt_builder=MagicMock(),
            citation_manager=MagicMock(),
            response_validator=MagicMock(),
            guardrails=MagicMock(),
            settings=Settings(),
        )
        assert engine._memory_engine is None


# =============================================================================
# API Route Tests
# =============================================================================

class TestMemoryRoutes:
    @pytest.fixture
    def client(self, temp_storage_dir, monkeypatch):
        from fastapi.testclient import TestClient
        from backend.app.main import app
        from backend.app.config.settings import Settings
        from backend.app.memory.memory_engine import MemoryEngine
        from backend.app.memory.memory_extractor import MemoryExtractor
        from backend.app.memory.memory_classifier import MemoryClassifier
        from backend.app.memory.memory_store import MemoryStore
        from backend.app.memory.memory_retriever import MemoryRetriever
        from backend.app.memory.importance_scorer import ImportanceScorer
        from backend.app.memory.consolidation import ConsolidationEngine
        from backend.app.memory.forgetting import ForgettingEngine

        settings = Settings()
        extractor = MemoryExtractor()
        classifier = MemoryClassifier()
        store = MemoryStore(storage_dir=temp_storage_dir)
        retriever = MemoryRetriever(top_k=10)
        scorer = ImportanceScorer(threshold=0.2)
        consolidation = ConsolidationEngine()
        forgetting = ForgettingEngine()
        memory_engine = MemoryEngine(
            extractor=extractor, classifier=classifier, store=store,
            retriever=retriever, scorer=scorer, consolidation=consolidation,
            forgetting=forgetting, settings=settings,
        )

        monkeypatch.setattr(
            "backend.app.api.memory_routes.get_services",
            lambda: {"memory_engine": memory_engine},
        )

        with TestClient(app) as c:
            yield c

        shutil.rmtree(Path(temp_storage_dir) / "memory", ignore_errors=True)

    def test_memory_health_endpoint(self, client):
        response = client.get("/api/v1/memory/health")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data

    def test_extract_memory_endpoint(self, client):
        response = client.post("/api/v1/memory/extract", json={
            "user_text": "My name is Ayush and I study Computer Science.",
            "user_id": "user1",
            "workspace_id": "default",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["extracted_count"] >= 1

    def test_extract_memory_empty_text(self, client):
        response = client.post("/api/v1/memory/extract", json={
            "user_text": "",
            "user_id": "user1",
        })
        assert response.status_code == 422

    def test_list_memories_endpoint(self, client):
        client.post("/api/v1/memory/extract", json={
            "user_text": "My name is Ayush.",
            "user_id": "user1",
        })
        response = client.get("/api/v1/memory?user_id=user1")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_search_memories_endpoint(self, client):
        client.post("/api/v1/memory/extract", json={
            "user_text": "My name is Ayush.",
            "user_id": "user1",
        })
        response = client.post("/api/v1/memory/search", json={
            "query": "Ayush",
            "user_id": "user1",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 1

    def test_delete_memory_endpoint(self, client):
        client.post("/api/v1/memory/extract", json={
            "user_text": "My name is Ayush.",
            "user_id": "user1",
        })
        list_resp = client.get("/api/v1/memory?user_id=user1")
        memories = list_resp.json()["memories"]
        if memories:
            mid = memories[0]["memory_id"]
            response = client.delete(f"/api/v1/memory/{mid}")
            assert response.status_code == 200

    def test_delete_memory_not_found(self, client):
        response = client.delete("/api/v1/memory/nonexistent-id")
        assert response.status_code == 404

    def test_consolidate_endpoint(self, client):
        response = client.post("/api/v1/memory/consolidate?user_id=user1")
        assert response.status_code == 200
        data = response.json()
        assert "consolidated_count" in data
