from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchQuery:
    text: str = ""
    workspace_id: str = "default"
    top_k: int = 10
    min_score: float = 0.0
    filters: Optional[Dict[str, Any]] = None
    language: Optional[str] = None
    document_type: Optional[str] = None
    document_ids: Optional[List[str]] = None


@dataclass
class SearchResultItem:
    chunk_id: str
    document_id: str
    text: str
    title: str
    section: str
    page: int
    score: float
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    metadata_score: float = 0.0
    language: str = ""
    document_type: str = ""
    workspace_id: str = "default"
    chunk_index: int = 0
    word_count: int = 0
    keywords: List[str] = field(default_factory=list)


@dataclass
class SearchStatistics:
    total_chunks_searched: int = 0
    semantic_chunks_retrieved: int = 0
    keyword_chunks_scored: int = 0
    final_chunks_returned: int = 0
    avg_semantic_score: float = 0.0
    avg_keyword_score: float = 0.0
    avg_final_score: float = 0.0
    semantic_latency_ms: float = 0.0
    keyword_latency_ms: float = 0.0
    ranking_latency_ms: float = 0.0
    total_latency_ms: float = 0.0


@dataclass
class SearchResult:
    query: str
    results: List[SearchResultItem] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    statistics: Optional[SearchStatistics] = None
    processing_time_ms: float = 0.0
    query_analysis: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "results": [
                {
                    "chunk_id": r.chunk_id,
                    "document_id": r.document_id,
                    "document": r.title,
                    "section": r.section,
                    "page": r.page,
                    "score": round(r.score, 4),
                    "preview": r.text[:200] if r.text else "",
                    "language": r.language,
                    "document_type": r.document_type,
                }
                for r in self.results
            ],
            "citations": self.citations,
            "statistics": {
                "chunks_searched": self.statistics.total_chunks_searched if self.statistics else 0,
                "chunks_returned": len(self.results),
                "avg_score": round(self.statistics.avg_final_score, 4) if self.statistics else 0.0,
                "latency_ms": round(self.processing_time_ms, 2),
            } if self.statistics else None,
            "query_analysis": self.query_analysis,
        }
