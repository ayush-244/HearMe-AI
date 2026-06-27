import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

from .memory_models import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)

_PROPER_NOUN = re.compile(r"\b[A-Z][a-z]{2,}\b")
_DIGIT = re.compile(r"\d+")
_EMPHASIS = re.compile(r"[!]{2,}|[A-Z]{4,}")
_QUESTION = re.compile(r"\?")
_SPECIFIC_TERMS = re.compile(
    r"\b(year|month|week|day|percent|version|language|framework|"
    r"library|tool|project|company|university|school)\b",
    re.IGNORECASE,
)


class ImportanceScorer:
    def __init__(self, threshold: float = 0.3, recency_hours: int = 24):
        self._threshold = threshold
        self._recency_hours = recency_hours
        logger.info("ImportanceScorer initialized: threshold=%.2f, recency_hours=%d", threshold, recency_hours)

    def score(self, entry: MemoryEntry, existing: Optional[List[MemoryEntry]] = None) -> float:
        base = self._base_importance(entry)
        recency = self._recency_bonus(entry)
        specificity = self._specificity_score(entry.content)
        emphasis = self._emphasis_score(entry.content)
        frequency = self._frequency_bonus(entry, existing or [])
        future = self._future_usefulness(entry.content)

        total = (
            base * 0.25
            + recency * 0.15
            + specificity * 0.25
            + emphasis * 0.10
            + frequency * 0.15
            + future * 0.10
        )

        total = round(min(max(total, 0.0), 1.0), 4)

        entry.importance = total

        logger.debug(
            "Importance score for '%s': base=%.2f, recency=%.2f, spec=%.2f, "
            "emphasis=%.2f, freq=%.2f, future=%.2f => total=%.4f",
            entry.content[:40], base, recency, specificity, emphasis, frequency, future, total,
        )

        return total

    def is_important(self, entry: MemoryEntry, existing: Optional[List[MemoryEntry]] = None) -> bool:
        return self.score(entry, existing) >= self._threshold

    def _base_importance(self, entry: MemoryEntry) -> float:
        type_scores = {
            MemoryType.SEMANTIC: 0.7,
            MemoryType.PREFERENCE: 0.6,
            MemoryType.EPISODIC: 0.4,
            MemoryType.WORKING: 0.1,
        }
        return type_scores.get(entry.type, 0.3)

    def _recency_bonus(self, entry: MemoryEntry) -> float:
        try:
            created = datetime.fromisoformat(entry.created_at)
            now = datetime.now(timezone.utc)
            delta_hours = (now - created).total_seconds() / 3600
            if delta_hours < self._recency_hours:
                return 0.2
            elif delta_hours < self._recency_hours * 7:
                return 0.1
            return 0.0
        except (ValueError, TypeError):
            return 0.0

    def _specificity_score(self, text: str) -> float:
        score = 0.0
        proper_nouns = _PROPER_NOUN.findall(text)
        score += min(len(proper_nouns) * 0.15, 0.4)
        digits = _DIGIT.findall(text)
        score += min(len(digits) * 0.1, 0.2)
        terms = _SPECIFIC_TERMS.findall(text)
        score += min(len(terms) * 0.1, 0.2)
        specific_verbs = re.findall(
            r"\b(uploaded|downloaded|created|installed|configured|implemented|"
            r"built|developed|designed|started|finished|completed|switched|"
            r"migrated|upgraded|purchased|bought|sold|joined|left)\b",
            text, re.IGNORECASE,
        )
        score += min(len(specific_verbs) * 0.1, 0.2)
        return round(min(score, 1.0), 2)

    def _emphasis_score(self, text: str) -> float:
        score = 0.0
        if _EMPHASIS.search(text):
            score += 0.2
        if text.strip().endswith("!"):
            score += 0.1
        if _QUESTION.search(text):
            score += 0.1
        words = text.split()
        cap_words = sum(1 for w in words if w.isupper() and len(w) > 2)
        if cap_words > 1:
            score += min(cap_words * 0.05, 0.2)
        return round(min(score, 0.5), 2)

    @staticmethod
    def _tokenize_words(text: str) -> set:
        return {w for w in re.findall(r"[a-z]+", text.lower()) if len(w) >= 2}

    def _frequency_bonus(self, entry: MemoryEntry, existing: List[MemoryEntry]) -> float:
        if not existing:
            return 0.0
        content_words = self._tokenize_words(entry.content)
        if not content_words:
            return 0.0
        overlap_scores = []
        for existing_entry in existing:
            existing_words = self._tokenize_words(existing_entry.content)
            if content_words and existing_words:
                overlap = len(content_words & existing_words) / len(content_words | existing_words)
                if overlap > 0.1:
                    overlap_scores.append(overlap)
        if overlap_scores:
            avg_overlap = sum(overlap_scores) / len(overlap_scores)
            return round(min(avg_overlap * 0.3, 0.3), 2)
        return 0.0

    def _future_usefulness(self, text: str) -> float:
        useful_signals = re.findall(
            r"\b(prefer|like|love|use|work|study|know|can|"
            r"have|need|want|wish|hope|plan|going to|will)\b",
            text, re.IGNORECASE,
        )
        score = min(len(useful_signals) * 0.08, 0.4)
        if len(text.split()) > 8:
            score += 0.1
        return round(min(score, 0.5), 2)

    @property
    def threshold(self) -> float:
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        self._threshold = value
