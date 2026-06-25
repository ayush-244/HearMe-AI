import pytest
from unittest.mock import Mock
from backend.app.services.toxicity_service import ToxicityService


class TestToxicityService:
    @pytest.fixture
    def mock_detector(self):
        detector = Mock()
        detector.detect.return_value = {"is_toxic": True, "category": "insults", "confidence": 0.87}
        return detector

    def test_analyze_returns_detection_result(self, mock_detector):
        service = ToxicityService(mock_detector)
        result = service.analyze("You are stupid")
        assert result["is_toxic"] is True
        assert result["category"] == "insults"

    def test_analyze_empty_text(self, mock_detector):
        service = ToxicityService(mock_detector)
        result = service.analyze("")
        assert result["is_toxic"] is False
        assert result["category"] == "none"
        assert result["confidence"] == 0.0

    def test_analyze_whitespace_text(self, mock_detector):
        service = ToxicityService(mock_detector)
        result = service.analyze("   ")
        assert result["is_toxic"] is False

    def test_analyze_delegates_to_detector(self, mock_detector):
        service = ToxicityService(mock_detector)
        service.analyze("Test")
        mock_detector.detect.assert_called_once_with("Test")
