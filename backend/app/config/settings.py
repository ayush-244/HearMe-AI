from pydantic_settings import BaseSettings
from pathlib import Path
from typing import ClassVar


class Settings(BaseSettings):
    groq_api_key: str = ""
    hf_token: str = ""
    google_api_key: str = ""

    sentiment_model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    llm_model_name: str = "llama-3.3-70b-versatile"
    zero_shot_model_name: str = "typeform/distilbert-base-uncased-mnli"

    max_history_messages: int = 10
    max_history_prompt_messages: int = 5
    max_sequence_length: int = 512
    sentiment_log_file: str = "sentiment_analysis_log.txt"
    max_upload_size: int = 20 * 1024 * 1024  # 20 MB

    embedding_model_name: str = "BAAI/bge-base-en-v1.5"
    embedding_batch_size: int = 32
    embedding_version: str = "1.0.0"
    embedding_max_seq_length: int = 512

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "knowledge_brain"
    qdrant_local_path: str = ""
    vector_dimension: int = 768
    distance_metric: str = "Cosine"

    search_semantic_weight: float = 0.65
    search_keyword_weight: float = 0.25
    search_metadata_weight: float = 0.10
    search_default_top_k: int = 10
    search_max_context_chunks: int = 20
    search_minimum_similarity: float = 0.0
    search_bm25_k1: float = 1.5
    search_bm25_b: float = 0.75
    search_semantic_top_k_multiplier: int = 3

    reasoning_max_context_chunks: int = 20
    reasoning_max_context_tokens: int = 4096
    reasoning_conversation_history_limit: int = 5
    reasoning_allow_external_knowledge: bool = False
    reasoning_citation_style: str = "inline"
    reasoning_temperature: float = 0.3
    reasoning_max_tokens: int = 1024

    memory_threshold: float = 0.3
    memory_limit: int = 10000
    working_memory_limit: int = 50
    forgetting_rate: float = 0.1
    importance_decay: float = 0.05
    memory_search_top_k: int = 10
    auto_consolidation: bool = False

    PROJECT_ROOT: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent.parent
    PROMPTS_DIR: ClassVar[Path] = PROJECT_ROOT / "prompts"
    UPLOAD_DIR: ClassVar[Path] = PROJECT_ROOT / "uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
