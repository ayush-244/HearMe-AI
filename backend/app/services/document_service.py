import logging
import json
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from ..schemas.document import (
    DocumentMetadata,
    DocumentStatus,
    FileType,
    UploadResponse,
    DocumentListItem,
    DeleteResponse,
    ExtractionResponse,
    ContentResponse,
    AnalysisResponse,
)
from ai.documents.common import ExtractedDocument, DocumentNormalizer
from ai.documents.analyzer import DocumentAnalyzer
from ai.documents.pdf_loader import PDFLoader
from ai.documents.docx_loader import DOCXLoader
from ai.documents.txt_loader import TXTLoader
from ai.documents.markdown_loader import MarkdownLoader
from ai.chunking.chunk_engine import ChunkEngine
from ai.chunking.chunk_models import ChunkStatistics

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


class DocumentExtractionError(Exception):
    def __init__(self, message: str, status_code: int = 422):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class DocumentService:
    def __init__(self, upload_dir: Path, analyzer: Optional[DocumentAnalyzer] = None):
        self._upload_dir = Path(upload_dir)
        self._metadata_path = self._upload_dir / "metadata.json"
        self._extracted_dir = self._upload_dir / "extracted"
        self._analysis_dir = self._upload_dir / "analysis"
        self._chunks_dir = self._upload_dir / "chunks"
        self._embeddings_dir = self._upload_dir / "embeddings"
        self._analyzer = analyzer
        self._chunk_engine = ChunkEngine()
        self._metadata: Dict[str, DocumentMetadata] = {}
        self._loaders: Dict[FileType, object] = {
            FileType.pdf: PDFLoader(),
            FileType.docx: DOCXLoader(),
            FileType.txt: TXTLoader(),
            FileType.markdown: MarkdownLoader(),
        }
        self._create_directories()
        self._load_metadata()

    def _create_directories(self) -> None:
        self._upload_dir.mkdir(parents=True, exist_ok=True)
        for ft in FileType:
            (self._upload_dir / ft.value).mkdir(parents=True, exist_ok=True)
        self._extracted_dir.mkdir(parents=True, exist_ok=True)
        self._analysis_dir.mkdir(parents=True, exist_ok=True)
        self._chunks_dir.mkdir(parents=True, exist_ok=True)
        self._embeddings_dir.mkdir(parents=True, exist_ok=True)

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

    def _extracted_path(self, document_id: str) -> Path:
        return self._extracted_dir / f"{document_id}.json"

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

        extracted_path = self._extracted_path(document_id)
        if extracted_path.exists():
            try:
                extracted_path.unlink()
            except OSError as e:
                logger.error("Delete failed (extracted file removal error): %s", e)

        analysis_path = self._analysis_path(document_id)
        if analysis_path.exists():
            try:
                analysis_path.unlink()
            except OSError as e:
                logger.error("Delete failed (analysis file removal error): %s", e)

        chunks_path = self._chunks_path(document_id)
        if chunks_path.exists():
            try:
                chunks_path.unlink()
            except OSError as e:
                logger.error("Delete failed (chunks file removal error): %s", e)

        embeddings_path = self._embeddings_path(document_id)
        if embeddings_path.exists():
            try:
                embeddings_path.unlink()
            except OSError as e:
                logger.error("Delete failed (embeddings file removal error): %s", e)

        del self._metadata[document_id]
        self._save_metadata()

        logger.info("Delete completed: id=%s, filename=%s", document_id, meta.filename)

        return DeleteResponse(
            status="deleted",
            document_id=document_id,
            message="Document deleted successfully",
        )

    def extract_document(self, document_id: str) -> ExtractionResponse:
        meta = self._metadata.get(document_id)
        if meta is None:
            raise DocumentExtractionError("Document not found", status_code=404)

        if meta.status == DocumentStatus.extracted:
            logger.info("Document already extracted: id=%s", document_id)
            extracted = self._load_extracted(document_id)
            if extracted is not None:
                return ExtractionResponse(
                    document_id=document_id,
                    status="extracted",
                    pages=extracted.pages,
                    words=extracted.words,
                    characters=extracted.characters,
                )

        filepath = Path(meta.storage_path)
        if not filepath.exists():
            raise DocumentExtractionError("Document file not found on disk", status_code=404)

        loader = self._loaders.get(meta.file_type)
        if loader is None:
            raise DocumentExtractionError(f"No loader available for type: {meta.file_type}")

        logger.info("Extraction started: id=%s, type=%s, path=%s", document_id, meta.file_type.value, filepath)
        start = time.time()

        try:
            extracted: ExtractedDocument = loader.extract(str(filepath))
        except (ValueError, FileNotFoundError) as e:
            logger.error("Extraction failed: id=%s — %s", document_id, e)
            raise DocumentExtractionError(str(e))

        elapsed = time.time() - start
        self._save_extracted(document_id, extracted)

        meta.status = DocumentStatus.extracted
        self._save_metadata()

        logger.info(
            "Extraction completed: id=%s, pages=%d, words=%d, chars=%d, duration=%.2fs",
            document_id, extracted.pages, extracted.words, extracted.characters, elapsed,
        )

        return ExtractionResponse(
            document_id=document_id,
            status="extracted",
            pages=extracted.pages,
            words=extracted.words,
            characters=extracted.characters,
        )

    def get_document_content(self, document_id: str) -> ContentResponse:
        meta = self._metadata.get(document_id)
        if meta is None:
            raise DocumentExtractionError("Document not found", status_code=404)

        extracted = self._load_extracted(document_id)
        if extracted is None:
            return ContentResponse(
                document_id=document_id,
                preview="",
                pages=0,
                words=0,
                characters=0,
                extracted=False,
            )

        return ContentResponse(
            document_id=document_id,
            preview=extracted.preview,
            pages=extracted.pages,
            words=extracted.words,
            characters=extracted.characters,
            extracted=True,
        )

    def get_document_full_text(self, document_id: str) -> Optional[str]:
        extracted = self._load_extracted(document_id)
        if extracted is None:
            return None
        return extracted.text

    def is_extracted(self, document_id: str) -> bool:
        return self._extracted_path(document_id).exists()

    def _save_extracted(self, document_id: str, extracted: ExtractedDocument) -> None:
        path = self._extracted_path(document_id)
        data = {
            "document_id": document_id,
            "pages": extracted.pages,
            "words": extracted.words,
            "characters": extracted.characters,
            "preview": extracted.preview,
            "text": extracted.text,
            "metadata": extracted.metadata,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save extracted content: %s", e)
            raise DocumentExtractionError("Failed to save extracted content", status_code=500)

    def _load_extracted(self, document_id: str) -> Optional[ExtractedDocument]:
        path = self._extracted_path(document_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ExtractedDocument(
                text=data["text"],
                preview=data["preview"],
                pages=data["pages"],
                words=data["words"],
                characters=data["characters"],
                metadata=data.get("metadata", {}),
            )
        except Exception as e:
            logger.error("Failed to load extracted content: %s", e)
            return None

    def _analysis_path(self, document_id: str) -> Path:
        return self._analysis_dir / f"{document_id}.json"

    def _embeddings_path(self, document_id: str) -> Path:
        return self._embeddings_dir / f"{document_id}.json"

    def _get_language_service(self):
        try:
            from . import get_services
            services = get_services()
            return services.get("language")
        except Exception:
            return None

    def analyze_document(self, document_id: str) -> AnalysisResponse:
        meta = self._metadata.get(document_id)
        if meta is None:
            raise DocumentExtractionError("Document not found", status_code=404)

        extracted = self._load_extracted(document_id)
        if extracted is None:
            raise DocumentExtractionError(
                "Document must be extracted before analysis",
                status_code=400,
            )

        if self._analyzer is None:
            logger.info("Initializing DocumentAnalyzer for analysis")
            self._analyzer = DocumentAnalyzer()

        logger.info("Analysis started: id=%s, filename=%s", document_id, meta.filename)

        language_service = self._get_language_service()
        analysis = self._analyzer.analyze(
            document_id=document_id,
            text=extracted.text,
            filename=meta.filename,
            file_metadata=extracted.metadata or {},
            pages=extracted.pages,
            language_service=language_service,
        )

        self._save_analysis(document_id, analysis)

        logger.info("Analysis completed: id=%s, type=%s", document_id, analysis["document_type"])

        return AnalysisResponse(
            status="analyzed",
            document_id=document_id,
            document_type=analysis["document_type"],
            classification_confidence=analysis["classification_confidence"],
            language=analysis["language"],
            language_code=analysis["language_code"],
            page_count=analysis["page_count"],
            word_count=analysis["word_count"],
            character_count=analysis["character_count"],
            reading_time=analysis["estimated_reading_time_minutes"],
            sections=analysis["sections"],
            contains_tables=analysis["contains_tables"],
            contains_images=analysis["contains_images"],
            contains_code_blocks=analysis["contains_code_blocks"],
            contains_urls=analysis["contains_urls"],
            contains_emails=analysis["contains_emails"],
            contains_phone_numbers=analysis["contains_phone_numbers"],
            contains_dates=analysis["contains_dates"],
            keywords=analysis["keywords"],
            summary_preview=analysis["summary_preview"],
            extracted_metadata=analysis["extracted_metadata"],
            created_at=analysis["created_at"],
        )

    def get_analysis(self, document_id: str) -> Optional[dict]:
        path = self._analysis_path(document_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load analysis: %s", e)
            return None

    def is_analyzed(self, document_id: str) -> bool:
        return self._analysis_path(document_id).exists()

    def _save_analysis(self, document_id: str, analysis: dict) -> None:
        path = self._analysis_path(document_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save analysis: %s", e)
            raise DocumentExtractionError("Failed to save analysis", status_code=500)

    def _chunks_path(self, document_id: str) -> Path:
        return self._chunks_dir / f"{document_id}.json"

    def chunk_document(self, document_id: str) -> dict:
        meta = self._metadata.get(document_id)
        if meta is None:
            raise DocumentExtractionError("Document not found", status_code=404)

        extracted = self._load_extracted(document_id)
        if extracted is None:
            raise DocumentExtractionError(
                "Document must be extracted before chunking",
                status_code=400,
            )

        full_text = extracted.text
        analysis = self.get_analysis(document_id)
        document_type = "unknown"
        sections = None

        if analysis:
            document_type = analysis.get("document_type", "unknown")
            sections = analysis.get("sections")

        result = self._chunk_engine.chunk_document(
            document_id=document_id,
            text=full_text,
            document_type=document_type,
            file_type=meta.file_type.value,
            sections=sections,
        )

        self._save_chunks(document_id, result)
        return result

    def _save_chunks(self, document_id: str, result: dict) -> None:
        path = self._chunks_path(document_id)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save chunks: %s", e)
            raise DocumentExtractionError("Failed to save chunks", status_code=500)

    def _load_chunks_data(self, document_id: str) -> Optional[dict]:
        path = self._chunks_path(document_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load chunks: %s", e)
            return None

    def is_chunked(self, document_id: str) -> bool:
        return self._chunks_path(document_id).exists()

    def get_chunks_preview(self, document_id: str) -> Optional[list]:
        data = self._load_chunks_data(document_id)
        if data is None:
            return None

        previews = []
        for c in data.get("chunks", []):
            preview_text = c["text"][:120]
            if len(c["text"]) > 120:
                preview_text += "..."
            previews.append({
                "chunk_id": c["chunk_id"],
                "section_name": c["section_name"],
                "chunk_index": c["chunk_index"],
                "word_count": c["word_count"],
                "character_count": c["character_count"],
                "estimated_tokens": c["estimated_tokens"],
                "page_start": c["page_start"],
                "page_end": c["page_end"],
                "preview": preview_text,
            })

        return previews

    def get_chunk(self, document_id: str, chunk_id: str) -> Optional[dict]:
        data = self._load_chunks_data(document_id)
        if data is None:
            return None

        for c in data.get("chunks", []):
            if c["chunk_id"] == chunk_id:
                return c

        return None

    def get_chunk_statistics(self, document_id: str) -> Optional[dict]:
        data = self._load_chunks_data(document_id)
        if data is None:
            return None
        return data.get("statistics")

    def get_chunks_data(self, document_id: str) -> Optional[dict]:
        return self._load_chunks_data(document_id)
