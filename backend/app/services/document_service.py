import logging
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from ..schemas.document import (
    DocumentMetadata,
    FileType,
    DocumentStatus,
    UploadResponse,
    DocumentListItem,
    DeleteResponse,
)

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS: Dict[str, FileType] = {
    ".pdf": FileType.pdf,
    ".docx": FileType.docx,
    ".txt": FileType.txt,
    ".md": FileType.markdown,
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


class DocumentValidationError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentService:
    def __init__(self, upload_dir: Path):
        self._upload_dir = Path(upload_dir)
        self._metadata_path = self._upload_dir / "metadata.json"
        self._metadata: Dict[str, DocumentMetadata] = {}
        self._create_directories()
        self._load_metadata()

    def _create_directories(self) -> None:
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        for ft in FileType:
            (self._upload_dir / ft.value).mkdir(parents=True, exist_ok=True)

    def _load_metadata(self) -> None:
        path = self._metadata_path
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self._metadata = {}
                for key, val in raw.items():
                    val["upload_time"] = datetime.fromisoformat(val["upload_time"])
                    self._metadata[key] = DocumentMetadata(**val)
                logger.info("Loaded %d document metadata entries", len(self._metadata))
            except Exception as e:
                logger.error("Failed to load metadata: %s", e)
                self._metadata = {}

    def _save_metadata(self) -> None:
        path = self._metadata_path
        try:
            raw = {}
            for key, val in self._metadata.items():
                d = val.model_dump()
                d["upload_time"] = d["upload_time"].isoformat()
                raw[key] = d
            with open(path, "w", encoding="utf-8") as f:
                json.dump(raw, f, indent=2)
        except Exception as e:
            logger.error("Failed to save metadata: %s", e)

    def _validate_extension(self, filename: str) -> FileType:
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise DocumentValidationError(
                f"Unsupported file type '{ext}'. Allowed: .pdf, .docx, .txt, .md"
            )
        return ALLOWED_EXTENSIONS[ext]

    def _validate_mime_type(self, content: bytes, file_type: FileType) -> None:
        if file_type == FileType.pdf:
            if not content[:4] == b"%PDF":
                raise DocumentValidationError("File is not a valid PDF")
        elif file_type == FileType.docx:
            if not content[:2] == b"PK":
                raise DocumentValidationError("File is not a valid DOCX")
        elif file_type in (FileType.txt, FileType.markdown):
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                raise DocumentValidationError(
                    f"File is not a valid {file_type.value.upper()} file (must be UTF-8 text)"
                )

    def _validate_size(self, size: int) -> None:
        if size > MAX_FILE_SIZE:
            raise DocumentValidationError(
                f"File exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)} MB"
            )

    def _validate_path_traversal(self, filename: str) -> None:
        clean = Path(filename).name
        if clean != filename or ".." in filename or "/" in filename or "\\" in filename:
            raise DocumentValidationError("Invalid filename")

    def upload(self, filename: str, content: bytes) -> UploadResponse:
        logger.info("Upload started: %s (%d bytes)", filename, len(content))

        self._validate_path_traversal(filename)
        file_type = self._validate_extension(filename)
        self._validate_mime_type(content, file_type)
        self._validate_size(len(content))

        document_id = str(uuid.uuid4())
        storage_name = f"{document_id}{Path(filename).suffix}"
        file_type_dir = self._upload_dir / file_type.value
        storage_path = file_type_dir / storage_name

        try:
            with open(storage_path, "wb") as f:
                f.write(content)
        except OSError as e:
            logger.error("Upload failed (write error): %s", e)
            raise DocumentValidationError("Failed to save file", status_code=500)

        metadata = DocumentMetadata(
            id=document_id,
            filename=filename,
            file_type=file_type,
            size=len(content),
            status=DocumentStatus.uploaded,
            upload_time=datetime.now(timezone.utc),
            storage_path=str(storage_path),
        )

        self._metadata[document_id] = metadata
        self._save_metadata()

        logger.info("Upload completed: id=%s, type=%s, size=%d", document_id, file_type.value, len(content))

        return UploadResponse(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            size=len(content),
            status=DocumentStatus.uploaded,
        )

    def list_documents(self) -> List[DocumentListItem]:
        items = []
        for meta in self._metadata.values():
            items.append(
                DocumentListItem(
                    id=meta.id,
                    filename=meta.filename,
                    file_type=meta.file_type,
                    size=meta.size,
                    upload_time=meta.upload_time,
                )
            )
        items.sort(key=lambda x: x.upload_time, reverse=True)
        return items

    def get_metadata(self, document_id: str) -> Optional[DocumentMetadata]:
        return self._metadata.get(document_id)

    def delete(self, document_id: str) -> DeleteResponse:
        meta = self._metadata.get(document_id)
        if meta is None:
            logger.warning("Delete failed: document %s not found", document_id)
            return DeleteResponse(
                status="not_found",
                document_id=document_id,
                message="Document not found",
            )

        storage_path = Path(meta.storage_path)
        if storage_path.exists():
            try:
                storage_path.unlink()
            except OSError as e:
                logger.error("Delete failed (file removal error): %s", e)

        del self._metadata[document_id]
        self._save_metadata()

        logger.info("Delete completed: id=%s, filename=%s", document_id, meta.filename)

        return DeleteResponse(
            status="deleted",
            document_id=document_id,
            message="Document deleted successfully",
        )
