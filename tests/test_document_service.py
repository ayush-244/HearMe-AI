"""Unit tests for DocumentService."""
import pytest
from pathlib import Path
from backend.app.services.document_service import (
    DocumentService,
    DocumentValidationError,
)
from backend.app.schemas.document import DocumentStatus


@pytest.fixture
def upload_dir(tmp_path):
    return tmp_path / "uploads"


@pytest.fixture
def service(upload_dir):
    return DocumentService(upload_dir)


class TestDocumentService:
    def test_upload_pdf(self, service):
        content = b"%PDF-1.4 some pdf content"
        result = service.upload("test.pdf", content)
        assert result.filename == "test.pdf"
        assert result.file_type.value == "pdf"
        assert result.size == len(content)
        assert result.status == DocumentStatus.uploaded
        assert len(result.document_id) == 36

        meta = service.get_metadata(result.document_id)
        assert meta is not None
        assert meta.filename == "test.pdf"
        assert meta.file_type.value == "pdf"

    def test_upload_docx(self, service):
        content = b"PK\x03\x04 docx content"
        result = service.upload("report.docx", content)
        assert result.file_type.value == "docx"

    def test_upload_txt(self, service):
        content = "Hello, world!".encode("utf-8")
        result = service.upload("notes.txt", content)
        assert result.file_type.value == "txt"

    def test_upload_markdown(self, service):
        content = "# Heading\n\nSome **bold** text.".encode("utf-8")
        result = service.upload("readme.md", content)
        assert result.file_type.value == "markdown"

    def test_invalid_extension(self, service):
        with pytest.raises(DocumentValidationError, match="Unsupported file type"):
            service.upload("file.exe", b"some content")

    def test_invalid_extension_exe(self, service):
        with pytest.raises(DocumentValidationError, match="Unsupported file type"):
            service.upload("script.exe", b"some content")

    def test_invalid_extension_image(self, service):
        with pytest.raises(DocumentValidationError, match="Unsupported file type"):
            service.upload("image.png", b"fake png")

    def test_oversized_file(self, service):
        content = b"%PDF-1.4 " + b"x" * (20 * 1024 * 1024 + 1)
        with pytest.raises(DocumentValidationError, match="exceeds maximum size"):
            service.upload("large.pdf", content)

    def test_bad_pdf_mime_type(self, service):
        content = b"Not a PDF at all"
        with pytest.raises(DocumentValidationError, match="not a valid PDF"):
            service.upload("fake.pdf", content)

    def test_bad_docx_mime_type(self, service):
        content = b"Not a ZIP file"
        with pytest.raises(DocumentValidationError, match="not a valid DOCX"):
            service.upload("fake.docx", content)

    def test_binary_txt_rejected(self, service):
        content = b"\x00\x01\x02\xff\xfe"
        with pytest.raises(DocumentValidationError, match="must be UTF-8"):
            service.upload("binary.txt", content)

    def test_duplicate_filenames_get_unique_ids(self, service):
        content = b"%PDF-1.4 content"
        r1 = service.upload("doc.pdf", content)
        r2 = service.upload("doc.pdf", content)
        assert r1.document_id != r2.document_id
        assert r1.filename == "doc.pdf"
        assert r2.filename == "doc.pdf"

    def test_list_documents(self, service):
        service.upload("a.pdf", b"%PDF-1.4 a")
        service.upload("b.txt", b"hello")
        docs = service.list_documents()
        assert len(docs) == 2
        assert docs[0].filename in ("a.pdf", "b.txt")  # sorted by upload_time desc

    def test_list_empty(self, service):
        docs = service.list_documents()
        assert docs == []

    def test_get_metadata_nonexistent(self, service):
        meta = service.get_metadata("nonexistent-id")
        assert meta is None

    def test_delete_document(self, service):
        content = b"%PDF-1.4 delete me"
        result = service.upload("delete_me.pdf", content)
        doc_id = result.document_id

        meta = service.get_metadata(doc_id)
        assert meta is not None

        delete_result = service.delete(doc_id)
        assert delete_result.status == "deleted"

        meta = service.get_metadata(doc_id)
        assert meta is None

    def test_delete_nonexistent(self, service):
        result = service.delete("nonexistent-id")
        assert result.status == "not_found"

    def test_delete_removes_file_from_disk(self, service, upload_dir):
        content = b"%PDF-1.4 file on disk"
        result = service.upload("ondisk.pdf", content)
        doc_id = result.document_id

        meta = service.get_metadata(doc_id)
        assert Path(meta.storage_path).exists()

        service.delete(doc_id)
        assert not Path(meta.storage_path).exists()

    def test_path_traversal_prevented(self, service):
        with pytest.raises(DocumentValidationError, match="Invalid filename"):
            service.upload("../etc/passwd.pdf", b"%PDF-1.4")

    def test_path_traversal_windows_prevented(self, service):
        with pytest.raises(DocumentValidationError, match="Invalid filename"):
            service.upload("..\\windows\\file.pdf", b"%PDF-1.4")

    def test_metadata_persists_to_disk(self, upload_dir):
        svc1 = DocumentService(upload_dir)
        svc1.upload("persist.pdf", b"%PDF-1.4 persist test")
        doc_id = list(svc1._metadata.keys())[0]

        svc2 = DocumentService(upload_dir)
        meta = svc2.get_metadata(doc_id)
        assert meta is not None
        assert meta.filename == "persist.pdf"

    def test_upload_creates_type_subdirectories(self, upload_dir):
        svc = DocumentService(upload_dir)
        for sub in ["pdf", "docx", "txt", "markdown"]:
            assert (upload_dir / sub).exists()
