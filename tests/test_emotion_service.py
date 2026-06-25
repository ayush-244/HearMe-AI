import pytest
from unittest.mock import Mock
from backend.app.services.emotion_service import EmotionService


class TestEmotionService:
    @pytest.fixture
    def mock_detector(self):
        detector = Mock()
        detector.detect.return_value = {"label": "joy", "confidence": 0.91}
        return detector

    def test_analyze_returns_detection_result(self, mock_detector):
        service = EmotionService(mock_detector)
        result = service.analyze("I am happy")
        assert result["label"] == "joy"
        assert result["confidence"] == 0.91

    def test_analyze_empty_text(self, mock_detector):
        service = EmotionService(mock_detector)
        result = service.analyze("")
        assert result["label"] == "neutral"
        assert result["confidence"] == 0.0

    def test_analyze_whitespace_text(self, mock_detector):
        service = EmotionService(mock_detector)
        result = service.analyze("   ")
        assert result["label"] == "neutral"

    def test_analyze_delegates_to_detector(self, mock_detector):
        service = EmotionService(mock_detector)
        service.analyze("Hello")
        mock_detector.detect.assert_called_once_with("Hello")
