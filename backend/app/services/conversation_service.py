import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional
from ..config.settings import settings

logger = logging.getLogger(__name__)


class ConversationService:
    def __init__(self):
        self._store_path = settings.UPLOAD_DIR / "conversations"
        self._store_path.mkdir(parents=True, exist_ok=True)
        self._conversations_file = self._store_path / "conversations.json"
        self._messages_dir = self._store_path / "messages"
        self._messages_dir.mkdir(parents=True, exist_ok=True)
        self._conversations: dict = {}
        self._load()

    def _load(self):
        if self._conversations_file.exists():
            try:
                with open(self._conversations_file, "r") as f:
                    self._conversations = json.load(f)
            except Exception as e:
                logger.error("Failed to load conversations: %s", e)
                self._conversations = {}

    def _save(self):
        with open(self._conversations_file, "w") as f:
            json.dump(self._conversations, f, indent=2)

    def _messages_path(self, conv_id: str) -> str:
        return str(self._messages_dir / f"{conv_id}.json")

    def _load_messages(self, conv_id: str) -> list:
        path = self._messages_path(conv_id)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to load messages for %s: %s", conv_id, e)
        return []

    def _save_messages(self, conv_id: str, messages: list):
        with open(self._messages_path(conv_id), "w") as f:
            json.dump(messages, f, indent=2)

    def create_conversation(self, title: str = "") -> dict:
        conv_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        if not title:
            title = "New Chat"
        conv = {
            "id": conv_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "pinned": False,
        }
        self._conversations[conv_id] = conv
        self._save()
        return {**conv, "last_message": None, "message_count": 0}

    def list_conversations(self) -> list:
        convs = []
        for conv_id, conv in self._conversations.items():
            messages = self._load_messages(conv_id)
            last_msg = messages[-1]["content"] if messages else None
            convs.append({
                "id": conv_id,
                "title": conv["title"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
                "last_message": last_msg[:120] + "..." if last_msg and len(last_msg) > 120 else last_msg,
                "message_count": len(messages),
                "pinned": conv.get("pinned", False),
            })
        convs.sort(key=lambda c: c["updated_at"], reverse=True)
        return convs

    def get_conversation(self, conv_id: str) -> Optional[dict]:
        conv = self._conversations.get(conv_id)
        if not conv:
            return None
        messages = self._load_messages(conv_id)
        for m in messages:
            if m.get("role") == "assistant":
                logger.info("[6] GET RESPONSE msg_id=%s retrieval_trace=%s", m.get("id"), m.get("retrieval_trace") is not None)
        return {
            **conv,
            "messages": messages,
            "attached_documents": self._load_attachments(conv_id),
        }

    def update_conversation(self, conv_id: str, updates: dict) -> Optional[dict]:
        conv = self._conversations.get(conv_id)
        if not conv:
            return None
        if "title" in updates and updates["title"]:
            conv["title"] = updates["title"]
        if "pinned" in updates:
            conv["pinned"] = updates["pinned"]
        conv["updated_at"] = datetime.utcnow().isoformat()
        self._save()
        messages = self._load_messages(conv_id)
        last_msg = messages[-1]["content"] if messages else None
        return {
            "id": conv_id,
            "title": conv["title"],
            "created_at": conv["created_at"],
            "updated_at": conv["updated_at"],
            "last_message": last_msg[:120] + "..." if last_msg and len(last_msg) > 120 else last_msg,
            "message_count": len(messages),
            "pinned": conv.get("pinned", False),
        }

    def delete_conversation(self, conv_id: str) -> bool:
        if conv_id not in self._conversations:
            return False
        del self._conversations[conv_id]
        self._save()
        path = self._messages_path(conv_id)
        if os.path.exists(path):
            os.remove(path)
        return True

    def add_message(self, conv_id: str, role: str, content: str, citations: list[str] = None, retrieval_trace: dict = None) -> Optional[dict]:
        if conv_id not in self._conversations:
            conv = self.create_conversation()
            conv_id = conv["id"]
        conv = self._conversations[conv_id]
        messages = self._load_messages(conv_id)
        msg = {
            "id": str(uuid.uuid4()),
            "conversation_id": conv_id,
            "role": role,
            "content": content,
            "citations": citations or [],
            "timestamp": datetime.utcnow().isoformat(),
        }
        if role == "assistant" and retrieval_trace is not None:
            msg["retrieval_trace"] = retrieval_trace
        logger.info("[4] SERVICE role=%s retrieval_trace_param=%s msg_has_trace=%s", role, retrieval_trace is not None, "retrieval_trace" in msg)
        messages.append(msg)
        self._save_messages(conv_id, messages)
        # [5] Read back file to verify physical persistence
        readback = self._load_messages(conv_id)
        if readback:
            last = readback[-1]
            logger.info("[5] FILE readback msg_id=%s has_retrieval_trace=%s", last.get("id"), "retrieval_trace" in last)
        conv["updated_at"] = msg["timestamp"]
        if role == "user" and "title" in conv and conv["title"] == "New Chat":
            conv["title"] = self._generate_title(content)
        self._save()
        return msg

    def _generate_title(self, content: str) -> str:
        max_len = 60
        cleaned = content.strip().replace("\n", " ").replace("\r", "")
        if len(cleaned) > max_len:
            cleaned = cleaned[:max_len].rsplit(" ", 1)[0] + "..."
        return cleaned if cleaned else "New Chat"

    def _attachments_path(self, conv_id: str) -> str:
        return str(self._store_path / f"{conv_id}_attachments.json")

    def _load_attachments(self, conv_id: str) -> list:
        path = self._attachments_path(conv_id)
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("Failed to load attachments for %s: %s", conv_id, e)
        return []

    def _save_attachments(self, conv_id: str, attachments: list):
        with open(self._attachments_path(conv_id), "w") as f:
            json.dump(attachments, f, indent=2)

    def add_attachment(self, conv_id: str, document_id: str, filename: str, file_type: str) -> Optional[dict]:
        if conv_id not in self._conversations:
            return None
        attachments = self._load_attachments(conv_id)
        for a in attachments:
            if a["document_id"] == document_id:
                return a
        attachment = {
            "document_id": document_id,
            "filename": filename,
            "file_type": file_type,
            "status": "attached",
            "attached_at": datetime.utcnow().isoformat(),
        }
        attachments.append(attachment)
        self._save_attachments(conv_id, attachments)
        self._conversations[conv_id]["updated_at"] = datetime.utcnow().isoformat()
        self._save()
        return attachment

    def remove_attachment(self, conv_id: str, document_id: str) -> bool:
        if conv_id not in self._conversations:
            return False
        attachments = self._load_attachments(conv_id)
        before = len(attachments)
        attachments = [a for a in attachments if a["document_id"] != document_id]
        if len(attachments) == before:
            return False
        self._save_attachments(conv_id, attachments)
        return True

    def get_history(self, conv_id: str, limit: int = 50) -> list:
        messages = self._load_messages(conv_id)
        return messages[-limit:]

    def search_conversations(self, query: str) -> list:
        q = query.lower()
        results = []
        for conv_id, conv in self._conversations.items():
            if q in conv["title"].lower():
                messages = self._load_messages(conv_id)
                last_msg = messages[-1]["content"] if messages else None
                results.append({
                    "id": conv_id,
                    "title": conv["title"],
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "last_message": last_msg[:120] + "..." if last_msg and len(last_msg) > 120 else last_msg,
                    "message_count": len(messages),
                    "pinned": conv.get("pinned", False),
                })
        results.sort(key=lambda c: c["updated_at"], reverse=True)
        return results
