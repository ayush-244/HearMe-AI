import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

SUMMARY_SEPARATOR = "\n• "


class ContextSummarizer:
    def __init__(self):
        logger.info("ContextSummarizer initialized")

    def summarize(self, messages: List[Dict[str, str]]) -> str:
        if not messages:
            return ""

        parts = []

        for msg in messages:
            role = msg.get("role", "unknown").capitalize()
            content = (msg.get("content", "") or "").strip()
            if not content:
                continue

            summary = self._condense_turn(content)
            if summary:
                parts.append(f"{role}: {summary}")

        if not parts:
            return ""

        return SUMMARY_SEPARATOR + SUMMARY_SEPARATOR.join(parts)

    def _condense_turn(self, text: str) -> str:
        text = text.strip()
        if not text:
            return ""

        if len(text) <= 120:
            return text

        sentences = self._split_sentences(text)
        if len(sentences) <= 2:
            return text[:120] + "..."

        key_sentences = []
        for s in sentences:
            s = s.strip()
            if len(s) < 10:
                continue
            if any(word in s.lower() for word in ["therefore", "however", "in conclusion", "importantly", "notably", "in summary", "overall", "key", "main", "primary"]):
                key_sentences.append(s)
                if len(key_sentences) >= 2:
                    break

        if not key_sentences:
            key_sentences = [s for s in sentences if len(s) > 20][:2]

        if not key_sentences:
            return text[:120] + "..."

        result = " | ".join(self._clean_sentence(s) for s in key_sentences)
        if len(result) > 200:
            result = result[:200] + "..."

        return result

    def _split_sentences(self, text: str) -> List[str]:
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _clean_sentence(self, sentence: str) -> str:
        sentence = sentence.strip()
        if sentence.startswith("["):
            bracket_end = sentence.find("]")
            if bracket_end > 0 and bracket_end < 60:
                sentence = sentence[bracket_end + 1:].strip()
        return sentence

    def get_topic_label(self, messages: List[Dict[str, str]]) -> str:
        from collections import Counter
        import re
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "i", "you", "it", "this", "that", "to", "for", "of", "in", "on", "with", "about", "what", "how", "why", "my", "me", "your", "do", "does", "can", "will"}

        nouns = []
        question_nouns = []

        for msg in messages[-4:]:
            content = (msg.get("content", "") or "").lower()
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content)
            if msg.get("role") == "user":
                question_nouns.extend([w for w in words if w not in stop_words])
            nouns.extend([w for w in words if w not in stop_words])

        if question_nouns:
            counter = Counter(question_nouns)
            top = counter.most_common(3)
            label = ", ".join(w for w, c in top)
            if label:
                return label

        if nouns:
            counter = Counter(nouns)
            top = counter.most_common(3)
            label = ", ".join(w for w, c in top)
            if label:
                return label

        return "general conversation"

    def extract_topics(self, summary: str) -> List[str]:
        if not summary:
            return []
        topics = []
        for line in summary.split(SUMMARY_SEPARATOR):
            line = line.strip()
            if line and ": " in line:
                content = line.split(": ", 1)[1]
                words = content.split()[:3]
                if words:
                    topics.append(" ".join(words).rstrip(".,!?"))
        return topics[:5]
