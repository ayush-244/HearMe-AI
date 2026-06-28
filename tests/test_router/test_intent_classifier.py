import pytest
from typing import List

from backend.app.reasoning.router.intent_classifier import IntentClassifier
from backend.app.reasoning.router.intent_models import IntentType, ConversationState


class TestIntentClassifier:
    @pytest.fixture
    def classifier(self):
        return IntentClassifier()

    @pytest.fixture
    def empty_state(self):
        return ConversationState()

    @pytest.fixture
    def state_with_history(self):
        return ConversationState(
            history=[{"role": "user", "content": "what is attention?"}, {"role": "assistant", "content": "attention is a mechanism"}],
            last_assistant_response="attention is a mechanism",
            turn_count=1,
        )

    # --- Greeting Tests ---

    @pytest.mark.parametrize("query", [
        "hello",
        "Hello",
        "hi",
        "Hi there",
        "hey",
        "greetings",
        "good morning",
        "good afternoon",
        "good evening",
        "good day",
        "sup",
        "yo",
        "howdy",
        "what's up",
        "nice to meet you",
    ])
    def test_greeting_detection(self, classifier, empty_state, query):
        result = classifier.classify(query, empty_state)
        assert result.intent == IntentType.GREETING
        assert result.confidence >= 0.9

    @pytest.mark.parametrize("query", [
        "",
        " ",
    ])
    def test_empty_query(self, classifier, empty_state, query):
        result = classifier.classify(query, empty_state)
        assert result.intent == IntentType.GENERAL_AI
        assert result.confidence <= 0.6

    # --- Small Talk Tests ---

    @pytest.mark.parametrize("query", [
        "how are you",
        "How are you?",
        "who are you",
        "where are you",
        "what can you do",
        "thank you",
        "thanks",
        "thx",
        "bye",
        "goodbye",
        "see you",
        "see ya",
        "later",
        "cool",
        "awesome",
        "nice!",
        "great",
        "ok",
        "okay",
        "sure",
        "fine",
        "got it",
        "understood",
        "alright",
        "how's your day",
        "how's your weekend",
        "how's it going",
    ])
    def test_small_talk_detection(self, classifier, empty_state, query):
        result = classifier.classify(query, empty_state)
        assert result.intent == IntentType.SMALL_TALK
        assert result.confidence >= 0.85

    # --- Personal Memory Tests ---

    @pytest.mark.parametrize("query", [
        "who am i",
        "What is my name?",
        "do you know me",
        "what do you know about me",
        "tell me about myself",
        "my name is John",
        "I am called Sarah",
        "what is my email",
        "what are my hobbies",
        "where do i work",
        "where did i study",
        "how old am i",
        "what are my skills",
        "what are my interests",
        "what is my phone number",
        "remember me",
        "do you remember my name",
        "what's my name",
        "what's my age",
        "what's my birthday",
    ])
    def test_personal_memory_detection(self, classifier, empty_state, query):
        result = classifier.classify(query, empty_state)
        assert result.intent == IntentType.PERSONAL_MEMORY
        assert result.confidence >= 0.85

    # --- Document Question Tests ---

    @pytest.mark.parametrize("query", [
        "summarize this document",
        "Summarize the paper",
        "sum up the main points",
        "give me the gist of this file",
        "overview of the document",
        "what does this document say",
        "what does my resume say",
        "compare document A and B",
        "contrast the two papers",
        "difference between the files",
        "what skills are listed",
        "what experience does this resume show",
        "what education is in this document",
        "page 3 says what",
        "section 2 analysis",
        "from the document what is the conclusion",
        "according to the paper",
        "documents related to AI",
        "files about transformers",
    ])
    def test_document_question_detection(self, classifier, empty_state, query):
        result = classifier.classify(query, empty_state)
        assert result.intent == IntentType.DOCUMENT_QUESTION
        assert result.confidence >= 0.75

    def test_document_question_with_attached_docs(self, classifier):
        state = ConversationState(attached_documents=[{"id": "d1", "title": "resume.pdf"}])
        result = classifier.classify("what skills are mentioned", state)
        assert result.intent == IntentType.DOCUMENT_QUESTION

    # --- General AI Tests ---

    @pytest.mark.parametrize("query", [
        "explain quantum computing",
        "Describe the solar system",
        "define machine learning",
        "what is the meaning of life",
        "what are black holes",
        "how does gravity work",
        "difference between AI and ML",
        "tell me about the Roman empire",
        "why is the sky blue",
        "how do rockets work",
        "what is the purpose of education",
        "how does photosynthesis work",
        "what are the laws of thermodynamics",
        "explain how neural networks work",
    ])
    def test_general_ai_detection(self, classifier, empty_state, query):
        result = classifier.classify(query, empty_state)
        assert result.intent == IntentType.GENERAL_AI
        assert result.confidence >= 0.7

    # --- Follow-up Tests ---

    @pytest.mark.parametrize("query", [
        "explain more",
        "tell me more",
        "continue",
        "go on",
        "keep going",
        "elaborate",
        "expand on that",
        "can you elaborate",
        "can you expand",
        "can you clarify",
        "can you simplify",
        "what about that",
        "how about the rest",
        "what about it",
        "and then?",
        "so?",
        "then?",
        "i see, but what else",
        "interesting, so what next",
        "simplify that",
        "dumb it down",
        "what does that mean",
        "what do you mean",
        "what else",
        "anything else",
        "more details",
        "can you repeat that",
    ])
    def test_follow_up_detection(self, classifier, state_with_history, query):
        result = classifier.classify(query, state_with_history)
        assert result.intent == IntentType.FOLLOW_UP
        assert result.confidence >= 0.8

    def test_follow_up_not_detected_on_first_turn(self, classifier, empty_state):
        result = classifier.classify("tell me more", empty_state)
        assert result.intent != IntentType.FOLLOW_UP

    # --- Edge Cases ---

    def test_short_query_no_history(self, classifier, empty_state):
        result = classifier.classify("transformers", empty_state)
        assert result.intent in (IntentType.GENERAL_AI, IntentType.SMALL_TALK)
        assert result.confidence >= 0.5

    def test_query_with_numbers(self, classifier, empty_state):
        result = classifier.classify("explain the 3 laws of robotics", empty_state)
        assert result.intent == IntentType.GENERAL_AI

    def test_query_with_special_chars(self, classifier, empty_state):
        result = classifier.classify("what's the difference between C++ and Rust?", empty_state)
        assert result.intent == IntentType.GENERAL_AI

    def test_query_that_could_be_mixed(self, classifier):
        state = ConversationState(attached_documents=[{"id": "d1"}])
        result = classifier.classify("what is my name and summarize the document", state)
        assert result.intent in (IntentType.MIXED, IntentType.PERSONAL_MEMORY)

    def test_classify_speed(self, classifier, empty_state):
        import time
        start = time.time()
        for _ in range(100):
            classifier.classify("explain quantum computing in simple terms", empty_state)
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 200, f"100 classifications took {elapsed_ms:.2f}ms (expected <200ms)"

    def test_classify_with_full_state(self, classifier):
        state = ConversationState(
            conversation_id="conv1",
            history=[{"role": "user", "content": "summarize my resume"}, {"role": "assistant", "content": "here is a summary"}],
            attached_documents=[{"id": "d1", "title": "resume.pdf"}],
            last_assistant_response="here is a summary",
            last_retrieved_chunks=[{"chunk_id": "c1", "text": "sample"}],
            turn_count=1,
        )
        result = classifier.classify("tell me more about my education", state)
        assert result.intent in (IntentType.DOCUMENT_QUESTION, IntentType.FOLLOW_UP)
