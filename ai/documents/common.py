"""Shared types and utilities for document extraction."""
from dataclasses import dataclass, field
from typing import Dict, Optional
import unicodedata
import re


@dataclass
class ExtractedDocument:
    text: str
    preview: str
    pages: int
    words: int
    characters: int
    metadata: Dict[str, object] = field(default_factory=dict)


class DocumentNormalizer:
    MAX_PREVIEW_CHARS = 500

    @staticmethod
    def normalize(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+(?=\n)", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip()
        return text

    @staticmethod
    def generate_preview(text: str, max_chars: int = MAX_PREVIEW_CHARS) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= max_chars:
            return text
        preview = text[:max_chars]
        last_space = preview.rfind(" ")
        if last_space > max_chars // 2:
            preview = preview[:last_space]
        return preview + "..."

    @staticmethod
    def count_words(text: str) -> int:
        return len(text.split())

    @staticmethod
    def count_characters(text: str) -> int:
        return len(text)
