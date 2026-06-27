import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class QueryParser:
    @staticmethod
    def parse(raw_query: str) -> Dict:
        if not raw_query or not raw_query.strip():
            return {
                "clean_query": "",
                "keywords": [],
                "phrases": [],
                "filters": {},
                "numbers": [],
                "has_date": False,
            }

        text = raw_query.strip()

        quoted_phrases = re.findall(r'"([^"]*)"', text)
        for phrase in quoted_phrases:
            text = text.replace(f'"{phrase}"', "")

        text = re.sub(r"\s+", " ", text).strip()

        filters = QueryParser._extract_filters(text)

        words = text.lower().split()
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "out", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "each", "every", "both", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only",
            "own", "same", "so", "than", "too", "very", "just", "because",
            "and", "but", "or", "if", "while", "about", "up", "it", "its",
            "this", "that", "these", "those", "i", "me", "my", "myself",
            "we", "our", "ours", "ourselves", "you", "your", "yours",
            "he", "him", "his", "she", "her", "hers", "they", "them",
            "their", "theirs", "what", "which", "who", "whom",
        }
        keywords = [w for w in words if w not in stop_words and len(w) > 1]

        numbers = QueryParser._extract_numbers(text)

        has_date = bool(re.search(r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}", text))

        return {
            "clean_query": text,
            "keywords": keywords,
            "phrases": quoted_phrases,
            "filters": filters,
            "numbers": numbers,
            "has_date": has_date,
        }

    @staticmethod
    def _extract_filters(text: str) -> Dict[str, str]:
        filters = {}
        patterns = [
            (r"\blang(?:uage)?:(\w+)", "language"),
            (r"\btype:(\w+)", "document_type"),
            (r"\bworkspace:(\w+)", "workspace_id"),
            (r"\bdoc(?:ument)?:([\w-]+)", "document_id"),
            (r"\bsection:([\w-]+)", "section"),
        ]
        for pattern, key in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                filters[key] = match.group(1)
        return filters

    @staticmethod
    def _extract_numbers(text: str) -> List[float]:
        return [float(n) for n in re.findall(r"\d+\.?\d*", text) if n.strip()]
