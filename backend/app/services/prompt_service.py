import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptService:
    def __init__(self, prompts_dir: Path):
        self._prompts_dir = prompts_dir
        self._language_configs: Dict[str, dict] = self._load_json("language_configs.json")
        self._sentiment_intros: Dict[str, List[str]] = self._load_json("sentiment_intros.json")
        self._chat_template: str = self._load_text("chat_template.txt")

    def _load_json(self, filename: str) -> dict:
        path = self._prompts_dir / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load %s: %s", filename, e)
            return {}

    def _load_text(self, filename: str) -> str:
        path = self._prompts_dir / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            logger.error("Failed to load %s: %s", filename, e)
            return ""

    @property
    def language_configs(self) -> Dict[str, dict]:
        return self._language_configs

    @property
    def sentiment_intros(self) -> Dict[str, List[str]]:
        return self._sentiment_intros

    def build_chat_prompt(
        self,
        user_input: str,
        language: str,
        sentiment: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        lang_config = self._language_configs.get(language, self._language_configs.get("en"))

        history_lines = []
        recent = history[-5:] if history else []
        for msg in recent:
            history_lines.append(f"{msg['role']}: {msg['content']}")
        history_str = "\n".join(history_lines)

        prompt = self._chat_template.format(
            system_prompt=lang_config["system_prompt"],
            language_instruction=lang_config["language_instruction"],
            sentiment=sentiment,
            history=history_str,
            user_input=user_input,
        )
        return prompt

    def select_intro(self, sentiment: str) -> str:
        intros = self._sentiment_intros.get(sentiment, self._sentiment_intros.get("Neutral", ["Here's a response:"]))
        return random.choice(intros)
