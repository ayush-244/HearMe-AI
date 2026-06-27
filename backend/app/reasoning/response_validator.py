import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

HALLUCINATION_INDICATORS: List[str] = [
    r"\bi\s+think\b",
    r"\bi\s+believe\b",
    r"\bin\s+my\s+opinion\b",
    r"\bi\s+guess\b",
    r"\bi\s+suppose\b",
    r"\bi\s+would\s+(imagine|assume|speculate)\b",
    r"\bit\s+seems\s+(like\s+)?(that\s+)?",
    r"\bi'm\s+not\s+(completely\s+)?sure",
    r"\bi\s+could\s+be\s+wrong",
    r"\bi\s+don't\s+(really\s+)?know",
    r"\bas\s+far\s+as\s+i\s+know",
    r"\bto\s+the\s+best\s+of\s+my\s+knowledge",
    r"\bi\s+may\s+be\s+mistaken",
    r"\bi\s+(would\s+)?say\s+that",
]

HALLUCINATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in HALLUCINATION_INDICATORS]

UNSUPPORTED_CLAIM_PATTERNS = [
    r"according\s+to\s+(my\s+)?(research|knowledge|understanding|analysis)",
    r"based\s+on\s+(my\s+)?(research|knowledge|understanding|analysis)",
    r"i\s+found\s+(that|out)",
    r"i\s+have\s+(read|seen|heard|learned)",
    r"i\s+recall\s+that",
    r"i\s+remember\s+that",
    r"studies\s+(show|suggest|indicate)",
    r"research\s+(shows|suggests|indicates)",
    r"experts\s+(say|claim|believe)",
    r"it\s+is\s+(widely\s+)?(known|believed|accepted|understood)",
    r"everyone\s+knows",
]

UNSUPPORTED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in UNSUPPORTED_CLAIM_PATTERNS]


class ResponseValidator:
    def __init__(self):
        logger.info("ResponseValidator initialized")

    def validate(self, response: str, chunks: List[Dict[str, Any]], citations: List[str]) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "passed": True,
            "issues": [],
            "empty_response": False,
            "hallucination_indicators": [],
            "missing_citations": False,
            "unsupported_claims": [],
            "broken_formatting": False,
        }

        if not response or not response.strip():
            result["passed"] = False
            result["empty_response"] = True
            result["issues"].append("Empty response")
            return result

        for pattern in HALLUCINATION_PATTERNS:
            match = pattern.search(response)
            if match:
                result["hallucination_indicators"].append(match.group())
                result["issues"].append(f"Hallucination indicator: '{match.group()}'")

        if citations:
            has_citation = False
            for citation in citations:
                for part in citation.split(" › "):
                    part = part.strip().rstrip("]")
                    if len(part) > 3 and part.lower() in response.lower():
                        has_citation = True
                        break
                if has_citation:
                    break
            if not has_citation:
                has_source_ref = bool(re.search(r"\[Source\s+\d+\]", response))
                if not has_source_ref:
                    result["missing_citations"] = True
                    result["issues"].append("Response does not reference any provided citations")

        for pattern in UNSUPPORTED_PATTERNS:
            match = pattern.search(response)
            if match:
                result["unsupported_claims"].append(match.group())
                result["issues"].append(f"Unsupported claim pattern: '{match.group()}'")

        if result["hallucination_indicators"] or result["unsupported_claims"]:
            result["passed"] = False

        if not result["issues"]:
            logger.info("Response validation passed")
        else:
            logger.warning("Response validation issues: %s", result["issues"])

        return result

    def is_knowledge_gap_response(self, response: str) -> bool:
        gap_phrases = [
            "couldn't find enough information",
            "cannot find enough information",
            "can't find enough information",
            "no enough information",
            "insufficient information",
            "no relevant information",
            "no relevant documents",
            "not found in the uploaded documents",
            "not found in the provided documents",
            "not covered in the uploaded documents",
            "not covered in the provided documents",
            "don't have enough information",
            "do not have enough information",
        ]
        response_lower = response.lower()
        return any(phrase in response_lower for phrase in gap_phrases)
