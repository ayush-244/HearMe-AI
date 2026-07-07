from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AttachedDocument(BaseModel):
    document_id: str
    filename: str
    file_type: str
    status: str
    attached_at: str


class MessageRequest(BaseModel):
    role: str
    content: str
    citations: list[str] = []


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    citations: list[str] = []
    timestamp: str
    retrieval_trace: Optional[dict] = None


class ConversationCreate(BaseModel):
    title: str = ""


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    pinned: Optional[bool] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    last_message: Optional[str] = None
    message_count: int = 0
    pinned: bool = False


class ConversationDetail(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: list[MessageResponse] = []
    attached_documents: list[AttachedDocument] = []
    pinned: bool = False


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]
    total: int


class AttachmentRequest(BaseModel):
    document_id: str
    filename: str
    file_type: str
