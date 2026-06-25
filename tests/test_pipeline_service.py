import pytest
from unittest.mock import Mock
from backend.app.services.pipeline_service import PipelineService


class TestPipelineService:
    @pytest.fixture
    def mock_pipeline(self):
        pipeline = Mock()
        pipeline.run.return_value = {
            "language": "English",
            "sentiment": "Positive",
            "emotion": "joy",
            "toxicity": "none",
            "threat": "none",
            "intent": "greeting",
            "confidence": {
                "sentiment": 0.95,
                "emotion": 0.91,
                "toxicity": 0.02,
                "threat": 0.01,
                "intent": 0.88,
            },
            "response": "Hello! How can I help?",
        }
        return pipeline

    def test_analyze_returns_pipeline_result(self, mock_pipeline):
        service = PipelineService(mock_pipeline)
        result = service.analyze("Hello!")
        assert result["language"] == "English"
        assert result["sentiment"] == "Positive"
        assert result["emotion"] == "joy"
        assert result["response"] == "Hello! How can I help?"

    def test_analyze_empty_text(self, mock_pipeline):
        service = PipelineService(mock_pipeline)
        result = service.analyze("")
        assert result["language"] == "Unknown"
        assert result["sentiment"] == "Neutral"
        assert result["response"] == "Please provide a valid message."
        mock_pipeline.run.assert_not_called()

    def test_analyze_whitespace_text(self, mock_pipeline):
        service = PipelineService(mock_pipeline)
        result = service.analyze("   ")
        assert result["response"] == "Please provide a valid message."

    def test_analyze_passes_language_and_history(self, mock_pipeline):
        service = PipelineService(mock_pipeline)
        history = [{"role": "user", "content": "Hi"}]
        service.analyze("Hello", language="fr", history=history)
        mock_pipeline.run.assert_called_once_with("Hello", "fr", history)
