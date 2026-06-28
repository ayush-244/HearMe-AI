import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_WINDOW_SIZE = 8


@dataclass
class ConversationWindowState:
    conversation_id: str
    recent_messages: List[Dict[str, str]] = field(default_factory=list)
    summary: str = ""
    turn_count: int = 0
    window_size: int = DEFAULT_WINDOW_SIZE
    needs_summary_update: bool = False

    def add_message(self, role: str, content: str) -> None:
        self.recent_messages.append({"role": role, "content": content})
        self.turn_count += 1
        if len(self.recent_messages) > self.window_size:
            self.needs_summary_update = True

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        if limit:
            return list(self.recent_messages[-limit:])
        return list(self.recent_messages)

    def compress(self) -> int:
        excess = len(self.recent_messages) - self.window_size
        if excess > 0:
            old_messages = self.recent_messages[:excess]
            self.recent_messages = self.recent_messages[-self.window_size:]
            self.needs_summary_update = True
            return len(old_messages)
        return 0

    def should_summarize(self) -> bool:
        return len(self.recent_messages) >= self.window_size * 1.5

    @property
    def message_count(self) -> int:
        return len(self.recent_messages)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "recent_messages": self.recent_messages,
            "summary": self.summary,
            "turn_count": self.turn_count,
            "message_count": self.message_count,
        }


class ConversationWindow:
    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE):
        self._window_size = window_size
        self._states: Dict[str, ConversationWindowState] = {}
        logger.info("ConversationWindow initialized: size=%d", window_size)

    def get_or_create(self, conversation_id: str) -> ConversationWindowState:
        if conversation_id not in self._states:
            self._states[conversation_id] = ConversationWindowState(
                conversation_id=conversation_id,
                window_size=self._window_size,
            )
        return self._states[conversation_id]

    def add_message(self, conversation_id: str, role: str, content: str) -> ConversationWindowState:
        state = self.get_or_create(conversation_id)
        state.add_message(role, content)
        return state

    def get_history(self, conversation_id: str, limit: Optional[int] = None) -> List[Dict[str, str]]:
        state = self.get_or_create(conversation_id)
        return state.get_history(limit)

    def get_summary(self, conversation_id: str) -> str:
        state = self.get_or_create(conversation_id)
        return state.summary

    def set_summary(self, conversation_id: str, summary: str) -> None:
        state = self.get_or_create(conversation_id)
        state.summary = summary
        state.needs_summary_update = False

    def compress(self, conversation_id: str) -> int:
        state = self.get_or_create(conversation_id)
        return state.compress()

    def should_summarize(self, conversation_id: str) -> bool:
        state = self.get_or_create(conversation_id)
        return state.should_summarize()

    def get_turn_count(self, conversation_id: str) -> int:
        state = self.get_or_create(conversation_id)
        return state.turn_count

    def clear(self, conversation_id: str) -> None:
        self._states.pop(conversation_id, None)
        logger.debug("Cleared window for conversation %s", conversation_id)

    def get_last_user_message(self, conversation_id: str) -> Optional[str]:
        state = self.get_or_create(conversation_id)
        for msg in reversed(state.recent_messages):
            if msg.get("role") == "user":
                return msg.get("content")
        return None

    def get_last_assistant_message(self, conversation_id: str) -> Optional[str]:
        state = self.get_or_create(conversation_id)
        for msg in reversed(state.recent_messages):
            if msg.get("role") == "assistant":
                return msg.get("content")
        return None

    def get_all_contexts(self) -> List[str]:
        return list(self._states.keys())
