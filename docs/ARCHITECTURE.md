# Architecture

## System Overview

```mermaid
graph TD
    subgraph "Frontend"
        ST[Streamlit UI]
    end
    subgraph "Backend API"
        FA[FastAPI]
        API[API Routes<br/>/chat /analyze /sentiment]
    end
    subgraph "Service Layer"
        SS[SentimentService]
        LS[LanguageService]
        PS[PromptService]
        CS[ChatService]
        HS[HistoryService]
        LGS[LoggingService]
        ES[EmotionService]
        TS[ToxicityService]
        THS[ThreatService]
        IS[IntentService]
        PLS[PipelineService]
    end
    subgraph "AI Models"
        SM[SentimentModel<br/>RoBERTa]
        LD[LanguageDetector<br/>langdetect]
        ZSC[ZeroShotClassifier<br/>DistilBERT-MNLI]
        LLM[Mixtral 8x7B<br/>via Groq]
    end
    subgraph "Detectors"
        ED[EmotionDetector]
        TD[ToxicityDetector]
        THD[ThreatDetector]
        IC[IntentClassifier]
    end
    subgraph "Configuration"
        STG[Settings<br/>Pydantic]
        ENV[.env]
        PRO[Prompts<br/>JSON + Text]
        ADP[Adaptive Prompts<br/>Config + Templates]
    end

    ST --> SS
    ST --> LS
    ST --> CS
    FA --> API
    API --> SS
    API --> LS
    API --> CS
    API --> PLS
    SS --> SM
    LS --> LD
    CS --> PS
    CS --> LLM
    PS --> PRO
    PS --> ADP
    PLS --> ES & TS & THS & IS
    PLS --> PS
    PLS --> CS
    ES --> ED
    TS --> TD
    THS --> THD
    IS --> IC
    ED & TD & THD & IC --> ZSC
    SS --> STG
    CS --> STG
    PLS --> STG
    STG --> ENV
```

## AI Pipeline Data Flow

```mermaid
graph LR
    subgraph "AI Pipeline"
        L1[1. Language Detection] --> L2[2. Sentiment Analysis]
        L2 --> L3[3. Emotion Detection]
        L3 --> L4[4. Toxicity Detection]
        L4 --> L5[5. Threat Detection]
        L5 --> L6[6. Intent Classification]
        L6 --> L7[7. Adaptive Prompt Construction]
        L7 --> L8[8. LLM Response]
    end
    UI[User Input] --> L1
    L8 --> RESP[Structured Response]
```

## Adaptive Prompt Routing

```mermaid
graph TD
    INPUT[Analysis Results] --> ROUTE{Route Selection}
    ROUTE -->|Threat Detected| SAFETY[Safety Prompt<br/>Crisis resources + calm tone]
    ROUTE -->|Toxicity Detected| DEESC[De-escalation Prompt<br/>Calm + constructive]
    ROUTE -->|Sadness Detected| EMP[Empathy Prompt<br/>Warm + supportive]
    ROUTE -->|Default| NORMAL[Normal Prompt<br/>Standard assistant]
    SAFETY & DEESC & EMP & NORMAL --> LLM[LLM Generation]
    LLM --> RESP[Response]
```

## Data Flow

```
User Input
    │
    ├──→ SentimentService.analyze() → SentimentModel.predict() → (sentiment, confidence)
    │
    ├──→ EmotionService.analyze() → EmotionDetector.detect() → (label, confidence)
    │
    ├──→ ToxicityService.analyze() → ToxicityDetector.detect() → (is_toxic, category, confidence)
    │
    ├──→ ThreatService.analyze() → ThreatDetector.detect() → (threat_detected, risk_level, confidence)
    │
    ├──→ IntentService.analyze() → IntentClassifier.classify() → (intent, confidence)
    │
    └──→ PipelineService.analyze() → AIPipeline.run()
            │
            ├──→ PromptService.build_adaptive_prompt()
            │       ├── Selects route based on threat/toxicity/emotion
            │       ├── Injects all analysis results
            │       └── Returns formatted prompt
            │
            └──→ ChatService.invoke_llm(prompt) → response text
```

## Service Responsibilities

| Service | Responsibility |
|---------|---------------|
| SentimentService | Wraps RoBERTa model, validates input, provides sentiment analysis |
| LanguageService | Wraps langdetect, provides language name mapping |
| EmotionService | Wraps EmotionDetector, validates input, returns emotion label + confidence |
| ToxicityService | Wraps ToxicityDetector, validates input, returns toxicity category + is_toxic flag |
| ThreatService | Wraps ThreatDetector, validates input, returns risk level + threat type |
| IntentService | Wraps IntentClassifier, validates input, returns intent + confidence |
| PromptService | Loads templates, builds prompts, selects sentiment intros, adaptive prompt routing |
| ChatService | Orchestrates LLM calls with prompt building |
| AIPipeline | End-to-end pipeline orchestrating all detectors and LLM |
| PipelineService | Wraps AIPipeline, validates input |
| HistoryService | Manages conversation history with sliding window |
| LoggingService | Handles sentiment log file writes |
