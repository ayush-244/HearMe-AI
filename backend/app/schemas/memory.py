from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class MemoryInfo(BaseModel):
    memory_id: str
    user_id: str = ""
    workspace_id: str = "default"
    type: str = "episodic"
    content: str = ""
    summary: str = ""
    importance: float = 0.0
    confidence: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    last_accessed: str = ""
    access_count: int = 0
    source: str = ""
    pinned: bool = False


class ExtractMemoryRequest(BaseModel):
    user_text: str = Field(..., min_length=1, description="User's message text")
    assistant_text: Optional[str] = Field(None, description="Assistant's response text")
    user_id: str = Field("", description="User identifier")
    workspace_id: str = Field("default", description="Workspace scope")


class ExtractMemoryResponse(BaseModel):
    extracted_count: int = 0
    stored_count: int = 0
    rejected_count: int = 0
    updated_count: int = 0
    working_memory_id: Optional[str] = None
    processing_time_ms: float = 0.0


class SearchMemoryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    user_id: str = Field("", description="User identifier")
    workspace_id: str = Field("default", description="Workspace scope")
    memory_types: Optional[List[str]] = Field(None, description="Filter by memory types")
    top_k: int = Field(10, ge=1, le=50, description="Number of results")
    min_importance: float = Field(0.0, ge=0.0, le=1.0, description="Minimum importance threshold")
    include_working: bool = Field(False, description="Include working memories")


class SearchMemoryResponse(BaseModel):
    memories: List[MemoryInfo] = Field(default_factory=list)
    count: int = 0
    processing_time_ms: float = 0.0


class ListMemoryResponse(BaseModel):
    memories: List[MemoryInfo] = Field(default_factory=list)
    count: int = 0


class ConsolidateMemoryResponse(BaseModel):
    consolidated_count: int = 0
    before_count: int = 0
    after_count: int = 0
    processing_time_ms: float = 0.0


class MemoryHealthResponse(BaseModel):
    ready: bool = False
    memory_count: Dict[str, int] = Field(default_factory=dict)
    memory_threshold: float = 0.0
    forgetting_rate: float = 0.0
    importance_decay: float = 0.0
    auto_consolidation_enabled: bool = False
