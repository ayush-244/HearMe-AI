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

## Knowledge Reasoning

### POST /knowledge/chat

Ask a question and get a grounded, citation-backed answer from uploaded documents. Uses hybrid search to retrieve relevant chunks, builds a structured prompt from templates, invokes the LLM, validates the response, and returns citations.

**Request:**
```json
{
  "question": "Explain transformer architecture.",
  "workspace_id": "default",
  "conversation_id": "",
  "top_k": 10,
  "min_score": 0.0,
  "language": null,
  "document_type": null,
  "document_ids": null,
  "filters": {}
}
```

**Parameters:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `question` | string | required | User question |
| `workspace_id` | string | `"default"` | Workspace scope |
| `conversation_id` | string | `""` | ID for multi-turn conversation history |
| `top_k` | int | `10` | Number of chunks to retrieve (1–50) |
| `min_score` | float | `0.0` | Minimum similarity threshold |
| `language` | string | null | Preferred response language |
| `document_type` | string | null | Filter by document type |
| `document_ids` | list[string] | null | Filter to specific documents |
| `filters` | dict | `{}` | Additional metadata filters |

**Response:**
```json
{
  "question": "Explain transformer architecture.",
  "answer": "Transformer models replace recurrence with attention mechanisms [Source 1]. The attention layer computes weighted sums of values based on query-key similarity [Source 1].",
  "citations": [
    "[Paper A › Methodology › Page 3]",
    "[Paper A › Methodology › Page 4]"
  ],
  "sources": [
    {
      "document_id": "d1",
      "title": "Paper A",
      "sections": ["Methodology"],
      "chunks": [
        {"chunk_id": "c1", "section": "Methodology", "page": 3, "score": 0.95},
        {"chunk_id": "c2", "section": "Methodology", "page": 4, "score": 0.90}
      ]
    }
  ],
  "processing_time_ms": 1234.56,
  "retrieval_time_ms": 45.12,
  "generation_time_ms": 1185.23,
  "chunk_count": 2,
  "context_token_estimate": 120,
  "validation_passed": true,
  "guardrail_triggered": false,
  "knowledge_gap": false,
  "conversation_id": ""
}
```

**When knowledge is insufficient:**
```json
{
  "answer": "I couldn't find enough information in the uploaded documents.",
  "knowledge_gap": true,
  "chunk_count": 0
}
```

**Errors:**
- `400` — Empty question
- `503` — Knowledge reasoning engine not available
- `500` — Internal reasoning failure

### GET /knowledge/health

Check the knowledge reasoning engine health status.

**Response:**
```json
{
  "ready": true,
  "search_engine_ready": true,
  "context_builder_max_tokens": 4096,
  "context_builder_max_chunks": 20,
  "citation_style": "inline",
  "allow_external_knowledge": false,
  "conversation_history_limit": 5,
  "active_conversations": 3
}
```

---

## Vector Store

### POST /documents/{id}/index

Index a document's chunks into the Qdrant vector store for semantic search. Document must be embedded first via `POST /documents/{id}/embed`.

**Response:**
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "chunks_indexed": 10,
  "status": "indexed"
}
```

**Errors:**
- `400` — Document not embedded yet (embed first)
- `404` — Document not found

### DELETE /documents/{id}/index

Remove a document's vectors from the Qdrant vector store.

**Response:**
```json
{
  "status": "deindexed",
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### GET /vectorstore/health

Check the Qdrant vector store health status.

**Response:**
```json
{
  "status": "healthy",
  "collection": "documents",
  "points_count": 150,
  "vector_dimension": 768
}
```

---

## Search

### POST /search

Hybrid semantic + keyword search across indexed document chunks. Supports filters, language/document type constraints, and query analysis.

**Request:**
```json
{
  "query": "transformer attention mechanism",
  "workspace_id": "default",
  "top_k": 10,
  "min_score": 0.0,
  "language": null,
  "document_type": null,
  "document_ids": null,
  "filters": {}
}
```

**Parameters:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | required | Search query text |
| `workspace_id` | string | `"default"` | Scope search to a workspace |
| `top_k` | int | `10` | Max results (clamped to 1–50) |
| `min_score` | float | `0.0` | Minimum hybrid score threshold (0.0–1.0) |
| `language` | string | null | Filter by language code (e.g. `"en"`) |
| `document_type` | string | null | Filter by document type (e.g. `"research_paper"`) |
| `document_ids` | list[string] | null | Filter to specific documents |
| `filters` | dict | `{}` | Additional metadata key-value filters |

Query text supports inline filters via prefixes:
- `lang:en` — Filter to English results
- `type:paper` — Filter to research paper type
- `workspace:team1` — Filter to workspace
- `doc:id` — Filter to specific document
- `section:Intro` — Filter to section name

Quoted phrases (`"deep learning"`) are preserved as exact match tokens.

**Response:**
```json
{
  "query": "transformer attention mechanism",
  "results": [
    {
      "chunk_id": "abc-123-def",
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "text": "The transformer attention mechanism allows models to weigh the importance of different input elements...",
      "title": "Attention Is All You Need",
      "section": "Methodology",
      "page": 3,
      "score": 0.8921,
      "semantic_score": 0.9100,
      "keyword_score": 0.7200,
      "metadata_score": 0.4500,
      "language": "en",
      "document_type": "research_paper",
      "workspace_id": "default",
      "chunk_index": 5,
      "word_count": 480,
      "keywords": ["transformer", "attention", "neural network"]
    }
  ],
  "citations": [
    "Attention Is All You Need, Methodology, Page 3 (Chunk abc-123…, Score 0.89)"
  ],
  "statistics": {
    "total_chunks_searched": 30,
    "semantic_chunks_retrieved": 30,
    "keyword_chunks_scored": 30,
    "final_chunks_returned": 10,
    "avg_semantic_score": 0.7521,
    "avg_keyword_score": 0.5412,
    "avg_final_score": 0.7123,
    "semantic_latency_ms": 45.12,
    "keyword_latency_ms": 2.34,
    "ranking_latency_ms": 1.23,
    "total_latency_ms": 48.69
  },
  "processing_time_ms": 48.69,
  "query_analysis": {
    "language": "en",
    "intent": "research",
    "complexity": "moderate",
    "estimated_depth": 3
  }
}
```

**Errors:**
- `400` — Empty query
- `422` — Invalid parameters (top_k out of range, min_score out of range)
- `503` — Search engine not available

### GET /search/health

Check the hybrid search engine health status.

**Response:**
```json
{
  "ready": true,
  "embedding_model_loaded": true,
  "vector_store_healthy": true,
  "keyword_backend": "BM25",
  "ranking_weights": {
    "semantic_weight": 0.65,
    "keyword_weight": 0.25,
    "metadata_weight": 0.10
  },
  "statistics": {
    "total_queries": 42,
    "avg_latency_ms": 52.3,
    "avg_chunks_searched": 35.0,
    "avg_chunks_returned": 8.5,
    "avg_score": 0.71,
    "p50_latency_ms": 48.0,
    "p95_latency_ms": 95.0,
    "p99_latency_ms": 120.0,
    "recent_queries": ["transformer attention", "machine learning basics"]
  }
}
```

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
