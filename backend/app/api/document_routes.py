import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from ..schemas.document import (
    UploadResponse,
    DocumentListResponse,
    DocumentListItem,
    DocumentMetadata,
    DocumentStatus,
    DeleteResponse,
    ExtractionResponse,
    ContentResponse,
    AnalysisResponse,
    ChunkResponse,
    ChunkListResponse,
    ChunkStatisticsResponse,
    EmbeddingResponse,
    EmbeddingListResponse,
    EmbeddingChunkResponse,
    IndexResponse,
    DeindexResponse,
    RetryResponse,
    FailedResponse,
)
from ..services import get_services
from ..services.document_service import DocumentValidationError, DocumentExtractionError
from ..services.embedding_service import EmbeddingError

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


@router.post("/documents/{document_id}/extract", response_model=ExtractionResponse)
async def extract_document(document_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/extract request: id=%s", document_id)

    try:
        result = doc_service.extract_document(document_id)
        logger.info(
            "/documents/{id}/extract success: pages=%d, words=%d, chars=%d",
            document_id, result.pages, result.words, result.characters,
        )
        return result
    except DocumentExtractionError as e:
        logger.warning("/documents/{id}/extract error: %s — %s", document_id, e.message)
        doc_service.set_failed(document_id, "extract")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("/documents/{id}/extract unexpected error: %s", document_id, exc_info=True)
        doc_service.set_failed(document_id, "extract")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/content", response_model=ContentResponse)
async def get_document_content(document_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/content request: id=%s", document_id)

    try:
        result = doc_service.get_document_content(document_id)
        logger.info(
            "/documents/{id}/content retrieved: extracted=%s, pages=%d, words=%d",
            document_id, result.extracted, result.pages, result.words,
        )
        return result
    except DocumentExtractionError as e:
        logger.warning("/documents/{id}/content error: %s — %s", document_id, e.message)
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/documents/{document_id}/analyze", response_model=AnalysisResponse)
async def analyze_document(document_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/analyze request: id=%s", document_id)

    try:
        result = doc_service.analyze_document(document_id)
        logger.info(
            "/documents/{id}/analyze success: type=%s, sections=%d, keywords=%d",
            document_id, result.document_type, len(result.sections), len(result.keywords),
        )
        return result
    except DocumentExtractionError as e:
        logger.warning("/documents/{id}/analyze error: %s — %s", document_id, e.message)
        doc_service.set_failed(document_id, "analyze")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("/documents/{id}/analyze unexpected error: %s", document_id, exc_info=True)
        doc_service.set_failed(document_id, "analyze")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/analysis")
async def get_document_analysis(document_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/analysis GET request: id=%s", document_id)

    analysis = doc_service.get_analysis(document_id)
    if analysis is None:
        meta = doc_service.get_metadata(document_id)
        if meta is None:
            raise HTTPException(status_code=404, detail="Document not found")
        raise HTTPException(status_code=404, detail="Analysis not found. Run analysis first.")

    logger.info("/documents/{id}/analysis retrieved", document_id)
    return analysis


@router.post("/documents/{document_id}/chunk", response_model=ChunkResponse)
async def chunk_document(document_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/chunk request: id=%s", document_id)

    try:
        result = doc_service.chunk_document(document_id)
        logger.info(
            "/documents/{id}/chunk success: strategy=%s, chunks=%d",
            document_id, result["strategy"], len(result["chunks"]),
        )
        return ChunkResponse(
            status="chunked",
            strategy=result["strategy"],
            chunk_count=len(result["chunks"]),
        )
    except DocumentExtractionError as e:
        logger.warning("/documents/{id}/chunk error: %s — %s", document_id, e.message)
        doc_service.set_failed(document_id, "chunk")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("/documents/{id}/chunk unexpected error: %s", document_id, exc_info=True)
        doc_service.set_failed(document_id, "chunk")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/chunks", response_model=ChunkListResponse)
async def list_chunks(document_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/chunks list request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    previews = doc_service.get_chunks_preview(document_id)
    if previews is None:
        raise HTTPException(status_code=404, detail="Chunks not found. Run chunking first.")

    stats = doc_service.get_chunk_statistics(document_id)

    return ChunkListResponse(
        document_id=document_id,
        chunks=previews,
        statistics=stats,
    )


@router.get("/documents/{document_id}/chunks/statistics", response_model=ChunkStatisticsResponse)
async def get_chunk_statistics(document_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/chunks/statistics request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    stats = doc_service.get_chunk_statistics(document_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Chunks not found. Run chunking first.")

    return ChunkStatisticsResponse(**stats)


@router.get("/documents/{document_id}/chunks/{chunk_id}")
async def get_chunk(document_id: str, chunk_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/chunks/{chunk_id} request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk = doc_service.get_chunk(document_id, chunk_id)
    if chunk is None:
        raise HTTPException(status_code=404, detail="Chunk not found")

    return chunk


@router.post("/documents/{document_id}/embed", response_model=EmbeddingResponse)
async def embed_document(document_id: str):
    services = get_services()
    doc_service = services["document"]
    emb_service = services["embedding"]

    logger.info("/documents/{id}/embed request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_data = doc_service.get_chunks_data(document_id)
    if chunks_data is None:
        doc_service.set_failed(document_id, "embed")
        raise HTTPException(status_code=400, detail="Document must be chunked before embedding")

    try:
        result = emb_service.embed_document(document_id, chunks_data)
        logger.info(
            "/documents/{id}/embed success: chunks=%d, dimension=%d, model=%s",
            document_id, len(result["chunks"]), result["dimension"], result["embedding_model"],
        )
        doc_service.update_status(document_id, DocumentStatus.embedded)
        return EmbeddingResponse(
            status="embedded",
            chunks=len(result["chunks"]),
            dimension=result["dimension"],
            model=result["embedding_model"],
            embedding_version=result["embedding_version"],
        )
    except EmbeddingError as e:
        logger.warning("/documents/{id}/embed error: %s — %s", document_id, e.message)
        doc_service.set_failed(document_id, "embed")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("/documents/{id}/embed unexpected error: %s", document_id, exc_info=True)
        doc_service.set_failed(document_id, "embed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/embeddings", response_model=EmbeddingListResponse)
async def list_embeddings(document_id: str):
    services = get_services()
    doc_service = services["document"]
    emb_service = services["embedding"]

    logger.info("/documents/{id}/embeddings list request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    result = emb_service.get_embedding_list(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Embeddings not found. Run embedding first.")

    return EmbeddingListResponse(**result)


@router.get("/documents/{document_id}/embeddings/{chunk_id}", response_model=EmbeddingChunkResponse)
async def get_embedding(document_id: str, chunk_id: str):
    services = get_services()
    doc_service = services["document"]
    emb_service = services["embedding"]

    logger.info("/documents/{id}/embeddings/{chunk_id} request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    result = emb_service.get_embedding(document_id, chunk_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Embedding not found")

    return EmbeddingChunkResponse(**result)


@router.post("/documents/{document_id}/index", response_model=IndexResponse)
async def index_document(document_id: str):
    services = get_services()
    doc_service = services["document"]
    emb_service = services["embedding_with_store"]

    logger.info("/documents/{id}/index request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_data = doc_service.get_chunks_data(document_id)
    if chunks_data is None:
        doc_service.set_failed(document_id, "index")
        raise HTTPException(status_code=400, detail="Document must be chunked before indexing")

    analysis = doc_service.get_analysis(document_id)

    try:
        result = emb_service.index_document(document_id, chunks_data, analysis)
        logger.info(
            "/documents/{id}/index success: vectors=%d, collection=%s",
            document_id, result["vectors"], result["collection"],
        )
        doc_service.update_status(document_id, DocumentStatus.indexed)
        return IndexResponse(
            status=result["status"],
            vectors=result["vectors"],
            collection=result["collection"],
        )
    except EmbeddingError as e:
        logger.warning("/documents/{id}/index error: %s — %s", document_id, e.message)
        doc_service.set_failed(document_id, "index")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("/documents/{id}/index unexpected error: %s", document_id, exc_info=True)
        doc_service.set_failed(document_id, "index")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}/index", response_model=DeindexResponse)
async def deindex_document(document_id: str):
    services = get_services()
    doc_service = services["document"]
    emb_service = services["embedding_with_store"]

    logger.info("/documents/{id}/index DELETE request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        result = emb_service.deindex_document(document_id)
        logger.info(
            "/documents/{id}/index DELETE success: vectors_removed=%d",
            document_id, result["vectors_removed"],
        )
        doc_service.update_status(document_id, DocumentStatus.chunked)
        return DeindexResponse(
            status=result["status"],
            document_id=result["document_id"],
            vectors_removed=result["vectors_removed"],
        )
    except EmbeddingError as e:
        logger.warning("/documents/{id}/index DELETE error: %s — %s", document_id, e.message)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("/documents/{id}/index DELETE unexpected error: %s", document_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}/failed", response_model=FailedResponse)
async def get_failed_details(document_id: str):
    services = get_services()
    doc_service = services["document"]

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if meta.status != DocumentStatus.failed:
        raise HTTPException(status_code=400, detail="Document is not in failed state")

    return FailedResponse(
        status="failed",
        document_id=document_id,
        failed_stage=meta.failed_stage or "unknown",
        message=f"Processing failed at stage: {meta.failed_stage or 'unknown'}",
    )


@router.post("/documents/{document_id}/retry")
async def retry_document(document_id: str):
    services = get_services()
    doc_service = services["document"]

    logger.info("/documents/{id}/retry request: id=%s", document_id)

    meta = doc_service.get_metadata(document_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")

    if meta.status != DocumentStatus.failed:
        raise HTTPException(status_code=400, detail="Document is not in failed state")

    failed_stage = doc_service.get_failed_stage(document_id)
    if failed_stage is None:
        failed_stage = "uploaded"

    # Clear failed status so the next endpoint can process
    doc_service.clear_failed(document_id)

    logger.info("/documents/{id}/retry: will retry from stage '%s'", document_id, failed_stage)

    return RetryResponse(
        status="retrying",
        document_id=document_id,
        stage=failed_stage,
        message=f"Retrying from stage: {failed_stage}",
    )
