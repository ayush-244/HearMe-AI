# API Reference

Base URL: `http://localhost:8000/api/v1`

## Endpoints

### POST /chat

Send a message and get a sentiment-aware multilingual response.

**Request:**
```json
{
  "message": "I'm feeling great today!",
  "language": "auto",
  "history": []
}
```

**Response:**
```json
{
  "reply": "That's wonderful to hear! How can I help you today?",
  "sentiment": "Positive",
  "confidence": 0.98,
  "detected_language": "en",
  "language_name": "English"
}
```

### POST /analyze

End-to-end AI pipeline analysis with adaptive response.

**Request:**
```json
{
  "message": "I'm feeling sad and lonely",
  "language": "auto",
  "history": []
}
```

**Response:**
```json
{
  "language": "English",
  "sentiment": "Negative",
  "emotion": "sadness",
  "toxicity": "none",
  "threat": "none",
  "intent": "conversation",
  "confidence": {
    "sentiment": 0.94,
    "emotion": 0.87,
    "toxicity": 0.02,
    "threat": 0.01,
    "intent": 0.76
  },
  "response": "I'm sorry you're feeling this way. I'm here for you. Would you like to talk about what's going on?"
}
```

### POST /sentiment

Analyze sentiment of a text without generating a response.

**Request:**
```json
{
  "text": "This is terrible, I'm so frustrated."
}
```

**Response:**
```json
{
  "sentiment": "Negative",
  "confidence": 0.94
}
```

### POST /detect-language

Detect the language of a text.

**Request:**
```json
{
  "text": "Bonjour, comment allez-vous?"
}
```

**Response:**
```json
{
  "detected_language": "fr",
  "language_name": "French"
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Document Management

### POST /documents/upload

Upload a document. Accepted types: PDF, DOCX, TXT, Markdown (.md).

Maximum file size: 20 MB.

**Request:** `multipart/form-data` with field `file`

**Response (201):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "report.pdf",
  "file_type": "pdf",
  "size": 123456,
  "status": "uploaded"
}
```

**Errors:**
- `400` — Unsupported file type
- `400` — Invalid file content (MIME mismatch)
- `400` — File exceeds maximum size
- `400` — Invalid filename

### GET /documents

List all uploaded documents (sorted by upload time, newest first).

**Response:**
```json
{
  "documents": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "report.pdf",
      "file_type": "pdf",
      "size": 123456,
      "upload_time": "2026-06-26T17:00:00Z"
    }
  ],
  "count": 1
}
```

### GET /documents/{id}

Get metadata for a single document.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "report.pdf",
  "file_type": "pdf",
  "size": 123456,
  "status": "uploaded",
  "upload_time": "2026-06-26T17:00:00Z",
  "storage_path": "uploads/pdf/550e8400-....pdf"
}
```

**Errors:**
- `404` — Document not found

### DELETE /documents/{id}

Delete a document (metadata and file removed from disk).

**Response:**
```json
{
  "status": "deleted",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document deleted successfully"
}
```

**Errors:**
- `404` — Document not found

### POST /documents/{id}/extract

Extract text content from an uploaded document. Uses the appropriate loader based on file type.

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "extracted",
  "pages": 10,
  "words": 2010,
  "characters": 12340
}
```

**Errors:**
- `404` — Document not found or file missing from disk
- `422` — Extraction failed (corrupted file, password-protected PDF, unsupported encoding)

### GET /documents/{id}/content

Get a preview of extracted document content.

Returns preview only (first ~500 chars). Does not return full text by default.

**Response (extracted):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "preview": "This is the beginning of the document...",
  "pages": 10,
  "words": 2010,
  "characters": 12340,
  "extracted": true
}
```

**Response (not yet extracted):**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "preview": "",
  "pages": 0,
  "words": 0,
  "characters": 0,
  "extracted": false
}
```

**Errors:**
- `404` — Document not found

### POST /documents/{id}/analyze

Analyze an extracted document to generate rich metadata (classification, sections, keywords, etc.).

Document must be extracted first via `POST /documents/{id}/extract`.

**Response:**
```json
{
  "status": "analyzed",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "research_paper",
  "classification_confidence": 15.0,
  "language": "English",
  "language_code": "en",
  "page_count": 10,
  "word_count": 4521,
  "character_count": 28450,
  "reading_time": 21,
  "sections": [
    {
      "name": "Abstract",
      "start_offset": 0,
      "end_offset": 150,
      "estimated_page": 1
    },
    {
      "name": "Introduction",
      "start_offset": 151,
      "end_offset": 450,
      "estimated_page": 1
    }
  ],
  "contains_tables": false,
  "contains_images": false,
  "contains_code_blocks": false,
  "contains_urls": true,
  "contains_emails": false,
  "contains_phone_numbers": false,
  "contains_dates": true,
  "keywords": [
    "natural language",
    "deep learning",
    "neural network",
    "transformer",
    "attention mechanism"
  ],
  "summary_preview": "This paper presents a novel approach to natural language processing using transformer architectures...",
  "extracted_metadata": {
    "title": "A Novel Approach to NLP",
    "author": "Dr. Sarah Johnson",
    "creation_date": "2026-01-15T10:00:00",
    "modification_date": "2026-06-01T14:30:00"
  },
  "created_at": "2026-06-26T17:00:00"
}
```

**Errors:**
- `400` — Document not extracted yet (extract first)
- `404` — Document not found

### GET /documents/{id}/analysis

Retrieve stored analysis for a document. Analysis persists on disk.

**Response:** Same schema as the analyze endpoint response above.

**Errors:**
- `404` — Document not found or analysis not yet generated

---

## Embeddings

### POST /documents/{id}/embed

Generate embeddings for all chunks of a document. Document must be chunked first via `POST /documents/{id}/chunk`.

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "embedding_version": "1.0.0",
  "dimension": 768,
  "created_at": "2026-06-27T12:00:00",
  "chunks": [
    {
      "chunk_id": "abc-123-def",
      "checksum": "sha256hex...",
      "vector": [0.012, -0.034, ...]
    }
  ]
}
```

**Errors:**
- `400` — Document not chunked yet (chunk first)
- `404` — Document not found

### GET /documents/{id}/embeddings

List all embeddings for a document (vectors omitted; includes checksum + dimension only).

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "embedding_model": "BAAI/bge-base-en-v1.5",
  "embedding_version": "1.0.0",
  "dimension": 768,
  "created_at": "2026-06-27T12:00:00",
  "chunks": [
    {
      "chunk_id": "abc-123-def",
      "checksum": "sha256hex...",
      "dimension": 768
    }
  ]
}
```

**Errors:**
- `404` — Document not found or embeddings not yet generated

### GET /documents/{id}/embeddings/{chunk_id}

Retrieve the full embedding vector for a single chunk.

**Response:**
```json
{
  "chunk_id": "abc-123-def",
  "checksum": "sha256hex...",
  "dimension": 768,
  "model": "BAAI/bge-base-en-v1.5",
  "vector": [0.012, -0.034, ...]
}
```

**Errors:**
- `404` — Document or chunk embedding not found

### DELETE /documents/{id}

Deleting a document also removes its embeddings (handled automatically).

---

## Chunking

### POST /documents/{id}/chunk

Generate chunks from an extracted document. Automatically selects chunking strategy based on document type.

Document must be extracted first via `POST /documents/{id}/extract`.

**Response:**
```json
{
  "status": "chunked",
  "strategy": "section",
  "chunk_count": 42
}
```

**Errors:**
- `400` — Document not extracted yet (extract first)
- `404` — Document not found

### GET /documents/{id}/chunks

List all chunks for a document (preview only, not full text).

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks": [
    {
      "chunk_id": "abc-123-def",
      "section_name": "Introduction",
      "chunk_index": 0,
      "word_count": 480,
      "character_count": 2750,
      "estimated_tokens": 624,
      "page_start": 1,
      "page_end": 1,
      "preview": "This is the beginning of the introduction section..."
    }
  ],
  "statistics": {
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "chunks": 42,
    "average_chunk_size": 480.0,
    "largest_chunk": 620,
    "smallest_chunk": 92,
    "strategy": "section"
  }
}
```

**Errors:**
- `404` — Document not found or chunks not yet generated

### GET /documents/{id}/chunks/{chunk_id}

Retrieve the full content of a single chunk by its chunk ID.

**Response:**
```json
{
  "chunk_id": "abc-123-def",
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "section_name": "Introduction",
  "chunk_index": 0,
  "page_start": 1,
  "page_end": 1,
  "start_offset": 0,
  "end_offset": 2750,
  "word_count": 480,
  "character_count": 2750,
  "estimated_tokens": 624,
  "overlap_previous": "",
  "overlap_next": "previous section content for context...",
  "text": "Full text content of this chunk...",
  "metadata": {}
}
```

**Errors:**
- `404` — Document or chunk not found

### GET /documents/{id}/chunks/statistics

Get chunk statistics for a document without returning chunk content.

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks": 42,
  "average_chunk_size": 480.0,
  "largest_chunk": 620,
  "smallest_chunk": 92,
  "strategy": "section"
}
```

**Errors:**
- `404` — Document not found or chunks not yet generated

---

### POST /feedback

Submit feedback on a response.

**Request:**
```json
{
  "message_id": "msg_123",
  "rating": 4,
  "comment": "Good response but could be shorter"
}
```

**Response:**
```json
{
  "status": "received",
  "message_id": "msg_123",
  "rating": 4
}
```
