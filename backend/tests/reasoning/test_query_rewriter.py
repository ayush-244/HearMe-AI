import pytest
import json
from unittest.mock import MagicMock
from backend.app.reasoning.query_rewriter import QueryRewriter, RewriteResult
from backend.app.services.chat_service import ChatService

@pytest.fixture
def chat_service_mock():
    return MagicMock(spec=ChatService)

@pytest.fixture
def rewriter(chat_service_mock):
    return QueryRewriter(chat_service=chat_service_mock)

def test_should_rewrite_short_query(rewriter):
    assert rewriter.should_rewrite("waht is ai") == True
    assert rewriter.should_rewrite("more") == True

def test_should_rewrite_followup_keywords(rewriter):
    assert rewriter.should_rewrite("why does it do that?") == True
    assert rewriter.should_rewrite("how can I use this API?") == True
    assert rewriter.should_rewrite("explain this further to me.") == True

def test_should_rewrite_shorthand(rewriter):
    assert rewriter.should_rewrite("tell me abt this document") == True
    assert rewriter.should_rewrite("hw wrks rag in this app") == True

def test_should_not_rewrite_clean_long_query(rewriter):
    assert rewriter.should_rewrite("What is the main concept behind Artificial Intelligence?") == False
    assert rewriter.should_rewrite("Please provide a summary of the latest financial report.") == False

def test_rewrite_bypassed_if_clean(rewriter, chat_service_mock):
    query = "What is the main concept behind Artificial Intelligence?"
    result = rewriter.rewrite(query)
    
    assert result.original_query == query
    assert result.rewritten_query == query
    assert result.modified == False
    assert result.confidence == 1.0
    
    chat_service_mock.invoke_llm.assert_not_called()

def test_rewrite_invokes_llm_and_parses_json(rewriter, chat_service_mock):
    query = "waht is ai"
    
    # Mock LLM response
    mock_json_response = '''```json
{
  "rewritten_query": "What is Artificial Intelligence?",
  "modified": true,
  "confidence": 0.98,
  "reason": "spelling"
}
```'''
    chat_service_mock.invoke_llm.return_value = mock_json_response
    
    result = rewriter.rewrite(query)
    
    assert result.original_query == query
    assert result.rewritten_query == "What is Artificial Intelligence?"
    assert result.modified == True
    assert result.confidence == 0.98
    assert result.reason == "spelling"
    
    chat_service_mock.invoke_llm.assert_called_once()

def test_rewrite_with_active_context(rewriter, chat_service_mock):
    query = "more"
    
    mock_json_response = '''{
  "rewritten_query": "Tell me more about Artificial Intelligence.",
  "modified": true,
  "confidence": 0.95,
  "reason": "follow-up"
}'''
    chat_service_mock.invoke_llm.return_value = mock_json_response
    
    result = rewriter.rewrite(
        query=query, 
        last_question="What is Artificial Intelligence?",
        last_answer="AI is a field of computer science...",
        current_topic="Artificial Intelligence"
    )
    
    assert result.original_query == "more"
    assert result.rewritten_query == "Tell me more about Artificial Intelligence."
    assert result.modified == True
    
    # Verify prompt contains single turn active context
    call_args = chat_service_mock.invoke_llm.call_args[0][0]
    assert "User: What is Artificial Intelligence?" in call_args
    assert "Assistant: AI is a field of computer science..." in call_args
    assert "Topic: Artificial Intelligence" in call_args

def test_rewrite_handles_json_parse_error(rewriter, chat_service_mock):
    query = "waht is ai"
    chat_service_mock.invoke_llm.return_value = "I am an AI, I cannot help with that."
    
    result = rewriter.rewrite(query)
    
    assert result.original_query == query
    assert result.rewritten_query == query  # Falls back to original
    assert result.modified == False
    assert result.reason == "JSON Parse Error"
