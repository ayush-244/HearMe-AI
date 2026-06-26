import logging
import time
from typing import Any, Dict, List, Optional
from threading import Lock

from transformers import pipeline

logger = logging.getLogger(__name__)


class ZeroShotClassifier:
    def __init__(self, model_name: str = "typeform/distilbert-base-uncased-mnli", token: str | None = None) -> None:
        self._model_name = model_name
        self._token = token
        self._pipeline: Any = None
        self._lock = Lock()

    def _load(self) -> None:
        if self._pipeline is None:
            with self._lock:
                if self._pipeline is None:
                    logger.info("Loading zero-shot classifier: %s", self._model_name)
                    self._pipeline = pipeline("zero-shot-classification", model=self._model_name, token=self._token)
                    logger.info("Zero-shot classifier loaded successfully")

    def classify(
        self,
        text: str,
        candidate_labels: List[str],
        multi_label: bool = False,
    ) -> Dict[str, Any]:
        self._load()
        logger.debug("ZSC classify: text_len=%d, labels=%s, multi_label=%s", len(text), candidate_labels, multi_label)
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
        start = time.time()

        # 1. Language Detection
        t0 = time.time()
        detected_lang = self._language_service.detect(text) if language == "auto" else language
        if detected_lang not in self._prompt_service.language_configs:
            detected_lang = "en"
        language_name = self._language_service.get_language_name(detected_lang)
        logger.debug("Pipeline stage 1 (lang): %s (%.3fs)", detected_lang, time.time() - t0)

        # 2. Sentiment Analysis
        t0 = time.time()
        sentiment, sentiment_confidence = self._sentiment_service.analyze(text)
        logger.debug("Pipeline stage 2 (sentiment): %s %.2f (%.3fs)", sentiment, sentiment_confidence, time.time() - t0)

        # 3. Emotion Detection
        t0 = time.time()
        emotion_result = self._emotion_service.analyze(text)
        logger.debug("Pipeline stage 3 (emotion): %s (%.3fs)", emotion_result.get("label"), time.time() - t0)

        # 4. Toxicity Detection
        t0 = time.time()
        toxicity_result = self._toxicity_service.analyze(text)
        logger.debug("Pipeline stage 4 (toxicity): %s (%.3fs)", toxicity_result.get("category"), time.time() - t0)

        # 5. Threat Detection
        t0 = time.time()
        threat_result = self._threat_service.analyze(text)
        logger.debug("Pipeline stage 5 (threat): %s (%.3fs)", threat_result.get("risk_level"), time.time() - t0)

        # 6. Intent Classification
        t0 = time.time()
        intent_result = self._intent_service.analyze(text)
        logger.debug("Pipeline stage 6 (intent): %s (%.3fs)", intent_result.get("intent"), time.time() - t0)

        # 7. Adaptive Prompt Construction
        t0 = time.time()
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
        logger.debug("Pipeline stage 7 (prompt): %d chars (%.3fs)", len(prompt), time.time() - t0)

        # 8. LLM Response
        t0 = time.time()
        response_text = self._chat_service.invoke_llm(prompt)
        logger.debug("Pipeline stage 8 (llm): %d chars (%.3fs)", len(response_text), time.time() - t0)

        elapsed = time.time() - start
        logger.info("Pipeline complete: %.3fs total (lang=%s, sentiment=%s, emotion=%s, threat=%s, intent=%s)",
                     elapsed, detected_lang, sentiment, emotion_result.get("label"),
                     threat_result.get("risk_level"), intent_result.get("intent"))

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
