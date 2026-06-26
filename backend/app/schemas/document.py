from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class FileType(str, Enum):
    pdf = "pdf"
    docx = "docx"
    txt = "txt"
    markdown = "markdown"


class DocumentStatus(str, Enum):
    uploaded = "uploaded"
    failed = "failed"


class DocumentMetadata(BaseModel):
    id: str
    filename: str
    file_type: FileType
    size: int
    status: DocumentStatus
    upload_time: datetime
    storage_path: str


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    file_type: FileType
    size: int
    status: DocumentStatus


class DocumentListItem(BaseModel):
    id: str
    filename: str
    file_type: FileType
    size: int
    upload_time: datetime


class DocumentListResponse(BaseModel):
    documents: List[DocumentListItem]
    count: int


class DeleteResponse(BaseModel):
    status: str
    document_id: str
    message: str
