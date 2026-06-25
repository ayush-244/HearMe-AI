from fastapi import APIRouter, HTTPException, Depends
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
from ..services import get_services

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    services = get_services()

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    detected = services["language"].detect(message)
    language_to_use = detected if request.language == "auto" else request.language
    if language_to_use not in services["prompt"].language_configs:
        language_to_use = "en"

    sentiment, confidence = services["sentiment"].analyze(message)

    reply = services["chat"].generate_response(
        user_input=message,
        language=language_to_use,
        sentiment=sentiment,
        history=request.history,
    )

    language_name = services["language"].get_language_name(language_to_use)

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
    return SentimentResponse(sentiment=sentiment, confidence=confidence)


@router.post("/detect-language", response_model=LanguageResponse)
async def detect_language_endpoint(request: LanguageRequest):
    services = get_services()
    detected = services["language"].detect(request.text)
    name = services["language"].get_language_name(detected)
    return LanguageResponse(detected_language=detected, language_name=name)


@router.get("/health", response_model=HealthResponse)
async def health_endpoint():
    return HealthResponse(status="healthy")


@router.post("/feedback")
async def feedback_endpoint(request: FeedbackRequest):
    return {"status": "received", "message_id": request.message_id, "rating": request.rating}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: AnalyzeRequest):
    services = get_services()

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = services["pipeline"].analyze(
        text=message,
        language=request.language,
        history=request.history,
    )

    return AnalyzeResponse(**result)
