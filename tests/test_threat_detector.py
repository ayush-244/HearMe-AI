import pytest
from unittest.mock import Mock
from ai.threat.detector import ThreatDetector


class TestThreatDetector:
    @pytest.fixture
    def mock_classifier(self):
        classifier = Mock()
        classifier.classify.return_value = {
            "labels": ["violence", "self-harm", "murder", "terrorism"],
            "scores": [0.92, 0.03, 0.03, 0.02],
        }
        return classifier

    def test_detect_high_risk_threat(self, mock_classifier):
        detector = ThreatDetector(mock_classifier)
        result = detector.detect("I will hurt someone")
        assert result["threat_detected"] is True
        assert result["risk_level"] == "high"
        assert result["confidence"] == 0.92
        assert result["threat_type"] == "violence"

    def test_detect_medium_risk_threat(self, mock_classifier):
        mock_classifier.classify.return_value = {
            "labels": ["violence", "self-harm", "murder", "terrorism"],
            "scores": [0.65, 0.12, 0.10, 0.08],
        }
        detector = ThreatDetector(mock_classifier)
        result = detector.detect("I might hurt someone")
        assert result["threat_detected"] is True
        assert result["risk_level"] == "medium"
        assert result["confidence"] == 0.65

    def test_detect_low_risk_threat(self, mock_classifier):
        mock_classifier.classify.return_value = {
            "labels": ["violence", "self-harm", "murder", "terrorism"],
            "scores": [0.35, 0.25, 0.20, 0.15],
        }
        detector = ThreatDetector(mock_classifier)
        result = detector.detect("That's violent movie")
        assert result["threat_detected"] is True
        assert result["risk_level"] == "low"

    def test_detect_no_threat(self, mock_classifier):
        mock_classifier.classify.return_value = {
            "labels": ["violence", "self-harm", "murder", "terrorism"],
            "scores": [0.05, 0.03, 0.02, 0.01],
        }
        detector = ThreatDetector(mock_classifier)
        result = detector.detect("I like pizza")
        assert result["threat_detected"] is False
        assert result["risk_level"] == "none"
        assert result["threat_type"] is None

    def test_detect_empty_text(self, mock_classifier):
        detector = ThreatDetector(mock_classifier)
        result = detector.detect("")
        assert result["threat_detected"] is False
        assert result["risk_level"] == "none"
        assert result["confidence"] == 0.0

    def test_detect_whitespace_text(self, mock_classifier):
        detector = ThreatDetector(mock_classifier)
        result = detector.detect("   ")
        assert result["threat_detected"] is False

    def test_detect_handles_exception(self, mock_classifier):
        mock_classifier.classify.side_effect = RuntimeError("Model error")
        detector = ThreatDetector(mock_classifier)
        result = detector.detect("Test text")
        assert result["threat_detected"] is False
        assert result["risk_level"] == "none"
        assert result["confidence"] == 0.0
