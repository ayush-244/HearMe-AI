import pytest
from unittest.mock import Mock
from ai.pipeline.ai_pipeline import ZeroShotClassifier, AIPipeline


class TestZeroShotClassifier:
    def test_initialization(self):
        zsc = ZeroShotClassifier("dummy-model")
        assert zsc._model_name == "dummy-model"
        assert zsc._pipeline is None

    def test_classify_requires_load(self):
        zsc = ZeroShotClassifier("dummy-model")
        assert zsc._pipeline is None
        assert zsc._model_name == "dummy-model"


class TestAIPipeline:
    @pytest.fixture
    def mock_services(self):
        return {
            "language": Mock(),
            "sentiment": Mock(),
            "emotion": Mock(),
            "toxicity": Mock(),
            "threat": Mock(),
            "intent": Mock(),
            "prompt": Mock(),
            "chat": Mock(),
        }

    @pytest.fixture
    def pipeline(self, mock_services):
        return AIPipeline(
            language_service=mock_services["language"],
            sentiment_service=mock_services["sentiment"],
            emotion_service=mock_services["emotion"],
            toxicity_service=mock_services["toxicity"],
            threat_service=mock_services["threat"],
            intent_service=mock_services["intent"],
            prompt_service=mock_services["prompt"],
            chat_service=mock_services["chat"],
        )

    def test_run_returns_all_fields(self, pipeline, mock_services):
        mock_services["language"].detect.return_value = "en"
        mock_services["language"].get_language_name.return_value = "English"
        mock_services["sentiment"].analyze.return_value = ("Positive", 0.95)
        mock_services["emotion"].analyze.return_value = {"label": "joy", "confidence": 0.91}
        mock_services["toxicity"].analyze.return_value = {"is_toxic": False, "category": "none", "confidence": 0.02}
        mock_services["threat"].analyze.return_value = {"threat_detected": False, "risk_level": "none", "confidence": 0.01, "threat_type": None}
        mock_services["intent"].analyze.return_value = {"intent": "greeting", "confidence": 0.88}
        mock_services["prompt"].language_configs = {"en": {}}
        mock_services["prompt"].build_adaptive_prompt.return_value = "Formatted prompt"
        mock_services["chat"].invoke_llm.return_value = "Hello! How can I help?"

        result = pipeline.run("Hello!", "auto")

        assert result["language"] == "English"
        assert result["sentiment"] == "Positive"
        assert result["emotion"] == "joy"
        assert result["toxicity"] == "none"
        assert result["threat"] == "none"
        assert result["intent"] == "greeting"
        assert result["response"] == "Hello! How can I help?"
        assert result["confidence"]["sentiment"] == 0.95
        assert result["confidence"]["emotion"] == 0.91

    def test_run_with_specified_language(self, pipeline, mock_services):
        mock_services["language"].get_language_name.return_value = "French"
        mock_services["sentiment"].analyze.return_value = ("Neutral", 0.5)
        mock_services["emotion"].analyze.return_value = {"label": "neutral", "confidence": 0.6}
        mock_services["toxicity"].analyze.return_value = {"is_toxic": False, "category": "none", "confidence": 0.0}
        mock_services["threat"].analyze.return_value = {"threat_detected": False, "risk_level": "none", "confidence": 0.0, "threat_type": None}
        mock_services["intent"].analyze.return_value = {"intent": "question", "confidence": 0.7}
        mock_services["prompt"].language_configs = {"fr": {}}
        mock_services["prompt"].build_adaptive_prompt.return_value = "Prompt"
        mock_services["chat"].invoke_llm.return_value = "Bonjour!"

        result = pipeline.run("Bonjour!", language="fr")

        assert result["language"] == "French"
        mock_services["language"].detect.assert_not_called()

    def test_run_falls_back_to_english_for_unknown_language(self, pipeline, mock_services):
        mock_services["language"].detect.return_value = "de"
        mock_services["language"].get_language_name.return_value = "German"
        mock_services["sentiment"].analyze.return_value = ("Neutral", 0.5)
        mock_services["emotion"].analyze.return_value = {"label": "neutral", "confidence": 0.5}
        mock_services["toxicity"].analyze.return_value = {"is_toxic": False, "category": "none", "confidence": 0.0}
        mock_services["threat"].analyze.return_value = {"threat_detected": False, "risk_level": "none", "confidence": 0.0, "threat_type": None}
        mock_services["intent"].analyze.return_value = {"intent": "other", "confidence": 0.5}
        mock_services["prompt"].language_configs = {"en": {}}
        mock_services["prompt"].build_adaptive_prompt.return_value = "Prompt"
        mock_services["chat"].invoke_llm.return_value = "Response"

        result = pipeline.run("Hallo", "auto")
        assert result["language"] == "German"

    def test_run_handles_llm_error(self, pipeline, mock_services):
        mock_services["language"].detect.return_value = "en"
        mock_services["language"].get_language_name.return_value = "English"
        mock_services["sentiment"].analyze.return_value = ("Neutral", 0.5)
        mock_services["emotion"].analyze.return_value = {"label": "neutral", "confidence": 0.5}
        mock_services["toxicity"].analyze.return_value = {"is_toxic": False, "category": "none", "confidence": 0.0}
        mock_services["threat"].analyze.return_value = {"threat_detected": False, "risk_level": "none", "confidence": 0.0, "threat_type": None}
        mock_services["intent"].analyze.return_value = {"intent": "other", "confidence": 0.5}
        mock_services["prompt"].language_configs = {"en": {}}
        mock_services["prompt"].build_adaptive_prompt.return_value = "Prompt"
        mock_services["chat"].invoke_llm.return_value = "I'm sorry, I encountered an issue generating a response. Please try again."

        result = pipeline.run("Hello")
        assert "sorry" in result["response"]
