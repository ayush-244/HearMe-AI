# Architecture

## System Overview

```mermaid
graph TD
    subgraph "Frontend"
        ST[Streamlit UI]
    end
    subgraph "Backend API"
        FA[FastAPI]
        API[API Routes]
    end
    subgraph "Service Layer"
        SS[SentimentService]
        LS[LanguageService]
        PS[PromptService]
        CS[ChatService]
        HS[HistoryService]
        LGS[LoggingService]
    end
    subgraph "AI Models"
        SM[SentimentModel<br/>RoBERTa]
        LD[LanguageDetector<br/>langdetect]
        LLM[Mixtral 8x7B<br/>via Groq]
    end
    subgraph "Configuration"
        STG[Settings<br/>Pydantic]
        ENV[.env]
        PRO[Prompts<br/>JSON + Text]
    end

    ST --> SS
    ST --> LS
    ST --> CS
    FA --> API
    API --> SS
    API --> LS
    API --> CS
    SS --> SM
    LS --> LD
    CS --> PS
    CS --> LLM
    PS --> PRO
    SS --> STG
    CS --> STG
    STG --> ENV
```

## Data Flow

```
User Input
    │
    ├──→ SentimentService.analyze() → SentimentModel.predict() → (sentiment, confidence)
    │
    ├──→ LanguageService.detect() → LanguageDetector.detect() → language_code
    │
    └──→ ChatService.generate_response()
            │
            ├──→ PromptService.build_chat_prompt()
            │       ├── Loads language config from prompts/language_configs.json
            │       ├── Loads chat template from prompts/chat_template.txt
            │       ├── Injects sentiment + language + history
            │       └── Returns formatted prompt
            │
            └──→ LLM.invoke(prompt) → response text
```

## Service Responsibilities

| Service | Responsibility |
|---------|---------------|
| SentimentService | Wraps RoBERTa model, validates input, provides sentiment analysis |
| LanguageService | Wraps langdetect, provides language name mapping |
| PromptService | Loads templates, builds prompts, selects sentiment intros |
| ChatService | Orchestrates LLM calls with prompt building |
| HistoryService | Manages conversation history with sliding window |
| LoggingService | Handles sentiment log file writes |
