import logging
from typing import Optional
from langchain_groq import ChatGroq
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, llm: ChatGroq, prompt_service: PromptService):
        self._llm = llm
        self._prompt_service = prompt_service
        logger.info("ChatService initialized (llm=%s)", type(llm).__name__)

    def generate_response(
        self,
        user_input: str,
        language: str,
        sentiment: str,
        history: Optional[list] = None
    ) -> str:
        logger.info("generate_response called (input_len=%d, lang=%s, sentiment=%s, history_len=%d)",
                     len(user_input), language, sentiment, len(history) if history else 0)
        prompt = self._prompt_service.build_chat_prompt(user_input, language, sentiment, history)
        logger.info("Prompt built (%d chars)", len(prompt))
        if not prompt:
            logger.warning("Empty prompt generated — returning fallback response")
            return "I'm sorry, I couldn't process your request. Please try again."
        return self.invoke_llm(prompt)

    def invoke_llm(self, prompt: str) -> str:
        logger.debug("Sending prompt to LLM (len=%d chars)", len(prompt))
        try:
            response = self._llm.invoke(prompt)
            content = response.content
            logger.info("LLM response received (len=%d chars, empty=%s)",
                         len(content), not bool(content))
            if not content:
                logger.warning("LLM returned empty response content")
                return "I'm sorry, I received an empty response. Please try again."
            return content
        except Exception:
            logger.exception("LLM invocation failed")
            return "I'm sorry, I encountered an issue generating a response. Please try again."
