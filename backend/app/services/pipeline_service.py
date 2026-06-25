import logging
from typing import Any, Dict, List, Optional

from ai.pipeline.ai_pipeline import AIPipeline

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self, pipeline: AIPipeline) -> None:
        self._pipeline = pipeline

    def analyze(
        self,
        text: str,
        language: str = "auto",
        history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        if not text or not text.strip():
            return {
                "language": "Unknown",
                "sentiment": "Neutral",
                "emotion": "neutral",
                "toxicity": "none",
                "threat": "none",
                "intent": "other",
                "confidence": {
                    "sentiment": 0.0,
                    "emotion": 0.0,
                    "toxicity": 0.0,
                    "threat": 0.0,
                    "intent": 0.0,
                },
                "response": "Please provide a valid message.",
            }
        return self._pipeline.run(text, language, history)
