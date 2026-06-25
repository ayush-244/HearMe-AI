from typing import Dict, Optional
from ..config.settings import Settings
from .sentiment_service import SentimentService
from .language_service import LanguageService
from .prompt_service import PromptService
from .chat_service import ChatService
from .history_service import HistoryService
from .logging_service import LoggingService
from ai.sentiment.model import SentimentModel
from ai.language.detector import LanguageDetector
from langchain_groq import ChatGroq

_services: Optional[Dict] = None


def init_services() -> None:
    global _services
    if _services is not None:
        return

    settings = Settings()

    sentiment_model = SentimentModel(settings.sentiment_model_name)
    sentiment_service = SentimentService(sentiment_model)

    language_detector = LanguageDetector()
    prompt_service = PromptService(settings.PROMPTS_DIR)
    language_service = LanguageService(language_detector, prompt_service.language_configs)

    llm = ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.llm_model_name,
    )
    chat_service = ChatService(llm, prompt_service)

    history_service = HistoryService(settings.max_history_messages)
    logging_service = LoggingService(settings.sentiment_log_file)

    _services = {
        "sentiment": sentiment_service,
        "language": language_service,
        "prompt": prompt_service,
        "chat": chat_service,
        "history": history_service,
        "logging": logging_service,
    }


def get_services() -> Dict:
    if _services is None:
        init_services()
    return _services
