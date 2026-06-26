# Folder Structure

```
├── app.py                          # Compatibility shim — runs the Streamlit UI
├── .env                            # Environment variables (API keys)
├── requirements.txt                # Python dependencies
│
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── main.py                 # FastAPI application entry point
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes.py           # Chat, sentiment, analyze, health, feedback endpoints
│       │   └── document_routes.py  # Document upload, list, get, delete endpoints
│       ├── services/
│       │   ├── __init__.py         # Service initialization & dependency injection
│       │   ├── sentiment_service.py
│       │   ├── language_service.py
│       │   ├── prompt_service.py
│       │   ├── chat_service.py
│       │   ├── history_service.py
│       │   ├── logging_service.py
│       │   ├── emotion_service.py
│       │   ├── toxicity_service.py
│       │   ├── threat_service.py
│       │   ├── intent_service.py
│       │   ├── pipeline_service.py
│       │   └── document_service.py # Document upload, validation, storage, metadata
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── chat.py             # Chat/analyze/sentiment/language Pydantic models
│       │   └── document.py         # Document metadata/upload/list/delete Pydantic models
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py         # Pydantic Settings from .env
│       ├── middleware/
│       │   └── __init__.py         # (placeholder for future middleware)
│       ├── utils/
│       │   └── __init__.py         # (placeholder for future utilities)
│       └── database/
│           └── __init__.py         # (placeholder for future database)
│
├── frontend/
│   ├── __init__.py
│   └── streamlit_ui.py             # Streamlit application
│
├── ai/
│   ├── __init__.py
│   ├── sentiment/
│   │   ├── __init__.py
│   │   └── model.py                # RoBERTa sentiment model wrapper
│   ├── language/
│   │   ├── __init__.py
│   │   └── detector.py             # Language detection wrapper
│   ├── emotion/
│   │   ├── __init__.py
│   │   └── detector.py
│   ├── toxicity/
│   │   ├── __init__.py
│   │   └── detector.py
│   ├── threat/
│   │   ├── __init__.py
│   │   └── detector.py
│   ├── intent/
│   │   ├── __init__.py
│   │   └── classifier.py
│   ├── pipeline/
│   │   ├── __init__.py
│   │   └── ai_pipeline.py          # ZeroShotClassifier, AIPipeline
│   ├── documents/                  # (stubs for future text extraction)
│   │   ├── __init__.py
│   │   ├── pdf_loader.py
│   │   ├── docx_loader.py
│   │   ├── txt_loader.py
│   │   └── markdown_loader.py
│   ├── translation/                # (placeholder)
│   ├── rag/                        # (placeholder)
│   ├── memory/                     # (placeholder)
│   └── embeddings/                 # (placeholder)
│
├── uploads/                        # Document storage (auto-created)
│   ├── pdf/
│   ├── docx/
│   ├── txt/
│   ├── markdown/
│   └── metadata.json               # Document metadata store
│
├── prompts/
│   ├── chat_template.txt           # Prompt template with placeholders
│   ├── language_configs.json       # Language configurations
│   └── sentiment_intros.json       # Sentiment-aware intro phrases
│
├── tests/
│   ├── __init__.py
│   ├── test_sentiment_service.py
│   ├── test_language_service.py
│   ├── test_prompt_service.py
│   ├── test_chat_service.py
│   ├── test_emotion_detector.py
│   ├── test_emotion_service.py
│   ├── test_toxicity_detector.py
│   ├── test_toxicity_service.py
│   ├── test_threat_detector.py
│   ├── test_threat_service.py
│   ├── test_intent_classifier.py
│   ├── test_intent_service.py
│   ├── test_pipeline_service.py
│   ├── test_ai_pipeline.py
│   ├── test_chat_integration.py
│   ├── test_api_client.py
│   ├── test_document_service.py    # Unit tests (22 tests)
│   └── test_document_routes.py     # Integration tests (8 tests)
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── FOLDER_STRUCTURE.md
│
└── logs/                           # Rotating log files
```
