from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class IntentType(Enum):
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    PERSONAL_MEMORY = "personal_memory"
    DOCUMENT_QUESTION = "document_question"
    GENERAL_AI = "general_ai"
    MIXED = "mixed"
    FOLLOW_UP = "follow_up"

    @property
    def requires_memory(self) -> bool:
        return self in (IntentType.PERSONAL_MEMORY, IntentType.MIXED)

    @property
    def requires_documents(self) -> bool:
        return self in (IntentType.DOCUMENT_QUESTION, IntentType.MIXED)

    @property
    def requires_general_llm(self) -> bool:
        return self in (
            IntentType.GREETING,
            IntentType.SMALL_TALK,
            IntentType.GENERAL_AI,
            IntentType.FOLLOW_UP,
        )

    @property
    def requires_history(self) -> bool:
        return self == IntentType.FOLLOW_UP


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float = 1.0
    requires_memory: Optional[bool] = None
    requires_documents: Optional[bool] = None
    requires_general_llm: Optional[bool] = None
    requires_history: Optional[bool] = None
    sub_questions: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.requires_memory is None:
            self.requires_memory = self.intent.requires_memory
        if self.requires_documents is None:
            self.requires_documents = self.intent.requires_documents
        if self.requires_general_llm is None:
            self.requires_general_llm = self.intent.requires_general_llm
        if self.requires_history is None:
            self.requires_history = self.intent.requires_history


@dataclass
class ConversationState:
    conversation_id: Optional[str] = None
    history: List[dict] = field(default_factory=list)
    attached_documents: List[dict] = field(default_factory=list)
    last_assistant_response: Optional[str] = None
    last_retrieved_chunks: List[dict] = field(default_factory=list)
    last_retrieved_context: Optional[str] = None
    turn_count: int = 0
