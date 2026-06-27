"""Unit tests for the Vector Storage Layer (all Qdrant mocked)."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from fastapi.testclient import TestClient

from backend.app.vectorstore.base import VectorStore
from backend.app.vectorstore.exceptions import VectorStoreError, CollectionError, IndexError, ConnectionError
from backend.app.vectorstore.metadata_mapper import MetadataMapper
from backend.app.vectorstore.collection_manager import CollectionManager
from backend.app.main import app


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_chunk():
    return {
        "chunk_id": "chunk-001",
        "document_id": "doc-123",
        "section_name": "Introduction",
        "text": "This is a sample chunk text for testing.",
        "chunk_index": 0,
        "page_start": 1,
        "page_end": 1,
        "word_count": 10,
        "character_count": 50,
        "estimated_tokens": 13,
        "language": "en",
        "document_type": "report",
        "keywords": ["test", "sample"],
        "workspace_id": "default",
    }


@pytest.fixture
def sample_vector():
    return [0.1] * 768


@pytest.fixture
def sample_chunks_data():
    return {
        "chunks": [
            {"chunk_id": "c1", "document_id": "doc-1", "section_name": "Intro",
             "text": "First chunk text.", "chunk_index": 0,
             "page_start": 1, "page_end": 1, "word_count": 3, "character_count": 18},
            {"chunk_id": "c2", "document_id": "doc-1", "section_name": "Body",
             "text": "Second chunk text.", "chunk_index": 1,
             "page_start": 2, "page_end": 2, "word_count": 3, "character_count": 19},
        ],
    }


@pytest.fixture
def mock_qdrant_client():
    client = MagicMock()
    client.get_collection.return_value = MagicMock(
        points_count=42,
        config=MagicMock(
            params=MagicMock(
                vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
            )
        ),
    )
    return client


# =============================================================================
# MetadataMapper Tests
# =============================================================================

class TestMetadataMapper:
    def test_chunk_to_payload(self, sample_chunk):
        payload = MetadataMapper.chunk_to_payload(sample_chunk, embedding_version="1.0", checksum="abc123")
        assert payload["document_id"] == "doc-123"
        assert payload["chunk_id"] == "chunk-001"
        assert payload["section"] == "Introduction"
        assert payload["workspace_id"] == "default"
        assert payload["page"] == 1
        assert payload["language"] == "en"
        assert payload["document_type"] == "report"
        assert payload["keywords"] == ["test", "sample"]
        assert payload["embedding_version"] == "1.0"
        assert payload["checksum"] == "abc123"
        assert payload["word_count"] == 10
        assert payload["character_count"] == 50
        assert payload["text"] == "This is a sample chunk text for testing."
        assert payload["chunk_index"] == 0
        assert "created_at" in payload
        assert payload["importance_score"] == 1.0

    def test_chunk_to_payload_with_defaults(self):
        minimal = {"chunk_id": "c1", "document_id": "d1", "section_name": "", "text": "hello world", "chunk_index": 0}
        payload = MetadataMapper.chunk_to_payload(minimal)
        assert payload["workspace_id"] == "default"
        assert payload["page"] == 0
        assert payload["language"] == ""
        assert payload["document_type"] == ""
        assert payload["keywords"] == []
        assert payload["word_count"] == 2
        assert payload["character_count"] == 11
        assert payload["importance_score"] == 1.0

    def test_payload_to_chunk(self, sample_chunk):
        payload = MetadataMapper.chunk_to_payload(sample_chunk, embedding_version="1.0", checksum="abc123")
        chunk = MetadataMapper.payload_to_chunk(payload)
        assert chunk["document_id"] == "doc-123"
        assert chunk["chunk_id"] == "chunk-001"
        assert chunk["section"] == "Introduction"
        assert chunk["text"] == "This is a sample chunk text for testing."
        assert chunk["word_count"] == 10

    def test_payload_to_chunk_with_defaults(self):
        payload = {}
        chunk = MetadataMapper.payload_to_chunk(payload)
        assert chunk["document_id"] == ""
        assert chunk["workspace_id"] == "default"
        assert chunk["importance_score"] == 1.0
        assert chunk["word_count"] == 0

    def test_chunk_to_point(self, sample_chunk, sample_vector):
        point = MetadataMapper.chunk_to_point(sample_chunk, sample_vector, embedding_version="1.0", checksum="abc")
        assert point["id"] == "chunk-001"
        assert point["vector"] == sample_vector
        assert point["payload"]["document_id"] == "doc-123"
        assert point["payload"]["chunk_id"] == "chunk-001"

    def test_build_filter_document_id(self):
        f = MetadataMapper.build_filter(document_id="doc-123")
        assert f == {"must": [{"key": "document_id", "match": {"value": "doc-123"}}]}

    def test_build_filter_chunk_id(self):
        f = MetadataMapper.build_filter(chunk_id="chunk-001")
        assert f == {"must": [{"key": "chunk_id", "match": {"value": "chunk-001"}}]}

    def test_build_filter_both(self):
        f = MetadataMapper.build_filter(document_id="doc-123", chunk_id="chunk-001")
        assert len(f["must"]) == 2

    def test_build_filter_empty(self):
        f = MetadataMapper.build_filter()
        assert f == {}

    def test_payload_schema(self):
        schema = MetadataMapper.get_payload_schema()
        assert "document_id" in schema
        assert "chunk_id" in schema
        assert "text" in schema
        assert "keywords" in schema
        assert "importance_score" in schema
        assert len(schema) == 17


# =============================================================================
# CollectionManager Tests
# =============================================================================

class TestCollectionManager:
    def test_initialize_collection_exists(self, mock_qdrant_client):
        mgr = CollectionManager(mock_qdrant_client, vector_dimension=768, distance_metric="Cosine")
        mgr.initialize()
        mock_qdrant_client.get_collection.assert_called_with("knowledge_brain")

    def test_initialize_creates_collection(self, mock_qdrant_client):
        mock_qdrant_client.get_collection.side_effect = Exception("not found")
        mgr = CollectionManager(mock_qdrant_client, vector_dimension=768, distance_metric="Cosine")
        mgr.initialize()
        mock_qdrant_client.recreate_collection.assert_called_once()

    def test_dimension_mismatch_raises(self, mock_qdrant_client):
        mock_qdrant_client.get_collection.return_value = MagicMock(
            config=MagicMock(params=MagicMock(vectors=MagicMock(size=384, distance=MagicMock(__str__=lambda self: "Cosine"))))
        )
        mgr = CollectionManager(mock_qdrant_client, vector_dimension=768, distance_metric="Cosine")
        with pytest.raises(CollectionError, match="Dimension mismatch"):
            mgr.initialize()

    def test_collection_exists_true(self, mock_qdrant_client):
        mgr = CollectionManager(mock_qdrant_client)
        assert mgr.collection_exists() is True

    def test_collection_exists_false(self, mock_qdrant_client):
        mock_qdrant_client.get_collection.side_effect = Exception("not found")
        mgr = CollectionManager(mock_qdrant_client)
        assert mgr.collection_exists() is False

    def test_delete_collection(self, mock_qdrant_client):
        mgr = CollectionManager(mock_qdrant_client)
        mgr.delete_collection()
        mock_qdrant_client.delete_collection.assert_called_with("knowledge_brain")

    def test_get_info(self, mock_qdrant_client):
        mgr = CollectionManager(mock_qdrant_client, vector_dimension=768, distance_metric="Cosine")
        info = mgr.get_info()
        assert info["collection_name"] == "knowledge_brain"
        assert info["vector_dimension"] == 768
        assert info["distance_metric"] == "Cosine"

    def test_get_vector_count(self, mock_qdrant_client):
        mgr = CollectionManager(mock_qdrant_client)
        count = mgr._get_vector_count()
        assert count == 42


# =============================================================================
# QdrantVectorStore Tests
# =============================================================================

class TestQdrantVectorStore:
    def test_initialization_with_local_path(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            mock_client_class.assert_called_once_with(path="/tmp/test_qdrant")

    def test_initialization_with_remote(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(host="qdrant.example.com", port=6333)
            store.initialize()

            mock_client_class.assert_called_once_with(host="qdrant.example.com", port=6333)

    def test_initialize_idempotent(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()
            store.initialize()
            assert mock_client_class.call_count == 1

    def test_connect_error_raises_connection_error(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_client_class.side_effect = Exception("Connection refused")
            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(host="localhost", port=6333)
            with pytest.raises(ConnectionError, match="Failed to connect"):
                store.initialize()

    def test_upsert_document(self, sample_chunks_data):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            chunks = [
                {**chunk, "vector": [0.1] * 768, "checksum": "abc", "embedding_version": "1.0"}
                for chunk in sample_chunks_data["chunks"]
            ]

            count = store.upsert_document("doc-1", chunks)
            assert count == 2
            mock_instance.upsert.assert_called_once()

    def test_upsert_document_empty(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()
            count = store.upsert_document("doc-1", [])
            assert count == 0

    def test_upsert_chunks(self, sample_chunks_data):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            chunks = [
                {**chunk, "vector": [0.1] * 768, "checksum": "abc", "embedding_version": "1.0"}
                for chunk in sample_chunks_data["chunks"]
            ]

            count = store.upsert_chunks(chunks)
            assert count == 2
            mock_instance.upsert.assert_called_once()

    def test_delete_document(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=10,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            result = store.delete_document("doc-1")
            assert result is True
            mock_instance.delete.assert_called_once()

    def test_delete_chunk(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=10,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            result = store.delete_chunk("chunk-001")
            assert result is True
            mock_instance.delete.assert_called_once()

    def test_get_chunk_found(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=10,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )

            from qdrant_client.http.models import Record
            mock_point = MagicMock(spec=Record)
            mock_point.id = "chunk-001"
            mock_point.vector = [0.1] * 768
            mock_point.payload = {
                "document_id": "doc-1",
                "chunk_id": "chunk-001",
                "workspace_id": "default",
                "text": "test",
                "section": "Intro",
            }
            mock_instance.retrieve.return_value = [mock_point]
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            result = store.get_chunk("chunk-001")
            assert result is not None
            assert result["chunk_id"] == "chunk-001"
            assert result["document_id"] == "doc-1"
            assert "vector" in result

    def test_get_chunk_not_found(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=10,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_instance.retrieve.return_value = []
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            result = store.get_chunk("nonexistent")
            assert result is None

    def test_count(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=42,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            assert store.count() == 42

    def test_health_healthy(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=42,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            health = store.health()
            assert health["status"] == "healthy"

    def test_health_not_initialized(self):
        from backend.app.vectorstore.qdrant_store import QdrantVectorStore
        store = QdrantVectorStore(local_path="/tmp/test_qdrant")
        health = store.health()
        assert health["status"] == "not_initialized"

    def test_close(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()
            store.close()
            mock_instance.close.assert_called_once()

    def test_create_collection(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()
            store.create_collection()
            mock_instance.recreate_collection.assert_called()

    def test_delete_collection(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()
            store.delete_collection()
            mock_instance.delete_collection.assert_called_with("knowledge_brain")

    def test_collection_exists_method(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()
            assert store.collection_exists() is True

    def test_upsert_failure_raises_index_error(self):
        with patch("backend.app.vectorstore.qdrant_store.QdrantClient") as mock_client_class:
            mock_instance = MagicMock()
            mock_instance.get_collection.return_value = MagicMock(
                points_count=0,
                config=MagicMock(
                    params=MagicMock(
                        vectors=MagicMock(size=768, distance=MagicMock(__str__=lambda self: "Cosine"))
                    )
                ),
            )
            mock_instance.upsert.side_effect = Exception("Storage full")
            mock_client_class.return_value = mock_instance

            from backend.app.vectorstore.qdrant_store import QdrantVectorStore
            store = QdrantVectorStore(local_path="/tmp/test_qdrant")
            store.initialize()

            chunks = [{"chunk_id": "c1", "document_id": "d1", "text": "test", "chunk_index": 0, "vector": [0.1] * 768}]
            with pytest.raises(IndexError, match="Failed to upsert"):
                store.upsert_document("d1", chunks)

    def test_abstract_class_cannot_be_instantiated(self):
        with pytest.raises(TypeError):
            VectorStore()


# =============================================================================
# Exception Tests
# =============================================================================

class TestExceptions:
    def test_vector_store_error(self):
        err = VectorStoreError("test error")
        assert err.message == "test error"
        assert err.status_code == 500

    def test_vector_store_error_custom_status(self):
        err = VectorStoreError("bad request", status_code=400)
        assert err.status_code == 400

    def test_collection_error(self):
        err = CollectionError("collection failed")
        assert isinstance(err, VectorStoreError)

    def test_index_error(self):
        err = IndexError("index failed")
        assert isinstance(err, VectorStoreError)

    def test_connection_error(self):
        err = ConnectionError("connection failed")
        assert isinstance(err, VectorStoreError)
        assert err.status_code == 503


# =============================================================================
# API Route Tests (mocked services)
# =============================================================================

@pytest.fixture
def mock_index_services():
    from unittest.mock import Mock
    doc_svc = MagicMock()
    from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus
    from datetime import datetime, timezone
    doc_svc.get_metadata.return_value = DocumentMetadata(
        id="doc-1", filename="test.pdf", file_type=FileType.pdf,
        size=100, status=DocumentStatus.extracted,
        upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        storage_path="/tmp/test.pdf",
    )
    doc_svc.get_chunks_data.return_value = {"chunks": [{"chunk_id": "c1", "text": "test"}]}

    emb_svc = MagicMock()
    emb_svc.index_document.return_value = {
        "status": "indexed",
        "vectors": 1,
        "collection": "knowledge_brain",
    }
    emb_svc.deindex_document.return_value = {
        "status": "deindexed",
        "document_id": "doc-1",
        "vectors_removed": 1,
    }

    vs = MagicMock()
    vs.health.return_value = {
        "status": "healthy",
        "collection": "knowledge_brain",
        "vectors": 42,
        "collection_exists": True,
        "client_version": "1.9.0",
    }

    return {
        "document": doc_svc,
        "embedding": MagicMock(),
        "embedding_with_store": emb_svc,
        "vector_store": vs,
    }


@pytest.fixture
def index_client(mock_index_services):
    with patch("backend.app.api.document_routes.get_services", return_value=mock_index_services):
        with patch("backend.app.api.routes.get_services", return_value=mock_index_services):
            with TestClient(app) as c:
                yield c


class TestIndexRoutes:
    def test_index_success(self, index_client):
        response = index_client.post("/api/v1/documents/doc-1/index")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "indexed"
        assert data["vectors"] == 1
        assert data["collection"] == "knowledge_brain"

    def test_index_document_not_found(self, index_client, mock_index_services):
        mock_index_services["document"].get_metadata.return_value = None
        response = index_client.post("/api/v1/documents/nonexistent/index")
        assert response.status_code == 404

    def test_index_not_chunked(self, index_client, mock_index_services):
        mock_index_services["document"].get_chunks_data.return_value = None
        response = index_client.post("/api/v1/documents/doc-1/index")
        assert response.status_code == 400

    def test_deindex_success(self, index_client):
        response = index_client.delete("/api/v1/documents/doc-1/index")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deindexed"
        assert data["vectors_removed"] == 1

    def test_deindex_not_found(self, index_client, mock_index_services):
        mock_index_services["document"].get_metadata.return_value = None
        response = index_client.delete("/api/v1/documents/nonexistent/index")
        assert response.status_code == 404

    def test_vectorstore_health(self, index_client):
        response = index_client.get("/api/v1/vectorstore/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["collection"] == "knowledge_brain"
        assert data["vectors"] == 42

    def test_vectorstore_health_no_vector_store(self, index_client, mock_index_services):
        mock_index_services.pop("vector_store")
        response = index_client.get("/api/v1/vectorstore/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_configured"
