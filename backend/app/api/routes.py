import logging
from fastapi import APIRouter, HTTPException
from ..schemas.chat import (
    ChatRequest,
    ChatResponse,
    SentimentRequest,
    SentimentResponse,
    LanguageRequest,
    LanguageResponse,
    FeedbackRequest,
    AnalyzeRequest,
    AnalyzeResponse,
    HealthResponse,
)
from ..schemas.document import VectorStoreHealthResponse
from ..services import get_services

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    services = get_services()

    message = request.message.strip()
    if not message:
        logger.warning("/chat empty message rejected")
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info("/chat request: lang=%s, msg_len=%d, history_len=%d",
                request.language, len(message), len(request.history) if request.history else 0)

    detected = services["language"].detect(message)
    language_to_use = detected if request.language == "auto" else request.language
    if language_to_use not in services["prompt"].language_configs:
        language_to_use = "en"

    sentiment, confidence = services["sentiment"].analyze(message)
    logger.info("/chat sentiment: %s (%.2f%%)", sentiment, confidence * 100)

    reply = services["chat"].generate_response(
        user_input=message,
        language=language_to_use,
        sentiment=sentiment,
        history=request.history,
    )

    language_name = services["language"].get_language_name(language_to_use)
    logger.info("/chat response: lang=%s, sentiment=%s, reply_len=%d",
                language_to_use, sentiment, len(reply))

    return ChatResponse(
        reply=reply,
        sentiment=sentiment,
        confidence=confidence,
        detected_language=language_to_use,
        language_name=language_name,
    )


@router.post("/sentiment", response_model=SentimentResponse)
async def sentiment_endpoint(request: SentimentRequest):
    services = get_services()
    sentiment, confidence = services["sentiment"].analyze(request.text)
    logger.info("/sentiment: %s (%.2f%%)", sentiment, confidence * 100)
    return SentimentResponse(sentiment=sentiment, confidence=confidence)


@router.post("/detect-language", response_model=LanguageResponse)
async def detect_language_endpoint(request: LanguageRequest):
    services = get_services()
    detected = services["language"].detect(request.text)
    name = services["language"].get_language_name(detected)
    logger.info("/detect-language: %s -> %s", detected, name)
    return LanguageResponse(detected_language=detected, language_name=name)


@router.get("/health", response_model=HealthResponse)
async def health_endpoint():
    return HealthResponse(status="healthy")


@router.get("/vectorstore/health", response_model=VectorStoreHealthResponse)
async def vectorstore_health_endpoint():
    services = get_services()
    vector_store = services.get("vector_store")
    if vector_store is None:
        return VectorStoreHealthResponse(
            status="not_configured",
            collection="",
            vectors=0,
        )
    try:
        health_info = vector_store.health()
        return VectorStoreHealthResponse(
            status=health_info.get("status", "unknown"),
            collection=health_info.get("collection", ""),
            vectors=health_info.get("vectors", 0),
        )
    except Exception as e:
        logger.error("Vector store health check failed: %s", e)
        return VectorStoreHealthResponse(
            status="unhealthy",
            collection="",
            vectors=0,
        )


@router.post("/feedback", response_model=dict)
async def feedback_endpoint(request: FeedbackRequest):
    logger.info("/feedback received: message_id=%s, rating=%d, has_comment=%s",
                request.message_id, request.rating, bool(request.comment))
    return {"status": "received", "message_id": request.message_id, "rating": request.rating}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: AnalyzeRequest):
    services = get_services()

    message = request.message.strip()
    if not message:
        logger.warning("/analyze empty message rejected")
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info("/analyze request: lang=%s, msg_len=%d, history_len=%d",
                request.language, len(message), len(request.history) if request.history else 0)

    result = services["pipeline"].analyze(
        text=message,
        language=request.language,
        history=request.history,
    )

    logger.info("/analyze response: lang=%s, sentiment=%s, emotion=%s, intent=%s, reply_len=%d",
                result.get("language"), result.get("sentiment"), result.get("emotion"),
                result.get("intent"), len(result.get("response", "")))

    return AnalyzeResponse(**result)
