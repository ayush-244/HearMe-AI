import logging
from typing import Any, Dict, List, Optional

from transformers import pipeline

logger = logging.getLogger(__name__)


class ZeroShotClassifier:
    def __init__(self, model_name: str = "typeform/distilbert-base-uncased-mnli") -> None:
        self._model_name = model_name
        self._pipeline: Any = None

    def _load(self) -> None:
        if self._pipeline is None:
            logger.info("Loading zero-shot classifier: %s", self._model_name)
            self._pipeline = pipeline("zero-shot-classification", model=self._model_name)
            logger.info("Zero-shot classifier loaded successfully")

    def classify(
        self,
        text: str,
        candidate_labels: List[str],
        multi_label: bool = False,
    ) -> Dict[str, Any]:
        self._load()
        result = self._pipeline(text, candidate_labels=candidate_labels, multi_label=multi_label)
        return {
            "labels": result["labels"],
            "scores": result["scores"],
        }


class AIPipeline:
    def __init__(
        self,
        language_service: Any,
        sentiment_service: Any,
        emotion_service: Any,
        toxicity_service: Any,
        threat_service: Any,
        intent_service: Any,
        prompt_service: Any,
        chat_service: Any,
    ) -> None:
        self._language_service = language_service
        self._sentiment_service = sentiment_service
        self._emotion_service = emotion_service
        self._toxicity_service = toxicity_service
        self._threat_service = threat_service
        self._intent_service = intent_service
        self._prompt_service = prompt_service
        self._chat_service = chat_service

    def run(
        self,
        text: str,
        language: str = "auto",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        history = history or []

        # 1. Language Detection
        detected_lang = self._language_service.detect(text) if language == "auto" else language
        if detected_lang not in self._prompt_service.language_configs:
            detected_lang = "en"
        language_name = self._language_service.get_language_name(detected_lang)

        # 2. Sentiment Analysis
        sentiment, sentiment_confidence = self._sentiment_service.analyze(text)

        # 3. Emotion Detection
        emotion_result = self._emotion_service.analyze(text)

        # 4. Toxicity Detection
        toxicity_result = self._toxicity_service.analyze(text)

        # 5. Threat Detection
        threat_result = self._threat_service.analyze(text)

        # 6. Intent Classification
        intent_result = self._intent_service.analyze(text)

        # 7. Adaptive Prompt Construction
        prompt = self._prompt_service.build_adaptive_prompt(
            user_input=text,
            language=detected_lang,
            sentiment=sentiment,
            emotion=emotion_result,
            toxicity=toxicity_result,
            threat=threat_result,
            intent=intent_result,
            history=history,
        )

        # 8. LLM Response
        response_text = self._chat_service.invoke_llm(prompt)

        return {
            "language": language_name,
            "sentiment": sentiment,
            "emotion": emotion_result["label"],
            "toxicity": toxicity_result["category"],
            "threat": threat_result["risk_level"],
            "intent": intent_result["intent"],
            "confidence": {
                "sentiment": sentiment_confidence,
                "emotion": emotion_result["confidence"],
                "toxicity": toxicity_result["confidence"],
                "threat": threat_result["confidence"],
                "intent": intent_result["confidence"],
            },
            "response": response_text,
        }
