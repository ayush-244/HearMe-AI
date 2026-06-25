import pytest
from unittest.mock import Mock
from backend.app.services.intent_service import IntentService


class TestIntentService:
    @pytest.fixture
    def mock_classifier(self):
        classifier = Mock()
        classifier.classify.return_value = {"intent": "question", "confidence": 0.88}
        return classifier

    def test_analyze_returns_classification_result(self, mock_classifier):
        service = IntentService(mock_classifier)
        result = service.analyze("What is this?")
        assert result["intent"] == "question"
        assert result["confidence"] == 0.88

    def test_analyze_empty_text(self, mock_classifier):
        service = IntentService(mock_classifier)
        result = service.analyze("")
        assert result["intent"] == "other"
        assert result["confidence"] == 0.0

    def test_analyze_whitespace_text(self, mock_classifier):
        service = IntentService(mock_classifier)
        result = service.analyze("   ")
        assert result["intent"] == "other"
        assert result["confidence"] == 0.0

    def test_analyze_delegates_to_classifier(self, mock_classifier):
        service = IntentService(mock_classifier)
        service.analyze("Hello")
        mock_classifier.classify.assert_called_once_with("Hello")
