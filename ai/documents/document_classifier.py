import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


RESEARCH_PAPER_HEADINGS = {
    "abstract", "introduction", "background", "related work",
    "methodology", "methods", "approach", "experiment",
    "results", "discussion", "conclusion", "references",
    "literature review", "proposed method", "evaluation",
}

RESUME_HEADINGS = {
    "education", "skills", "experience", "work experience",
    "projects", "certifications", "publications", "summary",
    "objective", "professional experience", "technical skills",
    "employment", "qualifications", "interests",
}

BOOK_HEADINGS = {
    "chapter", "appendix", "preface", "acknowledgements",
    "introduction", "epilogue", "prologue", "index",
    "bibliography", "table of contents",
}

REPORT_HEADINGS = {
    "executive summary", "introduction", "findings",
    "analysis", "recommendations", "appendix",
    "methodology", "scope", "limitations", "conclusion",
}

INVOICE_KEYWORDS = {
    "invoice", "invoice number", "invoice date", "due date",
    "total", "subtotal", "tax", "amount due", "bill to",
    "payment terms", "purchase order", "item", "quantity",
    "unit price", "balance due", "receipt",
}

PRESENTATION_HEADINGS = {
    "agenda", "overview", "summary", "key takeaways",
    "next steps", "thank you", "q&a", "outline",
}

MANUAL_HEADINGS = {
    "installation", "configuration", "usage", "troubleshooting",
    "specifications", "safety", "maintenance", "warranty",
    "getting started", "quick start", "faq", "setup",
}

ARTICLE_HEADINGS = {
    "summary", "conclusion", "related articles",
    "see also", "byline", "dateline",
}

NOTES_HEADINGS = {
    "lecture", "topic", "summary", "key points",
    "note", "definition", "example", "important",
}


class DocumentClassifier:
    TYPE_SCORES: Dict[str, List[str]] = {
        "research_paper": list(RESEARCH_PAPER_HEADINGS),
        "resume": list(RESUME_HEADINGS),
        "book": list(BOOK_HEADINGS),
        "report": list(REPORT_HEADINGS),
        "invoice": list(INVOICE_KEYWORDS),
        "presentation": list(PRESENTATION_HEADINGS),
        "manual": list(MANUAL_HEADINGS),
        "article": list(ARTICLE_HEADINGS),
        "notes": list(NOTES_HEADINGS),
    }

    def classify(
        self,
        text: str,
        filename: str,
        metadata: Optional[Dict[str, object]] = None,
    ) -> Tuple[str, float]:
        scores: Dict[str, float] = {}
        for doc_type in self.TYPE_SCORES:
            scores[doc_type] = 0.0

        text_lower = text.lower()
        filename_lower = filename.lower()

        self._score_filenames(scores, filename_lower)
        self._score_heading_patterns(scores, text_lower)
        self._score_keywords(scores, text_lower)
        self._score_invoice_patterns(scores, text_lower)
        self._score_chapter_patterns(scores, text_lower)
        self._score_code_blocks(scores, text)

        if metadata:
            self._score_metadata(scores, metadata, text_lower)

        book_chapters = len(re.findall(r"(?:^|\n)\s*(?:chapter|lecture)\s+\d+", text_lower))
        if book_chapters >= 3:
            scores["book"] = max(scores.get("book", 0), book_chapters * 5)

        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]

        if best_score <= 0:
            best_type = "unknown"
            best_score = 0.0
        elif best_type == "invoice":
            scores["report"] *= 0.5

        logger.debug(
            "Classification scores: %s | best=%s (%.1f)",
            {k: round(v, 1) for k, v in sorted(scores.items(), key=lambda x: -x[1])},
            best_type,
            best_score,
        )

        return best_type, best_score

    def _score_filenames(self, scores: Dict[str, float], filename: str) -> None:
        fn = filename
        if fn.startswith("resume") or fn.startswith("cv"):
            scores["resume"] += 20
        if "invoice" in fn or "receipt" in fn or "bill" in fn:
            scores["invoice"] += 20
        if "report" in fn:
            scores["report"] += 10
        if "manual" in fn or "guide" in fn or "handbook" in fn:
            scores["manual"] += 15
        if "paper" in fn or "article" in fn:
            scores["research_paper"] += 10
        if "presentation" in fn or "slides" in fn or "deck" in fn:
            scores["presentation"] += 15
        if "notes" in fn or fn.endswith("notes"):
            scores["notes"] += 10
        if "chapter" in fn or "book" in fn:
            scores["book"] += 10

    def _score_heading_patterns(self, scores: Dict[str, float], text: str) -> None:
        for doc_type, headings in self.TYPE_SCORES.items():
            for heading in headings:
                count = len(re.findall(
                    r"(?:^|\n)\s*"
                    + re.escape(heading)
                    + r"\s*[\n:]",
                    text,
                    re.MULTILINE,
                ))
                if count > 0:
                    scores[doc_type] += count * 3

    def _score_keywords(self, scores: Dict[str, float], text: str) -> None:
        lines = text.split("\n")
        for line in lines:
            clean = line.strip().strip(":#").strip().lower()
            if not clean:
                continue
            if clean in RESUME_HEADINGS:
                scores["resume"] += 2

    def _score_invoice_patterns(self, scores: Dict[str, float], text: str) -> None:
        if re.search(r"\$\s*[\d,]+\.\d{2}", text):
            scores["invoice"] += 3
        if re.search(r"(?:total|amount due|balance)\s*[:$]?\s*[\d,]+\.\d{2}", text, re.IGNORECASE):
            scores["invoice"] += 5
        if re.search(r"(?:invoice|receipt)\s*(?:#|number|no|:)\s*\w+", text, re.IGNORECASE):
            scores["invoice"] += 5

    def _score_chapter_patterns(self, scores: Dict[str, float], text: str) -> None:
        chapters = re.findall(r"(?:^|\n)\s*(?:chapter|lecture|part)\s+\d+", text.lower())
        if len(chapters) >= 2:
            scores["book"] += len(chapters) * 5

    def _score_code_blocks(self, scores: Dict[str, float], text: str) -> None:
        code_blocks = list(re.finditer(r"```[\s\S]*?```", text))
        if code_blocks:
            total_code = sum(len(m.group()) for m in code_blocks)
            code_ratio = total_code / max(len(text), 1)
            if code_ratio > 0.05:
                scores["manual"] += 5

    def _score_metadata(
        self,
        scores: Dict[str, float],
        metadata: Dict[str, object],
        text: str,
    ) -> None:
        title = ""
        if isinstance(metadata.get("title"), str):
            title = metadata["title"].lower()
        author = ""
        if isinstance(metadata.get("author"), str):
            author = metadata["author"].lower()

        if title and ("resume" in title or "cv" in title):
            scores["resume"] += 15
        if title and "invoice" in title:
            scores["invoice"] += 15
        if title and "report" in title:
            scores["report"] += 10

        if author and author != "unknown":
            scores["resume"] += 3

        if "keywords" in metadata and isinstance(metadata["keywords"], list):
            kw_text = " ".join(str(k).lower() for k in metadata["keywords"])
            if any(k in kw_text for k in ["research", "paper", "study"]):
                scores["research_paper"] += 5

    def get_confidence_label(self, score: float) -> str:
        if score >= 20:
            return "high"
        elif score >= 10:
            return "medium"
        elif score > 0:
            return "low"
        return "none"
