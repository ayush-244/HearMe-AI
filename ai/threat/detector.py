import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ThreatDetector:
    THREAT_LABELS: List[str] = [
        "violence", "self-harm", "murder", "terrorism",
    ]

    def __init__(self, classifier: Any) -> None:
        self._classifier = classifier

    def detect(self, text: str) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "threat_detected": False,
                "risk_level": "none",
                "confidence": 0.0,
                "threat_type": None,
            }
        try:
            result = self._classifier.classify(text, self.THREAT_LABELS, multi_label=True)
            scores = dict(zip(result["labels"], result["scores"]))
            max_label: str = max(scores, key=scores.get)
            max_score: float = scores[max_label]

            if max_score > 0.8:
                risk_level = "high"
            elif max_score > 0.5:
                risk_level = "medium"
            elif max_score > 0.3:
                risk_level = "low"
            else:
                risk_level = "none"

            threat_detected = max_score > 0.3
            return {
                "threat_detected": threat_detected,
                "risk_level": risk_level,
                "confidence": max_score,
                "threat_type": max_label if threat_detected else None,
            }
        except Exception:
            logger.exception("Threat detection failed for text: %s", text[:50])
            return {
                "threat_detected": False,
                "risk_level": "none",
                "confidence": 0.0,
                "threat_type": None,
            }
