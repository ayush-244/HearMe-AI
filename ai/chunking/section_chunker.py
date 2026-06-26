import logging
from typing import List, Optional
from .chunk_models import Chunk, create_chunk
from .fixed_chunker import FixedChunker
from .overlap import generate_overlap
from ai.documents.section_parser import Section

logger = logging.getLogger(__name__)

CHARS_PER_PAGE = 3000


class SectionChunker:
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._fixed_chunker = FixedChunker(chunk_size=chunk_size, overlap=overlap)

    def chunk(
        self,
        document_id: str,
        text: str,
        sections: Optional[List[Section]] = None,
    ) -> List[Chunk]:
        if not text or not text.strip():
            logger.warning("SectionChunker: empty text for document %s", document_id)
            return []

        if not sections:
            logger.info("SectionChunker: no sections found, falling back to fixed chunking")
            return self._fixed_chunker.chunk(document_id, text)

        all_chunks: List[Chunk] = []
        chunk_index = 0

        for section in sections:
            section_text = text[section.start_offset:section.end_offset].strip()
            if not section_text:
                logger.debug("SectionChunker: empty section '%s', skipping", section.name)
                continue

            section_words = section_text.split()
            page_start = max(1, section.start_offset // CHARS_PER_PAGE)

            if section_words == 1:
                section_chunks = self._fixed_chunker.chunk(
                    document_id=document_id,
                    text=section_text,
                    section_name=section.name,
                    start_offset=section.start_offset,
                    page_start=page_start,
                    page_end=page_start,
                )
            else:
                section_chunks = self._chunk_section(
                    document_id=document_id,
                    text=section_text,
                    section=section,
                    start_chunk_index=chunk_index,
                )

            all_chunks.extend(section_chunks)
            chunk_index += len(section_chunks)

        logger.info(
            "SectionChunker: %d chunks across %d sections",
            len(all_chunks), len(sections),
        )

        return all_chunks

    def _chunk_section(
        self,
        document_id: str,
        text: str,
        section: Section,
        start_chunk_index: int = 0,
    ) -> List[Chunk]:
        words = text.split()
        if len(words) <= self.chunk_size:
            page = max(1, section.start_offset // CHARS_PER_PAGE)
            chunk = create_chunk(
                document_id=document_id,
                text=text,
                section_name=section.name,
                chunk_index=start_chunk_index,
                start_offset=section.start_offset,
                end_offset=section.end_offset,
                page_start=page,
                page_end=page,
            )
            return [chunk]

        chunks: List[Chunk] = []
        pos = 0
        local_index = 0

        while pos < len(words):
            end = min(pos + self.chunk_size, len(words))
            chunk_words = words[pos:end]
            chunk_text = " ".join(chunk_words)

            chunk_start_offset = self._approximate_offset(text, words, pos) + section.start_offset
            chunk_end_offset = self._approximate_offset(text, words, end) + section.start_offset

            page_start = max(1, chunk_start_offset // CHARS_PER_PAGE)
            page_end = max(1, chunk_end_offset // CHARS_PER_PAGE)

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
                section_name=section.name,
                chunk_index=start_chunk_index + local_index,
                start_offset=chunk_start_offset,
                end_offset=chunk_end_offset,
                page_start=page_start,
                page_end=page_end,
                overlap_previous=prev_overlap,
                overlap_next=next_overlap,
            )
            chunks.append(chunk)
            local_index += 1
            pos = end

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
