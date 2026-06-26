# Multilingual Sentiment-Aware Chatbot

A production-ready multilingual chatbot that detects user sentiment, emotion, toxicity, threats, and intent — then responds adaptively in the user's language.

## Features

- **Sentiment Analysis**: Real-time emotional tone detection (Positive/Neutral/Negative)
- **Language Detection**: Automatic language identification (English, Spanish, French, Hindi)
- **Emotion Detection**: Detect 8 emotions — Joy, Sadness, Anger, Fear, Love, Surprise, Disgust, Neutral
- **Toxicity Detection**: Identify toxic content — Toxicity, Hate Speech, Abuse, Insults, Profanity
- **Threat Detection**: Detect violence, self-harm, murder, and terror threats with risk level assessment
- **Intent Classification**: Classify 10 intents — Greeting, Question, Conversation, Coding, Medical, Translation, Complaint, Mental Health, Goodbye, Other
- **Adaptive Prompt Routing**: Automatically selects safety, de-escalation, empathy, or normal prompts based on analysis
- **AI Pipeline**: End-to-end pipeline combining all detection modules with LLM response generation
- **Multilingual Responses**: LLM-powered responses in the detected or selected language
- **Chat History**: In-memory conversation history with sliding window
- **Document Management**: Upload, validate, list, and delete PDF, DOCX, TXT, and Markdown files with MIME validation and size enforcement
- **Text Extraction**: Extract, normalize, and store text content from PDF (PyMuPDF), DOCX (python-docx), TXT (multi-encoding), and Markdown files with preview generation
- **Document Intelligence**: Analyze document structure without LLMs — classify document type (research paper, resume, book, etc.), extract logical sections, detect tables/images/code/URLs/emails, extract keywords (lightweight RAKE-like), estimate reading time, generate summary preview, and detect language
- **Intelligent Chunking**: Production-grade chunking engine with three strategies — Fixed-size (500 words, 50 overlap), Section-aware (respects document sections), and Semantic (preserves paragraphs, tables, code blocks, lists). Automatic strategy selection per document type. Validation, deduplication, statistics, and persistent storage at `uploads/chunks/`
- **Embedding Layer**: SentenceTransformer-based embedding generation (default `BAAI/bge-base-en-v1.5`, 768 dimensions) with SHA256 checksum cache, lazy model initialization, batch encoding, configurable batch size from Settings, and persistent storage at `uploads/embeddings/`. Delete cascade with document removal.

## Architecture

```
├── app.py              # Streamlit entry point (compatibility shim)
├── backend/
│   └── app/            # FastAPI backend
│       ├── api/        # REST endpoints
│       ├── services/   # Business logic services (DI container)
│       ├── schemas/    # Pydantic request/response models
│       └── config/     # Pydantic Settings
├── frontend/
│   └── streamlit_ui.py # Streamlit application
├── ai/
│   ├── sentiment/      # RoBERTa sentiment model wrapper
│   ├── language/       # Language detection wrapper
│   ├── emotion/        # Emotion detector (zero-shot)
│   ├── toxicity/       # Toxicity detector (zero-shot)
│   ├── threat/         # Threat detector (zero-shot)
│   ├── intent/         # Intent classifier (zero-shot)
│   ├── pipeline/       # AI pipeline orchestrator & shared classifier
│   ├── chunking/       # Intelligent chunking engine
│   │   ├── chunk_engine.py       # Orchestrator
│   │   ├── chunk_models.py       # Chunk dataclass + statistics
│   │   ├── chunk_strategy.py     # Strategy selection logic
│   │   ├── fixed_chunker.py      # Fixed-size chunking
│   │   ├── section_chunker.py    # Section-aware chunking
│   │   ├── semantic_chunker.py   # Semantic chunking
│   │   └── overlap.py            # Overlap generation
│   ├── embeddings/     # Embedding layer
│   │   ├── embedding_model.py    # SentenceTransformer wrapper
│   │   └── embedding_cache.py    # SHA256 checksum cache
│   └── documents/      # Document processing
│       ├── analyzer.py           # Document intelligence orchestrator
│       ├── document_classifier.py# Heuristic document type classification
│       ├── section_parser.py     # Logical section extraction
│       └── metadata_extractor.py # Rich metadata extraction
├── prompts/            # Externalized prompt templates
├── uploads/            # Document storage (auto-created per file type)
├── tests/              # Unit tests (385+)
└── docs/               # Documentation
```

## Quick Start

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your API keys in `.env`:
   ```
   GROQ_API_KEY=your_groq_api_key
   HF_TOKEN=your_huggingface_token
   ```
4. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
5. Or run the FastAPI backend:
   ```bash
   uvicorn backend.app.main:app --reload
   ```

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Sentiment Model | CardiffNLP Twitter-RoBERTa |
| Emotion / Toxicity / Threat / Intent | Zero-shot classifier (DistilBERT-MNLI) |
| LLM | Mixtral 8x7B (Groq API) |
| Language Detection | langdetect |
| Embedding Model | BAAI/bge-base-en-v1.5 (SentenceTransformer) |
| Embedding Cache | SHA256 checksum deduplication |
| UI | Streamlit |
| Backend API | FastAPI |
| Configuration | Pydantic Settings |
