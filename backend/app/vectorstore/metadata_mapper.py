import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qdrant_client.http.models import Filter as QdrantFilter, FieldCondition, MatchValue, Range

logger = logging.getLogger(__name__)


class MetadataMapper:
    COLLECTION_NAME = "knowledge_brain"

    @staticmethod
    def chunk_to_payload(
        chunk: Dict[str, Any],
        embedding_version: str = "",
        checksum: str = "",
    ) -> Dict[str, Any]:
        text = chunk.get("text", "")
        return {
            "document_id": chunk.get("document_id", ""),
            "chunk_id": chunk.get("chunk_id", ""),
            "workspace_id": chunk.get("workspace_id", "default"),
            "title": chunk.get("title", chunk.get("section_name", "")),
            "section": chunk.get("section_name", ""),
            "page": chunk.get("page_start", 0),
            "language": chunk.get("language", ""),
            "document_type": chunk.get("document_type", ""),
            "keywords": chunk.get("keywords", []),
            "embedding_version": embedding_version,
            "checksum": checksum,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "importance_score": float(chunk.get("importance_score", 1.0)),
            "word_count": chunk.get("word_count", len(text.split())),
            "character_count": chunk.get("character_count", len(text)),
            "text": text,
            "chunk_index": chunk.get("chunk_index", 0),
        }

    @staticmethod
    def payload_to_chunk(payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "document_id": payload.get("document_id", ""),
            "chunk_id": payload.get("chunk_id", ""),
            "workspace_id": payload.get("workspace_id", "default"),
            "title": payload.get("title", ""),
            "section": payload.get("section", ""),
            "page": payload.get("page", 0),
            "language": payload.get("language", ""),
            "document_type": payload.get("document_type", ""),
            "keywords": payload.get("keywords", []),
            "embedding_version": payload.get("embedding_version", ""),
            "checksum": payload.get("checksum", ""),
            "created_at": payload.get("created_at", ""),
            "importance_score": payload.get("importance_score", 1.0),
            "word_count": payload.get("word_count", 0),
            "character_count": payload.get("character_count", 0),
            "text": payload.get("text", ""),
            "chunk_index": payload.get("chunk_index", 0),
        }

    @staticmethod
    def chunk_to_point(
        chunk: Dict[str, Any],
        vector: List[float],
        embedding_version: str = "",
        checksum: str = "",
    ) -> Dict[str, Any]:
        return {
            "id": chunk.get("chunk_id", ""),
            "vector": vector,
            "payload": MetadataMapper.chunk_to_payload(
                chunk, embedding_version=embedding_version, checksum=checksum,
            ),
        }

    @staticmethod
    def build_filter(document_id: Optional[str] = None, chunk_id: Optional[str] = None) -> Dict[str, Any]:
        must = []
        if document_id:
            must.append({"key": "document_id", "match": {"value": document_id}})
        if chunk_id:
            must.append({"key": "chunk_id", "match": {"value": chunk_id}})
        if not must:
            return {}
        return {"must": must}

    @staticmethod
    def build_qdrant_filter(conditions: Dict[str, Any]) -> Optional[Any]:
        must = []
        for key, value in conditions.items():
            if value is None:
                continue
            if isinstance(value, dict):
                if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                    must.append(FieldCondition(key=key, range=Range(**value)))
                elif "match" in value:
                    must.append(FieldCondition(key=key, match=MatchValue(value=value["match"])))
            elif isinstance(value, list):
                for v in value:
                    must.append(FieldCondition(key=key, match=MatchValue(value=v)))
            else:
                must.append(FieldCondition(key=key, match=MatchValue(value=value)))
        if not must:
            return None
        return QdrantFilter(must=must)

    @staticmethod
    def get_payload_schema() -> Dict[str, str]:
        return {
            "document_id": "str",
            "chunk_id": "str",
            "workspace_id": "str",
            "title": "str",
            "section": "str",
            "page": "int",
            "language": "str",
            "document_type": "str",
            "keywords": "list[str]",
            "embedding_version": "str",
            "checksum": "str",
            "created_at": "str",
            "importance_score": "float",
            "word_count": "int",
            "character_count": "int",
            "text": "str",
            "chunk_index": "int",
        }
