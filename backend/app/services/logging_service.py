import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class LoggingService:
    def __init__(self, log_path: str = "sentiment_analysis_log.txt"):
        self._log_path = Path(log_path)

    def log_sentiment(self, text: str, sentiment: str, confidence: float) -> None:
        try:
            timestamp = datetime.now().isoformat()
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Input: {text}\n")
                f.write(f"Sentiment: {sentiment}\n")
                f.write(f"Confidence: {confidence:.2%}\n\n")
            logger.info("Sentiment analysis logged to %s", self._log_path)
        except Exception as e:
            logger.error("Failed to log sentiment: %s", e)
