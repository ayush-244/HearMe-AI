import logging
from fastapi import APIRouter, HTTPException
from ..schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetail,
    ConversationListResponse,
    MessageResponse,
    AttachmentRequest,
)
from ..services.conversation_service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/conversations", tags=["conversations"])

_service: ConversationService = None


def get_service() -> ConversationService:
    global _service
    if _service is None:
        _service = ConversationService()
    return _service


@router.post("", response_model=ConversationResponse)
async def create_conversation(body: ConversationCreate):
    service = get_service()
    result = service.create_conversation(title=body.title)
    return result


@router.get("", response_model=ConversationListResponse)
async def list_conversations(search: str = ""):
    service = get_service()
    if search:
        convs = service.search_conversations(search)
    else:
        convs = service.list_conversations()
    return {"conversations": convs, "total": len(convs)}


@router.get("/{conv_id}", response_model=ConversationDetail)
async def get_conversation(conv_id: str):
    service = get_service()
    conv = service.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.patch("/{conv_id}", response_model=ConversationResponse)
async def update_conversation(conv_id: str, body: ConversationUpdate):
    service = get_service()
    updates = {}
    if body.title is not None:
        updates["title"] = body.title
    if body.pinned is not None:
        updates["pinned"] = body.pinned
    result = service.update_conversation(conv_id, updates)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str):
    service = get_service()
    if not service.delete_conversation(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}


@router.post("/{conv_id}/messages", response_model=MessageResponse)
async def add_message(conv_id: str, body: dict):
    service = get_service()
    role = body.get("role", "user")
    content = body.get("content", "")
    citations = body.get("citations", [])
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    msg = service.add_message(conv_id, role, content, citations)
    if not msg:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return msg


@router.get("/{conv_id}/messages")
async def get_messages(conv_id: str, limit: int = 100):
    service = get_service()
    conv = service.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = conv.get("messages", [])
    return {"messages": messages[-limit:], "total": len(messages)}


@router.post("/{conv_id}/attachments")
async def add_attachment(conv_id: str, body: AttachmentRequest):
    service = get_service()
    result = service.add_attachment(conv_id, body.document_id, body.filename, body.file_type)
    if not result:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@router.delete("/{conv_id}/attachments/{document_id}")
async def remove_attachment(conv_id: str, document_id: str):
    service = get_service()
    if not service.remove_attachment(conv_id, document_id):
        raise HTTPException(status_code=404, detail="Attachment not found")
    return {"deleted": True}
