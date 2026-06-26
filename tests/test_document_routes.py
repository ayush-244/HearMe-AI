"""Integration tests for document API endpoints using TestClient."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.document_service import DocumentService, DocumentExtractionError
from backend.app.schemas.document import (
    UploadResponse, FileType, DocumentStatus,
    ExtractionResponse, ContentResponse, DeleteResponse, DocumentListItem, DocumentMetadata,
)


@pytest.fixture
def mock_services():
    svc = Mock(spec=DocumentService)
    return {"document": svc}


@pytest.fixture
def client(mock_services):
    with patch("backend.app.api.document_routes.get_services", return_value=mock_services):
        with TestClient(app) as c:
            yield c


class TestDocumentRoutes:
    def test_upload_success(self, client, mock_services):
        mock_services["document"].upload.return_value = UploadResponse(
            document_id="abc-123",
            filename="test.pdf",
            file_type=FileType.pdf,
            size=1234,
            status=DocumentStatus.uploaded,
        )

        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.pdf", b"%PDF-1.4 content", "application/pdf")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["document_id"] == "abc-123"
        assert data["filename"] == "test.pdf"
        assert data["file_type"] == "pdf"
        assert data["status"] == "uploaded"

    def test_upload_validation_error(self, client, mock_services):
        from backend.app.services.document_service import DocumentValidationError

        mock_services["document"].upload.side_effect = DocumentValidationError(
            "Unsupported file type '.exe'. Allowed: .pdf, .docx, .txt, .md"
        )

        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("bad.exe", b"some content", "application/x-msdownload")},
        )

        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    def test_list_documents(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentListItem, FileType

        mock_services["document"].list_documents.return_value = [
            DocumentListItem(
                id="doc-1",
                filename="a.pdf",
                file_type=FileType.pdf,
                size=100,
                upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
        ]

        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["documents"][0]["filename"] == "a.pdf"

    def test_list_empty(self, client, mock_services):
        mock_services["document"].list_documents.return_value = []

        response = client.get("/api/v1/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["documents"] == []

    def test_get_document_found(self, client, mock_services):
        from datetime import datetime, timezone
        from backend.app.schemas.document import DocumentMetadata, FileType, DocumentStatus

        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1",
            filename="test.pdf",
            file_type=FileType.pdf,
            size=1234,
            status=DocumentStatus.uploaded,
            upload_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
            storage_path="/tmp/test.pdf",
        )

        response = client.get("/api/v1/documents/doc-1")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "doc-1"
        assert data["filename"] == "test.pdf"
        assert data["file_type"] == "pdf"

    def test_get_document_not_found(self, client, mock_services):
        mock_services["document"].get_metadata.return_value = None

        response = client.get("/api/v1/documents/nonexistent")

        assert response.status_code == 404

    def test_delete_success(self, client, mock_services):
        from backend.app.schemas.document import DeleteResponse

        mock_services["document"].delete.return_value = DeleteResponse(
            status="deleted",
            document_id="doc-1",
            message="Document deleted successfully",
        )

        response = client.delete("/api/v1/documents/doc-1")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"

    def test_delete_not_found(self, client, mock_services):
        from backend.app.schemas.document import DeleteResponse

        mock_services["document"].delete.return_value = DeleteResponse(
            status="not_found",
            document_id="nonexistent",
            message="Document not found",
        )

        response = client.delete("/api/v1/documents/nonexistent")

        assert response.status_code == 404

    def test_extract_success(self, client, mock_services):
        mock_services["document"].extract_document.return_value = ExtractionResponse(
            document_id="doc-1",
            status="extracted",
            pages=10,
            words=2010,
            characters=12340,
        )

        response = client.post("/api/v1/documents/doc-1/extract")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-1"
        assert data["status"] == "extracted"
        assert data["pages"] == 10
        assert data["words"] == 2010
        assert data["characters"] == 12340

    def test_extract_not_found(self, client, mock_services):
        mock_services["document"].extract_document.side_effect = DocumentExtractionError(
            "Document not found", status_code=404
        )

        response = client.post("/api/v1/documents/nonexistent/extract")

        assert response.status_code == 404

    def test_extract_error(self, client, mock_services):
        mock_services["document"].extract_document.side_effect = DocumentExtractionError(
            "Corrupted PDF", status_code=422
        )

        response = client.post("/api/v1/documents/doc-1/extract")

        assert response.status_code == 422
        data = response.json()
        assert "Corrupted PDF" in data["detail"]

    def test_content_success(self, client, mock_services):
        mock_services["document"].get_document_content.return_value = ContentResponse(
            document_id="doc-1",
            preview="This is a preview of the document...",
            pages=10,
            words=2010,
            characters=12340,
            extracted=True,
        )

        response = client.get("/api/v1/documents/doc-1/content")

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "doc-1"
        assert data["extracted"] is True
        assert data["pages"] == 10
        assert "preview" in data

    def test_content_not_extracted(self, client, mock_services):
        mock_services["document"].get_document_content.return_value = ContentResponse(
            document_id="doc-1",
            preview="",
            pages=0,
            words=0,
            characters=0,
            extracted=False,
        )

        response = client.get("/api/v1/documents/doc-1/content")

        assert response.status_code == 200
        data = response.json()
        assert data["extracted"] is False
        assert data["preview"] == ""

    def test_content_not_found(self, client, mock_services):
        mock_services["document"].get_document_content.side_effect = DocumentExtractionError(
            "Document not found", status_code=404
        )

        response = client.get("/api/v1/documents/nonexistent/content")

        assert response.status_code == 404
