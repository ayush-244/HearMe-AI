import pytest
from unittest.mock import Mock
from backend.app.services.threat_service import ThreatService


class TestThreatService:
    @pytest.fixture
    def mock_detector(self):
        detector = Mock()
        detector.detect.return_value = {
            "threat_detected": True,
            "risk_level": "high",
            "confidence": 0.92,
            "threat_type": "violence",
        }
        return detector

    def test_analyze_returns_detection_result(self, mock_detector):
        service = ThreatService(mock_detector)
        result = service.analyze("I will hurt you")
        assert result["threat_detected"] is True
        assert result["risk_level"] == "high"
        assert result["threat_type"] == "violence"

    def test_analyze_empty_text(self, mock_detector):
        service = ThreatService(mock_detector)
        result = service.analyze("")
        assert result["threat_detected"] is False
        assert result["risk_level"] == "none"
        assert result["confidence"] == 0.0

    def test_analyze_whitespace_text(self, mock_detector):
        service = ThreatService(mock_detector)
        result = service.analyze("   ")
        assert result["threat_detected"] is False
        assert result["risk_level"] == "none"

    def test_analyze_delegates_to_detector(self, mock_detector):
        service = ThreatService(mock_detector)
        service.analyze("Test")
        mock_detector.detect.assert_called_once_with("Test")
