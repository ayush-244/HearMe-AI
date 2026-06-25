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
│       │   └── routes.py           # REST API endpoints
│       ├── services/
│       │   ├── __init__.py         # Service initialization & dependency injection
│       │   ├── sentiment_service.py
│       │   ├── language_service.py
│       │   ├── prompt_service.py
│       │   ├── chat_service.py
│       │   ├── history_service.py
│       │   └── logging_service.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── chat.py             # Pydantic request/response models
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
│   ├── translation/                # (placeholder)
│   ├── rag/                        # (placeholder)
│   ├── memory/                     # (placeholder)
│   └── embeddings/                 # (placeholder)
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
│   └── test_chat_service.py
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── FOLDER_STRUCTURE.md
│
└── logs/                           # Rotating log files
```
