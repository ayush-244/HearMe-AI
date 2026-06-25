import pytest
from unittest.mock import Mock, MagicMock
from backend.app.services.chat_service import ChatService


@pytest.fixture
def mock_llm():
    llm = Mock()
    response = MagicMock()
    response.content = "I'm glad to hear that! How can I help?"
    llm.invoke.return_value = response
    return llm


@pytest.fixture
def mock_prompt_service():
    service = Mock()
    service.build_chat_prompt.return_value = "System: ...\nUser: I'm happy"
    service.select_intro.return_value = "Great!"
    return service


class TestChatService:
    def test_generate_response_returns_text(self, mock_llm, mock_prompt_service):
        service = ChatService(mock_llm, mock_prompt_service)
        response = service.generate_response(
            user_input="I'm happy",
            language="en",
            sentiment="Positive",
            history=[],
        )
        assert response == "I'm glad to hear that! How can I help?"

    def test_generate_response_calls_llm_with_prompt(self, mock_llm, mock_prompt_service):
        service = ChatService(mock_llm, mock_prompt_service)
        service.generate_response("Hello", "en", "Neutral")
        mock_llm.invoke.assert_called_once()
        args, _ = mock_llm.invoke.call_args
        assert args[0] == "System: ...\nUser: I'm happy"

    def test_generate_response_llm_failure_returns_error_message(self, mock_llm, mock_prompt_service):
        mock_llm.invoke.side_effect = Exception("API error")
        service = ChatService(mock_llm, mock_prompt_service)
        response = service.generate_response("Hello", "en", "Neutral")
        assert "I'm sorry" in response
