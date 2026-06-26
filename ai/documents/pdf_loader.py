import logging
from pathlib import Path
from typing import Optional
from .common import ExtractedDocument, DocumentNormalizer

logger = logging.getLogger(__name__)


class PDFLoader:
    def extract(self, filepath: str) -> ExtractedDocument:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {filepath}")

        try:
            import fitz
        except ImportError:
            raise ImportError("PyMuPDF (fitz) is required. Install: pip install PyMuPDF")

        doc = None
        try:
            doc = fitz.open(filepath)
            metadata = dict(doc.metadata) if doc.metadata else {}
            page_count = doc.page_count

            if doc.is_encrypted or doc.needs_pass:
                logger.warning("PDF is password-protected: %s", filepath)
                raise ValueError("PDF is password-protected")

            text_parts = []
            for page_num in range(page_count):
                page = doc.load_page(page_num)
                text = page.get_text()
                text_parts.append(text)

            raw_text = "\n\n".join(text_parts)
            text = DocumentNormalizer.normalize(raw_text)

            preview = DocumentNormalizer.generate_preview(text)
            words = DocumentNormalizer.count_words(text)
            characters = DocumentNormalizer.count_characters(text)

            extracted_meta = {
                "pdf_version": metadata.get("format", ""),
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "producer": metadata.get("producer", ""),
                "creator": metadata.get("creator", ""),
            }

            logger.info(
                "PDF extracted: pages=%d, words=%d, chars=%d",
                page_count, words, characters,
            )

            return ExtractedDocument(
                text=text,
                preview=preview,
                pages=page_count,
                words=words,
                characters=characters,
                metadata=extracted_meta,
            )

        except fitz.FileDataError as e:
            logger.error("Corrupted PDF: %s — %s", filepath, e)
            raise ValueError(f"Corrupted PDF: {e}")
        except ValueError:
            raise
        except Exception as e:
            msg = str(e).lower()
            if "encrypt" in msg or "password" in msg or "closed" in msg:
                logger.warning("PDF is password-protected: %s", filepath)
                raise ValueError("PDF is password-protected")
            logger.error("PDF extraction failed: %s — %s", filepath, e)
            raise ValueError(f"PDF extraction failed: {e}")
        finally:
            if doc is not None:
                doc.close()
