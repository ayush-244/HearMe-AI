import logging
import re
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Section:
    name: str
    start_offset: int
    end_offset: int
    estimated_page: int

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "start_offset": self.start_offset,
            "end_offset": self.end_offset,
            "estimated_page": self.estimated_page,
        }


ACADEMIC_SECTIONS = [
    r"abstract",
    r"introduction",
    r"background",
    r"related\s*work",
    r"literature\s*review",
    r"methodology",
    r"methods?",
    r"approach",
    r"proposed\s*approach",
    r"experiment",
    r"experimental\s*setup",
    r"results?",
    r"findings",
    r"discussion",
    r"conclusion",
    r"references?",
    r"bibliography",
    r"appendix",
    r"acknowledgements?",
    r"limitations",
    r"future\s*work",
]

RESUME_SECTIONS = [
    r"education",
    r"skills?",
    r"technical\s*skills?",
    r"experience",
    r"work\s*experience",
    r"professional\s*experience",
    r"projects?",
    r"certifications?",
    r"publications?",
    r"summary",
    r"objective",
    r"employment",
    r"qualifications?",
    r"languages?",
    r"interests?",
    r"volunteer",
]

BOOK_SECTIONS = [
    r"chapter\s+\d+",
    r"appendix\s+\w?",
    r"preface",
    r"introduction",
    r"prologue",
    r"epilogue",
    r"index",
    r"bibliography",
    r"table\s*of\s*contents",
    r"acknowledgements?",
]

REPORT_SECTIONS = [
    r"executive\s*summary",
    r"introduction",
    r"background",
    r"findings?",
    r"analysis",
    r"recommendations?",
    r"conclusion",
    r"appendix",
    r"methodology",
    r"scope",
    r"limitations?",
    r"references?",
]

MANUAL_SECTIONS = [
    r"installation",
    r"setup",
    r"configuration",
    r"getting\s*started",
    r"quick\s*start",
    r"usage",
    r"troubleshooting",
    r"specifications?",
    r"safety",
    r"maintenance",
    r"warranty",
    r"faq",
    r"uninstallation",
]

SECTION_PATTERNS_BY_TYPE = {
    "research_paper": ACADEMIC_SECTIONS,
    "article": ACADEMIC_SECTIONS,
    "resume": RESUME_SECTIONS,
    "book": BOOK_SECTIONS,
    "report": REPORT_SECTIONS,
    "manual": MANUAL_SECTIONS,
    "presentation": ACADEMIC_SECTIONS,
    "notes": [],
    "invoice": [],
    "unknown": [],
}


class SectionParser:
    CHARS_PER_PAGE = 3000

    def parse(
        self,
        text: str,
        document_type: str = "unknown",
    ) -> List[Section]:
        patterns = SECTION_PATTERNS_BY_TYPE.get(document_type, [])
        if not patterns:
            patterns = self._detect_generic_headings(text)

        matches: List[Tuple[int, int, str]] = []
        for pattern in patterns:
            for match in re.finditer(
                r"(?:^|\n)\s*(" + pattern + r")\s*[\n:]",
                text,
                re.IGNORECASE | re.MULTILINE,
            ):
                name = match.group(1).strip().strip(":#").strip()
                start = match.start()
                end = match.end()
                matches.append((start, end, name))

        matches.sort(key=lambda x: x[0])

        sections = self._build_sections(matches, text)
        return sections

    def _detect_generic_headings(self, text: str) -> List[str]:
        generic_headings = []
        heading_patterns = re.findall(
            r"(?:^|\n)([A-Z][A-Za-z\s]{2,50})\s*\n[-=]+\s*(?:\n|$)",
            text,
            re.MULTILINE,
        )
        for h in heading_patterns:
            clean = h.strip()
            if len(clean) >= 3:
                generic_headings.append(re.escape(clean))

        numbered = re.findall(
            r"(?:^|\n)(\d+(?:\.\d+)*\.?\s+[A-Z][A-Za-z\s]{2,50})\s*(?:\n|$)",
            text,
            re.MULTILINE,
        )
        for h in numbered:
            name = re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", h).strip()
            if len(name) >= 3:
                generic_headings.append(re.escape(name))

        return generic_headings[:20]

    def _build_sections(
        self,
        matches: List[Tuple[int, int, str]],
        text: str,
    ) -> List[Section]:
        if not matches:
            return []

        sections: List[Section] = []
        for i, (start, _end, name) in enumerate(matches):
            if i + 1 < len(matches):
                end_offset = matches[i + 1][0]
            else:
                end_offset = len(text)

            estimated_page = max(1, start // self.CHARS_PER_PAGE)

            sections.append(
                Section(
                    name=name,
                    start_offset=start,
                    end_offset=end_offset,
                    estimated_page=estimated_page,
                )
            )

        return sections
