from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConversationTurn:
    role: str
    content: str


@dataclass
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    text: str
    title: str = ""
    section: str = ""
    page: int = 0
    score: float = 0.0
    chunk_index: int = 0
    language: str = ""
    document_type: str = ""
    workspace_id: str = "default"
    keywords: List[str] = field(default_factory=list)


@dataclass
class KnowledgeQuery:
    question: str
    workspace_id: str = "default"
    conversation_id: str = ""
    top_k: int = 10
    min_score: float = 0.0
    language: Optional[str] = None
    document_type: Optional[str] = None
    document_ids: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None


@dataclass
class KnowledgeAnswer:
    question: str
    answer: str
    citations: List[str] = field(default_factory=list)
    sources: List[Dict[str, Any]] = field(default_factory=list)
    processing_time_ms: float = 0.0
    retrieval_time_ms: float = 0.0
    generation_time_ms: float = 0.0
    chunk_count: int = 0
    context_token_estimate: int = 0
    validation_passed: bool = True
    guardrail_triggered: bool = False
    knowledge_gap: bool = False
    conversation_id: str = ""
    intent: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "question": self.question,
            "answer": self.answer,
            "citations": self.citations,
            "sources": self.sources,
            "processing_time_ms": round(self.processing_time_ms, 2),
            "retrieval_time_ms": round(self.retrieval_time_ms, 2),
            "generation_time_ms": round(self.generation_time_ms, 2),
            "chunk_count": self.chunk_count,
            "context_token_estimate": self.context_token_estimate,
            "validation_passed": self.validation_passed,
            "guardrail_triggered": self.guardrail_triggered,
            "knowledge_gap": self.knowledge_gap,
            "conversation_id": self.conversation_id,
        }
        if self.intent:
            result["intent"] = self.intent
        return result
