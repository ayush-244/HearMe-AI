import logging
from typing import Dict, Optional
from ..config.settings import Settings
from .sentiment_service import SentimentService
from .language_service import LanguageService
from .prompt_service import PromptService
from .chat_service import ChatService
from .history_service import HistoryService
from .logging_service import LoggingService
from .emotion_service import EmotionService
from .toxicity_service import ToxicityService
from .threat_service import ThreatService
from .intent_service import IntentService
from .pipeline_service import PipelineService
from ai.sentiment.model import SentimentModel
from ai.language.detector import LanguageDetector
from ai.emotion.detector import EmotionDetector
from ai.toxicity.detector import ToxicityDetector
from ai.threat.detector import ThreatDetector
from ai.intent.classifier import IntentClassifier
from ai.pipeline.ai_pipeline import ZeroShotClassifier, AIPipeline
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)
_services: Optional[Dict] = None


def init_services() -> None:
    global _services
    if _services is not None:
        logger.debug("init_services called but already initialized — skipping")
        return

    logger.info("Initializing services...")
    settings = Settings()
    logger.info("Settings loaded (groq_key=%s, hf_token=%s, llm=%s)",
                bool(settings.groq_api_key), bool(settings.hf_token), settings.llm_model_name)

    logger.info("Loading SentimentModel: %s", settings.sentiment_model_name)
    sentiment_model = SentimentModel(settings.sentiment_model_name, settings.hf_token)
    sentiment_service = SentimentService(sentiment_model)

    language_detector = LanguageDetector()
    prompt_service = PromptService(settings.PROMPTS_DIR)
    language_service = LanguageService(language_detector, prompt_service.language_configs)

    logger.info("Initializing ChatGroq: model=%s", settings.llm_model_name)
    llm = ChatGroq(
        groq_api_key=settings.groq_api_key,
        model_name=settings.llm_model_name,
    )
    chat_service = ChatService(llm, prompt_service)

    history_service = HistoryService(settings.max_history_messages)
    logging_service = LoggingService(settings.sentiment_log_file)

    logger.info("Loading ZeroShotClassifier: %s", settings.zero_shot_model_name)
    zero_shot = ZeroShotClassifier(settings.zero_shot_model_name, settings.hf_token)
    emotion_detector = EmotionDetector(zero_shot)
    toxicity_detector = ToxicityDetector(zero_shot)
    threat_detector = ThreatDetector(zero_shot)
    intent_classifier = IntentClassifier(zero_shot)

    emotion_service = EmotionService(emotion_detector)
    toxicity_service = ToxicityService(toxicity_detector)
    threat_service = ThreatService(threat_detector)
    intent_service = IntentService(intent_classifier)

    ai_pipeline = AIPipeline(
        language_service=language_service,
        sentiment_service=sentiment_service,
        emotion_service=emotion_service,
        toxicity_service=toxicity_service,
        threat_service=threat_service,
        intent_service=intent_service,
        prompt_service=prompt_service,
        chat_service=chat_service,
    )
    pipeline_service = PipelineService(ai_pipeline)

    _services = {
        "sentiment": sentiment_service,
        "language": language_service,
        "prompt": prompt_service,
        "chat": chat_service,
        "history": history_service,
        "logging": logging_service,
        "emotion": emotion_service,
        "toxicity": toxicity_service,
        "threat": threat_service,
        "intent": intent_service,
        "pipeline": pipeline_service,
    }
    logger.info("All services initialized (%d services)", len(_services))


def get_services() -> Dict:
    if _services is None:
        logger.debug("get_services called before init — initializing")
        init_services()
    return _services
