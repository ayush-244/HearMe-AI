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
from .document_service import DocumentService
from .embedding_service import EmbeddingService
from ..vectorstore.base import VectorStore
from ..vectorstore.qdrant_store import QdrantVectorStore
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

    logger.info("Initializing DocumentService")
    from ai.documents.analyzer import DocumentAnalyzer
    document_analyzer = DocumentAnalyzer()
    document_service = DocumentService(settings.UPLOAD_DIR, analyzer=document_analyzer)

    logger.info("Initializing EmbeddingService: model=%s", settings.embedding_model_name)
    embedding_service = EmbeddingService(
        embeddings_dir=settings.UPLOAD_DIR / "embeddings",
        model_name=settings.embedding_model_name,
        batch_size=settings.embedding_batch_size,
        embedding_version=settings.embedding_version,
        max_seq_length=settings.embedding_max_seq_length,
    )

    logger.info("Initializing QdrantVectorStore: host=%s, port=%d, collection=%s",
                settings.qdrant_host, settings.qdrant_port, settings.qdrant_collection)
    local_path = settings.qdrant_local_path if settings.qdrant_local_path else None
    vector_store: VectorStore = QdrantVectorStore(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection_name=settings.qdrant_collection,
        vector_dimension=settings.vector_dimension,
        distance_metric=settings.distance_metric,
        local_path=local_path,
    )
    try:
        vector_store.initialize()
        logger.info("QdrantVectorStore initialized successfully")
    except Exception as e:
        logger.warning("QdrantVectorStore initialization failed (will retry on first use): %s", e)

    embedding_service_with_store = EmbeddingService(
        embeddings_dir=settings.UPLOAD_DIR / "embeddings",
        model_name=settings.embedding_model_name,
        batch_size=settings.embedding_batch_size,
        embedding_version=settings.embedding_version,
        max_seq_length=settings.embedding_max_seq_length,
        vector_store=vector_store,
    )

    from ..retrieval.search_engine import SearchEngine
    from ..retrieval.semantic_search import SemanticSearch
    from ..retrieval.keyword_search import KeywordSearch
    from ..retrieval.hybrid_ranker import HybridRanker
    from ..retrieval.query_analyzer import QueryAnalyzer
    from ..retrieval.retrieval_metrics import RetrievalMetrics

    logger.info("Initializing Search Engine: weights=(sem=%.2f, kw=%.2f, meta=%.2f), top_k=%d",
                settings.search_semantic_weight, settings.search_keyword_weight,
                settings.search_metadata_weight, settings.search_default_top_k)

    semantic_search = SemanticSearch(
        embedding_service=embedding_service,
        vector_store=vector_store,
        top_k=settings.search_default_top_k * settings.search_semantic_top_k_multiplier,
        min_score=settings.search_minimum_similarity,
    )

    keyword_search = KeywordSearch(
        bm25_k1=settings.search_bm25_k1,
        bm25_b=settings.search_bm25_b,
    )

    hybrid_ranker = HybridRanker(
        semantic_weight=settings.search_semantic_weight,
        keyword_weight=settings.search_keyword_weight,
        metadata_weight=settings.search_metadata_weight,
        default_top_k=settings.search_default_top_k,
        max_context_chunks=settings.search_max_context_chunks,
        minimum_similarity=settings.search_minimum_similarity,
    )

    query_analyzer = QueryAnalyzer(
        language_service=language_service,
        intent_service=intent_service,
    )

    metrics = RetrievalMetrics()

    search_engine = SearchEngine(
        semantic_search=semantic_search,
        keyword_search=keyword_search,
        hybrid_ranker=hybrid_ranker,
        query_analyzer=query_analyzer,
        metrics=metrics,
        top_k=settings.search_default_top_k,
        min_score=settings.search_minimum_similarity,
    )

    logger.info("Search Engine initialized: BM25=%s", keyword_search._use_bm25)

    from ..reasoning.context_builder import ContextBuilder
    from ..reasoning.prompt_builder import PromptBuilder
    from ..reasoning.citation_manager import CitationManager
    from ..reasoning.response_validator import ResponseValidator
    from ..reasoning.guardrails import Guardrails
    from ..reasoning.reasoning_engine import ReasoningEngine

    logger.info("Initializing Knowledge Reasoning Engine: max_chunks=%d, max_tokens=%d, history_limit=%d",
                settings.reasoning_max_context_chunks, settings.reasoning_max_context_tokens,
                settings.reasoning_conversation_history_limit)

    context_builder = ContextBuilder(
        max_tokens=settings.reasoning_max_context_tokens,
        max_chunks=settings.reasoning_max_context_chunks,
    )

    prompt_builder = PromptBuilder(prompts_dir=settings.PROMPTS_DIR)

    citation_manager = CitationManager(style=settings.reasoning_citation_style)

    response_validator = ResponseValidator()

    guardrails = Guardrails()

    reasoning_engine = ReasoningEngine(
        search_engine=search_engine,
        chat_service=chat_service,
        context_builder=context_builder,
        prompt_builder=prompt_builder,
        citation_manager=citation_manager,
        response_validator=response_validator,
        guardrails=guardrails,
        settings=settings,
    )

    logger.info("Knowledge Reasoning Engine initialized")

    _services = {
        "document": document_service,
        "embedding": embedding_service,
        "embedding_with_store": embedding_service_with_store,
        "vector_store": vector_store,
        "search_engine": search_engine,
        "reasoning_engine": reasoning_engine,
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
