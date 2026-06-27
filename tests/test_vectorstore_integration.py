"""Integration tests for the Vector Storage Layer with real embedded Qdrant."""
import uuid
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from backend.app.vectorstore.qdrant_store import QdrantVectorStore
from backend.app.vectorstore.collection_manager import CollectionManager
from backend.app.vectorstore.metadata_mapper import MetadataMapper
from backend.app.vectorstore.exceptions import CollectionError


@pytest.fixture
def qdrant_path(tmp_path):
    return str(tmp_path / "qdrant_storage")


@pytest.fixture
def vector_store(qdrant_path):
    store = QdrantVectorStore(
        local_path=qdrant_path,
        collection_name="test_knowledge_brain",
        vector_dimension=768,
        distance_metric="Cosine",
    )
    store.initialize()
    yield store
    try:
        store.close()
    except Exception:
        pass


@pytest.fixture
def sample_chunks():
    doc_id = str(uuid.uuid4())
    return [
        {
            "chunk_id": f"{doc_id}-c1",
            "document_id": doc_id,
            "section_name": "Introduction",
            "text": "This is the first chunk of the document for integration testing.",
            "chunk_index": 0,
            "page_start": 1,
            "page_end": 1,
            "word_count": 12,
            "character_count": 70,
            "estimated_tokens": 16,
            "language": "en",
            "document_type": "report",
            "keywords": ["test", "integration"],
            "workspace_id": "default",
            "vector": [0.1] * 768,
            "checksum": "abc123",
            "embedding_version": "1.0.0",
        },
        {
            "chunk_id": f"{doc_id}-c2",
            "document_id": doc_id,
            "section_name": "Methodology",
            "text": "This is the second chunk with more detailed methodology content.",
            "chunk_index": 1,
            "page_start": 2,
            "page_end": 3,
            "word_count": 12,
            "character_count": 72,
            "estimated_tokens": 16,
            "language": "en",
            "document_type": "report",
            "keywords": ["methodology", "integration"],
            "workspace_id": "default",
            "vector": [0.2] * 768,
            "checksum": "def456",
            "embedding_version": "1.0.0",
        },
    ], doc_id


# =============================================================================
# QdrantVectorStore Integration Tests
# =============================================================================

class TestQdrantVectorStoreIntegration:
    def test_initialize_and_collection_exists(self, qdrant_path):
        store = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_integration",
            vector_dimension=768,
        )
        assert store.collection_exists() is False
        store.initialize()
        assert store.collection_exists() is True
        store.close()

    def test_initialize_creates_collection(self, qdrant_path):
        store = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_auto_create",
            vector_dimension=768,
        )
        store.initialize()
        assert store.collection_exists() is True
        store.close()

    def test_upsert_and_count(self, vector_store, sample_chunks):
        chunks, doc_id = sample_chunks
        count = vector_store.upsert_document(doc_id, chunks)
        assert count == 2
        assert vector_store.count() == 2

    def test_get_chunk(self, vector_store, sample_chunks):
        chunks, doc_id = sample_chunks
        vector_store.upsert_document(doc_id, chunks)

        result = vector_store.get_chunk(chunks[0]["chunk_id"])
        assert result is not None
        assert result["chunk_id"] == chunks[0]["chunk_id"]
        assert result["document_id"] == doc_id
        assert "text" in result
        assert "vector" in result

    def test_get_chunk_not_found(self, vector_store):
        result = vector_store.get_chunk("nonexistent-chunk-id")
        assert result is None

    def test_upsert_chunks(self, vector_store, sample_chunks):
        chunks, doc_id = sample_chunks
        count = vector_store.upsert_chunks(chunks)
        assert count == 2
        assert vector_store.count() == 2

    def test_delete_document(self, vector_store, sample_chunks):
        chunks, doc_id = sample_chunks
        vector_store.upsert_document(doc_id, chunks)
        assert vector_store.count() == 2

        vector_store.delete_document(doc_id)
        assert vector_store.count() == 0

    def test_delete_chunk(self, vector_store, sample_chunks):
        chunks, doc_id = sample_chunks
        vector_store.upsert_document(doc_id, chunks)

        vector_store.delete_chunk(chunks[0]["chunk_id"])
        result = vector_store.get_chunk(chunks[0]["chunk_id"])
        assert result is None

    def test_health(self, vector_store, sample_chunks):
        chunks, doc_id = sample_chunks
        health_before = vector_store.health()
        assert health_before["status"] == "healthy"
        assert health_before["collection"] == "test_knowledge_brain"

        vector_store.upsert_document(doc_id, chunks)
        health_after = vector_store.health()
        assert health_after["vectors"] == 2

    def test_multiple_documents(self, vector_store):
        doc1_id = str(uuid.uuid4())
        doc2_id = str(uuid.uuid4())
        chunks1 = [
            {"chunk_id": f"{doc1_id}-c1", "document_id": doc1_id, "section_name": "S1",
             "text": "Doc1 chunk1", "chunk_index": 0, "page_start": 1, "page_end": 1,
             "word_count": 2, "character_count": 11, "vector": [0.1] * 768,
             "checksum": "a1", "embedding_version": "1.0"},
            {"chunk_id": f"{doc1_id}-c2", "document_id": doc1_id, "section_name": "S2",
             "text": "Doc1 chunk2", "chunk_index": 1, "page_start": 2, "page_end": 2,
             "word_count": 2, "character_count": 11, "vector": [0.2] * 768,
             "checksum": "a2", "embedding_version": "1.0"},
        ]
        chunks2 = [
            {"chunk_id": f"{doc2_id}-c1", "document_id": doc2_id, "section_name": "S1",
             "text": "Doc2 chunk1", "chunk_index": 0, "page_start": 1, "page_end": 1,
             "word_count": 2, "character_count": 11, "vector": [0.3] * 768,
             "checksum": "b1", "embedding_version": "1.0"},
        ]

        vector_store.upsert_document(doc1_id, chunks1)
        vector_store.upsert_document(doc2_id, chunks2)
        assert vector_store.count() == 3

        vector_store.delete_document(doc1_id)
        assert vector_store.count() == 1

    def test_collection_manager_dimension_validation(self, qdrant_path):
        store1 = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_dim_validation",
            vector_dimension=768,
        )
        store1.initialize()
        store1.close()

        with pytest.raises(CollectionError, match="Dimension mismatch"):
            store2 = QdrantVectorStore(
                local_path=qdrant_path,
                collection_name="test_dim_validation",
                vector_dimension=384,
            )
            store2.initialize()
            store2.close()

    def test_create_and_delete_collection(self, qdrant_path):
        store = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_create_delete",
            vector_dimension=768,
        )
        store.initialize()
        assert store.collection_exists() is True

        store.delete_collection()
        assert store.collection_exists() is False
        store.close()

    def test_close_and_reopen(self, qdrant_path, sample_chunks):
        chunks, doc_id = sample_chunks

        store1 = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_persistence",
            vector_dimension=768,
        )
        store1.initialize()
        store1.upsert_document(doc_id, chunks)
        count1 = store1.count()
        store1.close()

        store2 = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_persistence",
            vector_dimension=768,
        )
        store2.initialize()
        assert store2.count() == count1
        result = store2.get_chunk(chunks[0]["chunk_id"])
        assert result is not None
        store2.close()


# =============================================================================
# MetadataMapper Integration Tests
# =============================================================================

class TestMetadataMapperIntegration:
    def test_full_roundtrip(self, vector_store):
        chunk = {
            "chunk_id": "roundtrip-c1",
            "document_id": "roundtrip-doc",
            "section_name": "Test Section",
            "text": "Round trip test content for verification.",
            "chunk_index": 0,
            "page_start": 1,
            "page_end": 2,
            "word_count": 7,
            "character_count": 45,
            "language": "en",
            "document_type": "test",
            "keywords": ["roundtrip", "test"],
            "workspace_id": "default",
            "vector": [0.5] * 768,
            "checksum": "roundtrip123",
            "embedding_version": "1.0.0",
        }

        vector_store.upsert_chunks([chunk])
        retrieved = vector_store.get_chunk("roundtrip-c1")
        assert retrieved is not None
        assert retrieved["chunk_id"] == "roundtrip-c1"
        assert retrieved["document_id"] == "roundtrip-doc"
        assert retrieved["section"] == "Test Section"
        assert retrieved["text"] == "Round trip test content for verification."
        assert retrieved["language"] == "en"
        assert retrieved["document_type"] == "test"
        assert retrieved["keywords"] == ["roundtrip", "test"]
        assert retrieved["word_count"] == 7
        assert retrieved["character_count"] == 45
        assert retrieved["chunk_index"] == 0

    def test_payload_schema_invariants(self):
        schema = MetadataMapper.get_payload_schema()
        assert "document_id" in schema
        assert "chunk_id" in schema
        assert "workspace_id" in schema
        assert "title" in schema
        assert "section" in schema
        assert "page" in schema
        assert "language" in schema
        assert "document_type" in schema
        assert "keywords" in schema
        assert "embedding_version" in schema
        assert "checksum" in schema
        assert "created_at" in schema
        assert "importance_score" in schema
        assert "word_count" in schema
        assert "character_count" in schema
        assert "text" in schema
        assert "chunk_index" in schema


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    def test_upsert_empty_chunks(self, vector_store):
        count = vector_store.upsert_document("empty-doc", [])
        assert count == 0

    def test_upsert_chunks_without_vector_skipped(self, vector_store):
        chunks = [
            {"chunk_id": "no-vec", "document_id": "d1", "text": "no vector",
             "vector": [], "checksum": "abc", "embedding_version": "1.0"},
        ]
        count = vector_store.upsert_document("d1", chunks)
        assert count == 0

    def test_delete_nonexistent_document(self, vector_store):
        result = vector_store.delete_document("nonexistent")
        assert result is True

    def test_delete_nonexistent_chunk(self, vector_store):
        result = vector_store.delete_chunk("nonexistent")
        assert result is True

    def test_count_empty_collection(self, qdrant_path):
        store = QdrantVectorStore(
            local_path=qdrant_path,
            collection_name="test_empty",
            vector_dimension=768,
        )
        store.initialize()
        assert store.count() == 0
        store.close()
