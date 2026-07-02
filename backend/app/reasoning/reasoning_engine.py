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
from .router.intent_router import IntentRouter, SIMILARITY_THRESHOLD
from .router.intent_models import IntentResult, IntentType
from .conversation.conversation_context import ConversationContextManager
from .query_rewriter import QueryRewriter, RewriteResult

logger = logging.getLogger(__name__)

IGNORE_HISTORY_INTENTS = {IntentType.GREETING, IntentType.SMALL_TALK}
CITATION_REQUIRING_INTENTS = {IntentType.DOCUMENT_QUESTION, IntentType.MIXED}


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
        self._intent_router = IntentRouter()
        self._last_retrieved_chunks: Dict[str, List[Dict[str, Any]]] = {}
        self._last_retrieved_context: Dict[str, str] = {}
        self._context_manager = ConversationContextManager()
        self._query_rewriter = QueryRewriter(self._chat_service)
        logger.info("ReasoningEngine initialized with IntentRouter, QueryRewriter, and ConversationContextManager")

    def answer(self, query: KnowledgeQuery) -> KnowledgeAnswer:
        total_start = time.time()

        if not query.question or not query.question.strip():
            return KnowledgeAnswer(
                question=query.question or "",
                answer="Please provide a valid question.",
                processing_time_ms=0.0,
            )

        conversation_history = self._get_conversation_history(query.conversation_id)
        turn_count = self._get_turn_count(query.conversation_id)
        last_assistant = self._get_last_assistant_response(query.conversation_id)

        logger.info(
            "[CTX] conv_id=%r turn_count=%d history_msgs=%d last_assistant_snippet=%r",
            query.conversation_id or "(none)",
            turn_count,
            len(conversation_history) if conversation_history else 0,
            (last_assistant or "")[:80],
        )

        ctx = self._context_manager.get_or_create(query.conversation_id) if query.conversation_id else None
        routed_query = query.question
        if ctx and ctx.last_question:
            resolved = self._context_manager.resolve_query(
                query.conversation_id, query.question,
            )
            if resolved.had_reference:
                routed_query = resolved.resolved
                logger.info(
                    "[REF] Reference resolved: %r -> %r (refs=%s)",
                    query.question[:60], routed_query[:80], resolved.references,
                )

        # Phase 27.3 - Intelligent Query Rewrite
        rewrite_result = self._query_rewriter.rewrite(routed_query, conversation_history)
        routed_query = rewrite_result.rewritten_query

        intent_result, _ = self._intent_router.route(
            query=routed_query,
            conversation_id=query.conversation_id,
            history=conversation_history,
            last_assistant_response=last_assistant,
            last_retrieved_chunks=self._last_retrieved_chunks.get(query.conversation_id or "", []),
            turn_count=turn_count,
        )

        logger.info(
            "[INTENT] question=%r -> intent=%s conf=%.2f requires_docs=%s requires_mem=%s",
            routed_query[:60], intent_result.intent.value, intent_result.confidence,
            intent_result.requires_documents, intent_result.requires_memory,
        )

        if ctx and ctx.conversation_summary:
            summary = f"[Conversation Summary: {ctx.conversation_summary}]"
            if conversation_history:
                conversation_history = list(conversation_history) + [{"role": "system", "content": summary}]
            else:
                conversation_history = [{"role": "system", "content": summary}]

        if not self._guardrails.check_query(query.question):
            total_time = (time.time() - total_start) * 1000
            return KnowledgeAnswer(
                question=query.question,
                answer="I couldn't process that request.",
                processing_time_ms=total_time,
                guardrail_triggered=True,
                conversation_id=query.conversation_id,
                intent={"type": intent_result.intent.value, "confidence": intent_result.confidence},
            )

        should_search = self._intent_router.should_search_documents(intent_result)
        should_search_memory = self._intent_router.should_search_memory(intent_result)

        retrieval_time = 0.0
        raw_chunks: List[Dict[str, Any]] = []

        if should_search:
            retrieval_start = time.time()
            logger.info("[SEARCH] Searching docs with query: %r", routed_query[:80])
            try:
                search_result = self._search_engine.search(
                    SearchQuery(
                        text=routed_query,
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
                    intent={"type": intent_result.intent.value, "confidence": intent_result.confidence},
                )
            retrieval_time = (time.time() - retrieval_start) * 1000

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

        follow_up_without_new_search = (
            not raw_chunks
            and intent_result.intent == IntentType.FOLLOW_UP
            and self._last_retrieved_chunks.get(query.conversation_id)
        )
        if follow_up_without_new_search:
            raw_chunks = list(self._last_retrieved_chunks[query.conversation_id])
            logger.debug("Follow-up reusing %d previously retrieved chunks", len(raw_chunks))

        if should_search and not raw_chunks and intent_result.intent != IntentType.FOLLOW_UP:
            total_time = (time.time() - total_start) * 1000
            return KnowledgeAnswer(
                question=query.question,
                answer="I couldn't find enough information in the uploaded documents.",
                processing_time_ms=total_time,
                retrieval_time_ms=retrieval_time,
                chunk_count=0,
                context_token_estimate=0,
                knowledge_gap=True,
                conversation_id=query.conversation_id,
                intent={"type": intent_result.intent.value, "confidence": intent_result.confidence},
            )

        chunks_used = bool(raw_chunks)
        context = None
        guardrail_triggered = False

        if raw_chunks:
            filtered_chunks = self._guardrails.filter_chunks(raw_chunks)
            guardrail_triggered = len(filtered_chunks) < len(raw_chunks)

            if not filtered_chunks:
                total_time = (time.time() - total_start) * 1000
                return KnowledgeAnswer(
                    question=query.question,
                    answer="I couldn't find enough information in the uploaded documents.",
                    processing_time_ms=total_time,
                    retrieval_time_ms=retrieval_time,
                    chunk_count=0,
                    context_token_estimate=0,
                    knowledge_gap=True,
                    guardrail_triggered=True,
                    conversation_id=query.conversation_id,
                    intent={"type": intent_result.intent.value, "confidence": intent_result.confidence},
                )

            context = self._context_builder.build(filtered_chunks)
            self._citation_manager.track_chunks(context["chunks"])
            self._last_retrieved_chunks[query.conversation_id] = list(filtered_chunks)
            chunks_used = True

        memory_context = None
        if should_search_memory and self._memory_engine is not None and query.workspace_id:
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

        allow_external = self._settings.reasoning_allow_external_knowledge

        intent_requires_history = intent_result.intent not in IGNORE_HISTORY_INTENTS
        history_for_prompt = conversation_history if intent_requires_history else None

        logger.info(
            "[PROMPT] Building prompt: intent=%s resolved_q=%r history_turns=%d chunks=%d mem=%d",
            intent_result.intent.value, routed_query[:60],
            len(history_for_prompt) if history_for_prompt else 0,
            len(context["chunks"]) if context else 0,
            len(memory_context) if memory_context else 0,
        )

        prompt = self._prompt_builder.build(
            context=context,
            question=routed_query,
            conversation_history=history_for_prompt,
            language=query.language or "en",
            allow_external_knowledge=allow_external,
            memory_context=memory_context,
            intent=intent_result,
        )

        generation_start = time.time()
        try:
            answer_text = self._chat_service.invoke_llm(prompt)
        except Exception as e:
            logger.error("LLM invocation failed during reasoning: %s", e, exc_info=True)
            answer_text = "I encountered an error while generating an answer. Please try again."
        generation_time = (time.time() - generation_start) * 1000

        max_score = 0.0
        if context and context.get("chunks"):
            max_score = max((c.get("score", 0) for c in context["chunks"]), default=0.0)

        include_citations = self._intent_router.should_include_citations(
            intent_result, chunks_used, max_score,
        )
        citations = self._citation_manager.build_citations() if include_citations else []
        sources = self._citation_manager.build_sources() if include_citations else []

        total_time = (time.time() - total_start) * 1000
        chunk_count = len(context["chunks"]) if context else 0
        token_estimate = context["total_tokens"] if context else 0
        knowledge_gap = self._response_validator.is_knowledge_gap_response(answer_text)
        knowledge_gap = knowledge_gap or (intent_result.requires_documents and not chunks_used)

        self._update_conversation_history(
            query.conversation_id, query.question, answer_text,
        )

        if query.conversation_id:
            self._context_manager.update_after_turn(
                conversation_id=query.conversation_id,
                question=query.question,
                answer=answer_text,
                intent=intent_result.intent.value if intent_result else None,
                chunks=context["chunks"] if context else None,
            )

        logger.info(
            "[DONE] conv=%r intent=%s chunks=%d gap=%s answer_snippet=%r",
            query.conversation_id or "(none)", intent_result.intent.value,
            chunk_count, knowledge_gap, answer_text[:100],
        )

        logger.info(
            "Reasoning complete: intent=%s, conf=%.2f, question='%s', "
            "chunks=%d, tokens=%d, retrieval=%.2fms, generation=%.2fms, "
            "total=%.2fms, citations=%d, gap=%s, guardrail=%s",
            intent_result.intent.value, intent_result.confidence,
            query.question[:50], chunk_count, token_estimate,
            retrieval_time, generation_time, total_time,
            len(citations), knowledge_gap, guardrail_triggered,
        )

        return KnowledgeAnswer(
            question=query.question,
            answer=answer_text,
            citations=citations,
            sources=sources,
            processing_time_ms=total_time,
            retrieval_time_ms=retrieval_time,
            generation_time_ms=generation_time,
            chunk_count=chunk_count,
            context_token_estimate=token_estimate,
            validation_passed=True,
            guardrail_triggered=guardrail_triggered,
            knowledge_gap=knowledge_gap,
            conversation_id=query.conversation_id,
            intent={"type": intent_result.intent.value, "confidence": intent_result.confidence},
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

    def _get_turn_count(self, conversation_id: str) -> int:
        turns = self._conversation_histories.get(conversation_id, [])
        return len(turns) // 2

    def _get_last_assistant_response(self, conversation_id: str) -> Optional[str]:
        turns = self._conversation_histories.get(conversation_id, [])
        if turns and turns[-1].role == "assistant":
            return turns[-1].content
        return None

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
        self._context_manager.clear(conversation_id)
        logger.info("Cleared conversation history for %s", conversation_id)

    def health(self) -> Dict[str, Any]:
        search_health = self._search_engine.health()
        ctx_health = self._context_manager.health()
        return {
            "ready": search_health.get("ready", False),
            "search_engine_ready": search_health.get("ready", False),
            "context_builder_max_tokens": self._context_builder.max_tokens,
            "context_builder_max_chunks": self._context_builder.max_chunks,
            "citation_style": self._citation_manager.style,
            "allow_external_knowledge": self._settings.reasoning_allow_external_knowledge,
            "conversation_history_limit": self._settings.reasoning_conversation_history_limit,
            "active_conversations": len(self._conversation_histories),
            "active_contexts": ctx_health.get("active_contexts", 0),
            "active_windows": ctx_health.get("active_windows", 0),
        }
