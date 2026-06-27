import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from .memory_models import MemoryEntry, MemoryType, MemoryQuery

logger = logging.getLogger(__name__)

_GREETING_PATTERNS = re.compile(
    r"\b(hi|hello|hey|greetings|good\s*(morning|afternoon|evening)|"
    r"howdy|sup|yo|what'?s up|nice to meet|pleased to meet)\b",
    re.IGNORECASE,
)

_FAREWELL_PATTERNS = re.compile(
    r"\b(bye|goodbye|see\s*you|talk\s*to\s*you\s*later|take\s*care|"
    r"have\s*a\s*good\s*(day|night|one)|cya|later|cheers)\b",
    re.IGNORECASE,
)

_SMALL_TALK_PATTERNS = re.compile(
    r"\b(how are you|how'?s it going|what'?s up|how'?s everything|"
    r"how do you do|how have you been|long time no see)\b",
    re.IGNORECASE,
)

_ACKNOWLEDGMENT_PATTERNS = re.compile(
    r"\b(ok|okay|k|thanks|thank you|ty|sure|yes|no|"
    r"got it|i see|understood|alright|fine|perfect|great|awesome)\b",
    re.IGNORECASE,
)

_FACT_PREFIXES = re.compile(
    r"\b(i am|i'?m|my name is|i study|i work|i use|i have|"
    r"i live|i like|i love|i prefer|i enjoy|i hate|i dislike|"
    r"i know|i learned|i can|i cannot|i don'?t|i do not|"
    r"i think|i believe|i feel|my favorite|my favourite)\b",
    re.IGNORECASE,
)

_SELF_REFERENCE = re.compile(r"\b(i|my|me|mine)\b", re.IGNORECASE)

_PREFERENCE_SIGNALS = re.compile(
    r"\b(prefer|like|love|favourite|favorite|enjoy|would rather|"
    r"better|best|worst|hate|dislike|cant stand|cannot stand)\b",
    re.IGNORECASE,
)

_PROPER_NOUN = re.compile(r"\b[A-Z][a-z]{2,}\b")

_DIGIT = re.compile(r"\d+")


class MemoryExtractor:
    def __init__(self, min_content_length: int = 15):
        self._min_content_length = min_content_length
        logger.info("MemoryExtractor initialized: min_content_length=%d", min_content_length)

    def extract(
        self,
        user_text: str,
        assistant_text: Optional[str] = None,
        user_id: str = "",
        workspace_id: str = "default",
    ) -> List[MemoryEntry]:
        if not user_text or len(user_text.strip()) < self._min_content_length:
            return []

        cleaned = user_text.strip()

        if self._is_noise(cleaned):
            return []

        memories: List[MemoryEntry] = []

        if self._is_preference(cleaned):
            entry = self._build_entry(
                content=cleaned,
                type=MemoryType.PREFERENCE,
                user_id=user_id,
                workspace_id=workspace_id,
                confidence=self._estimate_confidence(cleaned),
            )
            memories.append(entry)
        elif self._is_semantic(cleaned):
            entry = self._build_entry(
                content=cleaned,
                type=MemoryType.SEMANTIC,
                user_id=user_id,
                workspace_id=workspace_id,
                confidence=self._estimate_confidence(cleaned),
            )
            memories.append(entry)
        elif self._is_episodic(cleaned):
            entry = self._build_entry(
                content=cleaned,
                type=MemoryType.EPISODIC,
                user_id=user_id,
                workspace_id=workspace_id,
                confidence=self._estimate_confidence(cleaned),
            )
            memories.append(entry)

        return memories

    def extract_working(
        self,
        user_text: str,
        user_id: str = "",
        workspace_id: str = "default",
    ) -> Optional[MemoryEntry]:
        if not user_text or len(user_text.strip()) < self._min_content_length:
            return None
        cleaned = user_text.strip()
        if self._is_noise(cleaned):
            return None
        entry = self._build_entry(
            content=cleaned,
            type=MemoryType.WORKING,
            user_id=user_id,
            workspace_id=workspace_id,
            summary=cleaned[:100],
        )
        return entry

    def _is_noise(self, text: str) -> bool:
        if len(text.split()) <= 3:
            return True
        if _GREETING_PATTERNS.search(text) and len(text.split()) <= 6:
            return True
        if _FAREWELL_PATTERNS.search(text) and len(text.split()) <= 6:
            return True
        if _SMALL_TALK_PATTERNS.search(text):
            return True
        first_word = text.strip().lower().rstrip(".,!?").split()[0] if text.strip() else ""
        if first_word in {"ok", "okay", "thanks", "thank", "ty", "sure", "yes", "no", "got", "k"} and len(text.split()) <= 5:
            return True
        if re.match(r"^[\s\W]+$", text):
            return True
        return False

    def _is_semantic(self, text: str) -> bool:
        return bool(_FACT_PREFIXES.search(text)) and bool(_SELF_REFERENCE.search(text))

    def _is_preference(self, text: str) -> bool:
        return bool(_PREFERENCE_SIGNALS.search(text)) and bool(_SELF_REFERENCE.search(text))

    def _is_episodic(self, text: str) -> bool:
        if len(text.split()) < 4:
            return False
        has_action = bool(re.search(r"\b(uploaded|downloaded|asked|created|wrote|read|"
                                    r"sent|started|finished|completed|tried|used|"
                                    r"installed|configured|set\s*up|switched)\b", text, re.IGNORECASE))
        if has_action and _SELF_REFERENCE.search(text):
            return True
        return False

    def _estimate_confidence(self, text: str) -> float:
        score = 0.5
        proper_nouns = _PROPER_NOUN.findall(text)
        score += min(len(proper_nouns) * 0.1, 0.3)
        digits = _DIGIT.findall(text)
        score += min(len(digits) * 0.05, 0.1)
        words = text.split()
        if len(words) > 10:
            score += 0.1
        if re.search(r"[.?!]$", text.strip()):
            score += 0.1
        if "!" in text:
            score += 0.1
        return min(round(score, 2), 1.0)

    def _build_entry(
        self,
        content: str,
        type: str,
        user_id: str,
        workspace_id: str,
        confidence: float = 0.5,
        summary: str = "",
    ) -> MemoryEntry:
        return MemoryEntry(
            content=content,
            type=type,
            user_id=user_id,
            workspace_id=workspace_id,
            confidence=confidence,
            summary=summary or content[:120],
            source="conversation",
        )
