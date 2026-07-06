import json
import logging
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from ..schemas.knowledge import KnowledgeChatRequest, KnowledgeChatResponse, KnowledgeHealthResponse
from ..services import get_services
from ..reasoning.answer_models import KnowledgeQuery
from ..reasoning.streaming_chat_service import (
    stage_event, token_event, done_event, error_event, citation_event,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/knowledge/chat", response_model=KnowledgeChatResponse)
async def knowledge_chat_endpoint(request: KnowledgeChatRequest):
    services = get_services()
    reasoning_engine = services.get("reasoning_engine")
    if reasoning_engine is None:
        raise HTTPException(status_code=503, detail="Knowledge reasoning engine not available")

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info(
        "/knowledge/chat request: question='%s', workspace=%s, conv=%s, top_k=%d",
        question[:80], request.workspace_id, request.conversation_id or "new", request.top_k,
    )

    knowledge_query = KnowledgeQuery(
        question=question,
        workspace_id=request.workspace_id,
        conversation_id=request.conversation_id,
        top_k=request.top_k,
        min_score=request.min_score,
        language=request.language,
        document_type=request.document_type,
        document_ids=request.document_ids,
        filters=request.filters,
    )

    try:
        result = reasoning_engine.answer(knowledge_query)
        logger.info(
            "/knowledge/chat result: chunks=%d, tokens=%d, retrieval=%.2fms, generation=%.2fms, total=%.2fms",
            result.chunk_count, result.context_token_estimate,
            result.retrieval_time_ms, result.generation_time_ms, result.processing_time_ms,
        )
        return KnowledgeChatResponse(**result.to_dict())
    except Exception as e:
        logger.error("/knowledge/chat error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Knowledge reasoning failed: {str(e)}")


@router.post("/knowledge/chat/stream")
async def knowledge_chat_stream(request: KnowledgeChatRequest):
    services = get_services()
    reasoning_engine = services.get("reasoning_engine")
    if reasoning_engine is None:
        raise HTTPException(status_code=503, detail="Knowledge reasoning engine not available")

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    knowledge_query = KnowledgeQuery(
        question=question,
        workspace_id=request.workspace_id,
        conversation_id=request.conversation_id,
        top_k=request.top_k,
        min_score=request.min_score,
        language=request.language,
        document_type=request.document_type,
        document_ids=request.document_ids,
        filters=request.filters,
    )

    streaming_service = services.get("streaming_chat_service")

    async def event_stream() -> AsyncGenerator[str, None]:
        intent = None
        search_docs = False
        search_mem = False
        answer_text = ""
        citations = []
        sources = []
        chunk_count = 0

        try:
            result = reasoning_engine.answer(knowledge_query)

            if result.intent:
                intent = result.intent.get("type", "general_ai")
                intent_info = result.intent

            if intent_info:
                intent = intent_info.get("type", "general_ai")
                search_docs = intent in ("document_question", "mixed")
                search_mem = intent in ("personal_memory", "mixed")

            stages = [
                {"stage": "thinking", "label": "Thinking..."},
            ]
            if search_docs:
                stages.append({"stage": "searching_documents", "label": "Searching documents..."})
            if search_mem:
                stages.append({"stage": "searching_memories", "label": "Searching memories..."})
            stages.append({"stage": "writing", "label": "Writing response..."})

            for s in stages:
                yield stage_event(s["stage"], s["label"])

            if streaming_service and result.answer:
                async for event in streaming_service.stream_response(result.answer):
                    yield event
                    answer_text = result.answer

            if not result.answer:
                yield token_event(result.answer or "")
                final_payload_empty = {
                    "answer": result.answer or "",
                    "chunk_count": result.chunk_count,
                    "knowledge_gap": result.knowledge_gap,
                    "guardrail_triggered": result.guardrail_triggered,
                }
                if result.retrieval_trace:
                    final_payload_empty["retrieval_trace"] = {
                        k: v for k, v in result.retrieval_trace.__dict__.items() if v is not None
                    }
                yield done_event(final_payload_empty)
                return

            answer_text = result.answer

            if result.citations:
                citations = result.citations
            if result.sources:
                sources = result.sources

            if citations:
                yield citation_event(citations, sources)

            final_payload = {
                "answer": answer_text,
                "chunk_count": result.chunk_count,
                "context_token_estimate": result.context_token_estimate,
                "knowledge_gap": result.knowledge_gap,
                "guardrail_triggered": result.guardrail_triggered,
                "citations": citations,
                "sources": sources,
                "retrieval_time_ms": result.retrieval_time_ms,
                "generation_time_ms": result.generation_time_ms,
                "processing_time_ms": result.processing_time_ms,
            }
            if result.retrieval_trace:
                final_payload["retrieval_trace"] = {
                    k: v for k, v in result.retrieval_trace.__dict__.items() if v is not None
                }
            yield done_event(final_payload)

        except Exception as e:
            logger.error("Streaming error: %s", e, exc_info=True)
            yield error_event(str(e))
            yield done_event({
                "answer": "I encountered an error while generating a response. Please try again.",
                "error": str(e),
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/knowledge/health", response_model=KnowledgeHealthResponse)
async def knowledge_health_endpoint():
    services = get_services()
    reasoning_engine = services.get("reasoning_engine")
    if reasoning_engine is None:
        return KnowledgeHealthResponse(ready=False)

    try:
        health_info = reasoning_engine.health()
        return KnowledgeHealthResponse(**health_info)
    except Exception as e:
        logger.error("Knowledge health check failed: %s", e)
        return KnowledgeHealthResponse(ready=False)
