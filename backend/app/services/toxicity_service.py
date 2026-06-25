import logging
from typing import Any, Dict

from ai.toxicity.detector import ToxicityDetector

logger = logging.getLogger(__name__)


class ToxicityService:
    def __init__(self, detector: ToxicityDetector) -> None:
        self._detector = detector

    def analyze(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"is_toxic": False, "category": "none", "confidence": 0.0}
        return self._detector.detect(text)
