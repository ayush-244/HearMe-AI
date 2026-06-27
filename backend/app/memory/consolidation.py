import logging
import re
import uuid
from typing import Dict, List, Optional, Set, Tuple

from .memory_models import MemoryEntry, MemoryType

logger = logging.getLogger(__name__)

_TOPIC_WORDS = re.compile(r"\b(python|java|rust|go|javascript|typescript|"
                          r"react|angular|vue|fastapi|django|flask|"
                          r"docker|kubernetes|aws|gcp|azure|"
                          r"linux|mac|windows|vscode|pycharm|vim|"
                          r"sql|nosql|postgres|mysql|mongo|redis|"
                          r"ai|ml|dl|nlp|llm|rag|api|rest|graphql)\b",
                          re.IGNORECASE)


class ConsolidationEngine:
    def __init__(self, max_merge_count: int = 10, min_importance: float = 0.2):
        self._max_merge_count = max_merge_count
        self._min_importance = min_importance
        logger.info("ConsolidationEngine initialized: max_merge=%d, min_imp=%.2f", max_merge_count, min_importance)

    def consolidate(self, entries: List[MemoryEntry]) -> List[MemoryEntry]:
        if not entries:
            return []

        factual = [e for e in entries if e.type in (MemoryType.SEMANTIC, MemoryType.PREFERENCE)]
        other = [e for e in entries if e.type not in (MemoryType.SEMANTIC, MemoryType.PREFERENCE)]

        if not factual:
            return entries

        clusters = self._cluster_by_topic(factual, self._max_merge_count)

        all_merged_ids: Set[str] = set()
        result: List[MemoryEntry] = list(other)

        for cluster in clusters:
            if len(cluster) < 2:
                for entry in cluster:
                    if entry.memory_id not in all_merged_ids:
                        result.append(entry)
                        all_merged_ids.add(entry.memory_id)
                continue

            new_entry = self._merge_cluster(cluster)
            if new_entry:
                result.append(new_entry)
                for original in cluster:
                    all_merged_ids.add(original.memory_id)
                logger.info(
                    "Consolidated %d memories into '%s' (imp=%.2f)",
                    len(cluster), new_entry.summary[:50], new_entry.importance,
                )

        for entry in factual:
            if entry.memory_id not in all_merged_ids:
                result.append(entry)
                all_merged_ids.add(entry.memory_id)

        return result

    def _cluster_by_topic(self, entries: List[MemoryEntry], max_cluster: int) -> List[List[MemoryEntry]]:
        scored: List[Tuple[MemoryEntry, set]] = []
        for e in entries:
            topics = set(_TOPIC_WORDS.findall(e.content.lower()))
            scored.append((e, topics))

        visited: Set[str] = set()
        clusters: List[List[MemoryEntry]] = []

        for entry, topics in scored:
            if entry.memory_id in visited:
                continue
            if not topics:
                continue

            cluster = [entry]
            visited.add(entry.memory_id)

            for other, other_topics in scored:
                if other.memory_id in visited:
                    continue
                if len(cluster) >= max_cluster:
                    break

                if topics & other_topics:
                    overlap_ratio = len(topics & other_topics) / max(len(topics | other_topics), 1)
                    if overlap_ratio >= 0.3:
                        cluster.append(other)
                        visited.add(other.memory_id)

            if len(cluster) >= 2:
                clusters.append(cluster)
            else:
                visited.discard(entry.memory_id)

        return clusters

    def _merge_cluster(self, cluster: List[MemoryEntry]) -> Optional[MemoryEntry]:
        if not cluster:
            return None

        cluster.sort(key=lambda e: e.importance, reverse=True)

        master = cluster[0]
        supporting = cluster[1:]

        topics = set()
        all_content: List[str] = [master.content]
        max_confidence = master.confidence
        max_importance = master.importance

        for entry in supporting:
            all_content.append(entry.content)
            topics.update(_TOPIC_WORDS.findall(entry.content.lower()))
            max_confidence = max(max_confidence, entry.confidence)
            max_importance = max(max_importance, entry.importance)

        merged_text = " ".join(all_content)

        topic_str = ", ".join(sorted(topics)) if topics else ""

        if master.type == MemoryType.SEMANTIC:
            summary = f"Related facts: {topic_str}" if topic_str else merged_text[:150]
        elif master.type == MemoryType.PREFERENCE:
            summary = f"Related preferences: {topic_str}" if topic_str else merged_text[:150]
        else:
            summary = merged_text[:150]

        new_entry = MemoryEntry(
            content=merged_text,
            type=master.type,
            user_id=master.user_id,
            workspace_id=master.workspace_id,
            importance=min(max_importance + 0.1, 1.0),
            confidence=max_confidence,
            summary=summary,
            source=f"consolidated from {len(cluster)} memories",
            memory_id=str(uuid.uuid4()),
        )

        return new_entry
