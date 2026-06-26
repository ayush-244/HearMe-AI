"""Frontend configuration — loaded from environment variables."""
import os
from dataclasses import dataclass


@dataclass
class FrontendConfig:
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")
    REQUEST_TIMEOUT: float = float(os.getenv("REQUEST_TIMEOUT", "30.0"))
    RETRY_COUNT: int = int(os.getenv("RETRY_COUNT", "3"))
    API_PREFIX: str = "/api/v1"

    @property
    def base_url(self) -> str:
        return f"{self.BACKEND_URL}{self.API_PREFIX}"


config = FrontendConfig()

LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "hi": "Hindi",
}
