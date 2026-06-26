import torch
import logging
from typing import Tuple
from transformers import AutoModelForSequenceClassification, AutoTokenizer

logger = logging.getLogger(__name__)

LABEL_NAMES = ['Negative', 'Neutral', 'Positive']


class SentimentModel:
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest", token: str | None = None):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, token=token)
        self.model.eval()
        logger.info("SentimentModel loaded: %s", model_name)

    def predict(self, text: str, max_length: int = 512) -> Tuple[str, float]:
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=max_length
        )
        with torch.no_grad():
            outputs = self.model(**inputs)

        probabilities = torch.softmax(outputs.logits, dim=1)
        predicted_idx = probabilities.argmax().item()
        sentiment = LABEL_NAMES[predicted_idx]
        confidence = probabilities[0][predicted_idx].item()
        return sentiment, confidence
