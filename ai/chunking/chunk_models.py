import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    section_name: str
    text: str
    chunk_index: int
    page_start: int
    page_end: int
    start_offset: int
    end_offset: int
    word_count: int
    character_count: int
    estimated_tokens: int
    overlap_previous: str
    overlap_next: str
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "section_name": self.section_name,
            "text": self.text,
            "chunk_index": self.chunk_index,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "estimated_tokens": self.estimated_tokens,
            "overlap_previous": self.overlap_previous,
            "overlap_next": self.overlap_next,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls(**data)

    def to_preview(self) -> dict:
        preview_text = self.text[:120]
        if len(self.text) > 120:
            preview_text += "..."
        return {
            "chunk_id": self.chunk_id,
            "section_name": self.section_name,
            "chunk_index": self.chunk_index,
            "word_count": self.word_count,
            "character_count": self.character_count,
            "estimated_tokens": self.estimated_tokens,
            "page_start": self.page_start,
            "page_end": self.page_end,
            "preview": preview_text,
        }


@dataclass
class ChunkStatistics:
    document_id: str
    chunks: int
    average_chunk_size: float
    largest_chunk: int
    smallest_chunk: int
    strategy: str

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "chunks": self.chunks,
            "average_chunk_size": self.average_chunk_size,
            "largest_chunk": self.largest_chunk,
            "smallest_chunk": self.smallest_chunk,
            "strategy": self.strategy,
        }


def create_chunk(
    document_id: str,
    text: str,
    section_name: str,
    chunk_index: int,
    start_offset: int,
    end_offset: int,
    page_start: int = 0,
    page_end: int = 0,
    overlap_previous: str = "",
    overlap_next: str = "",
    metadata: Optional[Dict[str, object]] = None,
) -> Chunk:
    words = text.split()
    word_count = len(words)
    character_count = len(text)
    estimated_tokens = int(word_count * 1.3)

    return Chunk(
        chunk_id=str(uuid.uuid4()),
        document_id=document_id,
        section_name=section_name,
        text=text,
        chunk_index=chunk_index,
        page_start=page_start,
        page_end=page_end,
        start_offset=start_offset,
        end_offset=end_offset,
        word_count=word_count,
        character_count=character_count,
        estimated_tokens=estimated_tokens,
        overlap_previous=overlap_previous,
        overlap_next=overlap_next,
        metadata=metadata or {},
    )
