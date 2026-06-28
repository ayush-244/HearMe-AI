import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

PRONOUN_PATTERNS = [
    (re.compile(r"\b(it|that|this)\b", re.IGNORECASE), "single"),
    (re.compile(r"\b(they|them|these|those)\b", re.IGNORECASE), "plural"),
]

PAGE_REF_PATTERN = re.compile(r"\bpage\s+(\d+)\b", re.IGNORECASE)
DOC_REF_PATTERN = re.compile(r"\b(the\s+)?(document|file|resume|paper|article|report|pdf)\b", re.IGNORECASE)
SECTION_REF_PATTERN = re.compile(r"\b(section|chapter|part)\s+(\d+)\b", re.IGNORECASE)
COMPARATIVE_PATTERN = re.compile(r"\b(compare|contrast|versus|vs\.?)\s+(it|this|that|them)\b", re.IGNORECASE)
SHORTEN_PATTERN = re.compile(r"\b(shorter|shorten|tighter|condense|summarize|simplify)\b", re.IGNORECASE)
CONTINUE_PATTERN = re.compile(r"\b(continue|go\s+on|keep\s+going|more|elaborate|expand|further)\b", re.IGNORECASE)
EXPLAIN_PATTERN = re.compile(r"\b(explain|clarify|elaborate|rewrite|rephrase|paraphrase|translate)\b", re.IGNORECASE)

STOP_WORDS = {"a", "an", "the", "is", "are", "was", "were", "it", "this", "that", "these", "those", "to", "for", "of", "in", "on", "at", "by", "with", "from", "about"}


@dataclass
class ResolvedQuery:
    original: str
    resolved: str
    references: List[str] = field(default_factory=list)
    page_refs: List[int] = field(default_factory=list)
    comparative_target: Optional[str] = None
    action: Optional[str] = None
    had_reference: bool = False


class ReferenceResolver:
    def __init__(self):
        logger.info("ReferenceResolver initialized")

    def resolve(self, query: str, last_question: str = "", last_answer: str = "", current_topic: str = "", attached_documents: Optional[List[Dict]] = None) -> ResolvedQuery:
        q_lower = query.strip().lower()
        if not q_lower:
            return ResolvedQuery(original=query, resolved=query)

        refs = []
        page_refs = []
        comparative_target = None
        action = None
        had_reference = False

        page_matches = PAGE_REF_PATTERN.findall(q_lower)
        if page_matches:
            page_refs = [int(p) for p in page_matches]
            refs.extend([f"page {p}" for p in page_refs])
            had_reference = True

        if SECTION_REF_PATTERN.search(q_lower):
            had_reference = True
            refs.append("section")

        doc_match = DOC_REF_PATTERN.search(q_lower)
        if doc_match:
            had_reference = True
            doc_word = doc_match.group(0).strip()
            refs.append(doc_word)

        has_pronoun = any(p[0].search(q_lower) for p in PRONOUN_PATTERNS)
        if has_pronoun:
            had_reference = True
            refs.append("pronoun")

        comp_match = COMPARATIVE_PATTERN.search(q_lower)
        if comp_match:
            comparative_target = current_topic or last_question or "previous topic"

        for pattern_name, pat in [("shorten", SHORTEN_PATTERN), ("continue", CONTINUE_PATTERN), ("explain", EXPLAIN_PATTERN)]:
            if pat.search(q_lower):
                action = pattern_name

        resolved = self._build_resolved(query, q_lower, had_reference, refs, last_question, last_answer, current_topic)

        logger.debug("Resolved query: '%s' -> '%s' (refs=%s, pages=%s)", query[:40], resolved[:60], refs, page_refs)

        return ResolvedQuery(
            original=query,
            resolved=resolved,
            references=refs,
            page_refs=page_refs,
            comparative_target=comparative_target,
            action=action,
            had_reference=had_reference,
        )

    def _build_resolved(self, query: str, q_lower: str, had_reference: bool, refs: List[str], last_question: str, last_answer: str, current_topic: str) -> str:
        if not had_reference:
            return query

        if not last_question and not current_topic:
            return query

        topic_phrase = current_topic or last_question.split("?")[0][:80] if last_question else ""

        resolved = query

        if re.search(r'\b(it|this|that)\b', q_lower):
            if topic_phrase:
                resolved = re.sub(
                    r'\b(it|this|that)\b',
                    f'"{topic_phrase}"',
                    resolved,
                    flags=re.IGNORECASE,
                    count=1,
                )

        if re.search(r'\b(they|them|these|those)\b', q_lower):
            if topic_phrase:
                resolved = re.sub(
                    r'\b(they|them|these|those)\b',
                    f'"{topic_phrase}"',
                    resolved,
                    flags=re.IGNORECASE,
                    count=1,
                )

        return resolved

    def extract_keywords(self, text: str, max_words: int = 5) -> List[str]:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        filtered = [w for w in words if w not in STOP_WORDS]
        seen = set()
        unique = []
        for w in filtered:
            if w not in seen:
                seen.add(w)
                unique.append(w)
        return unique[:max_words]


from typing import Dict as DictType
