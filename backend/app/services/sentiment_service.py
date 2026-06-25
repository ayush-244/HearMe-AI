import logging
from typing import Tuple
from ai.sentiment.model import SentimentModel

logger = logging.getLogger(__name__)


class SentimentService:
    def __init__(self, model: SentimentModel):
        self._model = model

    def analyze(self, text: str) -> Tuple[str, float]:
        if not text or not text.strip():
            return "Neutral", 0.0
        sentiment, confidence = self._model.predict(text)
        logger.debug("Sentiment: %s (%.2f%%) for input (len=%d)", sentiment, confidence * 100, len(text))
        return sentiment, confidence
