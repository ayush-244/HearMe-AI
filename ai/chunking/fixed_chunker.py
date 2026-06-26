import logging
from typing import List, Tuple
from .chunk_models import Chunk, create_chunk
from .overlap import generate_overlap

logger = logging.getLogger(__name__)

DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 50


class FixedChunker:
    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(
        self,
        document_id: str,
        text: str,
        section_name: str = "body",
        start_offset: int = 0,
        page_start: int = 0,
        page_end: int = 0,
    ) -> List[Chunk]:
        if not text or not text.strip():
            logger.warning("FixedChunker: empty text for document %s", document_id)
            return []

        words = text.split()
        chunks: List[Chunk] = []
        chunk_index = 0
        pos = 0

        while pos < len(words):
            end = min(pos + self.chunk_size, len(words))
            chunk_words = words[pos:end]
            chunk_text = " ".join(chunk_words)

            chunk_start_offset = self._approximate_offset(text, words, pos)
            chunk_end_offset = self._approximate_offset(text, words, end)

            prev_overlap = generate_overlap(
                " ".join(words[max(0, pos - self.overlap):pos]),
                self.overlap,
            ) if pos > 0 else ""

            next_overlap = generate_overlap(
                " ".join(words[end:min(len(words), end + self.overlap)]),
                self.overlap,
            ) if end < len(words) else ""

            chunk = create_chunk(
                document_id=document_id,
                text=chunk_text,
                section_name=section_name,
                chunk_index=chunk_index,
                start_offset=chunk_start_offset,
                end_offset=chunk_end_offset,
                page_start=page_start,
                page_end=page_end,
                overlap_previous=prev_overlap,
                overlap_next=next_overlap,
            )
            chunks.append(chunk)
            chunk_index += 1
            pos = end

        logger.debug(
            "FixedChunker: %d chunks from %d words (size=%d, overlap=%d)",
            len(chunks), len(words), self.chunk_size, self.overlap,
        )

        return chunks

    def _approximate_offset(self, text: str, words: List[str], word_index: int) -> int:
        if word_index <= 0:
            return 0
        if word_index >= len(words):
            return len(text)
        target = " ".join(words[:word_index])
        idx = text.find(target)
        if idx >= 0:
            return idx + len(target)
        return 0
