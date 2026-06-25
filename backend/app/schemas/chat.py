from pydantic import BaseModel, Field
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User input message")
    language: Optional[str] = Field(default="auto", description="Language code or 'auto' for detection")
    history: Optional[List[dict]] = Field(default_factory=list, description="Previous chat messages")


class ChatResponse(BaseModel):
    reply: str
    sentiment: str
    confidence: float
    detected_language: str
    language_name: str


class SentimentRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class SentimentResponse(BaseModel):
    sentiment: str
    confidence: float


class LanguageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class LanguageResponse(BaseModel):
    detected_language: str
    language_name: str


class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class AnalyzeRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User input message")
    language: Optional[str] = Field(default="auto", description="Language code or 'auto' for detection")
    history: Optional[List[dict]] = Field(default_factory=list, description="Previous chat messages")


class AnalyzeResponse(BaseModel):
    language: str
    sentiment: str
    emotion: str
    toxicity: str
    threat: str
    intent: str
    confidence: dict
    response: str


class HealthResponse(BaseModel):
    status: str
