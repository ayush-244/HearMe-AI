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

        if self._has_semantic_document_reference(q_lower):
            return True, 0.78

        return False, 0.0

    def _has_semantic_document_reference(self, q_lower: str) -> bool:
        from .intent_rules import SEMANTIC_TERMS_PATTERN, CONTEXTUAL_ANCHOR_PATTERN
        
        if not SEMANTIC_TERMS_PATTERN.search(q_lower):
            return False
            
        if CONTEXTUAL_ANCHOR_PATTERN.search(q_lower):
            return True
            
        return False

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
        """
        Determine whether the current query is a follow-up to the previous turn.

        A follow-up must explicitly refer to the previous discussion.
        Standalone questions such as "What is AI?" or "Who is Elon Musk?"
        must always start a new topic.
        """

        if state.turn_count == 0 or not state.last_assistant_response:
            return False

        # Standalone questions always start a new topic
        standalone_prefixes = (
            "what is ",
            "who is ",
            "what are ",
            "who are ",
            "define ",
            "describe ",
            "tell me about ",
            "introduce ",
        )

        if q_lower.startswith(standalone_prefixes):
            return False

        # Explicit follow-up phrases
        followup_prefixes = (
            "explain more",
            "tell me more",
            "continue",
            "go on",
            "elaborate",
            "expand",
            "give an example",
            "another example",
            "can you explain",
            "can you elaborate",
            "how does that",
            "how does it",
            "why is that",
            "what about that",
            "what else",
            "is that",
            "does that",
            "and then",
            "then what",
        )

        if any(q_lower.startswith(prefix) for prefix in followup_prefixes):
            return True

        # Very short pronoun-based references
        pronoun_queries = {
            "why",
            "how",
            "why?",
            "how?",
            "more",
            "again",
            "example",
            "examples",
            "it",
            "this",
            "that",
        }

        if q_lower.strip() in pronoun_queries:
            return True

        return False


    def _has_document_reference(self, q_lower: str) -> bool:
        for pattern in DOCUMENT_REFERENCE_PATTERNS:
            if pattern.search(q_lower):
                return True
        return False
