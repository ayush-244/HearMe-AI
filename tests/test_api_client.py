"""Tests for the frontend API client."""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from frontend.api_client import APIClient, APIClientError


@pytest.fixture
def api():
    return APIClient(base_url="http://test/api/v1", timeout=5.0, retries=1)


class MockResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json_data = json_data
        self.text = json.dumps(json_data)

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            from httpx import HTTPStatusError, Request
            raise HTTPStatusError(
                f"HTTP {self.status_code}",
                request=Request("POST", "http://test/"),
                response=self,
            )


class MockClient:
    def __init__(self, response: MockResponse | None = None, side_effect: Exception | None = None):
        self._response = response
        self._side_effect = side_effect
        self.last_url = None
        self.last_json = None
        self.last_method = None
        self.closed = False

    def get(self, url, **kwargs):
        self.last_method = "GET"
        self.last_url = url
        if self._side_effect:
            raise self._side_effect
        return self._response

    def post(self, url, json=None, **kwargs):
        self.last_method = "POST"
        self.last_url = url
        self.last_json = json
        if self._side_effect:
            raise self._side_effect
        return self._response

    def close(self):
        self.closed = True


class TestAPIClient:
    def test_health_success(self, api):
        mock = MockClient(MockResponse(200, {"status": "healthy"}))
        with patch.object(api, '_get_client', return_value=mock):
            assert api.health() is True
            assert "/health" in mock.last_url

    def test_health_unhealthy_status(self, api):
        mock = MockClient(MockResponse(200, {"status": "unhealthy"}))
        with patch.object(api, '_get_client', return_value=mock):
            assert api.health() is False

    def test_health_server_error(self, api):
        mock = MockClient(side_effect=Exception("Connection refused"))
        with patch.object(api, '_get_client', return_value=mock):
            assert api.health() is False

    def test_chat_success(self, api):
        response_data = {
            "reply": "Hello! How can I help?",
            "sentiment": "Positive",
            "confidence": 0.95,
            "detected_language": "en",
            "language_name": "English",
        }
        mock = MockClient(MockResponse(200, response_data))
        with patch.object(api, '_get_client', return_value=mock):
            result = api.chat("Hello", language="en", history=[])
            assert result["reply"] == "Hello! How can I help?"
            assert result["sentiment"] == "Positive"
            assert "/chat" in mock.last_url
            assert mock.last_json["message"] == "Hello"
            assert mock.last_json["language"] == "en"

    def test_chat_with_history(self, api):
        history = [{"role": "user", "content": "Hi"}]
        mock = MockClient(MockResponse(200, {"reply": "Hello!", "sentiment": "Neutral", "confidence": 0.5, "detected_language": "en", "language_name": "English"}))
        with patch.object(api, '_get_client', return_value=mock):
            api.chat("Hi", history=history)
            assert mock.last_json["history"] == history

    def test_chat_auto_language(self, api):
        mock = MockClient(MockResponse(200, {"reply": "Hola!", "sentiment": "Neutral", "confidence": 0.5, "detected_language": "es", "language_name": "Spanish"}))
        with patch.object(api, '_get_client', return_value=mock):
            result = api.chat("Hola", language="auto")
            assert result["detected_language"] == "es"

    def test_analyze_success(self, api):
        response_data = {
            "language": "English",
            "sentiment": "Negative",
            "emotion": "sadness",
            "toxicity": "none",
            "threat": "none",
            "intent": "conversation",
            "confidence": {"sentiment": 0.94, "emotion": 0.87, "toxicity": 0.02, "threat": 0.01, "intent": 0.76},
            "response": "I'm here for you.",
        }
        mock = MockClient(MockResponse(200, response_data))
        with patch.object(api, '_get_client', return_value=mock):
            result = api.analyze("I feel sad", language="en")
            assert result["emotion"] == "sadness"
            assert result["sentiment"] == "Negative"
            assert "/analyze" in mock.last_url

    def test_sentiment_success(self, api):
        mock = MockClient(MockResponse(200, {"sentiment": "Positive", "confidence": 0.95}))
        with patch.object(api, '_get_client', return_value=mock):
            result = api.sentiment("I love this!")
            assert result["sentiment"] == "Positive"
            assert result["confidence"] == 0.95
            assert mock.last_json["text"] == "I love this!"

    def test_detect_language_success(self, api):
        mock = MockClient(MockResponse(200, {"detected_language": "fr", "language_name": "French"}))
        with patch.object(api, '_get_client', return_value=mock):
            result = api.detect_language("Bonjour")
            assert result["detected_language"] == "fr"
            assert result["language_name"] == "French"

    def test_feedback_success(self, api):
        mock = MockClient(MockResponse(200, {"status": "received", "message_id": "msg_1", "rating": 5}))
        with patch.object(api, '_get_client', return_value=mock):
            result = api.send_feedback("msg_1", 5, "Great!")
            assert result["status"] == "received"

    def test_http_400_error(self, api):
        mock = MockClient(MockResponse(400, {"detail": "Message cannot be empty"}))
        with patch.object(api, '_get_client', return_value=mock):
            with pytest.raises(APIClientError, match="Server returned 400"):
                api.chat("", language="en")

    def test_http_500_error(self, api):
        mock = MockClient(MockResponse(500, {"detail": "Internal error"}))
        with patch.object(api, '_get_client', return_value=mock):
            with pytest.raises(APIClientError, match="Server returned 500"):
                api.chat("Hello", language="en")

    def test_timeout_retries_then_raises(self, api):
        from httpx import TimeoutException
        mock = MockClient(side_effect=TimeoutException("timed out"))
        with patch.object(api, '_get_client', return_value=mock):
            with pytest.raises(APIClientError, match="Backend unreachable"):
                api.chat("Hello", language="en")

    def test_connection_error_retries_then_raises(self, api):
        from httpx import ConnectError
        mock = MockClient(side_effect=ConnectError("Connection refused"))
        with patch.object(api, '_get_client', return_value=mock):
            with pytest.raises(APIClientError, match="Backend unreachable"):
                api.chat("Hello", language="en")

    def test_close_releases_client(self, api):
        mock = MockClient(MockResponse(200, {"status": "healthy"}))
        api._client = mock
        api.close()
        assert mock.closed
        assert api._client is None

    def test_client_lazy_initialization(self, api):
        assert api._client is None
        mock = MockClient(MockResponse(200, {"status": "healthy"}))
        with patch('httpx.Client', return_value=mock):
            api.health()
            assert api._client is mock

    def test_send_feedback_no_comment(self, api):
        mock = MockClient(MockResponse(200, {"status": "received", "message_id": "m1", "rating": 3}))
        with patch.object(api, '_get_client', return_value=mock):
            result = api.send_feedback("m1", 3)
            assert result["rating"] == 3

    def test_non_default_constructor(self, api):
        custom = APIClient(base_url="http://other/api", timeout=10, retries=5)
        assert custom.base_url == "http://other/api"
        assert custom._timeout == 10
        assert custom._retries == 5
