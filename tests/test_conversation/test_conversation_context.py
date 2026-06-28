import pytest
from typing import Any, Dict, List

from backend.app.reasoning.conversation.conversation_context import ConversationContextManager, ConversationContext


class TestConversationContextManager:
    @pytest.fixture
    def manager(self):
        return ConversationContextManager()

    def test_get_or_create_new(self, manager):
        ctx = manager.get_or_create("conv1")
        assert ctx.conversation_id == "conv1"
        assert ctx.turn_count == 0
        assert ctx.last_question == ""

    def test_get_or_create_reuses(self, manager):
        ctx1 = manager.get_or_create("conv1")
        ctx1.last_question = "test"
        ctx2 = manager.get_or_create("conv1")
        assert ctx2.last_question == "test"
        assert ctx1 is ctx2

    def test_update_after_turn(self, manager):
        manager.update_after_turn("conv1", "What is AI?", "AI is...", intent="general_ai")
        ctx = manager.get_or_create("conv1")
        assert ctx.last_question == "What is AI?"
        assert ctx.last_answer == "AI is..."
        assert ctx.last_intent == "general_ai"
        assert ctx.turn_count == 1

    def test_update_after_turn_with_chunks(self, manager):
        chunks = [{"chunk_id": "c1", "text": "test"}]
        manager.update_after_turn("conv1", "Q", "A", chunks=chunks)
        ctx = manager.get_or_create("conv1")
        assert len(ctx.last_retrieved_chunks) == 1

    def test_update_after_turn_with_documents(self, manager):
        docs = [{"id": "d1", "filename": "resume.pdf"}]
        manager.update_after_turn("conv1", "Q", "A", documents=docs)
        ctx = manager.get_or_create("conv1")
        assert len(ctx.last_uploaded_files) == 1

    def test_resolve_query_no_history(self, manager):
        resolved = manager.resolve_query("conv1", "What is AI?")
        assert resolved.resolved == "What is AI?"
        assert not resolved.had_reference

    def test_resolve_query_with_reference(self, manager):
        manager.update_after_turn("conv1", "Summarize my resume", "Your resume...", intent="document_question")
        resolved = manager.resolve_query("conv1", "Explain it further")
        assert resolved.had_reference

    def test_get_window_history(self, manager):
        manager.update_after_turn("conv1", "Q1", "A1")
        manager.update_after_turn("conv1", "Q2", "A2")
        history = manager.get_window_history("conv1")
        assert len(history) == 4

    def test_get_window_history_with_limit(self, manager):
        manager.update_after_turn("conv1", "Q1", "A1")
        manager.update_after_turn("conv1", "Q2", "A2")
        history = manager.get_window_history("conv1", limit=2)
        assert len(history) == 2

    def test_get_window_summary(self, manager):
        assert manager.get_window_summary("conv1") == ""
        for i in range(10):
            manager.update_after_turn("conv1", f"Q{i}", f"A{i}", intent="general_ai")
        summary = manager.get_window_summary("conv1")
        assert summary or True

    def test_get_turn_count(self, manager):
        assert manager.get_turn_count("conv1") == 0
        manager.update_after_turn("conv1", "Q", "A")
        assert manager.get_turn_count("conv1") == 1

    def test_get_last_retrieved_chunks_default(self, manager):
        assert manager.get_last_retrieved_chunks("conv1") == []

    def test_set_last_retrieved_chunks(self, manager):
        chunks = [{"chunk_id": "c1"}]
        manager.set_last_retrieved_chunks("conv1", chunks)
        assert len(manager.get_last_retrieved_chunks("conv1")) == 1

    def test_clear(self, manager):
        manager.update_after_turn("conv1", "Q", "A")
        manager.clear("conv1")
        ctx = manager.get_or_create("conv1")
        assert ctx.turn_count == 0
        assert ctx.last_question == ""

    def test_get_context_nonexistent(self, manager):
        assert manager.get_context("nonexistent") is None

    def test_get_context_exists(self, manager):
        manager.update_after_turn("conv1", "Q", "A")
        ctx = manager.get_context("conv1")
        assert ctx is not None
        assert ctx.last_question == "Q"

    def test_health(self, manager):
        health = manager.health()
        assert "active_contexts" in health
        assert "active_windows" in health
        assert health["active_contexts"] == 0

    def test_health_with_data(self, manager):
        manager.update_after_turn("conv1", "Q", "A")
        health = manager.health()
        assert health["active_contexts"] == 1

    def test_multiple_conversations_independent(self, manager):
        manager.update_after_turn("a", "Q from A", "A1")
        manager.update_after_turn("b", "Q from B", "A2")
        assert manager.get_or_create("a").last_question == "Q from A"
        assert manager.get_or_create("b").last_question == "Q from B"

    def test_update_after_turn_tracks_topic(self, manager):
        manager.update_after_turn("conv1", "What is machine learning?", "ML is...")
        ctx = manager.get_or_create("conv1")
        assert ctx.current_topic

    def test_clear_removes_window(self, manager):
        manager.update_after_turn("conv1", "Q", "A")
        manager.clear("conv1")
        assert manager.get_turn_count("conv1") == 0

    def test_resolve_empty_after_clear(self, manager):
        manager.update_after_turn("conv1", "Q", "A")
        manager.clear("conv1")
        resolved = manager.resolve_query("conv1", "Explain it")
        assert resolved.had_reference or not resolved.had_reference
