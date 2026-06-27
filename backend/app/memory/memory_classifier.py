import logging
from typing import Dict, List, Optional

from .memory_models import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)

_TYPE_KEYWORDS = {
    MemoryType.SEMANTIC: [
        "i am", "i'm", "my name", "i study", "i work", "i use",
        "i have", "i live", "i know", "i learned", "i can",
        "i cannot", "i don't", "i do not", "i speak", "i code",
        "i program", "i write", "fact", "remember that",
    ],
    MemoryType.PREFERENCE: [
        "i like", "i love", "i prefer", "i enjoy", "i hate",
        "i dislike", "my favorite", "my favourite", "i would rather",
        "better", "best", "worst", "i want", "i wish",
    ],
    MemoryType.EPISODIC: [
        "i uploaded", "i asked", "i created", "i wrote",
        "i started", "i finished", "i completed", "i tried",
        "i installed", "i configured", "i set up", "i switched",
        "i downloaded", "i sent", "i read", "i used",
        "yesterday", "today i", "last week", "earlier",
    ],
}


class MemoryClassifier:
    def classify(self, entry: MemoryEntry) -> str:
        if entry.type not in (MemoryType.EPISODIC, MemoryType.SEMANTIC, MemoryType.PREFERENCE, MemoryType.WORKING):
            detected = self._detect_type(entry.content)
            entry.type = detected
        return entry.type

    def _detect_type(self, text: str) -> str:
        text_lower = text.lower().strip()
        scores: Dict[str, int] = {
            MemoryType.SEMANTIC: 0,
            MemoryType.PREFERENCE: 0,
            MemoryType.EPISODIC: 0,
        }

        for mem_type, keywords in _TYPE_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    scores[mem_type] += 1

        max_score = 0
        best_type = MemoryType.EPISODIC
        for mem_type, score in scores.items():
            if score > max_score:
                max_score = score
                best_type = mem_type

        return best_type if max_score > 0 else MemoryType.EPISODIC

    def batch_classify(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        for entry in entries:
            self.classify(entry)
        return entries
