import logging
import re
from pathlib import Path
from .common import ExtractedDocument, DocumentNormalizer

logger = logging.getLogger(__name__)


class MarkdownLoader:
    def extract(self, filepath: str) -> ExtractedDocument:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Markdown not found: {filepath}")

        content = path.read_text(encoding="utf-8", errors="replace")
        raw_text = self._strip_markdown(content)
        text = DocumentNormalizer.normalize(raw_text)

        preview = DocumentNormalizer.generate_preview(text)
        words = DocumentNormalizer.count_words(text)
        characters = DocumentNormalizer.count_characters(text)

        logger.info(
            "Markdown extracted: words=%d, chars=%d",
            words, characters,
        )

        return ExtractedDocument(
            text=text,
            preview=preview,
            pages=0,
            words=words,
            characters=characters,
            metadata={},
        )

    @staticmethod
    def _strip_markdown(text: str) -> str:
        text = re.sub(r"```[\s\S]*?```", "", text)
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]*)\]\(.*?\)", r"\1", text)
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
        text = re.sub(r"\*(.*?)\*", r"\1", text)
        text = re.sub(r"__(.*?)__", r"\1", text)
        text = re.sub(r"_(.*?)_", r"\1", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*>\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"^\s*[-*+]{3,}\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"\|", " ", text)
        return text
