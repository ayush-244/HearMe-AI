import hashlib
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EmbeddingCache:
    def __init__(self):
        self._cache: Dict[str, List[float]] = {}

    def compute_checksum(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, checksum: str) -> Optional[List[float]]:
        return self._cache.get(checksum)

    def set(self, checksum: str, vector: List[float]) -> None:
        self._cache[checksum] = vector

    def contains(self, checksum: str) -> bool:
        return checksum in self._cache

    def size(self) -> int:
        return len(self._cache)

    def clear(self) -> None:
        self._cache.clear()

    def process_batch(
        self,
        texts: List[str],
        embed_fn,
    ) -> Tuple[List[List[float]], List[str]]:
        checksums = [self.compute_checksum(t) for t in texts]
        vectors: List[Optional[List[float]]] = []
        to_embed: dict = {}
        defer_map: dict = {}

        for i, (text, ck) in enumerate(zip(texts, checksums)):
            cached = self.get(ck)
            if cached is not None:
                vectors.append(cached)
            elif ck in to_embed:
                vectors.append(None)
                defer_map.setdefault(ck, []).append(i)
            else:
                vectors.append(None)
                to_embed[ck] = (text, i)

        if to_embed:
            texts_to_embed = [v[0] for v in to_embed.values()]
            new_vectors = embed_fn(texts_to_embed)
            for (ck, (text, idx)), vec in zip(to_embed.items(), new_vectors):
                vectors[idx] = vec
                self.set(ck, vec)
                for di in defer_map.get(ck, []):
                    vectors[di] = vec

        return vectors, checksums

    def log_stats(self) -> dict:
        return {
            "cache_size": self.size(),
        }
