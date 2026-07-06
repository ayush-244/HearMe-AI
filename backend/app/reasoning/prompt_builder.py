import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from .router.intent_models import IntentResult, IntentType

logger = logging.getLogger(__name__)

GREETING_RESPONSES = [
    "Hello! How can I help you today?",
    "Hi there! What can I assist you with?",
    "Hey! How can I help?",
    "Hello! Feel free to ask me anything.",
]


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

    def build_greeting(self) -> str:
        import random
        return random.choice(GREETING_RESPONSES)

    def build(
        self,
        context: Optional[Dict[str, Any]] = None,
        question: str = "",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        language: str = "en",
        allow_external_knowledge: bool = False,
        memory_context: Optional[List[Dict[str, Any]]] = None,
        intent: Optional[IntentResult] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        intent = intent or IntentResult(intent=IntentType.GENERAL_AI)

        knowledge_context = context.get("chunks", []) if context else []
        total_tokens = context.get("total_tokens", 0) if context else 0
        has_knowledge = bool(knowledge_context)

        if has_knowledge:
            knowledge_block = self._format_context(knowledge_context)
        else:
            knowledge_block = None

        if memory_context:
            memory_block = self._format_memory_context(memory_context)
        else:
            memory_block = None

        history_block = self._format_history(conversation_history)

        sections = []

        if system_prompt:
            sections.append("--- System Instructions ---\n" + system_prompt)

        intent_instruction = self._build_intent_instruction(intent)
        sections.append("--- Intent Instruction ---\n" + intent_instruction)

        if memory_block:
            sections.append("--- Personal Context ---\nThe following information is known about you:\n" + memory_block)

        if has_knowledge and knowledge_block:
            sections.append("--- Retrieved Knowledge ---\n" + knowledge_block)
        elif intent.requires_documents and not has_knowledge:
            sections.append("--- Note ---\nNo relevant document content was found for this query.")

        guardrails_block = self._format_guardrails(allow_external_knowledge, intent, has_knowledge)
        sections.append(guardrails_block)

        if history_block:
            sections.append("--- Conversation History ---\n" + history_block)

        if intent.intent == IntentType.FOLLOW_UP:
            sections.append("[Follow-Up Instruction]\nThe user is asking a follow-up question.\nContinue your previous explanation.\nAvoid repeating information already explained unless necessary.\nFocus on expanding the answer with new information.\nDo NOT restart the explanation from the beginning.")

        sections.append("--- User Question ---\n" + question.strip())

        full_prompt = "\n\n".join(sections)

        logger.info(
            "Prompt built: intent=%s, has_knowledge=%s, has_memory=%s, total=%d chars",
            intent.intent.value if intent else "unknown",
            has_knowledge, bool(memory_context), len(full_prompt),
        )

        return full_prompt

    def _build_intent_instruction(self, intent: IntentResult) -> str:
        if intent.intent == IntentType.GREETING:
            return "You are a friendly AI assistant. Greet the user warmly. Keep it brief."
        if intent.intent == IntentType.SMALL_TALK:
            return "You are a friendly AI assistant. Respond naturally in casual conversation. Be warm and engaging."
        if intent.intent == IntentType.PERSONAL_MEMORY:
            return "You are a helpful AI assistant. Answer based on what you know about the user. If you don't have enough personal context, say so honestly. Do NOT use document knowledge unless explicitly needed."
        if intent.intent == IntentType.DOCUMENT_QUESTION:
            return "You are a Knowledge Reasoning Assistant. Answer based on the retrieved document chunks provided below. Include inline citations like [Source N] when using specific document content. If no relevant content was retrieved, state that clearly."
        if intent.intent == IntentType.GENERAL_AI:
            return "You are a knowledgeable AI assistant. Answer the question using your general knowledge. Do NOT fabricate document citations. Be clear, accurate, and educational."
        if intent.intent == IntentType.MIXED:
            return "You are a helpful AI assistant with access to personal context and document knowledge. Integrate both sources naturally. Include citations only for document-derived statements. Use personal memory for user-specific context."
        if intent.intent == IntentType.FOLLOW_UP:
            return "You are a helpful AI assistant continuing a previous conversation. Use the conversation history to provide context-aware responses. If previous document context is available, reuse it without performing new searches."
        return "You are a helpful AI assistant. Answer the user's question accurately and concisely."

    def _format_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        if not memories:
            return ""
        lines = []
        for i, mem in enumerate(memories, 1):
            content = mem.get("content", "") or ""
            mem_type = mem.get("type", "fact")
            lines.append(f"[Memory {i}] ({mem_type}) {content}")
        return "\n".join(lines)

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
                header += f" \u203a {section}"
            if page:
                header += f" \u203a Page {page}"
            header += f" (ID: {chunk_id}\u2026)"

            truncated = chunk.get("truncated", False)
            if truncated:
                text += "\n[Note: This chunk was truncated due to token budget.]"

            lines.append(header)
            lines.append(text)
            lines.append("")

        return "\n".join(lines)

    def _format_history(self, history: Optional[List[Dict[str, str]]]) -> str:
        if not history:
            return ""
        lines = []
        for turn in history:
            role = turn.get("role", "unknown").capitalize()
            content = turn.get("content", "")
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _format_guardrails(self, allow_external_knowledge: bool, intent: IntentResult, has_knowledge: bool) -> str:
        if intent.intent in (IntentType.GREETING, IntentType.SMALL_TALK):
            return ""
        if intent.intent == IntentType.GENERAL_AI:
            return "- Use your general knowledge to answer.\n- Do NOT fabricate citations or document references."
        if intent.intent == IntentType.PERSONAL_MEMORY:
            return "- Answer based on personal context only.\n- Do NOT use document knowledge.\n- If you don't know, say so honestly."
        if intent.intent in (IntentType.DOCUMENT_QUESTION, IntentType.MIXED) and has_knowledge:
            if allow_external_knowledge:
                return (
                    "- You MAY use general knowledge to supplement document content.\n"
                    "- Clearly indicate when information comes from outside knowledge.\n"
                    "- Include inline citations like [Source N] for document-derived statements."
                )
            return (
                "- Answer using the retrieved knowledge provided.\n"
                "- Include inline citations like [Source N] for document-derived statements.\n"
                "- If the retrieved knowledge is insufficient, say so clearly."
            )
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

    def build_system_prompt(self, user_settings=None) -> str:
        base_prompt = (
            "You are HearMe AI, a helpful assistant for students and developers.\n"
            "Be accurate, structured, and helpful.\n"
        )

        if user_settings and user_settings.personality_prompt:
            base_prompt += (
                "\nUser Preferences:\n"
                f"{user_settings.personality_prompt}\n"
            )

        if user_settings and user_settings.tone:
            base_prompt += f"\nTone: {user_settings.tone}"

        if user_settings and user_settings.style:
            base_prompt += f"\nStyle: {user_settings.style}"

        return base_prompt

    def reload_templates(self) -> None:
        self._system_template = self._load("knowledge_system.txt")
        self._user_template = self._load("knowledge_user.txt")
        self._guardrails_template = self._load("knowledge_guardrails.txt")
        logger.info("Prompt templates reloaded")

        
