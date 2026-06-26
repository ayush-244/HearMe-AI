import logging
import time
from typing import Dict, List, Optional
from .chunk_models import Chunk, ChunkStatistics, create_chunk
from .chunk_strategy import select_strategy, create_chunker
from .fixed_chunker import FixedChunker
from .section_chunker import SectionChunker
from .semantic_chunker import SemanticChunker
from ai.documents.section_parser import SectionParser

logger = logging.getLogger(__name__)

MIN_CHUNK_WORDS = 30
MAX_CHUNK_WORDS = 1000


class ChunkEngine:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._section_parser = SectionParser()

    def chunk_document(
        self,
        document_id: str,
        text: str,
        document_type: str = "unknown",
        file_type: Optional[str] = None,
        sections: Optional[List[dict]] = None,
    ) -> Dict[str, object]:
        logger.info("Chunking started: document_id=%s", document_id)
        start_time = time.time()

        strategy = select_strategy(document_type, file_type)
        chunker = create_chunker(strategy, self.chunk_size, self.overlap)

        if isinstance(chunker, SectionChunker):
            parsed_sections = self._get_sections(text, document_type, sections)
            raw_chunks = chunker.chunk(document_id, text, parsed_sections)
        elif isinstance(chunker, FixedChunker):
            raw_chunks = chunker.chunk(document_id, text)
        elif isinstance(chunker, SemanticChunker):
            raw_chunks = chunker.chunk(document_id, text)
        else:
            logger.error("Unknown chunker type: %s", type(chunker))
            raw_chunks = FixedChunker(self.chunk_size, self.overlap).chunk(document_id, text)

        validated, rejected = self._validate_chunks(raw_chunks)
        chunks = self._deduplicate(validated)

        for r in rejected:
            logger.warning("Rejected chunk: word_count=%d, reason=%s", r.get("word_count", 0), r.get("reason", "unknown"))

        stats = self._compute_statistics(document_id, chunks, strategy)

        duration = time.time() - start_time
        logger.info(
            "Chunking completed: id=%s, strategy=%s, chunks=%d, rejected=%d, "
            "avg_size=%.1f, duration=%.2fs",
            document_id, strategy, stats.chunks, len(rejected),
            stats.average_chunk_size, duration,
        )

        return {
            "chunks": [c.to_dict() for c in chunks],
            "statistics": stats.to_dict(),
            "strategy": strategy,
            "duration_seconds": round(duration, 3),
            "rejected_count": len(rejected),
        }

    def _get_sections(
        self,
        text: str,
        document_type: str,
        sections: Optional[List[dict]],
    ) -> List:
        from ai.documents.section_parser import Section

        if sections:
            return [Section(**s) if not isinstance(s, Section) else s for s in sections]

        return self._section_parser.parse(text, document_type)

    def _validate_chunks(self, chunks: List[Chunk]) -> tuple:
        validated: List[Chunk] = []
        rejected: List[Dict[str, object]] = []

        for chunk in chunks:
            reason = self._check_valid(chunk)
            if reason:
                rejected.append({
                    "chunk_id": chunk.chunk_id,
                    "word_count": chunk.word_count,
                    "reason": reason,
                })
            else:
                validated.append(chunk)

        return validated, rejected

    def _check_valid(self, chunk: Chunk) -> Optional[str]:
        if not chunk.text or not chunk.text.strip():
            return "empty"

        if chunk.text.strip() != chunk.text:
            pass

        if chunk.word_count < MIN_CHUNK_WORDS:
            return f"too_few_words ({chunk.word_count} < {MIN_CHUNK_WORDS})"

        if chunk.word_count > MAX_CHUNK_WORDS:
            return f"too_many_words ({chunk.word_count} > {MAX_CHUNK_WORDS})"

        return None

    def _deduplicate(self, chunks: List[Chunk]) -> List[Chunk]:
        seen: set = set()
        unique: List[Chunk] = []
        for chunk in chunks:
            normalized = chunk.text.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                unique.append(chunk)
            else:
                logger.debug("Removed duplicate chunk: index=%d, section=%s", chunk.chunk_index, chunk.section_name)
        return unique

    def _compute_statistics(
        self,
        document_id: str,
        chunks: List[Chunk],
        strategy: str,
    ) -> ChunkStatistics:
        if not chunks:
            return ChunkStatistics(
                document_id=document_id,
                chunks=0,
                average_chunk_size=0.0,
                largest_chunk=0,
                smallest_chunk=0,
                strategy=strategy,
            )

        word_counts = [c.word_count for c in chunks]
        return ChunkStatistics(
            document_id=document_id,
            chunks=len(chunks),
            average_chunk_size=round(sum(word_counts) / len(word_counts), 1),
            largest_chunk=max(word_counts),
            smallest_chunk=min(word_counts),
            strategy=strategy,
        )
