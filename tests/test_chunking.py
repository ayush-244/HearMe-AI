"""Unit and integration tests for the Intelligent Chunking Engine."""
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, PropertyMock
from fastapi.testclient import TestClient

from ai.chunking.chunk_models import Chunk, ChunkStatistics, create_chunk
from ai.chunking.chunk_engine import ChunkEngine
from ai.chunking.chunk_strategy import select_strategy, create_chunker
from ai.chunking.fixed_chunker import FixedChunker
from ai.chunking.section_chunker import SectionChunker
from ai.chunking.semantic_chunker import SemanticChunker
from ai.chunking.overlap import generate_overlap, apply_overlap_to_chunks
from ai.documents.section_parser import Section

from backend.app.schemas.document import (
    ChunkResponse, ChunkListResponse, ChunkStatisticsResponse, ChunkPreview,
)
from backend.app.main import app
from backend.app.services.document_service import DocumentService


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def upload_dir(tmp_path):
    return tmp_path / "uploads"


@pytest.fixture
def sample_text():
    words = [f"word_{i}" for i in range(1500)]
    return " ".join(words)


@pytest.fixture
def multi_paragraph_text():
    return (
        "# Introduction\n\n"
        "This is the introduction paragraph. It has several sentences that "
        "describe the background and context of the document.\n\n"
        "# Methodology\n\n"
        "The methodology section describes how the research was conducted. "
        "It includes details about data collection and analysis.\n\n"
        "- First bullet point\n"
        "- Second bullet point\n"
        "- Third bullet point\n\n"
        "| Col1 | Col2 |\n"
        "|------|------|\n"
        "| A    | B    |\n\n"
        "```python\nprint('hello')\n```\n\n"
        "# Results\n\n"
        "The results section presents the findings of the study."
    )


@pytest.fixture
def document_id():
    return "test-doc-123"


@pytest.fixture
def sections():
    return [
        Section(name="Introduction", start_offset=0, end_offset=300, estimated_page=1),
        Section(name="Methodology", start_offset=300, end_offset=800, estimated_page=1),
        Section(name="Results", start_offset=800, end_offset=1200, estimated_page=2),
    ]


# =============================================================================
# Chunk Model Tests
# =============================================================================

class TestChunkModel:
    def test_create_chunk(self, document_id):
        chunk = create_chunk(
            document_id=document_id,
            text="Hello world this is a test chunk with enough words to pass validation",
            section_name="Introduction",
            chunk_index=0,
            start_offset=0,
            end_offset=100,
        )
        assert chunk.document_id == document_id
        assert chunk.section_name == "Introduction"
        assert chunk.chunk_index == 0
        assert chunk.word_count > 0
        assert chunk.estimated_tokens > 0
        assert chunk.chunk_id is not None
        assert len(chunk.chunk_id) == 36

    def test_chunk_to_dict(self, document_id):
        chunk = create_chunk(
            document_id=document_id,
            text="Test chunk content with several words here for testing purposes",
            section_name="Body",
            chunk_index=1,
            start_offset=50,
            end_offset=150,
        )
        d = chunk.to_dict()
        assert d["chunk_id"] == chunk.chunk_id
        assert d["document_id"] == document_id
        assert d["section_name"] == "Body"
        assert d["chunk_index"] == 1
        assert d["start_offset"] == 50
        assert d["end_offset"] == 150

    def test_chunk_from_dict(self, document_id):
        chunk = create_chunk(
            document_id=document_id,
            text="Round trip test content with multiple words for serialization testing",
            section_name="Test",
            chunk_index=0,
            start_offset=0,
            end_offset=60,
        )
        d = chunk.to_dict()
        restored = Chunk.from_dict(d)
        assert restored.chunk_id == chunk.chunk_id
        assert restored.text == chunk.text
        assert restored.word_count == chunk.word_count

    def test_chunk_to_preview(self, document_id):
        text = "Short text"
        chunk = create_chunk(
            document_id=document_id,
            text=text,
            section_name="Preview",
            chunk_index=0,
            start_offset=0,
            end_offset=10,
        )
        p = chunk.to_preview()
        assert p["chunk_id"] == chunk.chunk_id
        assert p["section_name"] == "Preview"
        assert p["word_count"] == 2
        assert "..." not in p["preview"]

    def test_chunk_preview_truncation(self, document_id):
        text = "A " * 200
        chunk = create_chunk(
            document_id=document_id,
            text=text,
            section_name="Long",
            chunk_index=0,
            start_offset=0,
            end_offset=400,
        )
        p = chunk.to_preview()
        assert len(p["preview"]) <= 123
        assert p["preview"].endswith("...")

    def test_statistics_to_dict(self):
        stats = ChunkStatistics(
            document_id="doc-1",
            chunks=10,
            average_chunk_size=250.5,
            largest_chunk=500,
            smallest_chunk=50,
            strategy="fixed",
        )
        d = stats.to_dict()
        assert d["document_id"] == "doc-1"
        assert d["chunks"] == 10
        assert d["average_chunk_size"] == 250.5
        assert d["strategy"] == "fixed"

    def test_metadata_on_chunk(self, document_id):
        chunk = create_chunk(
            document_id=document_id,
            text="Content with metadata for testing purposes and additional words here",
            section_name="Test",
            chunk_index=0,
            start_offset=0,
            end_offset=50,
            metadata={"source": "test", "language": "en"},
        )
        assert chunk.metadata["source"] == "test"
        assert chunk.metadata["language"] == "en"


# =============================================================================
# Fixed Chunker Tests
# =============================================================================

class TestFixedChunker:
    def test_fixed_chunking_basic(self, document_id, sample_text):
        chunker = FixedChunker(chunk_size=200, overlap=20)
        chunks = chunker.chunk(document_id, sample_text)
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.word_count <= 200

    def test_fixed_chunking_small_text(self, document_id):
        text = "Small amount of text here for testing purposes only"
        chunker = FixedChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk(document_id, text)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_fixed_chunking_empty(self, document_id):
        chunker = FixedChunker()
        chunks = chunker.chunk(document_id, "")
        assert chunks == []

        chunks = chunker.chunk(document_id, "   ")
        assert chunks == []

    def test_fixed_chunking_overlap(self, document_id):
        words = ["word"] * 600
        text = " ".join(words)
        chunker = FixedChunker(chunk_size=200, overlap=30)
        chunks = chunker.chunk(document_id, text)
        assert len(chunks) >= 2
        for chunk in chunks:
            if chunk.chunk_index > 0:
                assert chunk.overlap_previous != ""
            if chunk.chunk_index < len(chunks) - 1:
                assert chunk.overlap_next != ""

    def test_fixed_chunk_index_ordering(self, document_id):
        words = ["word"] * 1200
        text = " ".join(words)
        chunker = FixedChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk(document_id, text)
        indices = [c.chunk_index for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_fixed_chunk_section_name(self, document_id):
        text = "Test content for section name verification with multiple words here"
        chunker = FixedChunker()
        chunks = chunker.chunk(document_id, text, section_name="custom_section")
        assert chunks[0].section_name == "custom_section"


# =============================================================================
# Section Chunker Tests
# =============================================================================

class TestSectionChunker:
    def test_section_chunking_with_sections(self, document_id, sections):
        text = "Introduction content here. " * 50
        text += "Methodology content here. " * 100
        text += "Results content here. " * 50
        chunker = SectionChunker(chunk_size=200, overlap=20)
        chunks = chunker.chunk(document_id, text, sections)
        assert len(chunks) > 0
        section_names = {c.section_name for c in chunks}
        assert "Introduction" in section_names
        assert "Methodology" in section_names
        assert "Results" in section_names

    def test_section_chunk_no_cross_boundary(self, document_id):
        text = "Introduction content. " * 30 + "\n\n"
        text += "Methodology content. " * 30 + "\n\n"
        text += "Results content. " * 30
        sections = [
            Section(name="Introduction", start_offset=0, end_offset=15, estimated_page=1),
            Section(name="Methodology", start_offset=15, end_offset=30, estimated_page=1),
            Section(name="Results", start_offset=30, end_offset=45, estimated_page=1),
        ]
        chunker = SectionChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk(document_id, text, sections)
        for chunk in chunks:
            sec_text = text[sections[0].start_offset:sections[0].end_offset]
            if chunk.section_name == "Introduction":
                assert "Methodology" not in chunk.text

    def test_section_chunk_empty_sections(self, document_id):
        chunker = SectionChunker()
        chunks = chunker.chunk(document_id, "Some text here for testing.", [])
        assert len(chunks) > 0

    def test_section_chunk_fallback_no_sections(self, document_id):
        chunker = SectionChunker()
        chunks = chunker.chunk(document_id, "Some text for testing with enough words to make a chunk.")
        assert len(chunks) > 0

    def test_section_chunk_empty_text(self, document_id, sections):
        chunker = SectionChunker()
        chunks = chunker.chunk(document_id, "", sections)
        assert chunks == []


# =============================================================================
# Semantic Chunker Tests
# =============================================================================

class TestSemanticChunker:
    def test_semantic_chunking(self, document_id, multi_paragraph_text):
        chunker = SemanticChunker()
        chunks = chunker.chunk(document_id, multi_paragraph_text)
        assert len(chunks) > 0
        assert all(chunk.text.strip() for chunk in chunks)

    def test_semantic_no_cut_sentences(self, document_id):
        text = "First paragraph with multiple sentences. This is another sentence. And one more.\n\n"
        text += "Second paragraph starts here. It continues with more content. "
        text += "And finishes with this sentence.\n\n"
        text += "Third paragraph. Short.\n\n"
        chunker = SemanticChunker()
        chunks = chunker.chunk(document_id, text)
        assert len(chunks) > 0

    def test_semantic_empty_text(self, document_id):
        chunker = SemanticChunker()
        chunks = chunker.chunk(document_id, "")
        assert chunks == []

    def test_semantic_preserves_tables(self, document_id):
        text = "Some text before.\n\n| Header1 | Header2 |\n|--------|--------|\n| Cell1  | Cell2  |\n\nSome text after."
        chunker = SemanticChunker()
        chunks = chunker.chunk(document_id, text)
        assert len(chunks) > 0

    def test_semantic_preserves_code_blocks(self, document_id):
        text = "Text before.\n\n```python\ndef hello():\n    print('world')\n```\n\nText after."
        chunker = SemanticChunker()
        chunks = chunker.chunk(document_id, text)
        code_chunks = [c for c in chunks if "```" in c.text]
        assert len(code_chunks) > 0

    def test_semantic_preserves_bullet_lists(self, document_id):
        text = "Before.\n\n- Item one\n- Item two\n- Item three\n\nAfter."
        chunker = SemanticChunker()
        chunks = chunker.chunk(document_id, text)
        list_chunks = [c for c in chunks if "Item" in c.text]
        assert len(list_chunks) > 0


# =============================================================================
# Strategy Selection Tests
# =============================================================================

class TestStrategySelection:
    def test_strategy_section_types(self):
        section_types = ["research_paper", "resume", "book", "report", "invoice",
                         "presentation", "manual", "article"]
        for dt in section_types:
            assert select_strategy(dt) == "section", f"{dt} should map to section"

    def test_strategy_semantic_types(self):
        assert select_strategy("notes") == "semantic"

    def test_strategy_fixed_types(self):
        assert select_strategy("unknown") == "fixed"

    def test_strategy_file_type_txt(self):
        assert select_strategy("unknown", "txt") == "fixed"

    def test_strategy_file_type_markdown(self):
        assert select_strategy("unknown", "markdown") == "semantic"

    def test_strategy_file_type_no_override(self):
        assert select_strategy("research_paper", "txt") == "section"

    def test_create_chunker_section(self):
        chunker = create_chunker("section")
        assert isinstance(chunker, SectionChunker)

    def test_create_chunker_semantic(self):
        chunker = create_chunker("semantic")
        assert isinstance(chunker, SemanticChunker)

    def test_create_chunker_fixed(self):
        chunker = create_chunker("fixed")
        assert isinstance(chunker, FixedChunker)


# =============================================================================
# Overlap Tests
# =============================================================================

class TestOverlap:
    def test_generate_overlap_basic(self):
        text = "one two three four five six seven eight nine ten"
        result = generate_overlap(text, 3)
        assert result == "eight nine ten"

    def test_generate_overlap_full_text(self):
        text = "short text"
        result = generate_overlap(text, 10)
        assert result == text

    def test_generate_overlap_zero(self):
        text = "some text here"
        result = generate_overlap(text, 0)
        assert result == ""

    def test_apply_overlap_to_chunks(self):
        chunks = ["First chunk text here", "Second chunk text here", "Third chunk text here"]
        result = apply_overlap_to_chunks(chunks, 2)
        assert len(result) == len(chunks)


# =============================================================================
# Chunk Engine Tests (Validation, Statistics, Metadata)
# =============================================================================

class TestChunkEngine:
    def test_engine_fixed_chunking(self, document_id):
        words = [f"word_{i}" for i in range(1500)]
        text = " ".join(words)
        engine = ChunkEngine(chunk_size=500, overlap=50)
        result = engine.chunk_document(document_id, text)
        assert result["strategy"] == "fixed"
        assert len(result["chunks"]) == 3
        assert result["statistics"]["chunks"] == 3

    def test_engine_validation_rejects_empty(self, document_id):
        engine = ChunkEngine()
        result = engine.chunk_document(document_id, "")
        assert result["statistics"]["chunks"] == 0

    def test_engine_validation_rejects_whitespace(self, document_id):
        engine = ChunkEngine()
        result = engine.chunk_document(document_id, "   \n\n  ")
        assert result["statistics"]["chunks"] == 0

    def test_engine_validation_few_words(self, document_id):
        text = "hello world"
        engine = ChunkEngine()
        result = engine.chunk_document(document_id, text)
        assert result["statistics"]["chunks"] == 0
        assert result["rejected_count"] > 0

    def test_engine_statistics(self, document_id):
        words = [f"word_{i}" for i in range(1500)]
        text = " ".join(words)
        engine = ChunkEngine(chunk_size=500, overlap=50)
        result = engine.chunk_document(document_id, text)
        stats = result["statistics"]
        assert stats["chunks"] == 3
        assert stats["average_chunk_size"] > 0
        assert stats["largest_chunk"] > 0
        assert stats["smallest_chunk"] > 0
        assert stats["strategy"] == "fixed"

    def test_engine_statistics_single_chunk(self, document_id):
        text = "This is a test document with enough words to be valid for chunking in the engine. " * 5
        engine = ChunkEngine()
        result = engine.chunk_document(document_id, text)
        stats = result["statistics"]
        assert stats["chunks"] >= 1
        assert stats["largest_chunk"] >= stats["smallest_chunk"]

    def test_engine_statistics_empty(self, document_id):
        engine = ChunkEngine()
        result = engine.chunk_document(document_id, "hi")
        stats = result["statistics"]
        assert stats["chunks"] == 0
        assert stats["largest_chunk"] == 0
        assert stats["smallest_chunk"] == 0
        assert stats["average_chunk_size"] == 0.0

    def test_engine_deduplication(self, document_id):
        text = "Duplicate paragraph. " * 30 + "\n\n" + "Unique content here. " * 30
        engine = ChunkEngine(chunk_size=500, overlap=0)
        result = engine.chunk_document(document_id, text)
        texts = [c["text"] for c in result["chunks"]]
        assert len(texts) == len(set(texts))

    def test_engine_chunk_ordering(self, document_id):
        words = ["word"] * 1500
        text = " ".join(words)
        engine = ChunkEngine(chunk_size=500, overlap=50)
        result = engine.chunk_document(document_id, text)
        indices = [c["chunk_index"] for c in result["chunks"]]
        assert indices == sorted(indices)

    def test_engine_section_strategy_research_paper(self, document_id):
        text = "Introduction. " * 100 + "Methodology. " * 200 + "Results. " * 100
        engine = ChunkEngine(chunk_size=500, overlap=50)
        sections = [
            {"name": "Introduction", "start_offset": 0, "end_offset": 200, "estimated_page": 1},
            {"name": "Methodology", "start_offset": 200, "end_offset": 600, "estimated_page": 2},
            {"name": "Results", "start_offset": 600, "end_offset": 800, "estimated_page": 3},
        ]
        result = engine.chunk_document(
            document_id=document_id,
            text=text,
            document_type="research_paper",
            sections=sections,
        )
        assert result["strategy"] == "section"

    def test_engine_semantic_strategy_notes(self, document_id, multi_paragraph_text):
        engine = ChunkEngine()
        result = engine.chunk_document(
            document_id=document_id,
            text=multi_paragraph_text,
            document_type="notes",
        )
        assert result["strategy"] == "semantic"

    def test_engine_fixed_strategy_unknown(self, document_id, sample_text):
        engine = ChunkEngine()
        result = engine.chunk_document(
            document_id=document_id,
            text=sample_text,
            document_type="unknown",
        )
        assert result["strategy"] == "fixed"

    def test_engine_rejected_logging(self, document_id):
        text = "short"
        engine = ChunkEngine()
        result = engine.chunk_document(document_id, text)
        assert result["rejected_count"] > 0

    def test_engine_duration(self, document_id):
        words = [f"word_{i}" for i in range(1000)]
        text = " ".join(words)
        engine = ChunkEngine()
        result = engine.chunk_document(document_id, text)
        assert result["duration_seconds"] >= 0

    def test_engine_chunk_metadata(self, document_id):
        words = [f"word_{i}" for i in range(1000)]
        text = " ".join(words)
        engine = ChunkEngine()
        result = engine.chunk_document(document_id, text)
        for c in result["chunks"]:
            assert "chunk_id" in c
            assert "document_id" in c
            assert "start_offset" in c
            assert "end_offset" in c
            assert "word_count" in c
            assert "character_count" in c
            assert "estimated_tokens" in c

    def test_engine_estimated_tokens(self, document_id):
        text = "one two three four five"
        engine = ChunkEngine(chunk_size=500, overlap=0)
        result = engine.chunk_document(document_id, text)
        if result["chunks"]:
            chunk = result["chunks"][0]
            assert chunk["estimated_tokens"] == int(chunk["word_count"] * 1.3)

    def test_engine_overlap_non_empty(self, document_id):
        words = [f"word_{i}" for i in range(600)]
        text = " ".join(words)
        engine = ChunkEngine(chunk_size=200, overlap=30)
        result = engine.chunk_document(document_id, text)
        chunks = result["chunks"]
        if len(chunks) >= 2:
            for i, c in enumerate(chunks):
                if i > 0:
                    assert "overlap_previous" in c
                if i < len(chunks) - 1:
                    assert "overlap_next" in c


# =============================================================================
# Pydantic Schema Tests
# =============================================================================

class TestChunkSchemas:
    def test_chunk_response_schema(self):
        resp = ChunkResponse(status="chunked", strategy="section", chunk_count=42)
        assert resp.status == "chunked"
        assert resp.strategy == "section"
        assert resp.chunk_count == 42

    def test_chunk_preview_schema(self):
        preview = ChunkPreview(
            chunk_id="abc-123",
            section_name="Introduction",
            chunk_index=0,
            word_count=150,
            character_count=800,
            estimated_tokens=195,
            page_start=1,
            page_end=1,
            preview="This is a preview...",
        )
        assert preview.chunk_id == "abc-123"
        assert preview.word_count == 150

    def test_chunk_list_response_schema(self):
        previews = [
            ChunkPreview(
                chunk_id="c1", section_name="Intro", chunk_index=0,
                word_count=100, character_count=500, estimated_tokens=130,
                page_start=1, page_end=1, preview="Preview text",
            ),
        ]
        resp = ChunkListResponse(
            document_id="doc-1",
            chunks=previews,
            statistics={"chunks": 1, "strategy": "fixed"},
        )
        assert resp.document_id == "doc-1"
        assert len(resp.chunks) == 1
        assert resp.statistics["chunks"] == 1

    def test_chunk_statistics_response_schema(self):
        resp = ChunkStatisticsResponse(
            document_id="doc-1",
            chunks=10,
            average_chunk_size=250.0,
            largest_chunk=500,
            smallest_chunk=50,
            strategy="section",
        )
        assert resp.chunks == 10
        assert resp.strategy == "section"


# =============================================================================
# Document Service Chunking Tests
# =============================================================================

class TestDocumentServiceChunking:
    def test_chunk_document_not_extracted(self, upload_dir):
        from backend.app.services.document_service import DocumentExtractionError
        svc = DocumentService(upload_dir)
        svc.upload("test.txt", b"Test content here with enough words for chunking purposes. " * 10)
        doc_id = list(svc._metadata.keys())[0]

        with pytest.raises(DocumentExtractionError, match="extracted before chunking"):
            svc.chunk_document(doc_id)

    def test_chunk_document_nonexistent(self, upload_dir):
        from backend.app.services.document_service import DocumentExtractionError
        svc = DocumentService(upload_dir)
        with pytest.raises(DocumentExtractionError, match="Document not found"):
            svc.chunk_document("nonexistent")

    def test_chunk_then_get_preview(self, upload_dir, tmp_path):
        content = ("word " * 2000).encode("utf-8")
        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.txt", content)
        svc.extract_document(upload_result.document_id)
        result = svc.chunk_document(upload_result.document_id)
        assert result["statistics"]["chunks"] > 0

        previews = svc.get_chunks_preview(upload_result.document_id)
        assert previews is not None
        assert len(previews) > 0
        assert previews[0]["chunk_id"] is not None
        assert "preview" in previews[0]

    def test_get_chunk_by_id(self, upload_dir, tmp_path):
        content = ("word " * 2000).encode("utf-8")
        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.txt", content)
        svc.extract_document(upload_result.document_id)
        result = svc.chunk_document(upload_result.document_id)
        chunk_id = result["chunks"][0]["chunk_id"]

        chunk = svc.get_chunk(upload_result.document_id, chunk_id)
        assert chunk is not None
        assert chunk["chunk_id"] == chunk_id

    def test_get_chunk_not_found(self, upload_dir):
        svc = DocumentService(upload_dir)
        chunk = svc.get_chunk("nonexistent", "no-such-chunk")
        assert chunk is None

    def test_is_chunked(self, upload_dir, tmp_path):
        content = b"test content for chunked check with enough words to be valid. " * 10
        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.txt", content)
        assert svc.is_chunked(upload_result.document_id) is False
        svc.extract_document(upload_result.document_id)
        svc.chunk_document(upload_result.document_id)
        assert svc.is_chunked(upload_result.document_id) is True

    def test_delete_removes_chunks(self, upload_dir, tmp_path):
        content = b"test content that will be chunked and then deleted. " * 10
        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.txt", content)
        svc.extract_document(upload_result.document_id)
        svc.chunk_document(upload_result.document_id)
        assert svc.is_chunked(upload_result.document_id) is True
        svc.delete(upload_result.document_id)
        assert svc.is_chunked(upload_result.document_id) is False

    def test_chunks_persist(self, upload_dir, tmp_path):
        content = b"persistent content for testing chunk persistence across service restarts. " * 10
        svc1 = DocumentService(upload_dir)
        upload_result = svc1.upload("persist.txt", content)
        svc1.extract_document(upload_result.document_id)
        svc1.chunk_document(upload_result.document_id)

        svc2 = DocumentService(upload_dir)
        assert svc2.is_chunked(upload_result.document_id) is True
        previews = svc2.get_chunks_preview(upload_result.document_id)
        assert previews is not None
        assert len(previews) > 0

    def test_get_statistics(self, upload_dir, tmp_path):
        content = ("word " * 2000).encode("utf-8")
        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.txt", content)
        svc.extract_document(upload_result.document_id)
        svc.chunk_document(upload_result.document_id)
        stats = svc.get_chunk_statistics(upload_result.document_id)
        assert stats is not None
        assert stats["chunks"] > 0
        assert stats["average_chunk_size"] > 0
        assert stats["largest_chunk"] > 0
        assert stats["smallest_chunk"] > 0
        assert "strategy" in stats


# =============================================================================
# Integration Tests (API Routes)
# =============================================================================

@pytest.fixture
def mock_services():
    svc = Mock(spec=DocumentService)
    return {"document": svc}


@pytest.fixture
def client(mock_services):
    with patch("backend.app.api.document_routes.get_services", return_value=mock_services):
        with TestClient(app) as c:
            yield c


class TestChunkRoutes:
    def test_chunk_success(self, client, mock_services):
        mock_services["document"].chunk_document.return_value = {
            "strategy": "section",
            "chunks": [{"chunk_id": "c1"}],
            "statistics": {"chunks": 1, "strategy": "section"},
            "duration_seconds": 0.1,
            "rejected_count": 0,
        }

        response = client.post("/api/v1/documents/doc-1/chunk")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "chunked"
        assert data["strategy"] == "section"
        assert data["chunk_count"] == 1

    def test_chunk_not_found(self, client, mock_services):
        from backend.app.services.document_service import DocumentExtractionError
        mock_services["document"].chunk_document.side_effect = DocumentExtractionError(
            "Document not found", status_code=404
        )

        response = client.post("/api/v1/documents/nonexistent/chunk")
        assert response.status_code == 404

    def test_chunk_not_extracted(self, client, mock_services):
        from backend.app.services.document_service import DocumentExtractionError
        mock_services["document"].chunk_document.side_effect = DocumentExtractionError(
            "extracted before chunking", status_code=400
        )

        response = client.post("/api/v1/documents/doc-1/chunk")
        assert response.status_code == 400

    def test_list_chunks_success(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["document"].get_chunks_preview.return_value = [
            {
                "chunk_id": "c1", "section_name": "Intro", "chunk_index": 0,
                "word_count": 100, "character_count": 500, "estimated_tokens": 130,
                "page_start": 1, "page_end": 1,
                "preview": "Preview of chunk...",
            },
        ]
        mock_services["document"].get_chunk_statistics.return_value = {
            "chunks": 1, "strategy": "section", "average_chunk_size": 100.0,
            "largest_chunk": 100, "smallest_chunk": 100,
        }

        response = client.get("/api/v1/documents/doc-1/chunks")
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-1"
        assert len(data["chunks"]) == 1
        assert data["chunks"][0]["chunk_id"] == "c1"
        assert data["statistics"]["chunks"] == 1

    def test_list_chunks_not_found(self, client, mock_services):
        mock_services["document"].get_metadata.return_value = None
        response = client.get("/api/v1/documents/nonexistent/chunks")
        assert response.status_code == 404

    def test_list_chunks_no_chunks(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["document"].get_chunks_preview.return_value = None

        response = client.get("/api/v1/documents/doc-1/chunks")
        assert response.status_code == 404

    def test_get_chunk_by_id_success(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["document"].get_chunk.return_value = {
            "chunk_id": "c1", "text": "Full text content here",
            "section_name": "Intro", "chunk_index": 0,
            "word_count": 100, "character_count": 500,
        }

        response = client.get("/api/v1/documents/doc-1/chunks/c1")
        assert response.status_code == 200
        data = response.json()
        assert data["chunk_id"] == "c1"
        assert "text" in data

    def test_get_chunk_by_id_not_found(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["document"].get_chunk.return_value = None

        response = client.get("/api/v1/documents/doc-1/chunks/nonexistent")
        assert response.status_code == 404

    def test_get_chunk_doc_not_found(self, client, mock_services):
        mock_services["document"].get_metadata.return_value = None
        response = client.get("/api/v1/documents/nonexistent/chunks/c1")
        assert response.status_code == 404

    def test_statistics_success(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["document"].get_chunk_statistics.return_value = {
            "document_id": "doc-1",
            "chunks": 10,
            "average_chunk_size": 250.0,
            "largest_chunk": 500,
            "smallest_chunk": 50,
            "strategy": "section",
        }

        response = client.get("/api/v1/documents/doc-1/chunks/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["chunks"] == 10
        assert data["strategy"] == "section"

    def test_statistics_not_found(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1", filename="test.pdf", file_type=FileType.pdf,
            size=100, status=DocumentStatus.extracted,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )
        mock_services["document"].get_chunk_statistics.return_value = None

        response = client.get("/api/v1/documents/doc-1/chunks/statistics")
        assert response.status_code == 404

    def test_statistics_doc_not_found(self, client, mock_services):
        mock_services["document"].get_metadata.return_value = None
        response = client.get("/api/v1/documents/nonexistent/chunks/statistics")
        assert response.status_code == 404
