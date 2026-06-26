"""Tests for the EmbeddingService."""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from fastapi.testclient import TestClient

from backend.app.services.embedding_service import EmbeddingService, EmbeddingError
from backend.app.main import app
from backend.app.services.document_service import DocumentService
from backend.app.schemas.document import (
    EmbeddingResponse, EmbeddingListResponse, EmbeddingChunkResponse,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def upload_dir(tmp_path):
    return tmp_path / "uploads"


@pytest.fixture
def embeddings_dir(tmp_path):
    return tmp_path / "embeddings"


@pytest.fixture
def chunks_data():
    return {
        "chunks": [
            {
                "chunk_id": "chunk-1",
                "text": "This is the first chunk of text for testing embedding service functionality.",
                "section_name": "Introduction",
                "chunk_index": 0,
                "word_count": 12,
            },
            {
                "chunk_id": "chunk-2",
                "text": "This is the second chunk with different content for embedding service testing.",
                "section_name": "Methodology",
                "chunk_index": 1,
                "word_count": 14,
            },
        ],
        "statistics": {"chunks": 2, "strategy": "fixed"},
    }


@pytest.fixture
def mock_embedding_model():
    with patch("backend.app.services.embedding_service.EmbeddingModel") as mock:
        mock_instance = MagicMock()
        mock_instance.is_loaded = True
        mock_instance.dimension = 768
        mock_instance.embed.return_value = [0.1] * 768
        mock_instance.embed_batch.return_value = [[0.1] * 768, [0.2] * 768]
        mock_instance.get_model_info.return_value = {
            "model_name": "BAAI/bge-base-en-v1.5",
            "dimension": 768,
            "max_seq_length": 512,
            "batch_size": 32,
            "device": "cpu",
        }
        mock.return_value = mock_instance
        yield mock_instance


# =============================================================================
# EmbeddingService Unit Tests
# =============================================================================

class TestEmbeddingService:
    def test_initialization(self, embeddings_dir):
        svc = EmbeddingService(
            embeddings_dir=embeddings_dir,
            model_name="test-model",
            batch_size=16,
        )
        assert svc._model_name == "test-model"
        assert svc._batch_size == 16
        assert embeddings_dir.exists()

    def test_initialize(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        svc.initialize()
        assert svc._model is not None
        mock_embedding_model.initialize.assert_called_once()

    def test_initialize_idempotent(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        svc.initialize()
        svc.initialize()
        mock_embedding_model.initialize.assert_called_once()

    def test_embed_text(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        vector = svc.embed_text("Hello world")
        assert len(vector) == 768
        mock_embedding_model.embed.assert_called_once_with("Hello world")

    def test_embed_chunks(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        results = svc.embed_chunks(chunks_data["chunks"])
        assert len(results) == 2
        assert results[0]["chunk_id"] == "chunk-1"
        assert results[0]["checksum"] is not None
        assert len(results[0]["vector"]) == 768
        assert results[1]["chunk_id"] == "chunk-2"

    def test_embed_chunks_empty(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        results = svc.embed_chunks([])
        assert results == []

    def test_embed_document(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        result = svc.embed_document("doc-123", chunks_data)
        assert result["document_id"] == "doc-123"
        assert result["embedding_model"] == "BAAI/bge-base-en-v1.5"
        assert result["dimension"] == 768
        assert len(result["chunks"]) == 2
        assert "created_at" in result

    def test_embed_document_empty_chunks(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        result = svc.embed_document("doc-123", [])
        assert result["document_id"] == "doc-123"
        assert len(result["chunks"]) == 0

    def test_persistence(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        svc.embed_document("doc-123", chunks_data)

        embed_file = embeddings_dir / "doc-123.json"
        assert embed_file.exists()

        with open(embed_file, "r") as f:
            saved = json.load(f)
        assert saved["document_id"] == "doc-123"
        assert len(saved["chunks"]) == 2

    def test_reload_persistence(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc1 = EmbeddingService(embeddings_dir=embeddings_dir)
        svc1.embed_document("doc-123", chunks_data)

        svc2 = EmbeddingService(embeddings_dir=embeddings_dir)
        assert svc2.is_embedded("doc-123") is True

    def test_get_embedding_list(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        svc.embed_document("doc-123", chunks_data)

        result = svc.get_embedding_list("doc-123")
        assert result is not None
        assert result["document_id"] == "doc-123"
        assert result["dimension"] == 768
        assert len(result["chunks"]) == 2
        assert all("vector" not in c for c in result["chunks"])
        assert all("checksum" in c for c in result["chunks"])

    def test_get_embedding_list_not_found(self, embeddings_dir):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        result = svc.get_embedding_list("nonexistent")
        assert result is None

    def test_get_embedding_by_id(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        svc.embed_document("doc-123", chunks_data)

        result = svc.get_embedding("doc-123", "chunk-1")
        assert result is not None
        assert result["chunk_id"] == "chunk-1"
        assert "vector" in result
        assert len(result["vector"]) == 768

    def test_get_embedding_not_found(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        svc.embed_document("doc-123", chunks_data)

        result = svc.get_embedding("doc-123", "nonexistent-chunk")
        assert result is None

    def test_get_embedding_doc_not_found(self, embeddings_dir):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        result = svc.get_embedding("nonexistent", "chunk-1")
        assert result is None

    def test_is_embedded(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        assert svc.is_embedded("doc-123") is False
        svc.embed_document("doc-123", chunks_data)
        assert svc.is_embedded("doc-123") is True

    def test_delete_embeddings(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        svc.embed_document("doc-123", chunks_data)
        assert svc.is_embedded("doc-123") is True

        svc.delete_embeddings("doc-123")
        assert svc.is_embedded("doc-123") is False

    def test_get_embedding_stats(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        svc.initialize()
        stats = svc.get_embedding_stats()
        assert stats["model_name"] == "BAAI/bge-base-en-v1.5"
        assert stats["dimension"] == 768
        assert stats["batch_size"] == 32
        assert stats["model_loaded"] is True

    def test_cache_hit(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        chunks = [
            {"chunk_id": "c1", "text": "same text"},
            {"chunk_id": "c2", "text": "same text"},
        ]
        results = svc.embed_chunks(chunks)
        assert results[0]["checksum"] == results[1]["checksum"]
        assert results[0]["vector"] == results[1]["vector"]
        # embed_batch should only be called once for the distinct text
        assert mock_embedding_model.embed_batch.call_count == 1

    def test_cache_miss(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        chunks = [
            {"chunk_id": "c1", "text": "text one"},
            {"chunk_id": "c2", "text": "text two"},
        ]
        results = svc.embed_chunks(chunks)
        assert results[0]["checksum"] != results[1]["checksum"]
        assert mock_embedding_model.embed_batch.call_count == 1

    def test_embed_document_with_flat_chunk_list(self, embeddings_dir, mock_embedding_model):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        flat_chunks = [
            {"chunk_id": "c1", "text": "text one"},
            {"chunk_id": "c2", "text": "text two"},
        ]
        result = svc.embed_document("doc-123", flat_chunks)
        assert len(result["chunks"]) == 2

    def test_embedding_error_on_save(self, embeddings_dir, mock_embedding_model, chunks_data):
        svc = EmbeddingService(embeddings_dir=embeddings_dir)
        with patch.object(svc, "_save_embeddings", side_effect=EmbeddingError("write failed", 500)):
            with pytest.raises(EmbeddingError, match="write failed"):
                svc.embed_document("doc-123", chunks_data)


# =============================================================================
# Integration Tests: Upload → Extract → Chunk → Embed → Retrieve
# =============================================================================

class TestEmbeddingPipeline:
    def test_full_pipeline(self, upload_dir, tmp_path):
        content = ("test word for embedding pipeline integration test " * 100).encode("utf-8")

        doc_svc = DocumentService(upload_dir)
        upload_result = doc_svc.upload("pipeline.txt", content)
        doc_id = upload_result.document_id

        doc_svc.extract_document(doc_id)
        doc_svc.chunk_document(doc_id)
        chunks_data = doc_svc.get_chunks_data(doc_id)
        assert chunks_data is not None
        assert len(chunks_data["chunks"]) > 0

        emb_svc = EmbeddingService(embeddings_dir=upload_dir / "embeddings")
        result = emb_svc.embed_document(doc_id, chunks_data)
        assert result["dimension"] > 0
        assert len(result["chunks"]) == len(chunks_data["chunks"])

        assert emb_svc.is_embedded(doc_id) is True

        emb_list = emb_svc.get_embedding_list(doc_id)
        assert emb_list is not None
        assert len(emb_list["chunks"]) == len(chunks_data["chunks"])

        chunk_id = chunks_data["chunks"][0]["chunk_id"]
        single = emb_svc.get_embedding(doc_id, chunk_id)
        assert single is not None
        assert single["chunk_id"] == chunk_id

    def test_delete_removes_embeddings(self, upload_dir, tmp_path):
        content = b"test content for deletion test. " * 50

        doc_svc = DocumentService(upload_dir)
        upload_result = doc_svc.upload("delete_me.txt", content)
        doc_id = upload_result.document_id
        doc_svc.extract_document(doc_id)
        doc_svc.chunk_document(doc_id)

        emb_svc = EmbeddingService(embeddings_dir=upload_dir / "embeddings")
        chunks_data = doc_svc.get_chunks_data(doc_id)
        emb_svc.embed_document(doc_id, chunks_data)
        assert emb_svc.is_embedded(doc_id) is True

        doc_svc.delete(doc_id)
        assert emb_svc.is_embedded(doc_id) is False

    def test_embeddings_persist_across_restart(self, upload_dir, tmp_path):
        content = b"persistent embedding test content for cross session validation. " * 50

        doc_svc1 = DocumentService(upload_dir)
        upload_result = doc_svc1.upload("persist.txt", content)
        doc_id = upload_result.document_id
        doc_svc1.extract_document(doc_id)
        doc_svc1.chunk_document(doc_id)

        emb_svc1 = EmbeddingService(embeddings_dir=upload_dir / "embeddings")
        chunks_data = doc_svc1.get_chunks_data(doc_id)
        emb_svc1.embed_document(doc_id, chunks_data)

        emb_svc2 = EmbeddingService(embeddings_dir=upload_dir / "embeddings")
        assert emb_svc2.is_embedded(doc_id) is True
        emb_list = emb_svc2.get_embedding_list(doc_id)
        assert emb_list is not None
        assert len(emb_list["chunks"]) > 0

    def test_embed_empty_document(self, upload_dir):
        content = b"short"
        doc_svc = DocumentService(upload_dir)
        upload_result = doc_svc.upload("empty.txt", content)
        doc_id = upload_result.document_id
        doc_svc.extract_document(doc_id)

        from backend.app.services.document_service import DocumentExtractionError
        with pytest.raises(DocumentExtractionError, match="chunking"):
            doc_svc.chunk_document(doc_id)


# =============================================================================
# API Route Tests
# =============================================================================

@pytest.fixture
def mock_services():
    doc_svc = Mock(spec=DocumentService)
    emb_svc = Mock(spec=EmbeddingService)
    emb_svc.get_embedding_stats.return_value = {
        "model_name": "test",
        "dimension": 768,
        "batch_size": 32,
        "embedding_version": "1.0.0",
        "cache_size": 0,
        "model_loaded": True,
    }
    return {"document": doc_svc, "embedding": emb_svc}


@pytest.fixture
def client(mock_services):
    with patch("backend.app.api.document_routes.get_services", return_value=mock_services):
        with TestClient(app) as c:
            yield c


class TestEmbeddingRoutes:
    def test_embed_success(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["document"].get_chunks_data.return_value = {
            "chunks": [{"chunk_id": "c1", "text": "test"}],
        }
        mock_services["embedding"].embed_document.return_value = {
            "document_id": "doc-1",
            "embedding_model": "BAAI/bge-base-en-v1.5",
            "embedding_version": "1.0.0",
            "dimension": 768,
            "created_at": "2026-01-01T00:00:00",
            "chunks": [{"chunk_id": "c1", "checksum": "abc", "vector": [0.1] * 768}],
        }

        response = client.post("/api/v1/documents/doc-1/embed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "embedded"
        assert data["chunks"] == 1
        assert data["dimension"] == 768
        assert data["model"] == "BAAI/bge-base-en-v1.5"

    def test_embed_not_found(self, client, mock_services):
        mock_services["document"].get_metadata.return_value = None

        response = client.post("/api/v1/documents/nonexistent/embed")
        assert response.status_code == 404

    def test_embed_not_chunked(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["document"].get_chunks_data.return_value = None

        response = client.post("/api/v1/documents/doc-1/embed")
        assert response.status_code == 400

    def test_list_embeddings_success(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["embedding"].get_embedding_list.return_value = {
            "document_id": "doc-1",
            "embedding_model": "BAAI/bge-base-en-v1.5",
            "embedding_version": "1.0.0",
            "dimension": 768,
            "created_at": "2026-01-01T00:00:00",
            "chunks": [
                {"chunk_id": "c1", "checksum": "abc", "dimension": 768},
            ],
        }

        response = client.get("/api/v1/documents/doc-1/embeddings")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-1"
        assert data["dimension"] == 768
        assert len(data["chunks"]) == 1
        assert "vector" not in data["chunks"][0]

    def test_list_embeddings_not_found(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["embedding"].get_embedding_list.return_value = None

        response = client.get("/api/v1/documents/doc-1/embeddings")
        assert response.status_code == 404

    def test_list_embeddings_doc_not_found(self, client, mock_services):
        mock_services["document"].get_metadata.return_value = None

        response = client.get("/api/v1/documents/nonexistent/embeddings")
        assert response.status_code == 404

    def test_get_single_embedding_success(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["embedding"].get_embedding.return_value = {
            "chunk_id": "c1",
            "checksum": "abc123",
            "dimension": 768,
            "model": "BAAI/bge-base-en-v1.5",
            "vector": [0.1] * 768,
        }

        response = client.get("/api/v1/documents/doc-1/embeddings/c1")
        assert response.status_code == 200
        data = response.json()
        assert data["chunk_id"] == "c1"
        assert data["dimension"] == 768
        assert len(data["vector"]) == 768

    def test_get_single_embedding_not_found(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["embedding"].get_embedding.return_value = None

        response = client.get("/api/v1/documents/doc-1/embeddings/nonexistent")
        assert response.status_code == 404

    def test_get_single_embedding_doc_not_found(self, client, mock_services):
        mock_services["document"].get_metadata.return_value = None

        response = client.get("/api/v1/documents/nonexistent/embeddings/c1")
        assert response.status_code == 404

    def test_embed_not_chunked_doc_not_found(self, client, mock_services):
        mock_services["document"].get_metadata.return_value = None

        response = client.post("/api/v1/documents/nonexistent/embed")
        assert response.status_code == 404
