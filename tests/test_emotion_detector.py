import pytest
from unittest.mock import Mock
from ai.emotion.detector import EmotionDetector


class TestEmotionDetector:
    @pytest.fixture
    def mock_classifier(self):
        classifier = Mock()
        classifier.classify.return_value = {
            "labels": ["joy", "sadness", "anger", "fear", "love", "surprise", "disgust", "neutral"],
            "scores": [0.91, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01],
        }
        return classifier

    def test_detect_returns_label_and_confidence(self, mock_classifier):
        detector = EmotionDetector(mock_classifier)
        result = detector.detect("I am so happy today!")
        assert result["label"] == "joy"
        assert result["confidence"] == 0.91

    def test_detect_empty_text(self, mock_classifier):
        detector = EmotionDetector(mock_classifier)
        result = detector.detect("")
        assert result["label"] == "neutral"
        assert result["confidence"] == 1.0

    def test_detect_whitespace_text(self, mock_classifier):
        detector = EmotionDetector(mock_classifier)
        result = detector.detect("   ")
        assert result["label"] == "neutral"
        assert result["confidence"] == 1.0

    def test_detect_delegates_to_classifier(self, mock_classifier):
        detector = EmotionDetector(mock_classifier)
        detector.detect("Hello world")
        mock_classifier.classify.assert_called_once_with("Hello world", EmotionDetector.EMOTIONS)

    def test_detect_handles_exception(self, mock_classifier):
        mock_classifier.classify.side_effect = RuntimeError("Model error")
        detector = EmotionDetector(mock_classifier)
        result = detector.detect("Test text")
        assert result["label"] == "neutral"
        assert result["confidence"] == 0.0
