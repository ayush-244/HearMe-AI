import logging
from pathlib import Path
from .common import ExtractedDocument, DocumentNormalizer

logger = logging.getLogger(__name__)


class TXTLoader:
    def extract(self, filepath: str) -> ExtractedDocument:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"TXT not found: {filepath}")

        content_bytes = path.read_bytes()
        raw_text = self._decode(content_bytes)
        text = DocumentNormalizer.normalize(raw_text)

        preview = DocumentNormalizer.generate_preview(text)
        words = DocumentNormalizer.count_words(text)
        characters = DocumentNormalizer.count_characters(text)

        logger.info(
            "TXT extracted: words=%d, chars=%d",
            words, characters,
        )

        return ExtractedDocument(
            text=text,
            preview=preview,
            pages=0,
            words=words,
            characters=characters,
            metadata={"encoding": "utf-8"},
        )

    def _decode(self, content: bytes) -> str:
        if content[:3] == b"\xef\xbb\xbf":
            return content[3:].decode("utf-8")

        if content[:2] in (b"\xff\xfe", b"\xfe\xff"):
            return content.decode("utf-16")

        if b"\x00" in content:
            try:
                le_decoded = content.decode("utf-16-le")
                be_decoded = content.decode("utf-16-be")
                le_ascii = sum(1 for c in le_decoded if ord(c) < 128)
                be_ascii = sum(1 for c in be_decoded if ord(c) < 128)
                return le_decoded if le_ascii >= be_ascii else be_decoded
            except (UnicodeDecodeError, UnicodeError):
                pass

        for encoding in ("utf-8", "latin-1"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue

        logger.warning("All encodings failed, falling back to latin-1 with replacement")
        return content.decode("latin-1", errors="replace")
