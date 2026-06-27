import json
import logging
import os
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional, Set

from .memory_models import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)


class MemoryStore:
    def __init__(self, storage_dir: str):
        self._storage_dir = Path(storage_dir)
        self._memory_dir = self._storage_dir / "memory"
        self._memory_dir.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._entries: Dict[str, MemoryEntry] = {}
        self._dirty: bool = False

        self._STORE_FILES = {
            MemoryType.SEMANTIC: self._memory_dir / "semantic.json",
            MemoryType.EPISODIC: self._memory_dir / "episodic.json",
            MemoryType.PREFERENCE: self._memory_dir / "preferences.json",
            MemoryType.WORKING: self._memory_dir / "working.json",
        }

        self._load_all()
        logger.info("MemoryStore initialized: dir=%s, entries=%d", self._memory_dir, len(self._entries))

    def save(self, entry: MemoryEntry) -> None:
        with self._lock:
            self._entries[entry.memory_id] = entry
            self._dirty = True
            self._persist_type(entry.type)
            logger.debug("Memory saved: id=%s, type=%s, content='%s'", entry.memory_id, entry.type, entry.content[:50])

    def save_all(self, entries: List[MemoryEntry]) -> None:
        with self._lock:
            for entry in entries:
                self._entries[entry.memory_id] = entry
            self._dirty = True
            types_to_save: Set[str] = set(e.type for e in entries)
            for t in types_to_save:
                self._persist_type(t)
            logger.debug("Saved %d memories across types: %s", len(entries), types_to_save)

    def get(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            entry = self._entries.get(memory_id)
            if entry:
                entry.touch()
                self._dirty = True
            return entry

    def delete(self, memory_id: str) -> bool:
        with self._lock:
            if memory_id not in self._entries:
                return False
            entry = self._entries.pop(memory_id)
            self._dirty = True
            self._persist_type(entry.type)
            logger.info("Memory deleted: id=%s, type=%s", memory_id, entry.type)
            return True

    def list(
        self,
        user_id: str = "",
        workspace_id: str = "",
        memory_type: Optional[str] = None,
        include_working: bool = False,
    ) -> List[MemoryEntry]:
        with self._lock:
            result = list(self._entries.values())

        if memory_type:
            result = [e for e in result if e.type == memory_type]

        if user_id:
            result = [e for e in result if e.user_id == user_id]

        if workspace_id:
            result = [e for e in result if e.workspace_id == workspace_id]

        if not include_working:
            result = [e for e in result if e.type != MemoryType.WORKING]

        result.sort(key=lambda e: e.importance, reverse=True)
        return result

    def get_by_type(self, memory_type: str) -> List[MemoryEntry]:
        with self._lock:
            return [e for e in self._entries.values() if e.type == memory_type]

    def clear_working(self) -> int:
        with self._lock:
            working_ids = [mid for mid, e in self._entries.items() if e.type == MemoryType.WORKING]
            for mid in working_ids:
                del self._entries[mid]
            self._dirty = True
            self._persist_type(MemoryType.WORKING)
            logger.info("Cleared %d working memories", len(working_ids))
            return len(working_ids)

    def count(self) -> Dict[str, int]:
        with self._lock:
            counts: Dict[str, int] = {}
            for e in self._entries.values():
                counts[e.type] = counts.get(e.type, 0) + 1
            counts["total"] = sum(counts.values())
            return counts

    def _persist_type(self, memory_type: str) -> None:
        file_path = self._STORE_FILES.get(memory_type)
        if not file_path:
            logger.warning("Unknown memory type for persist: %s", memory_type)
            return
        entries = [e for e in self._entries.values() if e.type == memory_type]
        try:
            file_path.write_text(MemoryEntry.serialize_all(entries), encoding="utf-8")
        except Exception as e:
            logger.error("Failed to persist %s memories: %s", memory_type, e)

    def _load_all(self) -> None:
        for mem_type, file_path in self._STORE_FILES.items():
            if file_path.exists():
                try:
                    raw = file_path.read_text(encoding="utf-8")
                    if raw.strip():
                        entries = MemoryEntry.deserialize_all(raw)
                        for entry in entries:
                            self._entries[entry.memory_id] = entry
                        logger.info("Loaded %d %s memories from %s", len(entries), mem_type, file_path.name)
                except (json.JSONDecodeError, Exception) as e:
                    logger.error("Failed to load %s memories from %s: %s", mem_type, file_path, e)

    def flush(self) -> None:
        with self._lock:
            if not self._dirty:
                return
            for mem_type in MemoryType.ALL:
                self._persist_type(mem_type)
            self._dirty = False
            logger.debug("MemoryStore flushed all types to disk")

    @property
    def total_entries(self) -> int:
        return len(self._entries)

    @property
    def storage_dir(self) -> Path:
        return self._memory_dir
