import logging
from typing import Set
from langdetect import detect, DetectorFactory

logger = logging.getLogger(__name__)

DetectorFactory.seed = 42


class LanguageDetector:
    SUPPORTED_LANGUAGES: Set[str] = {"en", "es", "fr", "hi"}

    def detect(self, text: str) -> str:
        try:
            detected = detect(text)
            return detected if detected in self.SUPPORTED_LANGUAGES else "en"
        except Exception as e:
            logger.error("Language detection error: %s", str(e))
            return "en"
