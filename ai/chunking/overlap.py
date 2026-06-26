import logging
from typing import List

logger = logging.getLogger(__name__)


def generate_overlap(text: str, overlap_word_count: int = 50) -> str:
    if overlap_word_count <= 0:
        return ""
    words = text.split()
    if len(words) <= overlap_word_count:
        return text
    overlap_words = words[-overlap_word_count:]
    return " ".join(overlap_words)


def apply_overlap_to_chunks(
    chunks: List[str],
    overlap_word_count: int = 50,
) -> List[str]:
    if overlap_word_count <= 0 or len(chunks) <= 1:
        return chunks

    overlapped: List[str] = []
    for i, chunk_text in enumerate(chunks):
        prev_overlap = generate_overlap(chunks[i - 1], overlap_word_count) if i > 0 else ""
        next_overlap = generate_overlap(chunks[i + 1], overlap_word_count) if i < len(chunks) - 1 else ""

        combined = chunk_text
        if prev_overlap:
            combined = prev_overlap + " " + combined
        if next_overlap:
            combined = combined + " " + next_overlap

        overlapped.append(combined.strip())

    return overlapped
