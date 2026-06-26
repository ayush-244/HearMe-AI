import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from ..schemas.document import (
    UploadResponse,
    DocumentListResponse,
    DocumentListItem,
    DocumentMetadata,
    DeleteResponse,
)
from ..services import get_services
from ..services.document_service import DocumentValidationError

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/documents/upload", response_model=UploadResponse, status_code=201)
async def upload_document(file: UploadFile = File(...)):
    services = get_services()
    doc_service = services["document"]

    filename = file.filename or "unnamed"
    content = await file.read()

    logger.info("/documents/upload request: filename=%s, size=%d", filename, len(content))

    try:
        result = doc_service.upload(filename, content)
        logger.info("/documents/upload success: id=%s", result.document_id)
        return result
    except DocumentValidationError as e:
        logger.warning("/documents/upload validation error: %s", e.message)
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    services = get_services()
    doc_service = services["document"]
    docs = doc_service.list_documents()
    logger.info("/documents list: count=%d", len(docs))
    return DocumentListResponse(documents=docs, count=len(docs))


@router.get("/documents/{document_id}", response_model=DocumentMetadata)
async def get_document(document_id: str):
    services = get_services()
    doc_service = services["document"]
    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")
    logger.info("/documents/{id} retrieved: id=%s", document_id)
    return meta


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(document_id: str):
    services = get_services()
    doc_service = services["document"]
    result = doc_service.delete(document_id)
    if result.status == "not_found":
        raise HTTPException(status_code=404, detail="Document not found")
    logger.info("/documents/{id} deleted: id=%s", document_id)
    return result
