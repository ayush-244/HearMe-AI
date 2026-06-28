import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class CitationManager:
    def __init__(self, style: str = "inline"):
        self._style = style
        self._used_chunks: List[Dict[str, Any]] = []
        logger.info("CitationManager initialized: style=%s", style)

    def track_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        self._used_chunks = list(chunks)
        logger.debug("Tracking %d chunks for citations", len(chunks))

    def reset(self) -> None:
        self._used_chunks.clear()
        logger.debug("CitationManager reset")

    def build_citations(self) -> List[str]:
        citations: List[str] = []
        seen: set = set()
        for chunk in self._used_chunks:
            chunk_id = chunk.get("chunk_id", "")
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            citation = self._format_citation(chunk)
            if citation:
                citations.append(citation)
        return citations

    def build_sources(self) -> List[Dict[str, Any]]:
        seen_docs: Dict[str, Dict[str, Any]] = {}
        for chunk in self._used_chunks:
            doc_id = chunk.get("document_id", "")
            if not doc_id:
                continue
            if doc_id not in seen_docs:
                seen_docs[doc_id] = {
                    "document_id": doc_id,
                    "title": chunk.get("title", "") or "Untitled",
                    "sections": [],
                    "chunks": [],
                }
            section = chunk.get("section", "") or "General"
            if section not in seen_docs[doc_id]["sections"]:
                seen_docs[doc_id]["sections"].append(section)
            seen_docs[doc_id]["chunks"].append({
                "chunk_id": chunk.get("chunk_id", ""),
                "section": section,
                "page": chunk.get("page", 0),
                "score": chunk.get("score", 0.0),
            })
        return list(seen_docs.values())

    def format_inline(self, chunk: Dict[str, Any]) -> str:
        parts = []
        title = chunk.get("title", "") or "Untitled"
        parts.append(title)
        section = chunk.get("section", "") or ""
        if section and section.lower() != title.lower():
            parts.append(section)
        page = chunk.get("page", 0)
        if page:
            parts.append(f"Page {page}")
        return f"[{' › '.join(parts)}]"

    def format_markdown(self, chunk: Dict[str, Any]) -> str:
        parts = []
        title = chunk.get("title", "") or "Untitled"
        parts.append(f"**{title}**")
        section = chunk.get("section", "") or ""
        if section and section.lower() != title.lower():
            parts.append(f"*{section}*")
        page = chunk.get("page", 0)
        if page:
            parts.append(f"Page {page}")
        chunk_id = chunk.get("chunk_id", "")
        if chunk_id:
            parts.append(f"`{chunk_id[:8]}…`")
        score = chunk.get("score", 0.0)
        if score:
            parts.append(f"score={score:.2f}")
        return ", ".join(parts)

    def _format_citation(self, chunk: Dict[str, Any]) -> str:
        if self._style == "markdown":
            return self.format_markdown(chunk)
        return self.format_inline(chunk)

    def check_response_citations(self, response: str, citations: List[str]) -> bool:
        if not citations:
            return True
        for citation in citations:
            for part in citation.split(" › "):
                part = part.strip()
                if len(part) > 3 and part not in response:
                    return False
        return True

    @property
    def style(self) -> str:
        return self._style

    @style.setter
    def style(self, value: str) -> None:
        self._style = value
