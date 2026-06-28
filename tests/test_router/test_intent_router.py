import pytest
from typing import Any, Dict, List

from backend.app.reasoning.router.intent_router import IntentRouter, SIMILARITY_THRESHOLD
from backend.app.reasoning.router.intent_models import IntentResult, IntentType, ConversationState


class TestIntentRouter:
    @pytest.fixture
    def router(self):
        return IntentRouter()

    # --- Routing Tests ---

    @pytest.mark.parametrize("query,expected_intent", [
        ("hello", IntentType.GREETING),
        ("how are you", IntentType.SMALL_TALK),
        ("who am i", IntentType.PERSONAL_MEMORY),
        ("summarize this document", IntentType.DOCUMENT_QUESTION),
        ("explain quantum physics", IntentType.GENERAL_AI),
    ])
    def test_route_primary_intents(self, router, query, expected_intent):
        result, state = router.route(query)
        assert result.intent == expected_intent

    def test_route_empty_query(self, router):
        result, state = router.route("")
        assert result.intent == IntentType.GENERAL_AI
        assert result.confidence <= 0.6

    def test_route_with_conversation_history(self, router):
        history = [{"role": "user", "content": "explain transformers"}, {"role": "assistant", "content": "transformers use attention"}]
        result, state = router.route(
            "explain more",
            history=history,
            turn_count=1,
            last_assistant_response="transformers use attention",
        )
        assert result.intent == IntentType.FOLLOW_UP

    def test_route_with_attached_documents(self, router):
        docs = [{"id": "d1", "title": "resume.pdf"}]
        result, state = router.route(
            "what do you know about me",
            attached_documents=docs,
        )
        assert result.intent == IntentType.PERSONAL_MEMORY

    def test_route_follow_up_reuses_previous_chunks(self, router):
        chunks = [{"chunk_id": "c1", "text": "some content", "score": 0.9}]
        history = [{"role": "user", "content": "summarize"}, {"role": "assistant", "content": "summary here"}]
        result, state = router.route(
            "tell me more",
            history=history,
            turn_count=1,
            last_assistant_response="summary here",
            last_retrieved_chunks=chunks,
        )
        assert result.intent == IntentType.FOLLOW_UP
        assert result.requires_documents is True
        assert result.requires_general_llm is True

    def test_route_state_populated(self, router):
        result, state = router.route(
            "hello",
            conversation_id="conv1",
            turn_count=0,
        )
        assert state.conversation_id == "conv1"
        assert state.turn_count == 0

    # --- should_search_documents Tests ---

    @pytest.mark.parametrize("intent_type,expected", [
        (IntentType.GREETING, False),
        (IntentType.SMALL_TALK, False),
        (IntentType.PERSONAL_MEMORY, False),
        (IntentType.GENERAL_AI, False),
        (IntentType.DOCUMENT_QUESTION, True),
        (IntentType.MIXED, True),
        (IntentType.FOLLOW_UP, False),
    ])
    def test_should_search_documents(self, router, intent_type, expected):
        intent = IntentResult(intent=intent_type)
        assert router.should_search_documents(intent) == expected

    def test_should_search_documents_follow_up_with_chunks(self, router):
        intent = IntentResult(intent=IntentType.FOLLOW_UP, requires_documents=True)
        assert router.should_search_documents(intent) is True

    # --- should_search_memory Tests ---

    @pytest.mark.parametrize("intent_type,expected", [
        (IntentType.GREETING, False),
        (IntentType.SMALL_TALK, False),
        (IntentType.PERSONAL_MEMORY, True),
        (IntentType.GENERAL_AI, False),
        (IntentType.DOCUMENT_QUESTION, False),
        (IntentType.MIXED, True),
        (IntentType.FOLLOW_UP, False),
    ])
    def test_should_search_memory(self, router, intent_type, expected):
        intent = IntentResult(intent=intent_type)
        assert router.should_search_memory(intent) == expected

    # --- should_include_citations Tests ---

    @pytest.mark.parametrize("intent_type,chunks_used,max_score,expected", [
        (IntentType.GREETING, True, 0.9, False),
        (IntentType.SMALL_TALK, True, 0.9, False),
        (IntentType.PERSONAL_MEMORY, True, 0.9, False),
        (IntentType.GENERAL_AI, True, 0.9, False),
        (IntentType.DOCUMENT_QUESTION, True, 0.9, True),
        (IntentType.DOCUMENT_QUESTION, True, 0.5, False),
        (IntentType.DOCUMENT_QUESTION, False, 0.0, False),
        (IntentType.MIXED, True, 0.9, True),
        (IntentType.MIXED, True, 0.4, False),
        (IntentType.MIXED, False, 0.0, False),
        (IntentType.FOLLOW_UP, True, 0.9, True),
        (IntentType.FOLLOW_UP, False, 0.0, False),
    ])
    def test_should_include_citations(self, router, intent_type, chunks_used, max_score, expected):
        intent = IntentResult(intent=intent_type)
        result = router.should_include_citations(intent, chunks_used, max_score)
        assert result == expected

    def test_citations_suppressed_below_threshold(self, router):
        intent = IntentResult(intent=IntentType.DOCUMENT_QUESTION)
        near_threshold = SIMILARITY_THRESHOLD - 0.01
        assert router.should_include_citations(intent, True, near_threshold) is False
        at_threshold = SIMILARITY_THRESHOLD
        assert router.should_include_citations(intent, True, at_threshold) is True

    # --- Intent Properties Tests ---

    @pytest.mark.parametrize("intent_type,requires_docs,requires_mem,requires_llm,requires_hist", [
        (IntentType.GREETING, False, False, True, False),
        (IntentType.SMALL_TALK, False, False, True, False),
        (IntentType.PERSONAL_MEMORY, False, True, False, False),
        (IntentType.DOCUMENT_QUESTION, True, False, False, False),
        (IntentType.GENERAL_AI, False, False, True, False),
        (IntentType.MIXED, True, True, False, False),
        (IntentType.FOLLOW_UP, False, False, True, True),
    ])
    def test_intent_properties(self, intent_type, requires_docs, requires_mem, requires_llm, requires_hist):
        intent = IntentResult(intent=intent_type)
        assert intent.requires_documents == requires_docs
        assert intent.requires_memory == requires_mem
        assert intent.requires_general_llm == requires_llm
        assert intent.requires_history == requires_hist

    def test_intent_custom_confidence(self, router):
        intent = IntentResult(intent=IntentType.DOCUMENT_QUESTION, confidence=0.5)
        assert intent.confidence == 0.5

    def test_intent_sub_questions(self):
        intent = IntentResult(intent=IntentType.MIXED, sub_questions=["what is my name", "summarize the document"])
        assert len(intent.sub_questions) == 2

    # --- ConversationState Tests ---

    def test_conversation_state_defaults(self):
        state = ConversationState()
        assert state.conversation_id is None
        assert state.history == []
        assert state.attached_documents == []
        assert state.last_assistant_response is None
        assert state.last_retrieved_chunks == []
        assert state.last_retrieved_context is None
        assert state.turn_count == 0

    def test_conversation_state_full(self):
        state = ConversationState(
            conversation_id="conv1",
            history=[{"role": "user", "content": "hi"}],
            attached_documents=[{"id": "d1"}],
            last_assistant_response="hello",
            last_retrieved_chunks=[{"chunk_id": "c1"}],
            last_retrieved_context="some context",
            turn_count=1,
        )
        assert state.conversation_id == "conv1"
        assert len(state.history) == 1
        assert len(state.attached_documents) == 1
        assert state.last_assistant_response == "hello"
        assert len(state.last_retrieved_chunks) == 1
        assert state.last_retrieved_context == "some context"
        assert state.turn_count == 1

    # --- Router Decision Speed ---

    def test_router_speed(self, router):
        import time
        history = [{"role": "user", "content": "what is ML"}, {"role": "assistant", "content": "ML is machine learning"}]
        start = time.time()
        for _ in range(100):
            router.route(
                "explain more",
                history=history,
                turn_count=1,
                last_assistant_response="ML is machine learning",
                last_retrieved_chunks=[{"chunk_id": "c1", "score": 0.9}],
            )
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 200, f"100 route calls took {elapsed_ms:.2f}ms (expected <200ms)"
