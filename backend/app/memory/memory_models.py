import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class MemoryType:
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PREFERENCE = "preference"
    WORKING = "working"

    ALL = (EPISODIC, SEMANTIC, PREFERENCE, WORKING)


@dataclass
class MemoryEntry:
    memory_id: str = ""
    user_id: str = ""
    workspace_id: str = "default"
    type: str = MemoryType.EPISODIC
    content: str = ""
    summary: str = ""
    importance: float = 0.0
    confidence: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    last_accessed: str = ""
    access_count: int = 0
    embedding_version: str = ""
    checksum: str = ""
    source: str = ""
    pinned: bool = False

    @staticmethod
    def _utcnow() -> str:
        return datetime.now(timezone.utc).isoformat()

    def __post_init__(self):
        if not self.memory_id:
            self.memory_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = self._utcnow()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.last_accessed:
            self.last_accessed = self.created_at
        if not self.checksum:
            self.checksum = self._compute_checksum()

    def _compute_checksum(self) -> str:
        raw = f"{self.content}|{self.user_id}|{self.workspace_id}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    def touch(self) -> None:
        self.last_accessed = self._utcnow()
        self.access_count += 1

    def update_content(self, content: str) -> None:
        self.content = content
        self.updated_at = self._utcnow()
        self.checksum = self._compute_checksum()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "MemoryEntry":
        return MemoryEntry(**data)

    @staticmethod
    def serialize_all(entries: List["MemoryEntry"]) -> str:
        return json.dumps([e.to_dict() for e in entries], indent=2, default=str)

    @staticmethod
    def deserialize_all(raw: str) -> List["MemoryEntry"]:
        data = json.loads(raw)
        return [MemoryEntry.from_dict(d) for d in data]


@dataclass
class MemoryQuery:
    query: str
    user_id: str = ""
    workspace_id: str = "default"
    memory_types: Optional[List[str]] = None
    top_k: int = 10
    min_importance: float = 0.0
    include_working: bool = False
