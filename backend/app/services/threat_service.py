import logging
from typing import Any, Dict

from ai.threat.detector import ThreatDetector

logger = logging.getLogger(__name__)


class ThreatService:
    def __init__(self, detector: ThreatDetector) -> None:
        self._detector = detector

    def analyze(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "threat_detected": False,
                "risk_level": "none",
                "confidence": 0.0,
                "threat_type": None,
            }
        return self._detector.detect(text)
