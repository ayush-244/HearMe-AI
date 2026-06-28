# HearMe AI — Intelligent Knowledge Platform

A production-ready AI-powered platform with multilingual sentiment-aware chatbot, knowledge reasoning (RAG), document intelligence, long-term personal memory, and a modern Next.js frontend.

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
- **Vector Store**: Qdrant-based vector storage layer with upsert, delete, search, and health endpoints. Abstract `VectorStore` interface with `QdrantVectorStore` implementation. Collection management with dimension validation and automatic creation.
- **Hybrid Search Engine**: Production-grade hybrid search combining semantic (vector similarity) and keyword (BM25/TF-IDF) retrieval with configurable weighted ranking, metadata boosting (language match, title overlap, section overlap, importance score, keyword overlap), section diversity enforcement (max `ceil(top_k / 3)` per section), and deduplication via `difflib.SequenceMatcher`.
- **Knowledge Reasoning Engine**: Production RAG pipeline that transforms retrieved knowledge into accurate, citation-backed answers. Context builder with dedup, ordering, token budgeting, and adjacent chunk merging. Template-driven prompt builder loaded from `prompts/knowledge_*.txt`. Rule-based guardrails against prompt injection (24+ patterns). Response validator detecting hallucination indicators and unsupported claims. Citation manager supporting inline and markdown styles. Configurable conversation history (default 5 turns).
- **Personal Memory System**: Long-term memory subsystem that persists user information across conversations. Four memory types — Semantic (facts), Episodic (events), Preference (likes/dislikes), Working (temporary). Automatic extraction from conversation turns with noise filtering. Importance scoring based on frequency, recency, specificity, emphasis, and future usefulness. Rule-based classification. JSON file-based storage. Semantic deduplication with overlap detection. Lexical relevance retrieval. Consolidation engine merges related memories (e.g., "I know Python" + "I use FastAPI" → "Related facts: python, fastapi"). Forgetting engine with configurable decay rates; protects high-importance, pinned, and frequently accessed memories.
- **Modern Web UI**: Next.js 16 frontend with TypeScript, Tailwind CSS 4, shadcn/ui components, dark mode, responsive design, and dedicated pages for chat, documents, knowledge, memory, analytics, settings, and developer tools.

## Architecture

```
├── app.py              # Streamlit entry point (compatibility shim)
├── backend/
│   └── app/            # FastAPI backend
│       ├── api/        # REST endpoints (chat, documents, search, vectorstore, knowledge, memory)
│       ├── services/   # Business logic services (DI container)
│       ├── schemas/    # Pydantic request/response models
│       ├── retrieval/  # Hybrid search engine (semantic, keyword, ranking, citations)
│       ├── reasoning/  # Knowledge reasoning engine (context, prompt, citations, guardrails)
│       ├── memory/     # Personal memory system (extraction, classification, retrieval, consolidation, forgetting)
│       ├── vectorstore/# Qdrant vector storage (ABC, Qdrant impl, collection mgmt)
│       └── config/     # Pydantic Settings
├── frontend/
│   ├── streamlit_ui.py      # Streamlit application (legacy)
│   └── src/                 # Next.js 16 application (TypeScript)
│       ├── app/             # Pages (chat, documents, memory, knowledge, analytics, settings, developer)
│       ├── components/ui/   # shadcn/ui components (Radix primitives)
│       ├── hooks/           # Custom React hooks
│       ├── services/        # API client
│       ├── stores/          # Zustand state management
│       ├── providers/       # React context providers
│       └── lib/             # Utilities & constants
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
├── uploads/            # Document storage + memory storage (auto-created)
│   └── memory/         # JSON-based memory persistence (semantic, episodic, preferences, working)
├── tests/              # Unit tests (770+ across 28 files)
│   ├── test_retrieval.py                # Hybrid search engine
│   ├── test_reasoning.py                # Knowledge reasoning engine
│   ├── test_memory.py                   # Personal memory system
│   ├── test_vectorstore.py              # Vector store unit tests
│   ├── test_vectorstore_integration.py  # Vector store integration tests
│   ├── test_chunking.py                 # Intelligent chunking engine
│   ├── test_document_*.py               # Document management (4 files)
│   ├── test_embedding_*.py              # Embedding layer (2 files)
│   ├── test_ai_pipeline.py              # AI pipeline orchestrator
│   ├── test_chat_*.py                   # Chat service & integration
│   ├── test_*_service.py                # Service layer tests (10 files)
│   ├── test_*_detector.py               # Detector tests (4 files)
│   ├── test_*_classifier.py             # Classifier tests (2 files)
│   └── test_api_client.py               # API client test
└── docs/               # Documentation
```

## Quick Start

1. Clone the repository
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend && npm install
   ```
4. Set your API keys in `.env`:
   ```
   GROQ_API_KEY=your_groq_api_key
   HF_TOKEN=your_huggingface_token
   ```
5. Start the FastAPI backend:
   ```bash
   uvicorn backend.app.main:app --reload
   ```
6. Start the Next.js frontend (in a separate terminal):
   ```bash
   cd frontend && npm run dev
   ```
7. Open [http://localhost:3000](http://localhost:3000) in your browser
8. Or run the legacy Streamlit app:
   ```bash
   streamlit run app.py
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
| Vector Storage | Qdrant (embedded/remote) |
| Vector Store Interface | Abstract `VectorStore` ABC |
| Keyword Search | BM25 (rank-bm25) / TF-IDF (scikit-learn) |
| Hybrid Ranking | Configurable weighted scoring (semantic, keyword, metadata) |
| Section Diversity | Max `ceil(top_k / 3)` chunks per section |
| Knowledge RAG | Template-driven reasoning engine with guardrails, citation manager, response validator |
| Guardrails | 24+ rule-based prompt injection detection patterns |
| Context Budget | Configurable max tokens (4096) and max chunks (20) |
| Conversation History | Configurable turn limit (default 5) |
| Memory Types | Semantic, Episodic, Preference, Working |
| Memory Extraction | Rule-based with noise filtering, confidence estimation |
| Memory Classification | Regex-based type detection |
| Importance Scoring | Frequency, recency, specificity, emphasis, future usefulness |
| Memory Storage | JSON file persistence at `uploads/memory/` |
| Memory Retrieval | Lexical relevance + importance + recency weighting |
| Memory Consolidation | Topic-based clustering and merging |
| Memory Forgetting | Configurable decay with high-importance protection |
| Frontend (Legacy) | Streamlit |
| Frontend (Modern) | Next.js 16, TypeScript, Tailwind CSS 4 |
| UI Components | shadcn/ui (Radix UI primitives) |
| State Management | Zustand, TanStack React Query |
| Charts | Recharts |
| Animations | Framer Motion |
| Forms | React Hook Form + Zod |
| Backend API | FastAPI |
| Configuration | Pydantic Settings |
