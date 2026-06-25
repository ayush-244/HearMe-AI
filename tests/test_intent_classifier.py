import pytest
from unittest.mock import Mock
from ai.intent.classifier import IntentClassifier


class TestIntentClassifier:
    @pytest.fixture
    def mock_classifier(self):
        classifier = Mock()
        classifier.classify.return_value = {
            "labels": ["question", "greeting", "conversation", "coding", "medical",
                        "translation", "complaint", "mental health", "goodbye", "other"],
            "scores": [0.88, 0.04, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.0, 0.0],
        }
        return classifier

    def test_classify_returns_intent_and_confidence(self, mock_classifier):
        classifier = IntentClassifier(mock_classifier)
        result = classifier.classify("What is the weather?")
        assert result["intent"] == "question"
        assert result["confidence"] == 0.88

    def test_classify_greeting(self, mock_classifier):
        mock_classifier.classify.return_value = {
            "labels": ["greeting", "question", "conversation", "coding", "medical",
                        "translation", "complaint", "mental health", "goodbye", "other"],
            "scores": [0.95, 0.02, 0.01, 0.01, 0.01, 0.0, 0.0, 0.0, 0.0, 0.0],
        }
        classifier = IntentClassifier(mock_classifier)
        result = classifier.classify("Hello!")
        assert result["intent"] == "greeting"
        assert result["confidence"] == 0.95

    def test_classify_empty_text(self, mock_classifier):
        classifier = IntentClassifier(mock_classifier)
        result = classifier.classify("")
        assert result["intent"] == "other"
        assert result["confidence"] == 0.0

    def test_classify_whitespace_text(self, mock_classifier):
        classifier = IntentClassifier(mock_classifier)
        result = classifier.classify("   ")
        assert result["intent"] == "other"
        assert result["confidence"] == 0.0

    def test_classify_delegates_to_classifier(self, mock_classifier):
        classifier = IntentClassifier(mock_classifier)
        classifier.classify("Hello world")
        mock_classifier.classify.assert_called_once_with("Hello world", IntentClassifier.INTENTS)

    def test_classify_handles_exception(self, mock_classifier):
        mock_classifier.classify.side_effect = RuntimeError("Model error")
        classifier = IntentClassifier(mock_classifier)
        result = classifier.classify("Test text")
        assert result["intent"] == "other"
        assert result["confidence"] == 0.0
