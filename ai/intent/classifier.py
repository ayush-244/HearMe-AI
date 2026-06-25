import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class IntentClassifier:
    INTENTS: List[str] = [
        "greeting", "question", "conversation", "coding", "medical",
        "translation", "complaint", "mental health", "goodbye", "other",
    ]

    def __init__(self, classifier: Any) -> None:
        self._classifier = classifier

    def classify(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"intent": "other", "confidence": 0.0}
        try:
            result = self._classifier.classify(text, self.INTENTS)
            return {
                "intent": result["labels"][0],
                "confidence": result["scores"][0],
            }
        except Exception:
            logger.exception("Intent classification failed for text: %s", text[:50])
            return {"intent": "other", "confidence": 0.0}
