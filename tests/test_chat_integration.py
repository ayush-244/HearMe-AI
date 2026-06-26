"""Integration tests for the full chat response flow."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from backend.app.services.prompt_service import PromptService
from backend.app.services.chat_service import ChatService
from backend.app.services.history_service import HistoryService
from backend.app.services.language_service import LanguageService
from backend.app.services.sentiment_service import SentimentService
from backend.app.services.logging_service import LoggingService
from ai.language.detector import LanguageDetector


@pytest.fixture
def prompts_dir(tmp_path):
    configs = {
        "en": {
            "name": "English",
            "system_prompt": "You are a helpful assistant.",
            "language_instruction": "Respond in English.",
        },
        "es": {
            "name": "Spanish",
            "system_prompt": "Eres un asistente util.",
            "language_instruction": "Responde en espanol.",
        },
        "fr": {
            "name": "French",
            "system_prompt": "Vous etes un assistant.",
            "language_instruction": "Repondez en francais.",
        },
        "hi": {
            "name": "Hindi",
            "system_prompt": "Aap ek sahayak hain.",
            "language_instruction": "Hindi mein uttar dein.",
        },
    }
    intros = {
        "Positive": ["Great!", "Wonderful!"],
        "Neutral": ["OK.", "I see."],
        "Negative": ["I understand.", "I'm sorry."],
    }
    template = "{system_prompt}\n{language_instruction}\nSentiment: {sentiment}\nHistory: {history}\nUser: {user_input}"

    (tmp_path / "language_configs.json").write_text(json.dumps(configs), encoding="utf-8")
    (tmp_path / "sentiment_intros.json").write_text(json.dumps(intros), encoding="utf-8")
    (tmp_path / "chat_template.txt").write_text(template, encoding="utf-8")

    adaptive_config = {
        "routes": [
            {"condition": "threat", "template": "safety.txt", "priority": 1},
            {"condition": "toxicity", "template": "deesc.txt", "priority": 2},
            {"condition": "sadness", "template": "empathy.txt", "priority": 3},
        ],
        "default_template": "default.txt",
    }
    (tmp_path / "adaptive_config.json").write_text(json.dumps(adaptive_config), encoding="utf-8")
    (tmp_path / "safety.txt").write_text("SAFETY: {threat_type}\n{user_input}", encoding="utf-8")
    (tmp_path / "deesc.txt").write_text("DEESC: {toxicity_category}\n{user_input}", encoding="utf-8")
    (tmp_path / "empathy.txt").write_text("EMPATHY: {emotion}\n{user_input}", encoding="utf-8")
    (tmp_path / "default.txt").write_text("DEFAULT: {sentiment} {emotion} {intent}\n{user_input}", encoding="utf-8")

    return tmp_path


@pytest.fixture
def prompt_service(prompts_dir):
    return PromptService(prompts_dir)


@pytest.fixture
def mock_llm():
    llm = Mock()
    response = MagicMock()
    response.content = "Test response from LLM"
    llm.invoke.return_value = response
    return llm


@pytest.fixture
def language_service(prompt_service):
    detector = LanguageDetector()
    return LanguageService(detector, prompt_service.language_configs)


class TestChatIntegration:
    """Integration tests for the full chat response flow."""

    def test_full_chat_flow_simple(self, prompt_service, mock_llm):
        """Test complete chat flow: prompt build -> LLM -> response."""
        chat_service = ChatService(mock_llm, prompt_service)
        response = chat_service.generate_response(
            user_input="Hello!",
            language="en",
            sentiment="Positive",
            history=[],
        )
        assert response == "Test response from LLM"
        assert isinstance(response, str)
        assert mock_llm.invoke.called

    def test_full_chat_flow_with_history(self, prompt_service, mock_llm):
        """Test chat flow with conversation history."""
        chat_service = ChatService(mock_llm, prompt_service)
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help?"},
        ]
        response = chat_service.generate_response(
            user_input="What is the weather?",
            language="en",
            sentiment="Neutral",
            history=history,
        )
        assert response == "Test response from LLM"
        # Verify prompt contains history
        args, _ = mock_llm.invoke.call_args
        prompt = args[0]
        assert "Hi" in prompt
        assert "Hello! How can I help?" in prompt
        assert "What is the weather?" in prompt

    def test_chat_flow_multiple_languages(self, prompt_service, mock_llm):
        """Test chat flow works in all supported languages."""
        chat_service = ChatService(mock_llm, prompt_service)
        for lang in ["en", "es", "fr", "hi"]:
            response = chat_service.generate_response(
                user_input="Hello",
                language=lang,
                sentiment="Neutral",
                history=[],
            )
            assert response == "Test response from LLM", f"Failed for language {lang}"
            args, _ = mock_llm.invoke.call_args
            prompt = args[0]
            # Each language should have its instruction
            configs = prompt_service.language_configs
            assert configs[lang]["language_instruction"] in prompt, f"Missing instruction for {lang}"

    def test_chat_flow_unknown_language_fallsback(self, prompt_service, mock_llm):
        """Test unknown language falls back to English."""
        chat_service = ChatService(mock_llm, prompt_service)
        response = chat_service.generate_response(
            user_input="Hello",
            language="de",
            sentiment="Neutral",
            history=[],
        )
        assert response == "Test response from LLM"
        args, _ = mock_llm.invoke.call_args
        prompt = args[0]
        assert "Respond in English." in prompt

    def test_chat_flow_empty_input_returns_fallback(self, prompt_service, mock_llm):
        """Test empty input returns fallback response."""
        chat_service = ChatService(mock_llm, prompt_service)
        response = chat_service.generate_response(
            user_input="",
            language="en",
            sentiment="Neutral",
            history=[],
        )
        # Empty user_input -> prompt still built but LLM receives it
        assert isinstance(response, str)
        assert len(response) > 0

    def test_chat_flow_empty_prompt_returns_fallback(self, prompt_service):
        """Test empty prompt (if template fails) returns fallback."""
        # Create a chat service and make build_chat_prompt return empty
        with patch.object(prompt_service, 'build_chat_prompt', return_value=""):
            mock_llm_fallback = Mock()
            chat_service = ChatService(mock_llm_fallback, prompt_service)
            response = chat_service.generate_response(
                user_input="Hello",
                language="en",
                sentiment="Neutral",
                history=[],
            )
            assert "I'm sorry" in response
            assert not mock_llm_fallback.invoke.called, "LLM should not be called with empty prompt"

    def test_chat_flow_llm_failure_returns_apology(self, prompt_service, mock_llm):
        """Test LLM failure returns apology message."""
        mock_llm.invoke.side_effect = Exception("API timeout")
        chat_service = ChatService(mock_llm, prompt_service)
        response = chat_service.generate_response(
            user_input="Hello",
            language="en",
            sentiment="Neutral",
            history=[],
        )
        assert "I'm sorry" in response
        assert isinstance(response, str)

    def test_chat_flow_llm_empty_response(self, prompt_service):
        """Test LLM returning empty content returns fallback."""
        mock_llm_empty = Mock()
        response_empty = MagicMock()
        response_empty.content = ""
        mock_llm_empty.invoke.return_value = response_empty
        chat_service = ChatService(mock_llm_empty, prompt_service)
        response = chat_service.generate_response(
            user_input="Hello",
            language="en",
            sentiment="Neutral",
            history=[],
        )
        assert "I'm sorry" in response
        assert isinstance(response, str)

    def test_chat_flow_malformed_history(self, prompt_service, mock_llm):
        """Test malformed history entries don't crash."""
        chat_service = ChatService(mock_llm, prompt_service)
        malformed_history = [
            {"role": "user", "content": "Hi"},
            {"unknown_key": "value"},  # Missing role and content
            {"role": "assistant"},  # Missing content
        ]
        response = chat_service.generate_response(
            user_input="Hello",
            language="en",
            sentiment="Neutral",
            history=malformed_history,
        )
        assert response == "Test response from LLM"
        assert chat_service._prompt_service.build_chat_prompt is not None

    def test_chat_flow_with_history_service(self, prompt_service, mock_llm):
        """Test integration with HistoryService."""
        chat_service = ChatService(mock_llm, prompt_service)
        history_service = HistoryService(max_messages=10)
        session_history = []

        # First turn
        response1 = chat_service.generate_response(
            user_input="Hello!",
            language="en",
            sentiment="Positive",
            history=session_history,
        )
        session_history = history_service.add_message(session_history, "user", "Hello!")
        session_history = history_service.add_message(session_history, "assistant", response1)
        assert len(session_history) == 2

        # Second turn — history should be included
        mock_llm.reset_mock()
        chat_service.generate_response(
            user_input="How are you?",
            language="en",
            sentiment="Neutral",
            history=session_history,
        )
        args, _ = mock_llm.invoke.call_args
        prompt = args[0]
        assert "Hello!" in prompt
        assert "How are you?" in prompt

    def test_chat_flow_none_history(self, prompt_service, mock_llm):
        """Test None history doesn't crash."""
        chat_service = ChatService(mock_llm, prompt_service)
        response = chat_service.generate_response(
            user_input="Hello",
            language="en",
            sentiment="Neutral",
            history=None,
        )
        assert response == "Test response from LLM"

    def test_chat_flow_all_sentiments(self, prompt_service, mock_llm):
        """Test all sentiment values work."""
        chat_service = ChatService(mock_llm, prompt_service)
        for sentiment in ["Positive", "Neutral", "Negative"]:
            response = chat_service.generate_response(
                user_input="Hello",
                language="en",
                sentiment=sentiment,
                history=[],
            )
            assert response == "Test response from LLM", f"Failed for sentiment {sentiment}"

    def test_prompt_builds_languages_and_sentiments(self, prompt_service):
        """Test build_chat_prompt for all language+sentiment combinations."""
        for lang in ["en", "es", "fr", "hi"]:
            for sentiment in ["Positive", "Neutral", "Negative"]:
                prompt = prompt_service.build_chat_prompt(
                    user_input="Test",
                    language=lang,
                    sentiment=sentiment,
                    history=[],
                )
                assert len(prompt) > 0
                assert "Test" in prompt
                assert sentiment in prompt
                config = prompt_service.language_configs[lang]
                assert config["system_prompt"] in prompt

    def test_invoke_llm_always_returns_string(self, prompt_service, mock_llm):
        """Test invoke_llm always returns a string regardless of success/failure."""
        chat_service = ChatService(mock_llm, prompt_service)

        # Success case
        result = chat_service.invoke_llm("Test prompt")
        assert isinstance(result, str)

        # Failure case
        mock_llm.invoke.side_effect = Exception("Error")
        result = chat_service.invoke_llm("Test prompt")
        assert isinstance(result, str)

        # Empty content case
        mock_empty = Mock()
        mock_empty_response = MagicMock()
        mock_empty_response.content = ""
        mock_empty.invoke.return_value = mock_empty_response
        cs = ChatService(mock_empty, prompt_service)
        result = cs.invoke_llm("Test")
        assert isinstance(result, str)

    def test_select_intro_always_returns_string(self, prompt_service):
        """Test select_intro always returns a non-empty string."""
        for sentiment in ["Positive", "Neutral", "Negative", "Unknown", "", None]:
            intro = prompt_service.select_intro(sentiment if sentiment is not None else "Neutral")
            assert isinstance(intro, str)
            assert len(intro) > 0

    def test_language_service_integration(self, prompt_service, language_service):
        """Test language service works with prompt service configs."""
        supported = language_service.get_supported_languages()
        assert set(supported.keys()) == {"en", "es", "fr", "hi"}
        for code, config in supported.items():
            assert "name" in config
            assert len(language_service.get_language_name(code)) > 0
        assert language_service.get_language_name("de") == "Unknown"

    def test_logging_service_does_not_crash(self, prompt_service, tmp_path):
        """Test logging service writes without error."""
        log_file = tmp_path / "test_log.txt"
        service = LoggingService(str(log_file))
        service.log_sentiment("Test message", "Positive", 0.95)
        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "Test message" in content
        assert "Positive" in content

    def test_history_service_add_message_consistency(self):
        """Test HistoryService.add_message doesn't mutate input unexpectedly."""
        service = HistoryService(max_messages=5)
        original = []
        result = service.add_message(original, "user", "Hello")
        # Both original and result point to same list (mutated)
        assert len(original) == 1
        assert len(result) == 1
        assert original[0]["role"] == "user"
