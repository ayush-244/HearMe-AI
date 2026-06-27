import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContextBuilder:
    def __init__(self, max_tokens: int = 4096, max_chunks: int = 20):
        self._max_tokens = max_tokens
        self._max_chunks = max_chunks
        logger.info("ContextBuilder initialized: max_tokens=%d, max_chunks=%d", max_tokens, max_chunks)

    def build(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not chunks:
            return {"chunks": [], "total_tokens": 0, "sources": []}

        deduplicated = self._remove_duplicates(chunks)

        ordered = self._restore_order(deduplicated)

        budgeted = self._apply_token_budget(ordered)

        merged = self._merge_adjacent(budgeted)

        for i, chunk in enumerate(merged):
            chunk["context_index"] = i + 1

        total_tokens = sum(self._estimate_tokens(c.get("text", "") or "") for c in merged)
        sources = self._extract_sources(merged)

        logger.info(
            "Context built: input=%d, after_dedup=%d, after_budget=%d, after_merge=%d, tokens=%d, sources=%d",
            len(chunks), len(deduplicated), len(budgeted), len(merged), total_tokens, len(sources),
        )

        return {
            "chunks": merged,
            "total_tokens": total_tokens,
            "sources": sources,
        }

    def _remove_duplicates(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_ids = set()
        seen_texts = set()
        unique: List[Dict[str, Any]] = []
        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "")
            text = (chunk.get("text", "") or "").strip().lower()[:200]
            if chunk_id and chunk_id in seen_ids:
                continue
            if text and text in seen_texts:
                continue
            if chunk_id:
                seen_ids.add(chunk_id)
            if text:
                seen_texts.add(text)
            unique.append(chunk)
        return unique

    def _restore_order(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return sorted(
            chunks,
            key=lambda c: (
                c.get("document_id", ""),
                c.get("chunk_index", 0),
            ),
        )

    def _apply_token_budget(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        total = 0
        selected: List[Dict[str, Any]] = []
        for chunk in chunks:
            tokens = self._estimate_tokens(chunk.get("text", "") or "")
            if len(selected) >= self._max_chunks:
                break
            if total + tokens > self._max_tokens:
                remaining = self._max_tokens - total
                if remaining > 50:
                    truncated = self._truncate_text(chunk.get("text", "") or "", remaining)
                    chunk["text"] = truncated
                    chunk["truncated"] = True
                    selected.append(chunk)
                break
            selected.append(chunk)
            total += tokens
        return selected

    def _merge_adjacent(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not chunks:
            return []
        merged: List[Dict[str, Any]] = []
        current = dict(chunks[0])
        for next_chunk in chunks[1:]:
            if (
                current.get("document_id") == next_chunk.get("document_id")
                and current.get("section", "") == next_chunk.get("section", "")
                and current.get("chunk_index", 0) + 1 == next_chunk.get("chunk_index", 0)
            ):
                current_text = current.get("text", "") or ""
                next_text = next_chunk.get("text", "") or ""
                combined = current_text + "\n" + next_text
                combined_tokens = self._estimate_tokens(combined)
                if combined_tokens <= self._max_tokens // 2:
                    merged_tokens = []
                    for kw in current.get("keywords", []) or []:
                        if kw not in merged_tokens:
                            merged_tokens.append(kw)
                    for kw in next_chunk.get("keywords", []) or []:
                        if kw not in merged_tokens:
                            merged_tokens.append(kw)
                    current["text"] = combined
                    current["keywords"] = merged_tokens
                    current["chunk_index"] = next_chunk.get("chunk_index", 0)
                    current["page"] = next_chunk.get("page", current.get("page", 0))
                    continue
            merged.append(current)
            current = dict(next_chunk)
        merged.append(current)
        return merged

    def _estimate_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    def _truncate_text(self, text: str, max_tokens: int) -> str:
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    def _extract_sources(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen_docs: Dict[str, Dict[str, Any]] = {}
        for chunk in chunks:
            doc_id = chunk.get("document_id", "")
            if not doc_id:
                continue
            if doc_id not in seen_docs:
                seen_docs[doc_id] = {
                    "document_id": doc_id,
                    "title": chunk.get("title", "") or "Untitled",
                    "sections": [],
                    "pages": set(),
                }
            section = chunk.get("section", "") or "General"
            if section not in seen_docs[doc_id]["sections"]:
                seen_docs[doc_id]["sections"].append(section)
            page = chunk.get("page", 0)
            if page:
                seen_docs[doc_id]["pages"].add(page)
        result = []
        for doc in seen_docs.values():
            doc["pages"] = sorted(doc["pages"]) if doc["pages"] else []
            result.append(doc)
        return result

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @max_tokens.setter
    def max_tokens(self, value: int) -> None:
        self._max_tokens = value

    @property
    def max_chunks(self) -> int:
        return self._max_chunks

    @max_chunks.setter
    def max_chunks(self, value: int) -> None:
        self._max_chunks = value
