import json
import random
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptService:
    def __init__(self, prompts_dir: Path):
        self._prompts_dir = prompts_dir
        self._language_configs: Dict[str, dict] = self._load_json("language_configs.json")
        self._sentiment_intros: Dict[str, List[str]] = self._load_json("sentiment_intros.json")
        self._chat_template: str = self._load_text("chat_template.txt")
        self._adaptive_config: dict = self._load_json("adaptive_config.json")
        self._adaptive_templates: Dict[str, str] = self._load_adaptive_templates()

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

    def _load_adaptive_templates(self) -> Dict[str, str]:
        templates: Dict[str, str] = {}
        routes = self._adaptive_config.get("routes", [])
        for route in routes:
            tpl_file = route.get("template", "")
            condition = route.get("condition", "")
            if tpl_file and condition:
                templates[condition] = self._load_text(tpl_file)
        default = self._adaptive_config.get("default_template", "")
        if default:
            templates["default"] = self._load_text(default)
        logger.info("Loaded %d adaptive templates: %s", len(templates), list(templates.keys()))
        return templates

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
        lang_config = self._language_configs.get(language) or self._language_configs.get("en")

        history_lines = []
        recent = history[-5:] if history else []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")
        history_str = "\n".join(history_lines)

        prompt = self._chat_template.format(
            system_prompt=lang_config.get("system_prompt", "") if lang_config else "",
            language_instruction=lang_config.get("language_instruction", "") if lang_config else "",
            sentiment=sentiment or "Neutral",
            history=history_str,
            user_input=user_input or "",
        )
        logger.debug("build_chat_prompt: lang=%s, sentiment=%s, history=%d msgs, prompt=%d chars",
                     language, sentiment, len(recent), len(prompt))
        return prompt

    def select_intro(self, sentiment: str) -> str:
        intros = self._sentiment_intros.get(sentiment, self._sentiment_intros.get("Neutral", ["Here's a response:"]))
        return random.choice(intros)

    def build_adaptive_prompt(
        self,
        user_input: str,
        language: str,
        sentiment: str,
        emotion: Dict[str, Any],
        toxicity: Dict[str, Any],
        threat: Dict[str, Any],
        intent: Dict[str, Any],
        history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        lang_config = self._language_configs.get(language) or self._language_configs.get("en", {})
        route_key = self._select_adaptive_route(emotion, toxicity, threat)
        template = self._adaptive_templates.get(route_key, self._chat_template)

        history_lines = []
        recent = history[-5:] if history else []
        for msg in recent:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_lines.append(f"{role}: {content}")
        history_str = "\n".join(history_lines)

        prompt = template.format(
            system_prompt=lang_config.get("system_prompt", "") if lang_config else "",
            language_instruction=lang_config.get("language_instruction", "") if lang_config else "",
            sentiment=sentiment or "Neutral",
            emotion=emotion.get("label", "unknown"),
            toxicity_category=toxicity.get("category", "none"),
            threat_type=threat.get("threat_type", "none"),
            intent=intent.get("intent", "unknown"),
            history=history_str,
            user_input=user_input or "",
        )
        logger.debug("build_adaptive_prompt: route=%s, lang=%s, sentiment=%s, prompt=%d chars",
                     route_key, language, sentiment, len(prompt))
        return prompt

    def _select_adaptive_route(
        self,
        emotion: Dict[str, Any],
        toxicity: Dict[str, Any],
        threat: Dict[str, Any],
    ) -> str:
        routes = self._adaptive_config.get("routes", [])
        sorted_routes = sorted(routes, key=lambda r: r.get("priority", 99))
        for route in sorted_routes:
            condition = route.get("condition", "")
            if condition == "threat" and threat.get("threat_detected", False):
                return "threat"
            if condition == "toxicity" and toxicity.get("is_toxic", False):
                return "toxicity"
            if condition == "sadness" and emotion.get("label") == "sadness":
                return "sadness"
        return "default"
