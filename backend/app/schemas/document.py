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
    extracted = "extracted"
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


class ExtractionResponse(BaseModel):
    document_id: str
    status: str
    pages: int
    words: int
    characters: int


class ContentResponse(BaseModel):
    document_id: str
    preview: str
    pages: int
    words: int
    characters: int
    extracted: bool


class AnalysisResponse(BaseModel):
    status: str
    document_id: str
    document_type: str
    classification_confidence: float
    language: str
    language_code: str
    page_count: int
    word_count: int
    character_count: int
    reading_time: int
    sections: List[dict]
    contains_tables: bool
    contains_images: bool
    contains_code_blocks: bool
    contains_urls: bool
    contains_emails: bool
    contains_phone_numbers: bool
    contains_dates: bool
    keywords: List[str]
    summary_preview: str
    extracted_metadata: dict
    created_at: str


class ExtractionError(BaseModel):
    document_id: str
    status: str
    message: str


class ChunkPreview(BaseModel):
    chunk_id: str
    section_name: str
    chunk_index: int
    word_count: int
    character_count: int
    estimated_tokens: int
    page_start: int
    page_end: int
    preview: str


class ChunkResponse(BaseModel):
    status: str
    strategy: str
    chunk_count: int


class ChunkDetailResponse(BaseModel):
    chunk_id: str
    document_id: str
    section_name: str
    chunk_index: int
    page_start: int
    page_end: int
    start_offset: int
    end_offset: int
    word_count: int
    character_count: int
    estimated_tokens: int
    overlap_previous: str
    overlap_next: str
    text: str
    metadata: dict


class ChunkListResponse(BaseModel):
    document_id: str
    chunks: List[ChunkPreview]
    statistics: Optional[dict] = None


class ChunkStatisticsResponse(BaseModel):
    document_id: str
    chunks: int
    average_chunk_size: float
    largest_chunk: int
    smallest_chunk: int
    strategy: str


class EmbeddingChunkInfo(BaseModel):
    chunk_id: str
    checksum: str
    dimension: int


class EmbeddingResponse(BaseModel):
    status: str
    chunks: int
    dimension: int
    model: str
    embedding_version: str


class EmbeddingListResponse(BaseModel):
    document_id: str
    embedding_model: str
    embedding_version: str
    dimension: int
    created_at: str
    chunks: List[EmbeddingChunkInfo]


class EmbeddingChunkResponse(BaseModel):
    chunk_id: str
    checksum: str
    dimension: int
    model: str
    vector: List[float]
