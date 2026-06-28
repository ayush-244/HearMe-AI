import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from .intent_models import IntentResult, IntentType, ConversationState
from .intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.55


class IntentRouter:
    def __init__(self, classifier: Optional[IntentClassifier] = None):
        self._classifier = classifier or IntentClassifier()
        logger.info("IntentRouter initialized with similarity_threshold=%.2f", SIMILARITY_THRESHOLD)

    def route(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        attached_documents: Optional[List[Dict[str, Any]]] = None,
        last_assistant_response: Optional[str] = None,
        last_retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
        turn_count: int = 0,
    ) -> Tuple[IntentResult, ConversationState]:
        start = time.time()

        state = ConversationState(
            conversation_id=conversation_id,
            history=history or [],
            attached_documents=attached_documents or [],
            last_assistant_response=last_assistant_response,
            turn_count=turn_count,
        )

        state.last_retrieved_chunks = last_retrieved_chunks or []

        intent_result = self._classifier.classify(query, state)

        if intent_result.intent == IntentType.FOLLOW_UP and state.history:
            if state.last_retrieved_chunks:
                intent_result.requires_documents = True
                intent_result.requires_general_llm = True
                logger.debug("Follow-up reusing previous retrieved context (%d chunks)", len(state.last_retrieved_chunks))

        if intent_result.intent == IntentType.PERSONAL_MEMORY and intent_result.requires_memory:
            logger.debug("Personal memory intent: will query memory first")

        elapsed_ms = (time.time() - start) * 1000
        logger.info(
            "Router decision: query='%s' -> %s (mem=%s, docs=%s, gen=%s, conf=%.2f, time=%.2fms)",
            query[:40], intent_result.intent.value,
            intent_result.requires_memory, intent_result.requires_documents,
            intent_result.requires_general_llm, intent_result.confidence, elapsed_ms,
        )

        return intent_result, state

    def should_search_documents(self, intent: IntentResult) -> bool:
        if intent.intent in (IntentType.GREETING, IntentType.SMALL_TALK, IntentType.GENERAL_AI):
            return False
        if intent.intent == IntentType.PERSONAL_MEMORY:
            return False
        if intent.intent == IntentType.FOLLOW_UP and not intent.requires_documents:
            return False
        return intent.requires_documents

    def should_search_memory(self, intent: IntentResult) -> bool:
        return intent.requires_memory

    def should_include_citations(self, intent: IntentResult, chunks_used: bool, max_score: float = 0.0) -> bool:
        if intent.intent in (IntentType.GREETING, IntentType.SMALL_TALK, IntentType.GENERAL_AI, IntentType.PERSONAL_MEMORY):
            return False
        if not chunks_used:
            return False
        if max_score < SIMILARITY_THRESHOLD:
            logger.debug("Citations suppressed: max_score=%.4f < threshold=%.2f", max_score, SIMILARITY_THRESHOLD)
            return False
        return True

    def should_include_citations_for_answer(self, intent: IntentResult) -> bool:
        return intent.intent in (IntentType.DOCUMENT_QUESTION, IntentType.MIXED)
