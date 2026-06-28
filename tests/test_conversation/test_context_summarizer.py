import pytest
from backend.app.reasoning.conversation.context_summarizer import ContextSummarizer


class TestContextSummarizer:
    @pytest.fixture
    def summarizer(self):
        return ContextSummarizer()

    def test_summarize_empty(self, summarizer):
        assert summarizer.summarize([]) == ""

    def test_summarize_single_message(self, summarizer):
        result = summarizer.summarize([{"role": "user", "content": "Hello"}])
        assert "User: Hello" in result

    def test_summarize_multiple_messages(self, summarizer):
        messages = [
            {"role": "user", "content": "Summarize my resume"},
            {"role": "assistant", "content": "Your resume shows experience in AI."},
            {"role": "user", "content": "Compare it with Google jobs"},
        ]
        result = summarizer.summarize(messages)
        assert "User:" in result
        assert "Assistant:" in result
        assert "resume" in result.lower()

    def test_summarize_empty_content(self, summarizer):
        result = summarizer.summarize([{"role": "user", "content": ""}])
        assert result == ""

    def test_summarize_none_content(self, summarizer):
        result = summarizer.summarize([{"role": "user", "content": None}])
        assert result == ""

    def test_condense_short_text(self, summarizer):
        assert summarizer._condense_turn("Hello") == "Hello"

    def test_condense_long_text(self, summarizer):
        long_text = "This is a very long text that should be condensed because it exceeds the character limit of one hundred and twenty characters for short texts."
        result = summarizer._condense_turn(long_text)
        assert len(result) <= 123

    def test_condense_text_with_key_markers(self, summarizer):
        text = "First sentence. Therefore this is the key finding. However there are limitations."
        result = summarizer._condense_turn(text)
        assert "key finding" in result.lower() or "Therefore" in result

    def test_condense_very_short(self, summarizer):
        assert summarizer._condense_turn("Hi!") == "Hi!"

    def test_get_topic_label(self, summarizer):
        messages = [
            {"role": "user", "content": "What is machine learning?"},
            {"role": "assistant", "content": "Machine learning is a subset of AI."},
        ]
        topic = summarizer.get_topic_label(messages)
        assert "machine" in topic.lower() or "learning" in topic.lower()

    def test_get_topic_label_only_user(self, summarizer):
        messages = [
            {"role": "user", "content": "Tell me about neural networks and deep learning"},
        ]
        topic = summarizer.get_topic_label(messages)
        assert topic

    def test_get_topic_label_empty(self, summarizer):
        assert summarizer.get_topic_label([]) == "general conversation"

    def test_extract_topics(self, summarizer):
        summary = "\n• User: What is AI?\n• Assistant: AI is artificial intelligence."
        topics = summarizer.extract_topics(summary)
        assert len(topics) > 0

    def test_extract_topics_empty(self, summarizer):
        assert summarizer.extract_topics("") == []

    def test_split_sentences(self, summarizer):
        sentences = summarizer._split_sentences("First sentence. Second sentence! Third?")
        assert len(sentences) == 3

    def test_clean_sentence_with_brackets(self, summarizer):
        cleaned = summarizer._clean_sentence("[Source 1] This is content.")
        assert "Source" not in cleaned

    def test_clean_sentence_no_brackets(self, summarizer):
        assert summarizer._clean_sentence("Normal sentence.") == "Normal sentence."

    def test_summarize_handles_long_conversation(self, summarizer):
        messages = [
            {"role": "user", "content": f"Question {i}"}
            for i in range(20)
        ]
        result = summarizer.summarize(messages)
        assert result
        assert all(f"User: Question {i}" in result for i in range(20)) or "Question" in result
