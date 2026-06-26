import logging
import re
from typing import List, Optional, Tuple
from .chunk_models import Chunk, create_chunk

logger = logging.getLogger(__name__)

MIN_MERGE_WORDS = 80
MAX_CHUNK_WORDS = 600


class SemanticChunker:
    def chunk(
        self,
        document_id: str,
        text: str,
        section_name: str = "body",
        start_offset: int = 0,
    ) -> List[Chunk]:
        if not text or not text.strip():
            logger.warning("SemanticChunker: empty text for document %s", document_id)
            return []

        segments = self._split_semantic(text)
        merged = self._merge_segments(segments)
        chunks = self._build_chunks(document_id, merged, section_name, start_offset)

        logger.info(
            "SemanticChunker: %d chunks from %d segments",
            len(chunks), len(segments),
        )

        return chunks

    def _split_semantic(self, text: str) -> List[str]:
        segments: List[str] = []
        lines = text.split("\n")
        current: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if self._is_code_block_start(line):
                block, i = self._extract_code_block(lines, i)
                if current:
                    segments.append("\n".join(current))
                    current = []
                segments.append(block)
                i += 1
                continue

            if self._is_table_row(line):
                table, i = self._extract_table(lines, i)
                if current:
                    segments.append("\n".join(current))
                    current = []
                segments.append(table)
                i += 1
                continue

            if self._is_heading(line):
                if current:
                    segments.append("\n".join(current))
                    current = []
                segments.append(line)
                i += 1
                continue

            if self._is_bullet_list_start(line):
                list_block, i = self._extract_bullet_list(lines, i)
                if current:
                    segments.append("\n".join(current))
                    current = []
                segments.append(list_block)
                i += 1
                continue

            if self._is_paragraph_break(line):
                if current:
                    segments.append("\n".join(current))
                    current = []
                i += 1
                continue

            current.append(line)
            i += 1

        if current:
            segments.append("\n".join(current))

        return segments

    def _is_code_block_start(self, line: str) -> bool:
        return line.strip().startswith("```") or line.strip().startswith("~~~")

    def _extract_code_block(self, lines: List[str], start: int) -> Tuple[str, int]:
        block_lines = [lines[start]]
        i = start + 1
        while i < len(lines):
            block_lines.append(lines[i])
            if lines[i].strip().startswith("```") or lines[i].strip().startswith("~~~"):
                break
            i += 1
        return "\n".join(block_lines), i

    def _is_table_row(self, line: str) -> bool:
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            return True
        if re.match(r"^[\s]*[|+][-\s|+]+[|+]", stripped):
            return True
        return False

    def _extract_table(self, lines: List[str], start: int) -> Tuple[str, int]:
        table_lines = [lines[start]]
        i = start + 1
        while i < len(lines) and self._is_table_row(lines[i]):
            table_lines.append(lines[i])
            i += 1
        return "\n".join(table_lines), i - 1

    def _is_heading(self, line: str) -> bool:
        stripped = line.strip()
        if re.match(r"^#{1,6}\s+", stripped):
            return True
        if re.match(r"^[A-Z][A-Za-z\s]{2,50}$", stripped) and len(stripped) >= 3:
            return True
        if re.match(r"^\d+(?:\.\d+)*\.?\s+[A-Z]", stripped):
            return True
        return False

    def _is_bullet_list_start(self, line: str) -> bool:
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("+ "):
            return True
        if re.match(r"^\d+[.)]\s+", stripped):
            return True
        return False

    def _extract_bullet_list(self, lines: List[str], start: int) -> Tuple[str, int]:
        list_lines = [lines[start]]
        i = start + 1
        while i < len(lines):
            stripped = lines[i].strip()
            if not stripped:
                break
            if stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("+ "):
                list_lines.append(lines[i])
                i += 1
            elif re.match(r"^\d+[.)]\s+", stripped):
                list_lines.append(lines[i])
                i += 1
            elif stripped and not stripped[0].isupper() and not stripped.startswith("#"):
                list_lines.append(lines[i])
                i += 1
            else:
                break
        return "\n".join(list_lines), i - 1

    def _is_paragraph_break(self, line: str) -> bool:
        return line.strip() == ""

    def _merge_segments(self, segments: List[str]) -> List[str]:
        if not segments:
            return []

        merged: List[str] = []
        current = segments[0]

        for seg in segments[1:]:
            combined_words = len(current.split()) + len(seg.split())
            if combined_words <= MAX_CHUNK_WORDS and len(current.split()) < MIN_MERGE_WORDS:
                current = current + "\n\n" + seg
            else:
                merged.append(current)
                current = seg

        if current:
            merged.append(current)

        return merged

    def _build_chunks(
        self,
        document_id: str,
        segments: List[str],
        section_name: str,
        base_offset: int,
    ) -> List[Chunk]:
        chunks: List[Chunk] = []
        offset = base_offset
        chars_per_page = 3000

        for i, segment in enumerate(segments):
            segment = segment.strip()
            if not segment:
                continue

            char_count = len(segment)
            start_offset = offset
            end_offset = offset + char_count
            page_start = max(1, start_offset // chars_per_page)
            page_end = max(1, end_offset // chars_per_page)

            chunk = create_chunk(
                document_id=document_id,
                text=segment,
                section_name=section_name,
                chunk_index=i,
                start_offset=start_offset,
                end_offset=end_offset,
                page_start=page_start,
                page_end=page_end,
            )
            chunks.append(chunk)
            offset = end_offset

        return chunks
