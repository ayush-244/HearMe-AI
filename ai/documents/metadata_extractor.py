import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class MetadataExtractor:
    def extract(
        self,
        text: str,
        file_metadata: Optional[Dict[str, object]] = None,
        filename: str = "",
    ) -> Dict[str, object]:
        result: Dict[str, object] = {}

        result["title"] = self._extract_title(text, file_metadata, filename)
        result["author"] = self._extract_author(file_metadata)
        result["creation_date"] = self._extract_creation_date(file_metadata)
        result["modification_date"] = self._extract_modification_date(file_metadata)

        urls = self._extract_urls(text)
        emails = self._extract_emails(text)
        phone_numbers = self._extract_phone_numbers(text)
        dates = self._extract_dates(text)

        result["contains_urls"] = len(urls) > 0
        result["contains_emails"] = len(emails) > 0
        result["contains_phone_numbers"] = len(phone_numbers) > 0
        result["contains_dates"] = len(dates) > 0
        result["contains_tables"] = self._contains_tables(text)
        result["contains_images"] = self._extract_image_indicators(text, file_metadata)
        result["contains_code_blocks"] = self._contains_code_blocks(text)

        result["urls"] = urls
        result["emails"] = emails
        result["phone_numbers"] = phone_numbers
        result["dates"] = dates

        return result

    def _extract_title(
        self,
        text: str,
        file_metadata: Optional[Dict[str, object]],
        filename: str,
    ) -> str:
        if file_metadata:
            raw = file_metadata.get("title")
            if raw and isinstance(raw, str) and raw.strip():
                return raw.strip()

        lines = text.strip().split("\n")
        for line in lines[:20]:
            clean = line.strip().strip("#*_").strip()
            if clean and len(clean) >= 3 and len(clean) <= 200:
                if clean.isupper() or clean[0].isupper():
                    return clean

        for line in lines[:5]:
            if line.startswith("#"):
                clean = line.lstrip("#").strip()
                if clean:
                    return clean

        name = Path(filename).stem if filename else ""
        if name:
            return name.replace("_", " ").replace("-", " ").title()

        return "Untitled"

    def _extract_author(
        self,
        file_metadata: Optional[Dict[str, object]],
    ) -> str:
        if file_metadata:
            author = file_metadata.get("author")
            if author and isinstance(author, str) and author.strip():
                return author.strip()
        return ""

    def _extract_creation_date(
        self,
        file_metadata: Optional[Dict[str, object]],
    ) -> Optional[str]:
        if file_metadata:
            raw = file_metadata.get("creation_date")
            if raw:
                return self._normalize_date(raw)
        return None

    def _extract_modification_date(
        self,
        file_metadata: Optional[Dict[str, object]],
    ) -> Optional[str]:
        if file_metadata:
            raw = file_metadata.get("modification_date") or file_metadata.get("modDate")
            if raw:
                return self._normalize_date(raw)
        return None

    def _normalize_date(self, raw: object) -> Optional[str]:
        if isinstance(raw, str):
            raw = raw.replace("D:", "")
            for fmt in [
                "%Y%m%d%H%M%S",
                "%Y%m%d%H%M%S%z",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
            ]:
                try:
                    return datetime.strptime(raw[:len(fmt)], fmt).isoformat()
                except (ValueError, IndexError):
                    continue
            if re.match(r"^\d{4}", raw):
                return raw[:10]
        return None

    def _extract_urls(self, text: str) -> List[str]:
        return re.findall(
            r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[\w./?%&=-]*)?",
            text,
        )

    def _extract_emails(self, text: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)

    def _extract_phone_numbers(self, text: str) -> List[str]:
        patterns = [
            r"\+\d{1,3}[\s.-]?\d{3}[\s.-]?\d{3}[\s.-]?\d{4}",
            r"\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}",
            r"\d{3}[\s.-]\d{3}[\s.-]\d{4}",
        ]
        results = []
        for pattern in patterns:
            results.extend(re.findall(pattern, text))
        return list(set(results))

    def _extract_dates(self, text: str) -> List[str]:
        patterns = [
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{2}/\d{2}/\d{4}\b",
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},?\s*\d{4}\b",
            r"\b\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{4}\b",
        ]
        results = []
        for pattern in patterns:
            results.extend(re.findall(pattern, text))
        return list(set(results))

    def _contains_tables(self, text: str) -> bool:
        lines = text.split("\n")
        pipe_count = 0
        for line in lines:
            if "|" in line and ("---" in line or line.strip().startswith("|")):
                pipe_count += 1
                if pipe_count >= 3:
                    return True

        tab_count = 0
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 3:
                tab_count += 1
                if tab_count >= 2:
                    return True

        return False

    def _extract_image_indicators(
        self,
        text: str,
        file_metadata: Optional[Dict[str, object]],
    ) -> bool:
        if file_metadata:
            pages_val = file_metadata.get("pages")
            extracted_text = file_metadata.get("extracted_text", "")
            if isinstance(pages_val, (int, float)) and pages_val > 0:
                if isinstance(extracted_text, str) and len(extracted_text) < 100 and pages_val > 1:
                    return True

        image_markers = re.findall(r"!\[.*?\]\(.*?\)", text)
        if image_markers:
            return True

        image_captions = re.findall(
            r"(?:^|\n)\s*(?:Figure|Fig\.|Image|Illustration)\s+\d+",
            text,
            re.MULTILINE | re.IGNORECASE,
        )
        if image_captions:
            return True

        return False

    def _contains_code_blocks(self, text: str) -> bool:
        code_fences = re.findall(r"```[\s\S]*?```", text)
        if code_fences:
            return True

        indented = re.findall(r"(?:^|\n)(?:    |\t).+", text)
        if len(indented) >= 5:
            total_indented = sum(len(m) for m in indented)
            if total_indented > len(text) * 0.05:
                return True

        return False
