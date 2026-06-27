import logging
from fastapi import APIRouter, HTTPException
from ..schemas.knowledge import KnowledgeChatRequest, KnowledgeChatResponse, KnowledgeHealthResponse
from ..services import get_services
from ..reasoning.answer_models import KnowledgeQuery

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
