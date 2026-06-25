import pytest
from unittest.mock import Mock
from ai.toxicity.detector import ToxicityDetector


class TestToxicityDetector:
    @pytest.fixture
    def mock_classifier(self):
        classifier = Mock()
        classifier.classify.return_value = {
            "labels": ["toxicity", "hate speech", "abuse", "insults", "profanity"],
            "scores": [0.87, 0.12, 0.05, 0.32, 0.08],
        }
        return classifier

    def test_detect_returns_toxic_category(self, mock_classifier):
        detector = ToxicityDetector(mock_classifier)
        result = detector.detect("You are terrible!")
        assert result["category"] == "toxicity"
        assert result["confidence"] == 0.87
        assert result["is_toxic"] is True

    def test_detect_nontoxic_text(self, mock_classifier):
        mock_classifier.classify.return_value = {
            "labels": ["toxicity", "hate speech", "abuse", "insults", "profanity"],
            "scores": [0.02, 0.01, 0.01, 0.03, 0.01],
        }
        detector = ToxicityDetector(mock_classifier)
        result = detector.detect("Have a nice day!")
        assert result["is_toxic"] is False

    def test_detect_empty_text(self, mock_classifier):
        detector = ToxicityDetector(mock_classifier)
        result = detector.detect("")
        assert result["is_toxic"] is False
        assert result["category"] == "none"
        assert result["confidence"] == 0.0

    def test_detect_whitespace_text(self, mock_classifier):
        detector = ToxicityDetector(mock_classifier)
        result = detector.detect("   ")
        assert result["is_toxic"] is False
        assert result["category"] == "none"

    def test_detect_handles_exception(self, mock_classifier):
        mock_classifier.classify.side_effect = RuntimeError("Model error")
        detector = ToxicityDetector(mock_classifier)
        result = detector.detect("Test text")
        assert result["is_toxic"] is False
        assert result["category"] == "none"
        assert result["confidence"] == 0.0

    def test_detect_delegates_with_multi_label(self, mock_classifier):
        detector = ToxicityDetector(mock_classifier)
        detector.detect("Some text")
        mock_classifier.classify.assert_called_once_with(
            "Some text", ToxicityDetector.CATEGORIES, multi_label=True
        )
