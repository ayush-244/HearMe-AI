import logging
from typing import Any, Dict

from ai.emotion.detector import EmotionDetector

logger = logging.getLogger(__name__)


class EmotionService:
    def __init__(self, detector: EmotionDetector) -> None:
        self._detector = detector

    def analyze(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"label": "neutral", "confidence": 0.0}
        return self._detector.detect(text)
