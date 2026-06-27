import logging
import time
from typing import Any, Dict, List, Optional, Set

from ..config.settings import Settings
from .memory_models import MemoryEntry, MemoryQuery, MemoryType
from .memory_extractor import MemoryExtractor
from .memory_classifier import MemoryClassifier
from .memory_store import MemoryStore
from .memory_retriever import MemoryRetriever
from .importance_scorer import ImportanceScorer
from .consolidation import ConsolidationEngine
from .forgetting import ForgettingEngine

logger = logging.getLogger(__name__)


class MemoryEngine:
    def __init__(
        self,
        extractor: MemoryExtractor,
        classifier: MemoryClassifier,
        store: MemoryStore,
        retriever: MemoryRetriever,
        scorer: ImportanceScorer,
        consolidation: ConsolidationEngine,
        forgetting: ForgettingEngine,
        settings: Settings,
    ):
        self._extractor = extractor
        self._classifier = classifier
        self._store = store
        self._retriever = retriever
        self._scorer = scorer
        self._consolidation = consolidation
        self._forgetting = forgetting
        self._settings = settings
        logger.info("MemoryEngine initialized")

    def process_conversation_turn(
        self,
        user_text: str,
        assistant_text: Optional[str] = None,
        user_id: str = "",
        workspace_id: str = "default",
    ) -> Dict[str, Any]:
        start = time.time()
        result: Dict[str, Any] = {
            "extracted_count": 0,
            "stored_count": 0,
            "rejected_count": 0,
            "updated_count": 0,
            "working_memory_id": None,
        }

        candidates = self._extractor.extract(
            user_text=user_text,
            assistant_text=assistant_text,
            user_id=user_id,
            workspace_id=workspace_id,
        )

        result["extracted_count"] = len(candidates)

        for candidate in candidates:
            self._classifier.classify(candidate)

            existing = self._find_semantic_duplicates(candidate)
            if existing:
                existing.update_content(candidate.content)
                existing.confidence = max(existing.confidence, candidate.confidence)
                self._scorer.score(existing)
                self._store.save(existing)
                result["updated_count"] += 1
                logger.info("Memory updated: id=%s, type=%s", existing.memory_id, existing.type)
                continue

            is_important = self._scorer.is_important(
                candidate,
                existing=self._store.list(user_id=user_id, workspace_id=workspace_id),
            )
            if not is_important:
                self._scorer.score(candidate)
                logger.info(
                    "Memory rejected: importance=%.2f < threshold=%.2f, content='%s'",
                    candidate.importance, self._scorer.threshold, candidate.content[:40],
                )
                result["rejected_count"] += 1
                continue

            self._store.save(candidate)
            result["stored_count"] += 1
            logger.info(
                "Memory stored: id=%s, type=%s, importance=%.2f, content='%s'",
                candidate.memory_id, candidate.type, candidate.importance, candidate.content[:40],
            )

        working = self._extractor.extract_working(
            user_text=user_text,
            user_id=user_id,
            workspace_id=workspace_id,
        )
        if working:
            self._scorer.score(working)
            self._store.save(working)
            result["working_memory_id"] = working.memory_id

        elapsed = (time.time() - start) * 1000
        result["processing_time_ms"] = round(elapsed, 2)
        logger.info(
            "Memory processing: extracted=%d, stored=%d, rejected=%d, updated=%d, working=%s, time=%.2fms",
            result["extracted_count"], result["stored_count"], result["rejected_count"],
            result["updated_count"], result["working_memory_id"] or "none", elapsed,
        )

        return result

    def retrieve_for_query(
        self,
        query: MemoryQuery,
    ) -> Dict[str, Any]:
        start = time.time()

        all_entries = self._store.list(
            user_id=query.user_id,
            workspace_id=query.workspace_id,
            include_working=query.include_working,
        )

        if not all_entries:
            elapsed = (time.time() - start) * 1000
            logger.debug("MemoryRetrieval: no memories available for query='%s'", query.query[:40])
            return {
                "memories": [],
                "count": 0,
                "processing_time_ms": round(elapsed, 2),
            }

        relevant = self._retriever.retrieve(query, all_entries)

        self._store.flush()

        elapsed = (time.time() - start) * 1000
        logger.info(
            "Memory retrieval: query='%s', total=%d, relevant=%d, time=%.2fms",
            query.query[:40], len(all_entries), len(relevant), elapsed,
        )

        return {
            "memories": [m.to_dict() for m in relevant],
            "count": len(relevant),
            "processing_time_ms": round(elapsed, 2),
        }

    def consolidate(self, user_id: str = "", workspace_id: str = "") -> Dict[str, Any]:
        start = time.time()

        entries = self._store.list(user_id=user_id, workspace_id=workspace_id)
        if not entries:
            return {"consolidated_count": 0, "processing_time_ms": 0.0}

        before_count = len(entries)
        consolidated = self._consolidation.consolidate(entries)

        for entry in consolidated:
            self._store.save(entry)

        self._store.flush()

        after_count = self._store.total_entries
        elapsed = (time.time() - start) * 1000

        logger.info(
            "Consolidation: before=%d, after=%d, consolidated=%d, time=%.2fms",
            before_count, after_count, len(consolidated), elapsed,
        )

        return {
            "consolidated_count": len(consolidated),
            "before_count": before_count,
            "after_count": after_count,
            "processing_time_ms": round(elapsed, 2),
        }

    def forget(self, user_id: str = "", workspace_id: str = "") -> Dict[str, Any]:
        start = time.time()

        entries = self._store.list(user_id=user_id, workspace_id=workspace_id)
        if not entries:
            return {"forgotten_count": 0, "survivor_count": 0, "processing_time_ms": 0.0}

        before_count = len(entries)
        survivors = self._forgetting.apply_forgetting(entries)

        forgotten_entries = [e for e in entries if e.memory_id not in {s.memory_id for s in survivors}]
        for entry in forgotten_entries:
            self._store.delete(entry.memory_id)

        for survivor in survivors:
            self._store.save(survivor)

        self._store.flush()

        elapsed = (time.time() - start) * 1000
        logger.info(
            "Forgetting: before=%d, forgotten=%d, survivors=%d, time=%.2fms",
            before_count, len(forgotten_entries), len(survivors), elapsed,
        )

        return {
            "forgotten_count": len(forgotten_entries),
            "survivor_count": len(survivors),
            "processing_time_ms": round(elapsed, 2),
        }

    def retrieve_memories(
        self,
        query: str,
        user_id: str = "",
        workspace_id: str = "default",
        top_k: int = 10,
    ) -> Dict[str, Any]:
        memory_query = MemoryQuery(
            query=query,
            user_id=user_id,
            workspace_id=workspace_id,
            top_k=top_k,
        )
        return self.retrieve_for_query(memory_query)

    def get_memories(
        self,
        user_id: str = "",
        workspace_id: str = "",
        memory_type: Optional[str] = None,
        include_working: bool = False,
    ) -> List[Dict[str, Any]]:
        entries = self._store.list(
            user_id=user_id,
            workspace_id=workspace_id,
            memory_type=memory_type,
            include_working=include_working,
        )
        return [e.to_dict() for e in entries]

    def delete_memory(self, memory_id: str) -> bool:
        return self._store.delete(memory_id)

    def clear_working_memory(self) -> int:
        return self._store.clear_working()

    def _find_semantic_duplicates(self, candidate: MemoryEntry) -> Optional[MemoryEntry]:
        existing = self._store.get_by_type(candidate.type)
        if not existing:
            return None
        content_lower = candidate.content.lower().strip()
        content_words = set(content_lower.split())
        for entry in existing:
            entry_lower = entry.content.lower().strip()
            entry_words = set(entry_lower.split())
            if not content_words or not entry_words:
                continue
            overlap = len(content_words & entry_words) / max(len(content_words | entry_words), 1)
            if overlap > 0.7:
                return entry
            from difflib import SequenceMatcher
            ratio = SequenceMatcher(None, content_lower, entry_lower).ratio()
            if ratio > 0.8:
                return entry
        return None

    def health(self) -> Dict[str, Any]:
        counts = self._store.count()
        return {
            "ready": True,
            "memory_count": counts,
            "memory_threshold": self._scorer.threshold,
            "forgetting_rate": self._forgetting._forgetting_rate,
            "importance_decay": self._forgetting._importance_decay,
            "auto_consolidation_enabled": self._settings.memory_auto_consolidation if hasattr(self._settings, 'memory_auto_consolidation') else False,
        }
