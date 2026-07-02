import logging
import json
from pydantic import BaseModel
from typing import List, Optional, Any

from .answer_models import ConversationTurn
from ..services.chat_service import ChatService

logger = logging.getLogger(__name__)

class RewriteResult(BaseModel):
    original_query: str
    rewritten_query: str
    modified: bool
    confidence: float
    reason: str

class QueryRewriter:
    def __init__(self, chat_service: ChatService):
        self._chat_service = chat_service
        self._shorthands = {
            "waht", "wht", "hw", "wrks", "abt", "pls", "plz", "thx", "u", "ur", "b4",
            "gr8", "l8r", "im", "idk", "btw", "fyi", "asap"
        }
        self._follow_up_keywords = {
            "more", "why", "how", "explain", "continue", "elaborate", "example",
            "tell me more", "compare", "difference", "what about", "and"
        }

    def should_rewrite(self, query: str) -> bool:
        """
        Determine if the query requires rewriting.
        Skip rewriting when the query is long and looks clean.
        """
        if not query or not query.strip():
            return False

        q_lower = query.lower().strip()
        words = q_lower.split()
        
        # 1. Very short messages are often follow-ups or abbreviations
        if len(words) < 5:
            return True
            
        # 2. Check for obvious typos / abbreviations
        if any(word in self._shorthands for word in words):
            return True
            
        # 3. Check for follow-up ambiguity at the start of the query
        for keyword in self._follow_up_keywords:
            if q_lower.startswith(keyword):
                return True

        # Otherwise, assume it's a good enough query
        return False

    def rewrite(self, query: str, last_question: str = "", last_answer: str = "", current_topic: str = "") -> RewriteResult:
        if not self.should_rewrite(query):
            return RewriteResult(
                original_query=query,
                rewritten_query=query,
                modified=False,
                confidence=1.0,
                reason="Query is already clean"
            )

        prompt = self._build_prompt(query, last_question, last_answer, current_topic)
        
        try:
            llm_response = self._chat_service.invoke_llm(prompt)
            
            cleaned_response = llm_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:-3].strip()
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:-3].strip()
                
            data = json.loads(cleaned_response)
            
            result = RewriteResult(
                original_query=query,
                rewritten_query=data.get("rewritten_query", query),
                modified=data.get("modified", False),
                confidence=data.get("confidence", 0.0),
                reason=data.get("reason", "unknown")
            )
            
            if result.modified:
                logger.info(
                    "[REWRITE]\nOriginal:\n%s\n↓\nRewritten:\n%s\nModified=%s\nReason=%s\nConfidence=%.2f",
                    result.original_query, result.rewritten_query, result.modified, result.reason, result.confidence
                )
                
            return result
            
        except json.JSONDecodeError:
            logger.warning("QueryRewriter failed to parse JSON. Raw response: %s", llm_response)
            return RewriteResult(
                original_query=query,
                rewritten_query=query,
                modified=False,
                confidence=0.0,
                reason="JSON Parse Error"
            )
        except Exception as e:
            logger.error("QueryRewriter encountered an error: %s", e)
            return RewriteResult(
                original_query=query,
                rewritten_query=query,
                modified=False,
                confidence=0.0,
                reason=f"Error: {str(e)}"
            )

    def _build_prompt(self, query: str, last_question: str, last_answer: str, current_topic: str) -> str:
        topic_text = current_topic if current_topic else "Unknown"
        history_text = "None"
        if last_question or last_answer:
            history_text = f"User: {last_question}\nAssistant: {last_answer}"

        return f"""You are HearMe AI's Query Rewriter.
Your ONLY task is rewriting the user's latest query.

Never answer.
Never explain.
Never add facts.

Rules:
• Correct spelling.
• Correct grammar.
• Correct punctuation.
• Expand abbreviations.
• Use the active conversation topic and immediate context to rewrite follow-ups into standalone queries.
• Do not include unrelated past topics. Focus ONLY on the active conversation context.
• Preserve meaning exactly.
• Return ONLY a valid JSON object.

Output Format:
{{
  "rewritten_query": "The cleanly rewritten query string",
  "modified": true,
  "confidence": 0.95,
  "reason": "spelling / grammar / abbreviation / follow-up / etc."
}}

Active Context:
Topic: {topic_text}
{history_text}

User Query:
{query}
"""

