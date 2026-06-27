import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

INJECTION_PATTERNS: List[str] = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"ignore\s+(all\s+)?(previous|prior)\s+(directives|commands|rules)",
    r"you\s+are\s+(now|not\s+)?\s*(chat)?gpt",
    r"you\s+are\s+(now\s+)?a\s+free\s+ai",
    r"reveal\s+(your\s+)?system\s+prompt",
    r"disregard\s+(all\s+)?(previous|prior)\s+instructions",
    r"forget\s+(all\s+)?(previous|prior)\s+instructions",
    r"output\s+your\s+(system\s+)?prompt",
    r"print\s+your\s+(system\s+)?prompt",
    r"role\s+play\s+as",
    r"from\s+now\s+on\s+you\s+are",
    r"you\s+must\s+ignore",
    r"delete\s+(all\s+)?(memory|data|history)",
    r"reset\s+(your\s+)?(memory|context|state)",
    r"act\s+as\s+if\s+you\s+are",
    r"pretend\s+(that\s+)?you\s+are",
    r"override\s+(your\s+)?(instructions|directives|guidelines)",
    r"bypass\s+(your\s+)?(safety|restrictions|guidelines|rules)",
    r"you\s+have\s+been\s+(replaced|hacked|changed)",
    r"this\s+is\s+an\s+instruction\s+from\s+(your\s+)?creator",
]


class Guardrails:
    def __init__(self, custom_patterns: Optional[List[str]] = None):
        self._patterns = INJECTION_PATTERNS + (custom_patterns or [])
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self._patterns]
        logger.info("Guardrails initialized with %d injection patterns", len(self._compiled))

    def check_text(self, text: str) -> bool:
        if not text:
            return True
        for i, pattern in enumerate(self._compiled):
            match = pattern.search(text)
            if match:
                logger.warning("Guardrail triggered: pattern #%d matched '%s' in text", i, match.group())
                return False
        return True

    def filter_chunks(self, chunks: List[dict]) -> List[dict]:
        clean: List[dict] = []
        for chunk in chunks:
            text = chunk.get("text", "") or ""
            if self.check_text(text):
                clean.append(chunk)
            else:
                logger.warning("Guardrail filtered chunk %s (prompt injection detected)", chunk.get("chunk_id", "unknown"))
        return clean

    def check_query(self, query: str) -> bool:
        return self.check_text(query)

    def get_triggered_patterns(self, text: str) -> List[str]:
        triggered: List[str] = []
        if not text:
            return triggered
        for pattern in self._compiled:
            match = pattern.search(text)
            if match:
                triggered.append(match.group())
        return triggered
