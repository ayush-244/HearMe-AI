import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class CitationBuilder:
    @staticmethod
    def build_citations(results: List[Dict[str, Any]]) -> List[str]:
        citations = []
        for i, r in enumerate(results):
            title = r.get("title", "") or "Untitled"
            section = r.get("section", "") or "General"
            page = r.get("page", 0)
            chunk_id = r.get("chunk_id", "")
            score = r.get("final_score", r.get("score", 0.0))

            citation = f"{title}"
            if section and section != title:
                citation += f", {section}"
            if page:
                citation += f", Page {page}"
            citation += f" (Chunk {chunk_id[:8]}…, Score {score:.2f})"

            citations.append(citation)

        return citations

    @staticmethod
    def format_citations_markdown(results: List[Dict[str, Any]]) -> str:
        lines = []
        for i, r in enumerate(results):
            title = r.get("title", "") or "Untitled"
            section = r.get("section", "") or "General"
            page = r.get("page", 0)
            score = r.get("final_score", r.get("score", 0.0))
            preview = (r.get("text", "") or "")[:150]

            lines.append(f"**{i+1}. {title}**")
            if section:
                lines.append(f"   *Section: {section}*")
            if page:
                lines.append(f"   *Page: {page}*")
            lines.append(f"   *Relevance: {score:.2f}*")
            lines.append(f"   > {preview}")
            lines.append("")

        return "\n".join(lines)
