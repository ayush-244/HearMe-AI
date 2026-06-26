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

    PROJECT_ROOT: ClassVar[Path] = Path(__file__).resolve().parent.parent.parent.parent
    PROMPTS_DIR: ClassVar[Path] = PROJECT_ROOT / "prompts"
    UPLOAD_DIR: ClassVar[Path] = PROJECT_ROOT / "uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
