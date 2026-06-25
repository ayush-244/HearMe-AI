import logging
from typing import Optional
from langchain_groq import ChatGroq
from .prompt_service import PromptService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, llm: ChatGroq, prompt_service: PromptService):
        self._llm = llm
        self._prompt_service = prompt_service

    def generate_response(
        self,
        user_input: str,
        language: str,
        sentiment: str,
        history: Optional[list] = None
    ) -> str:
        prompt = self._prompt_service.build_chat_prompt(user_input, language, sentiment, history)
        return self.invoke_llm(prompt)

    def invoke_llm(self, prompt: str) -> str:
        logger.debug("Sending prompt to LLM (len=%d chars)", len(prompt))
        try:
            response = self._llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error("LLM invocation failed: %s", str(e))
            return "I'm sorry, I encountered an issue generating a response. Please try again."
