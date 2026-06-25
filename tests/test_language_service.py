import pytest
from unittest.mock import Mock, patch
from backend.app.services.language_service import LanguageService


@pytest.fixture
def mock_detector():
    detector = Mock()
    detector.detect.return_value = "fr"
    return detector


@pytest.fixture
def language_configs():
    return {
        "en": {"name": "English", "system_prompt": "", "language_instruction": ""},
        "fr": {"name": "French", "system_prompt": "", "language_instruction": ""},
    }


class TestLanguageService:
    def test_detect_returns_language_code(self, mock_detector, language_configs):
        service = LanguageService(mock_detector, language_configs)
        result = service.detect("Bonjour")
        assert result == "fr"

    def test_detect_empty_text_returns_en(self, mock_detector, language_configs):
        service = LanguageService(mock_detector, language_configs)
        result = service.detect("")
        assert result == "en"

    def test_get_language_name_returns_name(self, mock_detector, language_configs):
        service = LanguageService(mock_detector, language_configs)
        assert service.get_language_name("fr") == "French"
        assert service.get_language_name("en") == "English"

    def test_get_language_name_unknown_returns_unknown(self, mock_detector, language_configs):
        service = LanguageService(mock_detector, language_configs)
        assert service.get_language_name("de") == "Unknown"

    def test_get_supported_languages_returns_copy(self, mock_detector, language_configs):
        service = LanguageService(mock_detector, language_configs)
        langs = service.get_supported_languages()
        assert langs == language_configs
        langs["new"] = {}
        assert "new" not in service.get_supported_languages()
