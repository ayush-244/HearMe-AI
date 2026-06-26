import logging
import re
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


STOP_WORDS: set = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "need",
    "dare", "ought", "used", "this", "that", "these", "those", "it", "its",
    "they", "them", "their", "we", "us", "our", "you", "your", "he", "him",
    "his", "she", "her", "hers", "i", "me", "my", "mine", "not", "no",
    "nor", "neither", "so", "such", "just", "about", "above", "after",
    "again", "against", "all", "also", "any", "because", "before", "between",
    "both", "each", "few", "more", "most", "much", "neither", "nor",
    "other", "same", "some", "than", "too", "very", "into", "over", "under",
    "up", "down", "out", "off", "then", "once", "here", "there", "when",
    "where", "why", "how", "what", "which", "who", "whom", "whose",
    "during", "through", "without", "within", "along", "around", "behind",
    "below", "beneath", "beside", "between", "beyond", "inside", "outside",
    "upon", "while", "if", "else", "than",
}


BOILERPLATE_PATTERNS: List[str] = [
    r"copyright\s+©?\s*\d{4}",
    r"all rights reserved",
    r"confidential",
    r"page\s+\d+\s+of\s+\d+",
    r"powered by",
    r"generated on",
    r"created with",
    r"disclaimer",
    r"terms\s+and\s+conditions",
    r"privacy\s+policy",
    r"http\S+",
    r"www\.\S+",
]


class DocumentAnalyzer:
    def __init__(
        self,
        classifier=None,
        section_parser=None,
        metadata_extractor=None,
    ):
        from .document_classifier import DocumentClassifier
        from .section_parser import SectionParser
        from .metadata_extractor import MetadataExtractor

        self._classifier = classifier or DocumentClassifier()
        self._section_parser = section_parser or SectionParser()
        self._metadata_extractor = metadata_extractor or MetadataExtractor()

    def analyze(
        self,
        document_id: str,
        text: str,
        filename: str,
        file_metadata: Optional[Dict[str, object]] = None,
        pages: int = 0,
        language_service=None,
    ) -> dict:
        logger.info("Analysis started: document_id=%s, filename=%s, text_length=%d", document_id, filename, len(text))

        start = time.time()

        word_count = len(text.split())
        char_count = len(text)

        doc_type, confidence = self._classifier.classify(text, filename, file_metadata)

        logger.info("Classification: type=%s, confidence=%.1f, confidence_level=%s", doc_type, confidence, self._classifier.get_confidence_label(confidence))

        language_code = "en"
        language_name = "English"
        if language_service is not None:
            language_code = language_service.detect(text)
            language_name = language_service.get_language_name(language_code)

        logger.info("Language: code=%s, name=%s", language_code, language_name)

        sections = self._section_parser.parse(text, doc_type)

        logger.info("Sections: count=%d", len(sections))

        metadata = self._metadata_extractor.extract(text, file_metadata, filename)

        reading_time = max(1, round(word_count / 220))

        keywords = self._extract_keywords(text)

        logger.info("Keywords: count=%d", len(keywords))

        summary_preview = self._generate_summary_preview(text)

        page_count = pages or max(1, round(len(text) / 3000))

        analysis = {
            "document_id": document_id,
            "title": metadata.get("title", "Untitled"),
            "document_type": doc_type,
            "classification_confidence": confidence,
            "language": language_name,
            "language_code": language_code,
            "page_count": page_count,
            "word_count": word_count,
            "character_count": char_count,
            "estimated_reading_time_minutes": reading_time,
            "sections": [s.to_dict() for s in sections],
            "contains_tables": metadata.get("contains_tables", False),
            "contains_images": metadata.get("contains_images", False),
            "contains_code_blocks": metadata.get("contains_code_blocks", False),
            "contains_urls": metadata.get("contains_urls", False),
            "contains_emails": metadata.get("contains_emails", False),
            "contains_phone_numbers": metadata.get("contains_phone_numbers", False),
            "contains_dates": metadata.get("contains_dates", False),
            "keywords": keywords,
            "summary_preview": summary_preview,
            "extracted_metadata": {
                "title": metadata.get("title", "Untitled"),
                "author": metadata.get("author", ""),
                "creation_date": metadata.get("creation_date"),
                "modification_date": metadata.get("modification_date"),
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        elapsed = time.time() - start
        logger.info(
            "Analysis completed: document_id=%s, type=%s, sections=%d, keywords=%d, reading_time=%d min, duration=%.2fs",
            document_id, doc_type, len(sections), len(keywords), reading_time, elapsed,
        )

        return analysis

    def _extract_keywords(self, text: str, top_n: int = 15) -> List[str]:
        if not text or not text.strip():
            return []

        sentences = re.split(r"[.!?\n]+", text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        phrase_scores: Counter = Counter()

        for sentence in sentences:
            words = re.findall(r"\b[a-zA-Z]{3,}\b", sentence.lower())
            words = [w for w in words if w not in STOP_WORDS]

            if len(words) < 2:
                continue

            for i in range(len(words) - 1):
                phrase = " ".join(words[i:i+2])
                if len(phrase) > 3:
                    phrase_scores[phrase] += 1

            for i in range(len(words) - 2):
                phrase = " ".join(words[i:i+3])
                if len(phrase) > 5:
                    phrase_scores[phrase] += 1

        for phrase in list(phrase_scores):
            words_in = phrase.split()
            if all(w in STOP_WORDS for w in words_in):
                del phrase_scores[phrase]

        top_phrases = [p for p, _ in phrase_scores.most_common(top_n)]

        return top_phrases[:top_n]

    def _generate_summary_preview(self, text: str, max_chars: int = 500) -> str:
        lines = text.strip().split("\n")
        meaningful_lines = []

        for line in lines:
            clean = line.strip().strip("#*_ ").strip()
            if not clean or len(clean) < 20:
                continue
            if self._is_boilerplate(clean):
                continue
            if re.match(r"^[-=]{3,}$", clean):
                continue
            if re.match(r"^\d+\s*$", clean):
                continue
            meaningful_lines.append(clean)

        if not meaningful_lines:
            preview = text[:max_chars].strip()
            if len(text) > max_chars:
                preview = preview[:preview.rfind(" ")] + "..."
            return preview

        preview = ""
        for line in meaningful_lines:
            if len(preview) + len(line) + 1 > max_chars:
                remaining = max_chars - len(preview)
                if remaining > 20:
                    preview += " " + line[:remaining]
                    preview = preview[:preview.rfind(" ")]
                break
            if preview:
                preview += " "
            preview += line

        return preview.strip()[:max_chars]

    def _is_boilerplate(self, text: str) -> bool:
        lower = text.lower()
        for pattern in BOILERPLATE_PATTERNS:
            if re.search(pattern, lower):
                return True
        return False
