import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class EmotionDetector:
    EMOTIONS: List[str] = [
        "joy", "sadness", "anger", "fear", "love",
        "surprise", "disgust", "neutral",
    ]

    def __init__(self, classifier: Any) -> None:
        self._classifier = classifier

    def detect(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"label": "neutral", "confidence": 1.0}
        try:
            result = self._classifier.classify(text, self.EMOTIONS)
            return {
                "label": result["labels"][0],
                "confidence": result["scores"][0],
            }
        except Exception:
            logger.exception("Emotion detection failed for text: %s", text[:50])
            return {"label": "neutral", "confidence": 0.0}
