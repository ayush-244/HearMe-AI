import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    def __init__(self, language_service=None, intent_service=None):
        self._language_service = language_service
        self._intent_service = intent_service

    def analyze(self, query: str) -> Dict[str, Any]:
        if not query or not query.strip():
            return {
                "language": "unknown",
                "language_confidence": 0.0,
                "intent": "unknown",
                "intent_confidence": 0.0,
                "complexity": "simple",
                "estimated_depth": 1,
            }

        language = "unknown"
        language_confidence = 0.0
        if self._language_service:
            try:
                lang_code = self._language_service.detect(query)
                language = lang_code if lang_code else "unknown"
                language_confidence = 1.0 if language != "unknown" else 0.0
            except Exception as e:
                logger.debug("Language detection failed: %s", e)

        intent = "search"
        intent_confidence = 0.0
        if self._intent_service:
            try:
                result = self._intent_service.analyze(query)
                intent = result.get("intent", "search")
                intent_confidence = result.get("confidence", 0.0)
            except Exception as e:
                logger.debug("Intent detection failed: %s", e)

        word_count = len(query.split())
        if word_count <= 3:
            complexity = "simple"
            estimated_depth = 5
        elif word_count <= 10:
            complexity = "moderate"
            estimated_depth = 10
        else:
            complexity = "complex"
            estimated_depth = 15

        return {
            "language": language,
            "language_confidence": language_confidence,
            "intent": intent,
            "intent_confidence": intent_confidence,
            "complexity": complexity,
            "estimated_depth": estimated_depth,
        }
