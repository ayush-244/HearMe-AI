import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PromptBuilder:
    def __init__(self, prompts_dir: Path):
        self._prompts_dir = prompts_dir
        self._system_template: str = self._load("knowledge_system.txt")
        self._user_template: str = self._load("knowledge_user.txt")
        self._guardrails_template: str = self._load("knowledge_guardrails.txt")
        logger.info(
            "PromptBuilder initialized: system=%d chars, user=%d chars, guardrails=%d chars",
            len(self._system_template), len(self._user_template), len(self._guardrails_template),
        )

    def _load(self, filename: str) -> str:
        path = self._prompts_dir / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if not content:
                logger.warning("Prompt template %s is empty", filename)
            return content
        except FileNotFoundError:
            logger.warning("Prompt template %s not found at %s, using fallback", filename, path)
            return ""
        except Exception as e:
            logger.error("Failed to load prompt template %s: %s", filename, e)
            return ""

    def build(
        self,
        context: Dict[str, Any],
        question: str = "",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        language: str = "en",
        allow_external_knowledge: bool = False,
    ) -> str:
        chunks = context.get("chunks", [])
        total_tokens = context.get("total_tokens", 0)

        context_block = self._format_context(chunks)

        history_block = self._format_history(conversation_history)

        guardrails_block = self._format_guardrails(allow_external_knowledge)

        system_prompt = self._system_template.format(
            guardrails=guardrails_block,
        )

        user_prompt = self._user_template.format(
            context=context_block,
            conversation_history=history_block,
            question=question.strip(),
            language=language,
            token_estimate=total_tokens,
            chunk_count=len(chunks),
        )

        if self._system_template and self._user_template:
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
        else:
            full_prompt = self._build_fallback_prompt(
                context_block, question, history_block, guardrails_block, language,
            )

        logger.info(
            "Prompt built: system=%d chars, user=%d chars, total=%d chars, chunks=%d, tokens=%d",
            len(system_prompt), len(user_prompt), len(full_prompt), len(chunks), total_tokens,
        )
        return full_prompt

    def _format_context(self, chunks: List[Dict[str, Any]]) -> str:
        if not chunks:
            return "[No knowledge retrieved from documents]"

        lines = []
        for chunk in chunks:
            idx = chunk.get("context_index", 0)
            text = (chunk.get("text", "") or "").strip()
            title = chunk.get("title", "") or "Untitled"
            section = chunk.get("section", "") or "General"
            page = chunk.get("page", 0)
            chunk_id = chunk.get("chunk_id", "")[:8]

            header = f"[Source {idx}] {title}"
            if section and section.lower() != title.lower():
                header += f" › {section}"
            if page:
                header += f" › Page {page}"
            header += f" (ID: {chunk_id}…)"

            truncated = chunk.get("truncated", False)
            if truncated:
                text += "\n[Note: This chunk was truncated due to token budget.]"

            lines.append(header)
            lines.append(text)
            lines.append("")

        return "\n".join(lines)

    def _format_history(self, history: Optional[List[Dict[str, str]]]) -> str:
        if not history:
            return "No previous conversation."
        lines = []
        for turn in history:
            role = turn.get("role", "unknown").capitalize()
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _format_guardrails(self, allow_external_knowledge: bool) -> str:
        if self._guardrails_template:
            return self._guardrails_template.format(
                external_knowledge="enabled" if allow_external_knowledge else "disabled",
            )
        if allow_external_knowledge:
            return (
                "- You MAY use general knowledge to supplement document content.\n"
                "- Clearly indicate when information comes from outside knowledge."
            )
        return (
            "- Answer ONLY using the retrieved knowledge provided above.\n"
            "- Do NOT use any external or general knowledge.\n"
            "- If the retrieved knowledge is insufficient, respond: "
            '"I couldn\'t find enough information in the uploaded documents."'
        )

    def _build_fallback_prompt(
        self,
        context_block: str,
        question: str,
        history_block: str,
        guardrails_block: str,
        language: str,
    ) -> str:
        return f"""You are a Knowledge Reasoning Assistant. Your role is to answer questions based ONLY on the retrieved document chunks provided below.

{guardrails_block}

--- Retrieved Knowledge ---

{context_block}

--- Conversation History ---

{history_block}

--- User Question ---

{question}

--- Instructions ---

1. Answer the question using ONLY the retrieved knowledge above.
2. If the knowledge is insufficient, say: "I couldn't find enough information in the uploaded documents."
3. Include inline citations like [Source 1], [Source 2], etc.
4. Respond in {language}.
5. Be concise, accurate, and well-structured.
6. Do NOT hallucinate or use outside knowledge.
"""

    def reload_templates(self) -> None:
        self._system_template = self._load("knowledge_system.txt")
        self._user_template = self._load("knowledge_user.txt")
        self._guardrails_template = self._load("knowledge_guardrails.txt")
        logger.info("Prompt templates reloaded")
