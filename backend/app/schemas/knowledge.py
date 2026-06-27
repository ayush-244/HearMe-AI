from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class KnowledgeChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    workspace_id: str = Field("default", description="Workspace scope")
    conversation_id: str = Field("", description="Conversation ID for history tracking")
    top_k: int = Field(10, ge=1, le=50, description="Number of chunks to retrieve")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="Minimum similarity threshold")
    language: Optional[str] = Field(None, description="Preferred response language")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    document_ids: Optional[List[str]] = Field(None, description="Filter by document IDs")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional metadata filters")


class KnowledgeChatResponse(BaseModel):
    question: str
    answer: str
    citations: List[str] = Field(default_factory=list)
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    processing_time_ms: float = 0.0
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    chunk_count: int = 0
    context_token_estimate: int = 0
    validation_passed: bool = True
    guardrail_triggered: bool = False
    knowledge_gap: bool = False
    conversation_id: str = ""


class KnowledgeHealthResponse(BaseModel):
    ready: bool = False
    search_engine_ready: bool = False
    context_builder_max_tokens: int = 0
    context_builder_max_chunks: int = 0
    citation_style: str = ""
    allow_external_knowledge: bool = False
    conversation_history_limit: int = 0
    active_conversations: int = 0
