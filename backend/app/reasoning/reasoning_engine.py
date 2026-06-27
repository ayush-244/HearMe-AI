import logging
import time
from typing import Any, Dict, List, Optional

from ..config.settings import Settings
from ..services.chat_service import ChatService
from ..retrieval.search_models import SearchQuery
from ..retrieval.search_engine import SearchEngine
from .context_builder import ContextBuilder
from .prompt_builder import PromptBuilder
from .citation_manager import CitationManager
from .response_validator import ResponseValidator
from .guardrails import Guardrails
from .answer_models import KnowledgeQuery, KnowledgeAnswer, ConversationTurn

logger = logging.getLogger(__name__)


class ReasoningEngine:
    def __init__(
        self,
        search_engine: SearchEngine,
        chat_service: ChatService,
        context_builder: ContextBuilder,
        prompt_builder: PromptBuilder,
        citation_manager: CitationManager,
        response_validator: ResponseValidator,
        guardrails: Guardrails,
        settings: Settings,
        memory_engine: Any = None,
    ):
        self._search_engine = search_engine
        self._chat_service = chat_service
        self._context_builder = context_builder
        self._prompt_builder = prompt_builder
        self._citation_manager = citation_manager
        self._response_validator = response_validator
        self._guardrails = guardrails
        self._settings = settings
        self._memory_engine = memory_engine
        self._conversation_histories: Dict[str, List[ConversationTurn]] = {}
        logger.info("ReasoningEngine initialized")

    def answer(self, query: KnowledgeQuery) -> KnowledgeAnswer:
        total_start = time.time()

        if not query.question or not query.question.strip():
            return KnowledgeAnswer(
                question=query.question or "",
                answer="Please provide a valid question.",
                processing_time_ms=0.0,
            )

        retrieval_start = time.time()
        try:
            search_result = self._search_engine.search(
                SearchQuery(
                    text=query.question,
                    workspace_id=query.workspace_id,
                    top_k=query.top_k,
                    min_score=query.min_score,
                    filters=query.filters,
                    language=query.language,
                    document_type=query.document_type,
                    document_ids=query.document_ids,
                )
            )
        except Exception as e:
            logger.error("Search failed during reasoning: %s", e, exc_info=True)
            return KnowledgeAnswer(
                question=query.question,
                answer="I encountered an error while searching for information. Please try again.",
                processing_time_ms=(time.time() - total_start) * 1000,
            )
        retrieval_time = (time.time() - retrieval_start) * 1000

        raw_chunks = []
        if search_result.results:
            for item in search_result.results:
                raw_chunks.append({
                    "chunk_id": item.chunk_id,
                    "document_id": item.document_id,
                    "text": item.text,
                    "title": item.title,
                    "section": item.section,
                    "page": item.page,
                    "score": item.score,
                    "chunk_index": item.chunk_index,
                    "language": item.language,
                    "document_type": item.document_type,
                    "workspace_id": item.workspace_id,
                    "keywords": item.keywords,
                })

        if not raw_chunks:
            gap_answer = "I couldn't find enough information in the uploaded documents."
            total_time = (time.time() - total_start) * 1000
            return KnowledgeAnswer(
                question=query.question,
                answer=gap_answer,
                processing_time_ms=total_time,
                retrieval_time_ms=retrieval_time,
                generation_time_ms=0.0,
                chunk_count=0,
                context_token_estimate=0,
                knowledge_gap=True,
                conversation_id=query.conversation_id,
            )

        filtered_chunks = self._guardrails.filter_chunks(raw_chunks)
        if not filtered_chunks:
            gap_answer = "I couldn't find enough information in the uploaded documents."
            total_time = (time.time() - total_start) * 1000
            return KnowledgeAnswer(
                question=query.question,
                answer=gap_answer,
                processing_time_ms=total_time,
                retrieval_time_ms=retrieval_time,
                generation_time_ms=0.0,
                chunk_count=0,
                context_token_estimate=0,
                knowledge_gap=True,
                guardrail_triggered=True,
                conversation_id=query.conversation_id,
            )

        guardrail_triggered = len(filtered_chunks) < len(raw_chunks)

        context = self._context_builder.build(filtered_chunks)

        memory_context = None
        if self._memory_engine is not None and query.workspace_id:
            try:
                memory_result = self._memory_engine.retrieve_memories(
                    query=query.question,
                    workspace_id=query.workspace_id,
                    top_k=5,
                )
                if memory_result.get("memories"):
                    memory_context = memory_result["memories"]
                    logger.debug(
                        "Memory context retrieved: %d memories for query='%s'",
                        len(memory_context), query.question[:40],
                    )
            except Exception as e:
                logger.warning("Memory retrieval failed (non-fatal): %s", e)

        self._citation_manager.track_chunks(context["chunks"])

        conversation_history = self._get_conversation_history(query.conversation_id)

        allow_external = self._settings.reasoning_allow_external_knowledge

        prompt = self._prompt_builder.build(
            context=context,
            question=query.question,
            conversation_history=conversation_history,
            language=query.language or "en",
            allow_external_knowledge=allow_external,
            memory_context=memory_context,
        )

        if not self._guardrails.check_query(query.question):
            gap_answer = "I couldn't find enough information in the uploaded documents."
            total_time = (time.time() - total_start) * 1000
            return KnowledgeAnswer(
                question=query.question,
                answer=gap_answer,
                processing_time_ms=total_time,
                retrieval_time_ms=retrieval_time,
                generation_time_ms=0.0,
                chunk_count=len(context["chunks"]),
                context_token_estimate=context["total_tokens"],
                guardrail_triggered=True,
                knowledge_gap=True,
                conversation_id=query.conversation_id,
            )

        generation_start = time.time()
        try:
            answer_text = self._chat_service.invoke_llm(prompt)
        except Exception as e:
            logger.error("LLM invocation failed during reasoning: %s", e, exc_info=True)
            answer_text = "I encountered an error while generating an answer. Please try again."
        generation_time = (time.time() - generation_start) * 1000

        citations = self._citation_manager.build_citations()
        sources = self._citation_manager.build_sources()

        validation = self._response_validator.validate(answer_text, context["chunks"], citations)
        validation_passed = validation["passed"]
        knowledge_gap = self._response_validator.is_knowledge_gap_response(answer_text)

        total_time = (time.time() - total_start) * 1000

        self._update_conversation_history(
            query.conversation_id,
            query.question,
            answer_text,
        )

        logger.info(
            "Reasoning complete: question='%s', chunks=%d, tokens=%d, "
            "retrieval=%.2fms, generation=%.2fms, total=%.2fms, "
            "citations=%d, validation=%s, gap=%s, guardrail=%s",
            query.question[:50], len(context["chunks"]), context["total_tokens"],
            retrieval_time, generation_time, total_time,
            len(citations), validation_passed, knowledge_gap, guardrail_triggered,
        )

        return KnowledgeAnswer(
            question=query.question,
            answer=answer_text,
            citations=citations,
            sources=sources,
            processing_time_ms=total_time,
            retrieval_time_ms=retrieval_time,
            generation_time_ms=generation_time,
            chunk_count=len(context["chunks"]),
            context_token_estimate=context["total_tokens"],
            validation_passed=validation_passed,
            guardrail_triggered=guardrail_triggered,
            knowledge_gap=knowledge_gap,
            conversation_id=query.conversation_id,
        )

    def _get_conversation_history(self, conversation_id: str) -> Optional[List[Dict[str, str]]]:
        if not conversation_id:
            return None
        turns = self._conversation_histories.get(conversation_id, [])
        if not turns:
            return None
        limit = self._settings.reasoning_conversation_history_limit
        recent = turns[-limit:]
        return [{"role": t.role, "content": t.content} for t in recent]

    def _update_conversation_history(self, conversation_id: str, question: str, answer: str) -> None:
        if not conversation_id:
            return
        if conversation_id not in self._conversation_histories:
            self._conversation_histories[conversation_id] = []
        self._conversation_histories[conversation_id].append(
            ConversationTurn(role="user", content=question)
        )
        self._conversation_histories[conversation_id].append(
            ConversationTurn(role="assistant", content=answer)
        )
        limit = self._settings.reasoning_conversation_history_limit
        if len(self._conversation_histories[conversation_id]) > limit * 2:
            self._conversation_histories[conversation_id] = (
                self._conversation_histories[conversation_id][-(limit * 2):]
            )

    def clear_conversation_history(self, conversation_id: str) -> None:
        self._conversation_histories.pop(conversation_id, None)
        logger.info("Cleared conversation history for %s", conversation_id)

    def health(self) -> Dict[str, Any]:
        search_health = self._search_engine.health()
        return {
            "ready": search_health.get("ready", False),
            "search_engine_ready": search_health.get("ready", False),
            "context_builder_max_tokens": self._context_builder.max_tokens,
            "context_builder_max_chunks": self._context_builder.max_chunks,
            "citation_style": self._citation_manager.style,
            "allow_external_knowledge": self._settings.reasoning_allow_external_knowledge,
            "conversation_history_limit": self._settings.reasoning_conversation_history_limit,
            "active_conversations": len(self._conversation_histories),
        }
