# Multilingual Sentiment-Aware Chatbot

A production-ready multilingual chatbot that detects user sentiment and responds in the user's language.

## Features

- **Sentiment Analysis**: Real-time emotional tone detection (Positive/Neutral/Negative)
- **Language Detection**: Automatic language identification (English, Spanish, French, Hindi)
- **Multilingual Responses**: LLM-powered responses in the detected or selected language
- **Sentiment-Aware Tone**: Response tone adapts to detected sentiment
- **Chat History**: In-memory conversation history with sliding window

## Architecture

```
├── app.py              # Streamlit entry point (compatibility shim)
├── backend/
│   └── app/            # FastAPI backend
│       ├── api/        # REST endpoints
│       ├── services/   # Business logic services
│       ├── schemas/    # Pydantic request/response models
│       └── config/     # Pydantic Settings
├── frontend/
│   └── streamlit_ui.py # Streamlit application
├── ai/
│   ├── sentiment/      # RoBERTa sentiment model wrapper
│   └── language/       # Language detection wrapper
├── prompts/            # Externalized prompt templates
├── tests/              # Unit tests
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
| LLM | Mixtral 8x7B (Groq API) |
| Language Detection | langdetect |
| UI | Streamlit |
| Backend API | FastAPI |
| Configuration | Pydantic Settings |
