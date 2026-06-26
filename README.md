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
│   └── pipeline/       # AI pipeline orchestrator & shared classifier
├── prompts/            # Externalized prompt templates
├── uploads/            # Document storage (auto-created per file type)
├── tests/              # Unit tests (133+)
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
| UI | Streamlit |
| Backend API | FastAPI |
| Configuration | Pydantic Settings |
