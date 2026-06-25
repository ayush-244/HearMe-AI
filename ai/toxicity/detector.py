import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ToxicityDetector:
    CATEGORIES: List[str] = [
        "toxicity", "hate speech", "abuse", "insults", "profanity",
    ]

    def __init__(self, classifier: Any) -> None:
        self._classifier = classifier

    def detect(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"is_toxic": False, "category": "none", "confidence": 0.0}
        try:
            result = self._classifier.classify(text, self.CATEGORIES, multi_label=True)
            scores = dict(zip(result["labels"], result["scores"]))
            max_label = max(scores, key=scores.get)
            max_score = scores[max_label]
            return {
                "is_toxic": max_score > 0.5,
                "category": max_label,
                "confidence": max_score,
            }
        except Exception:
            logger.exception("Toxicity detection failed for text: %s", text[:50])
            return {"is_toxic": False, "category": "none", "confidence": 0.0}
