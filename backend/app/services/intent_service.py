import logging
from typing import Any, Dict

from ai.intent.classifier import IntentClassifier

logger = logging.getLogger(__name__)


class IntentService:
    def __init__(self, classifier: IntentClassifier) -> None:
        self._classifier = classifier

    def analyze(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"intent": "other", "confidence": 0.0}
        return self._classifier.classify(text)
