import pytest
from backend.app.reasoning.conversation.reference_resolver import ReferenceResolver


class TestReferenceResolver:
    @pytest.fixture
    def resolver(self):
        return ReferenceResolver()

    def test_no_reference(self, resolver):
        result = resolver.resolve("What is the capital of France?", "", "")
        assert not result.had_reference
        assert result.resolved == "What is the capital of France?"

    def test_pronoun_it(self, resolver):
        result = resolver.resolve("Explain it further.", "What is attention?", "Attention is...")
        assert result.had_reference
        assert "attention" in result.resolved.lower() or "\"what is attention\"" in result.resolved.lower()

    def test_pronoun_this(self, resolver):
        result = resolver.resolve("Tell me more about this.", "Summarize my resume", "Your resume shows...")
        assert result.had_reference

    def test_pronoun_they(self, resolver):
        result = resolver.resolve("Compare them.", "Paper A and Paper B", "Both papers...")
        assert result.had_reference

    def test_page_reference(self, resolver):
        result = resolver.resolve("What does page 5 say?", "", "", "report.pdf")
        assert result.had_reference
        assert 5 in result.page_refs

    def test_document_reference(self, resolver):
        result = resolver.resolve("What does the document say?", "", "", "resume.pdf")
        assert result.had_reference
        assert any("document" in ref for ref in result.references)

    def test_section_reference(self, resolver):
        result = resolver.resolve("Explain section 3.", "", "", "paper.pdf")
        assert result.had_reference
        assert "section" in result.references

    def test_comparative_reference(self, resolver):
        result = resolver.resolve("Compare it with Google.", "My resume", "Your resume...")
        assert result.had_reference
        assert result.comparative_target is not None

    def test_shorten_action(self, resolver):
        result = resolver.resolve("Make it shorter.", "Long paragraph", "Long answer...")
        assert result.action == "shorten"

    def test_continue_action(self, resolver):
        result = resolver.resolve("Continue.", "Topic", "Partial answer...")
        assert result.action == "continue"

    def test_explain_action(self, resolver):
        result = resolver.resolve("Explain this in simpler terms.", "Complex topic", "Complex answer...")
        assert result.action == "explain"

    def test_empty_query(self, resolver):
        result = resolver.resolve("", "", "")
        assert result.resolved == ""
        assert not result.had_reference

    def test_no_context_no_change(self, resolver):
        result = resolver.resolve("What about page 4?", "", "")
        assert result.had_reference
        assert "page 4" in result.resolved.lower() or 4 in result.page_refs

    def test_it_without_context_unchanged(self, resolver):
        result = resolver.resolve("Explain it.", "", "")
        assert result.had_reference
        assert "it" in result.original

    def test_resolve_with_topic(self, resolver):
        result = resolver.resolve("Tell me more about it.", "neural networks", "Neural networks are...", "deep learning")
        assert result.had_reference
        assert result.resolved != "Tell me more about it."

    def test_extract_keywords(self, resolver):
        keywords = resolver.extract_keywords("The transformer architecture uses attention mechanisms for sequence modeling.")
        assert "transformer" in keywords
        assert "attention" in keywords
        assert "the" not in keywords

    def test_extract_keywords_empty(self, resolver):
        keywords = resolver.extract_keywords("")
        assert keywords == []

    def test_extract_keywords_stop_words(self, resolver):
        keywords = resolver.extract_keywords("a an the is it for of")
        assert keywords == []

    def test_rewrite_reference(self, resolver):
        result = resolver.resolve("Rewrite that.", "Original text", "Rewritten text needed")
        assert result.action == "explain"
        assert result.had_reference

    def test_paraphrase_reference(self, resolver):
        result = resolver.resolve("Paraphrase this.", "Some content", "Some response")
        assert result.action == "explain"
        assert result.had_reference

    def test_resolve_speed(self, resolver):
        import time
        start = time.time()
        for _ in range(1000):
            resolver.resolve("Explain it further.", "What is machine learning?", "Machine learning is...")
        elapsed_ms = (time.time() - start) * 1000
        assert elapsed_ms < 1000, f"1000 resolutions took {elapsed_ms:.2f}ms (expected <1000ms)"
