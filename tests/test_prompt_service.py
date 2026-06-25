import pytest
import json
from pathlib import Path
from backend.app.services.prompt_service import PromptService


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
            "system_prompt": "Eres un asistente útil.",
            "language_instruction": "Responde en español.",
        },
    }
    intros = {
        "Positive": ["Great!"],
        "Neutral": ["OK."],
        "Negative": ["I understand."],
    }
    template = "{system_prompt}\n{language_instruction}\nSentiment: {sentiment}\nHistory: {history}\nUser: {user_input}"

    (tmp_path / "language_configs.json").write_text(json.dumps(configs), encoding="utf-8")
    (tmp_path / "sentiment_intros.json").write_text(json.dumps(intros), encoding="utf-8")
    (tmp_path / "chat_template.txt").write_text(template, encoding="utf-8")
    return tmp_path


class TestPromptService:
    def test_build_chat_prompt(self, prompts_dir):
        service = PromptService(prompts_dir)
        prompt = service.build_chat_prompt(
            user_input="Hello",
            language="en",
            sentiment="Positive",
            history=[{"role": "user", "content": "Hi"}],
        )
        assert "You are a helpful assistant." in prompt
        assert "Respond in English." in prompt
        assert "Sentiment: Positive" in prompt
        assert "Hello" in prompt

    def test_build_chat_prompt_fallback_to_english(self, prompts_dir):
        service = PromptService(prompts_dir)
        prompt = service.build_chat_prompt(
            user_input="Hola",
            language="de",
            sentiment="Neutral",
        )
        assert "You are a helpful assistant." in prompt
        assert "Respond in English." in prompt

    def test_select_intro(self, prompts_dir):
        service = PromptService(prompts_dir)
        intro = service.select_intro("Positive")
        assert intro == "Great!"

    def test_select_intro_fallback(self, prompts_dir):
        service = PromptService(prompts_dir)
        intro = service.select_intro("Unknown")
        assert intro == "OK."

    def test_language_configs_property(self, prompts_dir):
        service = PromptService(prompts_dir)
        configs = service.language_configs
        assert "en" in configs
        assert "es" in configs
