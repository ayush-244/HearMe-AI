import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .conversation_window import ConversationWindow
from .context_summarizer import ContextSummarizer
from .reference_resolver import ReferenceResolver, ResolvedQuery

logger = logging.getLogger(__name__)


@dataclass
class ConversationContext:
    conversation_id: str
    last_question: str = ""
    last_answer: str = ""
    last_retrieved_chunks: List[Dict[str, Any]] = field(default_factory=list)
    last_cited_documents: List[Dict[str, Any]] = field(default_factory=list)
    last_uploaded_files: List[Dict[str, Any]] = field(default_factory=list)
    current_topic: str = ""
    conversation_summary: str = ""
    turn_count: int = 0
    last_intent: Optional[str] = None


class ConversationContextManager:
    def __init__(self):
        self._contexts: Dict[str, ConversationContext] = {}
        self._window = ConversationWindow()
        self._summarizer = ContextSummarizer()
        self._resolver = ReferenceResolver()
        logger.info("ConversationContextManager initialized")

    def get_or_create(self, conversation_id: str) -> ConversationContext:
        if conversation_id not in self._contexts:
            self._contexts[conversation_id] = ConversationContext(
                conversation_id=conversation_id,
            )
        return self._contexts[conversation_id]

    def update_after_turn(self, conversation_id: str, question: str, answer: str, intent: Optional[str] = None, chunks: Optional[List[Dict]] = None, documents: Optional[List[Dict]] = None) -> None:
        ctx = self.get_or_create(conversation_id)

        ctx.last_question = question
        ctx.last_answer = answer
        ctx.turn_count += 1
        if intent:
            ctx.last_intent = intent

        if chunks is not None:
            ctx.last_retrieved_chunks = chunks
        if documents is not None:
            ctx.last_uploaded_files = documents

        topic = self._summarizer.get_topic_label(
            [{"role": "user", "content": question}, {"role": "assistant", "content": answer}]
        )
        if topic:
            ctx.current_topic = topic

        self._window.add_message(conversation_id, "user", question)
        self._window.add_message(conversation_id, "assistant", answer)

        if self._window.should_summarize(conversation_id):
            messages = self._window.get_history(conversation_id)
            summary = self._summarizer.summarize(messages)
            if summary:
                self._window.set_summary(conversation_id, summary)
                ctx.conversation_summary = summary

            self._window.compress(conversation_id)

    def resolve_query(self, conversation_id: str, query: str) -> ResolvedQuery:
        ctx = self.get_or_create(conversation_id)
        window = self._window.get_or_create(conversation_id)

        if window.recent_messages:
            last_user = self._window.get_last_user_message(conversation_id) or ""
            last_assistant = self._window.get_last_assistant_message(conversation_id) or ""
        else:
            last_user = ctx.last_question
            last_assistant = ctx.last_answer

        return self._resolver.resolve(
            query=query,
            last_question=last_user,
            last_answer=last_assistant,
            current_topic=ctx.current_topic,
            attached_documents=ctx.last_uploaded_files,
        )

    def get_window_history(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        return self._window.get_history(conversation_id, limit)

    def get_window_summary(self, conversation_id: str) -> str:
        return self._window.get_summary(conversation_id)

    def get_turn_count(self, conversation_id: str) -> int:
        ctx = self.get_or_create(conversation_id)
        return ctx.turn_count

    def get_last_retrieved_chunks(self, conversation_id: str) -> List[Dict]:
        ctx = self.get_or_create(conversation_id)
        return ctx.last_retrieved_chunks

    def set_last_retrieved_chunks(self, conversation_id: str, chunks: List[Dict]) -> None:
        ctx = self.get_or_create(conversation_id)
        ctx.last_retrieved_chunks = list(chunks)

    def clear(self, conversation_id: str) -> None:
        self._contexts.pop(conversation_id, None)
        self._window.clear(conversation_id)
        logger.info("Cleared context for conversation %s", conversation_id)

    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        return self._contexts.get(conversation_id)

    def health(self) -> Dict[str, Any]:
        return {
            "active_contexts": len(self._contexts),
            "active_windows": len(self._window.get_all_contexts()),
        }
