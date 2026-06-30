import logging
import time
from typing import Optional

from .intent_models import IntentResult, IntentType, ConversationState
from .intent_rules import (
    GREETING_PATTERNS,
    SMALL_TALK_PATTERNS,
    PERSONAL_MEMORY_PATTERNS,
    DOCUMENT_QUESTION_PATTERNS,
    GENERAL_AI_PATTERNS,
    FOLLOW_UP_PATTERNS,
    SHORT_QUERY_THRESHOLD,
    DOCUMENT_REFERENCE_PATTERNS,
)

logger = logging.getLogger(__name__)


class IntentClassifier:
    def __init__(self):
        logger.info("IntentClassifier initialized")

    def classify(
        self,
        query: str,
        state: Optional[ConversationState] = None,
    ) -> IntentResult:
        start = time.time()
        query = query.strip()
        if not query:
            return IntentResult(intent=IntentType.GENERAL_AI, confidence=0.5)

        if state is None:
            state = ConversationState()

        q_lower = query.lower()

        intent, confidence = self._classify_internal(q_lower, query, state)

        elapsed_ms = (time.time() - start) * 1000
        logger.debug(
            "Intent classified: query='%s' -> %s (confidence=%.2f, time=%.2fms)",
            query[:40], intent.value, confidence, elapsed_ms,
        )

        return IntentResult(intent=intent, confidence=confidence)

    def _classify_internal(
        self,
        q_lower: str,
        query: str,
        state: ConversationState,
    ) -> tuple:
        if self._is_greeting(q_lower):
            return IntentType.GREETING, 0.95

        if self._is_small_talk(q_lower, query):
            return IntentType.SMALL_TALK, 0.90

        if self._is_follow_up(q_lower, state):
            return IntentType.FOLLOW_UP, 0.85

        if self._is_personal_memory(q_lower, query):
            return IntentType.PERSONAL_MEMORY, 0.90

        is_doc_question, doc_conf = self._is_document_question(q_lower, query, state)
        if is_doc_question:
            return IntentType.DOCUMENT_QUESTION, doc_conf

        if self._is_mixed(q_lower, state):
            return IntentType.MIXED, 0.75

        if self._is_general_ai(q_lower):
            return IntentType.GENERAL_AI, 0.80

        is_doc_ref = self._has_document_reference(q_lower)
        if is_doc_ref and state.attached_documents:
            return IntentType.DOCUMENT_QUESTION, 0.65

        return IntentType.GENERAL_AI, 0.60

    def _is_greeting(self, q_lower: str) -> bool:
        for pattern in GREETING_PATTERNS:
            if pattern.match(q_lower):
                return True
        return q_lower.strip() in ("hello", "hi", "hey", "hi there", "hello there")

    def _is_small_talk(self, q_lower: str, query: str) -> bool:
        for pattern in SMALL_TALK_PATTERNS:
            if pattern.search(q_lower):
                return True
        if len(query.split()) <= SHORT_QUERY_THRESHOLD:
            simple_responses = {"ok", "okay", "sure", "cool", "nice", "great", "thanks", "thank you", "bye", "goodbye", "alright", "fine"}
            if q_lower.strip() in simple_responses:
                return True
        return False

    def _is_personal_memory(self, q_lower: str, query: str) -> bool:
        for pattern in PERSONAL_MEMORY_PATTERNS:
            if pattern.search(q_lower):
                return True
        from .intent_rules import PERSONAL_MEMORY_QUESTION_WORDS
        words = set(query.lower().split())
        if words & PERSONAL_MEMORY_QUESTION_WORDS:
            has_my = "my" in words or "me" in words or "mine" in words
            if has_my:
                return True
        return False

    def _is_document_question(
        self,
        q_lower: str,
        query: str,
        state: ConversationState,
    ) -> tuple:
        for pattern in DOCUMENT_QUESTION_PATTERNS:
            if pattern.search(q_lower):
                return True, 0.88

        has_doc_ref = self._has_document_reference(q_lower)
        has_docs = bool(state.attached_documents)
        if has_doc_ref and has_docs:
            return True, 0.82

        from .intent_rules import DOCUMENT_QUESTION_WORDS
        words = set(query.lower().split())
        if words & DOCUMENT_QUESTION_WORDS:
            return True, 0.75

        return False, 0.0

    def _is_mixed(self, q_lower: str, state: ConversationState) -> bool:
        has_memory_ref = any(p.search(q_lower) for p in PERSONAL_MEMORY_PATTERNS)
        has_doc_ref = any(p.search(q_lower) for p in DOCUMENT_REFERENCE_PATTERNS)
        if has_memory_ref and has_doc_ref:
            return True
        if has_memory_ref and state.attached_documents:
            return True
        return False

    def _is_general_ai(self, q_lower: str) -> bool:
        for pattern in GENERAL_AI_PATTERNS:
            if pattern.search(q_lower):
                return True
        return False

    def _is_follow_up(self, q_lower: str, state: ConversationState) -> bool:
        if state.turn_count == 0:
            return False
        for pattern in FOLLOW_UP_PATTERNS:
            if pattern.match(q_lower):
                return True
        # Short queries (≤4 words) when there's previous context
        words = q_lower.split()
        if len(words) <= 4 and state.last_assistant_response:
            short_queries = {
                "what", "why", "how", "when", "where", "explain", "more",
                "and", "so", "then", "elaborate", "continue", "example",
                "examples", "really", "like", "tell", "show", "give",
                "again", "different", "another", "next", "also",
            }
            if words and words[0] in short_queries:
                return True
        return False

    def _has_document_reference(self, q_lower: str) -> bool:
        for pattern in DOCUMENT_REFERENCE_PATTERNS:
            if pattern.search(q_lower):
                return True
        return False
