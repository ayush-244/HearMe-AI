import logging
import math
from datetime import datetime, timezone
from typing import Dict, List, Set, Tuple

from .memory_models import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


class ForgettingEngine:
    def __init__(
        self,
        forgetting_rate: float = 0.1,
        importance_decay: float = 0.05,
        high_importance_threshold: float = 0.7,
        max_age_days: int = 365,
    ):
        self._forgetting_rate = forgetting_rate
        self._importance_decay = importance_decay
        self._high_importance_threshold = high_importance_threshold
        self._max_age_days = max_age_days
        logger.info(
            "ForgettingEngine initialized: rate=%.2f, decay=%.2f, high_thresh=%.2f, max_age=%d",
            forgetting_rate, importance_decay, high_importance_threshold, max_age_days,
        )

    def apply_forgetting(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        if not entries:
            return []

        protected: Set[str] = set()
        for entry in entries:
            if self._should_protect(entry):
                protected.add(entry.memory_id)

        survivors: List[MemoryEntry] = []
        forgotten: List[MemoryEntry] = []

        for entry in entries:
            if entry.memory_id in protected:
                survivors.append(entry)
                continue

            decayed = self._decay_importance(entry)

            if self._should_forget(decayed):
                forgotten.append(entry)
                logger.info(
                    "Memory forgotten: id=%s, type=%s, content='%s', importance=%.2f",
                    entry.memory_id, entry.type, entry.content[:40], entry.importance,
                )
            else:
                entry.importance = decayed.importance
                survivors.append(entry)

        if forgotten:
            logger.info(
                "Forgetting: forgotten=%d, protected=%d, survivors=%d",
                len(forgotten), len(protected), len(survivors),
            )

        return survivors

    def _should_protect(self, entry: MemoryEntry) -> bool:
        if entry.pinned:
            return True
        if entry.importance >= self._high_importance_threshold:
            return True
        if entry.access_count >= 20:
            return True
        if entry.type == MemoryType.PREFERENCE and entry.importance >= 0.5:
            return True
        return False

    def _decay_importance(self, entry: MemoryEntry) -> MemoryEntry:
        try:
            last_access = datetime.fromisoformat(entry.last_accessed)
            now = datetime.now(timezone.utc)
            days_since_access = (now - last_access).total_seconds() / 86400
        except (ValueError, TypeError):
            days_since_access = 0

        if days_since_access <= 1:
            return entry

        decay_factor = math.exp(-self._forgetting_rate * days_since_access)
        base_decay = self._importance_decay * days_since_access / 30.0

        access_modifier = max(0.5, 1.0 - (entry.access_count * 0.01))
        total_decay = base_decay * access_modifier * (1.0 - decay_factor)

        new_importance = max(0.0, entry.importance - total_decay)
        entry.importance = round(new_importance, 4)

        return entry

    def _should_forget(self, entry: MemoryEntry) -> bool:
        if entry.pinned:
            return False
        if entry.importance >= 0.3:
            return False
        try:
            last_access = datetime.fromisoformat(entry.last_accessed)
            now = datetime.now(timezone.utc)
            days_since_access = (now - last_access).total_seconds() / 86400
        except (ValueError, TypeError):
            days_since_access = 0

        if days_since_access > self._max_age_days and entry.importance < 0.2:
            return True
        if entry.importance <= 0.05 and days_since_access > 7:
            return True
        if entry.importance < 0.1 and days_since_access > 90 and entry.access_count < 3:
            return True
        return False
