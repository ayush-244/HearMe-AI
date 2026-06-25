import logging
from typing import Dict, Optional
from ai.language.detector import LanguageDetector

logger = logging.getLogger(__name__)


class LanguageService:
    def __init__(self, detector: LanguageDetector, language_configs: Dict[str, dict]):
        self._detector = detector
        self._language_configs = language_configs

    def detect(self, text: str) -> str:
        if not text or not text.strip():
            return "en"
        detected = self._detector.detect(text)
        logger.debug("Detected language: %s", detected)
        return detected

    def get_language_name(self, code: str) -> str:
        config = self._language_configs.get(code)
        return config["name"] if config else "Unknown"

    def get_supported_languages(self) -> Dict[str, dict]:
        return dict(self._language_configs)
