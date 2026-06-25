import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class HistoryService:
    def __init__(self, max_messages: int = 10):
        self._max_messages = max_messages

    def add_message(
        self,
        history: List[Dict[str, str]],
        role: str,
        content: str
    ) -> List[Dict[str, str]]:
        history.append({"role": role, "content": content})
        if len(history) > self._max_messages:
            trimmed = history[-self._max_messages:]
            logger.debug("Trimmed history from %d to %d messages", len(history), self._max_messages)
            return trimmed
        return history

    def get_recent(self, history: List[Dict[str, str]], count: int = 5) -> List[Dict[str, str]]:
        return history[-count:] if history else []
