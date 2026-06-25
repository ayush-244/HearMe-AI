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
