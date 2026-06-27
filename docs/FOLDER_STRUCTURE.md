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
│       │   ├── document_routes.py  # Document upload, list, get, delete, extract, content
│       │   ├── search_routes.py   # Search endpoints (POST /search, GET /search/health)
│       │   └── knowledge_routes.py # Knowledge chat endpoints (POST /knowledge/chat, GET /knowledge/health)
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
│       │   ├── document_service.py # Document upload, validation, storage, metadata
│       │   └── embedding_service.py # Embedding generation, caching, CRUD
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── search_engine.py     # Hybrid search orchestrator
│       │   ├── search_models.py     # SearchQuery, SearchResult, SearchResultItem
│       │   ├── query_parser.py      # Query parsing, filter extraction, stop word removal
│       │   ├── query_analyzer.py    # Language/intent/complexity analysis
│       │   ├── semantic_search.py   # Embedding + vector store search
│       │   ├── keyword_search.py    # BM25 / TF-IDF keyword scoring
│       │   ├── hybrid_ranker.py     # Weighted hybrid ranking + dedup + diversity
│       │   ├── citation_builder.py  # Citation string generation
│       │   └── retrieval_metrics.py # Query latency tracking, percentiles
│       ├── reasoning/
│       │   ├── __init__.py
│       │   ├── reasoning_engine.py  # Knowledge RAG orchestrator
│       │   ├── context_builder.py   # Context dedup, ordering, token budgeting, merging
│       │   ├── prompt_builder.py    # Template-driven prompt construction
│       │   ├── citation_manager.py  # Citation tracking and formatting
│       │   ├── response_validator.py # Hallucination + unsupported claim detection
│       │   ├── guardrails.py        # Prompt injection detection (24+ patterns)
│       │   └── answer_models.py     # KnowledgeQuery, KnowledgeAnswer, ConversationTurn
│       ├── vectorstore/
│       │   ├── __init__.py
│       │   ├── base.py             # VectorStore ABC (interface)
│       │   ├── qdrant_store.py     # QdrantVectorStore implementation
│       │   ├── collection_manager.py # Qdrant collection lifecycle
│       │   ├── metadata_mapper.py  # Chunk ↔ payload mapping, filter building
│       │   └── exceptions.py       # VectorStoreError, CollectionError, IndexError
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── chat.py             # Chat/analyze/sentiment/language Pydantic models
│       │   ├── document.py         # Document metadata/upload/list/delete Pydantic models
│       │   ├── search.py           # SearchRequest, SearchResponse, SearchHealthResponse
│       │   └── knowledge.py        # KnowledgeChatRequest, KnowledgeChatResponse, KnowledgeHealthResponse
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py         # Pydantic Settings from .env (incl. Qdrant & search config)
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
│   ├── chunking/
│   │   ├── __init__.py
│   │   ├── chunk_engine.py         # Chunking orchestrator
│   │   ├── chunk_models.py         # Chunk dataclass + statistics
│   │   ├── chunk_strategy.py       # Strategy selection logic
│   │   ├── fixed_chunker.py        # Fixed-size chunking
│   │   ├── section_chunker.py      # Section-aware chunking
│   │   ├── semantic_chunker.py     # Semantic chunking
│   │   └── overlap.py              # Overlap generation
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── embedding_model.py      # SentenceTransformer wrapper
│   │   └── embedding_cache.py      # SHA256 checksum cache
│   └── documents/
│       ├── __init__.py
│       ├── analyzer.py             # Document intelligence orchestrator
│       ├── document_classifier.py  # Heuristic document type classification
│       ├── section_parser.py       # Logical section extraction
│       └── metadata_extractor.py   # Rich metadata extraction
│
├── uploads/                        # Document storage (auto-created)
│   ├── pdf/
│   ├── docx/
│   ├── txt/
│   ├── markdown/
│   ├── metadata.json              # Document metadata store
│   ├── extracted/                  # Extracted text content
│   ├── chunked/                    # Generated chunks
│   └── embeddings/                # Embedding vectors
│
├── prompts/
│   ├── chat_template.txt           # Prompt template with placeholders
│   ├── language_configs.json       # Language configurations
│   ├── sentiment_intros.json       # Sentiment-aware intro phrases
│   ├── knowledge_system.txt        # Knowledge reasoning system instructions
│   ├── knowledge_user.txt          # Knowledge reasoning user message template
│   └── knowledge_guardrails.txt    # Critical guardrail rules for knowledge LLM
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
│   ├── test_document_routes.py     # Integration tests (8 tests)
│   ├── test_document_loaders.py    # Loader tests (PDF, DOCX, TXT, Markdown)
│   ├── test_document_intelligence.py # Analyzer, classifier, section parser, metadata
│   ├── test_chunking.py           # Chunking engine tests (60+ tests)
│   ├── test_embedding_model.py    # Embedding model unit tests
│   ├── test_embedding_service.py  # Embedding service tests (40+ tests)
│   ├── test_vectorstore.py        # Vector store unit tests (50 tests, mocked Qdrant)
│   ├── test_vectorstore_integration.py  # Vector store integration tests (20 tests, real embedded Qdrant)
│   ├── test_retrieval.py          # Hybrid search engine tests (88 tests, mocked & integration)
│   └── test_reasoning.py          # Knowledge reasoning engine tests (117 tests, mocked)
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── FOLDER_STRUCTURE.md
│
└── logs/                           # Rotating log files
```
