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
