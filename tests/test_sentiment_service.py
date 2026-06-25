import pytest
from unittest.mock import Mock, patch
from backend.app.services.sentiment_service import SentimentService


@pytest.fixture
def mock_model():
    model = Mock()
    model.predict.return_value = ("Positive", 0.95)
    return model


class TestSentimentService:
    def test_analyze_returns_sentiment_and_confidence(self, mock_model):
        service = SentimentService(mock_model)
        sentiment, confidence = service.analyze("I love this!")
        assert sentiment == "Positive"
        assert confidence == 0.95

    def test_analyze_empty_text_returns_neutral(self, mock_model):
        service = SentimentService(mock_model)
        sentiment, confidence = service.analyze("")
        assert sentiment == "Neutral"
        assert confidence == 0.0

    def test_analyze_whitespace_text_returns_neutral(self, mock_model):
        service = SentimentService(mock_model)
        sentiment, confidence = service.analyze("   ")
        assert sentiment == "Neutral"

    def test_analyze_delegates_to_model(self, mock_model):
        service = SentimentService(mock_model)
        service.analyze("Hello world")
        mock_model.predict.assert_called_once_with("Hello world")
