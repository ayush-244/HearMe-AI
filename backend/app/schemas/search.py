from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query text")
    workspace_id: str = Field("default", description="Workspace scope")
    top_k: int = Field(10, ge=1, le=100, description="Number of results")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    language: Optional[str] = Field(None, description="Filter by language")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    document_ids: Optional[List[str]] = Field(None, description="Filter by document IDs")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional metadata filters")


class SearchResultItemResponse(BaseModel):
    chunk_id: str
    document_id: str
    document: str
    section: str
    page: int
    score: float
    preview: str
    language: str = ""
    document_type: str = ""


class SearchStatisticsResponse(BaseModel):
    chunks_searched: int = 0
    chunks_returned: int = 0
    avg_score: float = 0.0
    latency_ms: float = 0.0


class SearchResponse(BaseModel):
    query: str
    processing_time_ms: float
    results: List[SearchResultItemResponse] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    statistics: Optional[SearchStatisticsResponse] = None
    query_analysis: Optional[Dict[str, Any]] = None


class SearchHealthResponse(BaseModel):
    ready: bool = False
    embedding_model_loaded: bool = False
    vector_store_healthy: bool = False
    keyword_backend: str = ""
    ranking_weights: Dict[str, float] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)
