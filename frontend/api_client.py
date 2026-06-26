"""HTTP API client for the FastAPI backend.

Streamlit uses this client instead of loading AI models locally.
"""
import logging
from typing import Any, Dict, List, Optional

import httpx

from .config import config

logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors."""


class APIClient:
    """Thin HTTP client for all backend endpoints.

    - Retries on transient failures
    - Raises ``APIClientError`` on non-recoverable errors
    - Never exposes raw stack traces
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float | None = None,
        retries: int | None = None,
    ) -> None:
        self.base_url = base_url or config.base_url
        self._timeout = timeout or config.REQUEST_TIMEOUT
        self._retries = retries or config.RETRY_COUNT
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=httpx.Timeout(self._timeout))
        return self._client

    def _request(self, method: str, path: str, json_data: dict | None = None) -> Any:
        url = f"{self.base_url}{path}"
        client = self._get_client()
        last_error: Exception | None = None

        for attempt in range(1, self._retries + 1):
            try:
                if method == "GET":
                    resp = client.get(url)
                else:
                    resp = client.post(url, json=json_data)

                resp.raise_for_status()
                return resp.json()

            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning("API timeout (%d/%d): %s", attempt, self._retries, url)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                detail = exc.response.text[:500]
                raise APIClientError(f"Server returned {status}: {detail}") from exc
            except httpx.RequestError as exc:
                last_error = exc
                logger.warning("API request failed (%d/%d): %s", attempt, self._retries, str(exc))

        raise APIClientError(
            f"Backend unreachable after {self._retries} retries"
        ) from last_error

    def health(self) -> bool:
        """Check if the backend is healthy."""
        try:
            result = self._request("GET", "/health")
            return result.get("status") == "healthy"
        except Exception:
            return False

    def chat(
        self,
        message: str,
        language: str = "auto",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/chat — returns ChatResponse as dict."""
        return self._request("POST", "/chat", {
            "message": message,
            "language": language,
            "history": history or [],
        })

    def analyze(
        self,
        message: str,
        language: str = "auto",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/analyze — returns AnalyzeResponse as dict."""
        return self._request("POST", "/analyze", {
            "message": message,
            "language": language,
            "history": history or [],
        })

    def sentiment(self, text: str) -> Dict[str, Any]:
        """POST /api/v1/sentiment — returns SentimentResponse as dict."""
        return self._request("POST", "/sentiment", {"text": text})

    def detect_language(self, text: str) -> Dict[str, Any]:
        """POST /api/v1/detect-language — returns LanguageResponse as dict."""
        return self._request("POST", "/detect-language", {"text": text})

    def send_feedback(
        self,
        message_id: str,
        rating: int,
        comment: str | None = None,
    ) -> Dict[str, Any]:
        """POST /api/v1/feedback — returns feedback receipt."""
        return self._request("POST", "/feedback", {
            "message_id": message_id,
            "rating": rating,
            "comment": comment,
        })

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
