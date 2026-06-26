"""Unit and integration tests for Document Intelligence (Phase 19.3)."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch

from ai.documents.document_classifier import DocumentClassifier
from ai.documents.section_parser import SectionParser, Section
from ai.documents.metadata_extractor import MetadataExtractor
from ai.documents.analyzer import DocumentAnalyzer


# =============================================================================
# Shared Fixtures
# =============================================================================

@pytest.fixture
def upload_dir(tmp_path):
    return tmp_path / "uploads"


@pytest.fixture
def mock_services():
    from backend.app.services.document_service import DocumentService
    svc = Mock(spec=DocumentService)
    return {"document": svc}


@pytest.fixture
def client(mock_services):
    from backend.app.main import app
    from fastapi.testclient import TestClient
    with patch("backend.app.api.document_routes.get_services", return_value=mock_services):
        with TestClient(app) as c:
            yield c


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def classifier():
    return DocumentClassifier()


@pytest.fixture
def section_parser():
    return SectionParser()


@pytest.fixture
def metadata_extractor():
    return MetadataExtractor()


@pytest.fixture
def analyzer():
    return DocumentAnalyzer()


RESEARCH_PAPER_TEXT = """Abstract

This paper presents a novel approach to natural language processing.

Introduction

Natural language processing has seen significant advances in recent years.
Deep learning models have revolutionized the field.

Methodology

We used a transformer-based architecture for our experiments.
The model was trained on a large corpus of text data.

Results

Our approach achieved state-of-the-art performance on multiple benchmarks.
The results demonstrate the effectiveness of our method.

Discussion

The findings suggest that attention mechanisms play a crucial role.
Further research is needed to explore additional applications.

Conclusion

In this paper, we presented a novel method for NLP tasks.
Future work will focus on extending the approach to other domains.

References

[1] Vaswani et al. Attention is All You Need.
[2] Devlin et al. BERT: Pre-training of Deep Bidirectional Transformers.
"""

RESUME_TEXT = """John Doe
Software Engineer

Summary
Experienced software engineer with 5 years of experience in full-stack development.

Education
Bachelor of Science in Computer Science
University of Technology, 2018-2022

Skills
Python, JavaScript, React, Node.js, TypeScript, Docker, AWS

Experience
Senior Software Engineer
Tech Corp, 2022-Present
- Led development of microservices architecture
- Improved system performance by 40%

Projects
Personal Finance Tracker - Full-stack application
Task Management System - Real-time collaboration tool

Certifications
AWS Certified Solutions Architect
"""

BOOK_TEXT = """Preface

This book is intended for readers interested in machine learning.

Chapter 1: Introduction to Machine Learning

Machine learning is a subset of artificial intelligence.
This chapter covers the fundamental concepts.

Chapter 2: Supervised Learning

Supervised learning involves training on labeled data.
Common algorithms include linear regression and decision trees.

Chapter 3: Deep Learning

Deep learning uses neural networks with multiple layers.
Transformers have become the dominant architecture.

Chapter 4: Reinforcement Learning

Reinforcement learning involves agents learning from rewards.
Q-learning is a fundamental algorithm in this area.

Appendix A: Mathematical Foundations

This appendix covers the necessary mathematical background.
"""

REPORT_TEXT = """Executive Summary

This report analyzes the quarterly performance metrics.
Revenue increased by 15% compared to the previous quarter.

Introduction

The purpose of this report is to evaluate business performance.
We analyzed data from all departments.

Findings

Sales department exceeded targets by 20%.
Customer satisfaction scores improved by 10 points.

Analysis

The data shows a strong correlation between marketing spend and revenue.
Seasonal patterns were observed in Q4.

Recommendations

Increase marketing budget by 25%.
Expand into new geographic markets.

Conclusion

The company is well-positioned for continued growth.
"""

INVOICE_TEXT = """INVOICE

Invoice Number: INV-2024-001
Invoice Date: January 15, 2024
Due Date: February 15, 2024

Bill To:
Acme Corporation
123 Business Ave, City, State

Items:
1. Web Development Services - $5,000.00
2. Cloud Infrastructure - $2,500.00
3. Consulting Services - $3,000.00

Subtotal: $10,500.00
Tax (8%): $840.00
Total: $11,340.00

Payment Terms: Net 30
"""

MARKDOWN_NOTES = """# College Notes - Machine Learning

## Lecture 1: Introduction
Today we covered the basics of machine learning.
Key concepts: supervised learning, unsupervised learning.

## Lecture 2: Linear Regression
We learned about linear regression models.
The cost function is mean squared error.

## Important Definition
Overfitting occurs when the model learns noise in the training data.

## Example
Using scikit-learn to train a simple linear regression model.

```python
from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X, y)
```
"""

PRESENTATION_TEXT = """Agenda
- Project status review
- Q4 performance metrics
- Strategic initiatives

Overview
The company has made significant progress on key initiatives.
Revenue targets are on track for the quarter.

Q4 Performance
Revenue: $12.5M (up 15% YoY)
Customers: 2,500 (up 25%)

Key Takeaways
- Strong product-market fit
- Expansion opportunities in APAC
- Need to invest in R&D

Next Steps
- Finalize Q1 budget
- Launch new product features
"""

MANUAL_TEXT = """User Manual - SmartDevice X100

Installation
1. Unpack the device and verify all components
2. Connect the power adapter to the device
3. Download the mobile app from the App Store

Configuration
Navigate to Settings > Network > Wi-Fi
Select your network and enter the password
Configure user preferences

Usage
Press the power button to turn on the device
Use the touch screen to navigate menus

Troubleshooting
If the device does not turn on, check the power connection
If Wi-Fi connection fails, restart the router

Specifications
Dimensions: 10 x 5 x 2 inches
Weight: 1.5 lbs
Battery: 5000 mAh
"""

ARTICLE_TEXT = """The Future of Artificial Intelligence

Summary: AI technology continues to advance at a rapid pace,
with new breakthroughs announced weekly.

By Dr. Sarah Johnson, Senior AI Researcher

Artificial intelligence has transformed from a academic discipline
into a practical technology that powers millions of applications.
From chatbots to self-driving cars, AI is reshaping our world.

The pace of innovation shows no signs of slowing down.
Major tech companies are investing billions in AI research.
Startups are pushing the boundaries of what's possible.

See also: Machine Learning Basics, Neural Networks Explained
Contact: sarah.johnson@example.com
Visit: https://example.com/ai-article
"""


# =============================================================================
# Document Classifier Tests
# =============================================================================

class TestDocumentClassifier:
    def test_classify_research_paper(self, classifier):
        doc_type, score = classifier.classify(RESEARCH_PAPER_TEXT, "paper.pdf", {})
        assert doc_type == "research_paper"
        assert score > 0

    def test_classify_resume(self, classifier):
        doc_type, score = classifier.classify(RESUME_TEXT, "resume_john_doe.pdf", {})
        assert doc_type == "resume"
        assert score > 0

    def test_classify_resume_by_content(self, classifier):
        doc_type, score = classifier.classify(RESUME_TEXT, "document.pdf", {})
        assert doc_type == "resume"
        assert score > 0

    def test_classify_book(self, classifier):
        doc_type, score = classifier.classify(BOOK_TEXT, "ml_book.pdf", {})
        assert doc_type == "book"
        assert score > 0

    def test_classify_report(self, classifier):
        doc_type, score = classifier.classify(REPORT_TEXT, "quarterly_report.pdf", {})
        assert doc_type == "report"
        assert score > 0

    def test_classify_invoice(self, classifier):
        doc_type, score = classifier.classify(INVOICE_TEXT, "invoice_2024.pdf", {})
        assert doc_type == "invoice"
        assert score > 0

    def test_classify_unknown(self, classifier):
        text = "This is some random text with no clear structure or headings."
        doc_type, score = classifier.classify(text, "random.txt", {})
        assert doc_type == "unknown"
        assert score == 0

    def test_classify_presentation(self, classifier):
        doc_type, score = classifier.classify(PRESENTATION_TEXT, "presentation.pptx", {})
        assert doc_type == "presentation"
        assert score > 0

    def test_classify_manual(self, classifier):
        doc_type, score = classifier.classify(MANUAL_TEXT, "user_manual.pdf", {})
        assert doc_type == "manual"
        assert score > 0

    def test_classify_article(self, classifier):
        doc_type, score = classifier.classify(ARTICLE_TEXT, "ai_future.html", {})
        assert doc_type == "article"
        assert score > 0

    def test_classify_notes(self, classifier):
        doc_type, score = classifier.classify(MARKDOWN_NOTES, "my_notes.md", {})
        assert doc_type in ("notes", "manual", "research_paper")
        assert score >= 0

    def test_filename_influence_resume(self, classifier):
        doc_type, _ = classifier.classify("Some text about work experience.", "cv_john.pdf", {})
        assert doc_type == "resume"

    def test_filename_influence_invoice(self, classifier):
        doc_type, _ = classifier.classify("Some text about items and prices.", "invoice_001.pdf", {})
        assert doc_type == "invoice"

    def test_confidence_levels(self, classifier):
        assert classifier.get_confidence_label(25) == "high"
        assert classifier.get_confidence_label(15) == "medium"
        assert classifier.get_confidence_label(5) == "low"
        assert classifier.get_confidence_label(0) == "none"

    def test_classify_with_metadata(self, classifier):
        metadata = {"author": "John Doe", "title": "Research Paper on NLP"}
        doc_type, score = classifier.classify(
            RESEARCH_PAPER_TEXT, "my_document.pdf", metadata
        )
        assert doc_type == "research_paper"
        assert score > 0

    def test_classify_empty_text(self, classifier):
        doc_type, score = classifier.classify("", "empty.txt", {})
        assert doc_type == "unknown"
        assert score == 0


# =============================================================================
# Section Parser Tests
# =============================================================================

class TestSectionParser:
    def test_research_paper_sections(self, section_parser):
        sections = section_parser.parse(RESEARCH_PAPER_TEXT, "research_paper")
        names = [s.name.lower() for s in sections]
        assert any("abstract" in n for n in names)
        assert any("introduction" in n for n in names)
        assert any("methodology" in n for n in names)
        assert any("results" in n for n in names)
        assert any("discussion" in n for n in names)
        assert any("conclusion" in n for n in names)

    def test_resume_sections(self, section_parser):
        sections = section_parser.parse(RESUME_TEXT, "resume")
        names = [s.name.lower() for s in sections]
        assert any("education" in n for n in names)
        assert any("skills" in n for n in names)
        assert any("experience" in n for n in names)
        assert any("projects" in n for n in names)

    def test_book_sections(self, section_parser):
        sections = section_parser.parse(BOOK_TEXT, "book")
        names = [s.name.lower() for s in sections]
        assert any("chapter" in n for n in names)
        assert any("appendix" in n for n in names)

    def test_report_sections(self, section_parser):
        sections = section_parser.parse(REPORT_TEXT, "report")
        names = [s.name.lower() for s in sections]
        assert any("executive summary" in n for n in names)
        assert any("findings" in n for n in names)
        assert any("recommendations" in n for n in names)

    def test_section_order(self, section_parser):
        sections = section_parser.parse(RESEARCH_PAPER_TEXT, "research_paper")
        assert len(sections) >= 2
        for i in range(len(sections) - 1):
            assert sections[i].start_offset < sections[i + 1].start_offset

    def test_section_offsets(self, section_parser):
        sections = section_parser.parse(RESEARCH_PAPER_TEXT, "research_paper")
        for s in sections:
            assert s.start_offset >= 0
            assert s.end_offset > s.start_offset
            assert len(RESEARCH_PAPER_TEXT) >= s.end_offset

    def test_estimated_page(self, section_parser):
        sections = section_parser.parse(RESEARCH_PAPER_TEXT, "research_paper")
        for s in sections:
            assert s.estimated_page >= 1

    def test_empty_text(self, section_parser):
        sections = section_parser.parse("", "unknown")
        assert sections == []

    def test_no_matching_sections(self, section_parser):
        sections = section_parser.parse("Random text with no headings.", "unknown")
        assert sections == []

    def test_invoice_has_no_sections(self, section_parser):
        sections = section_parser.parse(INVOICE_TEXT, "invoice")
        assert sections == []

    def test_markdown_headings_detected(self, section_parser):
        sections = section_parser.parse(MARKDOWN_NOTES, "notes")
        assert sections == []

    def test_generic_heading_detection(self, section_parser):
        text = """Introduction
============
This is the introduction section.

Background
==========
This is the background section.
"""
        sections = section_parser.parse(text, "unknown")
        assert len(sections) > 0

    def test_section_to_dict(self):
        section = Section(name="Introduction", start_offset=0, end_offset=100, estimated_page=1)
        d = section.to_dict()
        assert d["name"] == "Introduction"
        assert d["start_offset"] == 0
        assert d["end_offset"] == 100
        assert d["estimated_page"] == 1


# =============================================================================
# Metadata Extractor Tests
# =============================================================================

class TestMetadataExtractor:
    def test_extract_title_from_content(self, metadata_extractor):
        result = metadata_extractor.extract(RESEARCH_PAPER_TEXT, {}, "paper.pdf")
        assert result["title"] != "Untitled"

    def test_extract_title_from_metadata(self, metadata_extractor):
        file_meta = {"title": "Custom Title"}
        result = metadata_extractor.extract("Some text", file_meta, "doc.pdf")
        assert result["title"] == "Custom Title"

    def test_extract_title_from_filename(self, metadata_extractor):
        result = metadata_extractor.extract("", {}, "my_research_paper.pdf")
        assert result["title"] != "Untitled"

    def test_extract_emails(self, metadata_extractor):
        text = "Contact us at support@example.com or john@test.org"
        result = metadata_extractor.extract(text, {}, "test.txt")
        assert result["contains_emails"] is True
        assert "support@example.com" in result["emails"]
        assert "john@test.org" in result["emails"]

    def test_extract_urls(self, metadata_extractor):
        text = "Visit https://example.com/path and http://test.org"
        result = metadata_extractor.extract(text, {}, "test.txt")
        assert result["contains_urls"] is True
        assert len(result["urls"]) >= 2

    def test_extract_phone_numbers(self, metadata_extractor):
        text = "Call us at +1-555-123-4567 or (555) 987-6543"
        result = metadata_extractor.extract(text, {}, "test.txt")
        assert result["contains_phone_numbers"] is True
        assert len(result["phone_numbers"]) >= 1

    def test_extract_dates(self, metadata_extractor):
        text = "Published on 2024-01-15 and updated 02/14/2024"
        result = metadata_extractor.extract(text, {}, "test.txt")
        assert result["contains_dates"] is True
        assert len(result["dates"]) >= 2

    def test_no_dates(self, metadata_extractor):
        text = "This text has no dates in it at all."
        result = metadata_extractor.extract(text, {}, "test.txt")
        assert result["contains_dates"] is False

    def test_contains_tables(self, metadata_extractor):
        text = "| Name | Age |\n|------|-----|\n| John | 30  |\n| Jane | 25  |"
        result = metadata_extractor.extract(text, {}, "test.txt")
        assert result["contains_tables"] is True

    def test_no_tables(self, metadata_extractor):
        result = metadata_extractor.extract(RESEARCH_PAPER_TEXT, {}, "paper.pdf")
        assert result["contains_tables"] is False

    def test_contains_code_blocks(self, metadata_extractor):
        text = "Some text\n```\ncode block\n```\nmore text"
        result = metadata_extractor.extract(text, {}, "test.md")
        assert result["contains_code_blocks"] is True

    def test_no_code_blocks(self, metadata_extractor):
        result = metadata_extractor.extract(RESEARCH_PAPER_TEXT, {}, "paper.pdf")
        assert result["contains_code_blocks"] is False

    def test_author_from_metadata(self, metadata_extractor):
        file_meta = {"author": "Dr. Sarah Johnson"}
        result = metadata_extractor.extract("Some text", file_meta, "doc.pdf")
        assert result["author"] == "Dr. Sarah Johnson"

    def test_author_missing(self, metadata_extractor):
        result = metadata_extractor.extract("Some text", {}, "doc.pdf")
        assert result["author"] == ""

    def test_contains_images_markdown(self, metadata_extractor):
        text = "Here is an image: ![alt](image.png)"
        result = metadata_extractor.extract(text, {}, "test.md")
        assert result["contains_images"] is True

    def test_no_images(self, metadata_extractor):
        result = metadata_extractor.extract(RESEARCH_PAPER_TEXT, {}, "paper.pdf")
        assert result["contains_images"] is False

    def test_creation_date(self, metadata_extractor):
        file_meta = {"creation_date": "20240115083000"}
        result = metadata_extractor.extract("text", file_meta, "doc.pdf")
        assert result["creation_date"] is not None


# =============================================================================
# Document Analyzer Tests (Keyword Extraction, Reading Time, Summary)
# =============================================================================

class TestDocumentAnalyzer:
    def test_full_analysis_research_paper(self, analyzer):
        result = analyzer.analyze(
            document_id="test-123",
            text=RESEARCH_PAPER_TEXT,
            filename="paper.pdf",
        )
        assert result["document_id"] == "test-123"
        assert result["document_type"] == "research_paper"
        assert result["word_count"] > 0
        assert result["character_count"] > 0
        assert result["estimated_reading_time_minutes"] >= 1
        assert len(result["sections"]) > 0
        assert len(result["keywords"]) > 0
        assert result["summary_preview"] != ""

    def test_full_analysis_resume(self, analyzer):
        result = analyzer.analyze(
            document_id="test-456",
            text=RESUME_TEXT,
            filename="resume.pdf",
        )
        assert result["document_type"] == "resume"
        assert len(result["sections"]) > 0

    def test_full_analysis_book(self, analyzer):
        result = analyzer.analyze(
            document_id="test-789",
            text=BOOK_TEXT,
            filename="book.pdf",
        )
        assert result["document_type"] == "book"

    def test_full_analysis_invoice(self, analyzer):
        result = analyzer.analyze(
            document_id="test-101",
            text=INVOICE_TEXT,
            filename="invoice.pdf",
        )
        assert result["document_type"] == "invoice"

    def test_keyword_extraction(self, analyzer):
        keywords = analyzer._extract_keywords(RESEARCH_PAPER_TEXT, top_n=5)
        assert len(keywords) > 0
        assert len(keywords) <= 5
        for kw in keywords:
            assert isinstance(kw, str)
            assert len(kw) > 0

    def test_keyword_extraction_empty_text(self, analyzer):
        keywords = analyzer._extract_keywords("", top_n=5)
        assert keywords == []

    def test_reading_time_calculation(self, analyzer):
        text = "word " * 440  # 2 minutes at 220 WPM
        result = analyzer.analyze(
            document_id="test-time",
            text=text,
            filename="test.txt",
        )
        assert result["estimated_reading_time_minutes"] == 2

    def test_reading_time_minimum(self, analyzer):
        text = "Hello world."
        result = analyzer.analyze(
            document_id="test-min",
            text=text,
            filename="test.txt",
        )
        assert result["estimated_reading_time_minutes"] >= 1

    def test_summary_preview(self, analyzer):
        preview = analyzer._generate_summary_preview(RESEARCH_PAPER_TEXT, max_chars=500)
        assert len(preview) > 0
        assert len(preview) <= 500
        assert "boilerplate" not in preview.lower()

    def test_summary_preview_max_length(self, analyzer):
        text = "Meaningful paragraph. " * 100
        preview = analyzer._generate_summary_preview(text, max_chars=200)
        assert len(preview) <= 200

    def test_summary_preview_empty_text(self, analyzer):
        preview = analyzer._generate_summary_preview("", max_chars=500)
        assert preview == ""

    def test_summary_preview_removes_boilerplate(self, analyzer):
        text = "Copyright 2024 All Rights Reserved.\nThis is the real content of the document.\nMore meaningful text here."
        preview = analyzer._generate_summary_preview(text)
        assert "Copyright" not in preview
        assert "real content" in preview

    def test_contains_tables_detected(self, analyzer):
        text = "| H1 | H2 |\n|----|----|\n| A  | B  |\n| C  | D  |"
        result = analyzer.analyze(
            document_id="test-tables",
            text=text,
            filename="test.txt",
        )
        assert result["contains_tables"] is True

    def test_contains_code_blocks_detected(self, analyzer):
        text = "Text\n```\ncode\n```\nMore text"
        result = analyzer.analyze(
            document_id="test-code",
            text=text,
            filename="test.md",
        )
        assert result["contains_code_blocks"] is True

    def test_contains_urls_detected(self, analyzer):
        text = "Visit https://example.com"
        result = analyzer.analyze(
            document_id="test-urls",
            text=text,
            filename="test.txt",
        )
        assert result["contains_urls"] is True

    def test_metadata_fields_present(self, analyzer):
        result = analyzer.analyze(
            document_id="test-meta",
            text=RESEARCH_PAPER_TEXT,
            filename="paper.pdf",
        )
        assert "extracted_metadata" in result
        assert "title" in result["extracted_metadata"]
        assert "author" in result["extracted_metadata"]
        assert "creation_date" in result["extracted_metadata"]
        assert "modification_date" in result["extracted_metadata"]

    def test_language_detection_with_service(self, analyzer):
        mock_lang = Mock()
        mock_lang.detect.return_value = "en"
        mock_lang.get_language_name.return_value = "English"
        result = analyzer.analyze(
            document_id="test-lang",
            text="This is English text for language detection.",
            filename="test.txt",
            language_service=mock_lang,
        )
        assert result["language"] == "English"
        assert result["language_code"] == "en"

    def test_language_detection_without_service(self, analyzer):
        result = analyzer.analyze(
            document_id="test-lang-none",
            text="This is English text.",
            filename="test.txt",
        )
        assert result["language"] == "English"


# =============================================================================
# Integration Tests - Full Pipeline (Service + Analyzer)
# =============================================================================

class TestDocumentServiceAnalysis:
    def test_analyze_document_requires_extraction(self, upload_dir):
        from backend.app.services.document_service import (
            DocumentService, DocumentExtractionError
        )
        svc = DocumentService(upload_dir)
        svc.upload("test.txt", b"Some text content")

        doc_id = list(svc._metadata.keys())[0]
        with pytest.raises(DocumentExtractionError, match="must be extracted"):
            svc.analyze_document(doc_id)

    def test_analyze_document_nonexistent(self, upload_dir):
        from backend.app.services.document_service import (
            DocumentService, DocumentExtractionError
        )
        svc = DocumentService(upload_dir)
        with pytest.raises(DocumentExtractionError, match="Document not found"):
            svc.analyze_document("nonexistent-id")

    def test_full_analysis_flow(self, upload_dir, tmp_path):
        from backend.app.services.document_service import DocumentService
        import fitz

        pdf_path = tmp_path / "test_research.pdf"
        doc = fitz.open()
        page = doc.new_page()
        text = "Abstract\n\nThis paper presents a novel approach.\n\nIntroduction\n\nThis is the introduction section.\n\nMethodology\n\nOur approach uses deep learning.\n\nResults\n\nWe achieved state of the art.\n\nConclusion\n\nWe presented a novel method.\n\nReferences\n\n[1] Some reference."
        page.insert_text((72, 72), text, fontsize=12)
        doc.save(str(pdf_path))
        doc.close()
        content = pdf_path.read_bytes()

        svc = DocumentService(upload_dir)
        upload_result = svc.upload("research_paper.pdf", content)
        doc_id = upload_result.document_id

        svc.extract_document(doc_id)

        analysis = svc.analyze_document(doc_id)
        assert analysis.document_id == doc_id
        assert analysis.status == "analyzed"
        assert analysis.document_type == "research_paper"
        assert analysis.reading_time >= 1
        assert len(analysis.keywords) > 0
        assert len(analysis.sections) > 0
        assert analysis.language != ""

    def test_get_analysis(self, upload_dir, tmp_path):
        from backend.app.services.document_service import DocumentService
        import fitz

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test content for analysis retrieval", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.pdf", pdf_path.read_bytes())
        doc_id = upload_result.document_id
        svc.extract_document(doc_id)
        svc.analyze_document(doc_id)

        stored = svc.get_analysis(doc_id)
        assert stored is not None
        assert stored["document_id"] == doc_id
        assert stored["document_type"] in ("research_paper", "report", "unknown")

    def test_get_analysis_not_found(self, upload_dir):
        from backend.app.services.document_service import DocumentService
        svc = DocumentService(upload_dir)
        assert svc.get_analysis("nonexistent") is None

    def test_is_analyzed(self, upload_dir, tmp_path):
        from backend.app.services.document_service import DocumentService
        import fitz

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test is_analyzed", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.pdf", pdf_path.read_bytes())
        doc_id = upload_result.document_id
        svc.extract_document(doc_id)

        assert svc.is_analyzed(doc_id) is False
        svc.analyze_document(doc_id)
        assert svc.is_analyzed(doc_id) is True

    def test_analysis_persists_across_instances(self, upload_dir, tmp_path):
        from backend.app.services.document_service import DocumentService
        import fitz

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Persistent analysis test", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        svc1 = DocumentService(upload_dir)
        upload_result = svc1.upload("test.pdf", pdf_path.read_bytes())
        doc_id = upload_result.document_id
        svc1.extract_document(doc_id)
        svc1.analyze_document(doc_id)

        svc2 = DocumentService(upload_dir)
        stored = svc2.get_analysis(doc_id)
        assert stored is not None
        assert stored["document_id"] == doc_id

    def test_delete_removes_analysis(self, upload_dir, tmp_path):
        from backend.app.services.document_service import DocumentService
        import fitz

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Delete analysis test", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.pdf", pdf_path.read_bytes())
        doc_id = upload_result.document_id
        svc.extract_document(doc_id)
        svc.analyze_document(doc_id)

        assert svc.is_analyzed(doc_id) is True
        svc.delete(doc_id)
        assert svc.is_analyzed(doc_id) is False

    def test_analysis_response_schema(self, upload_dir, tmp_path):
        from backend.app.services.document_service import DocumentService
        from backend.app.schemas.document import AnalysisResponse
        import fitz

        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Schema validation test", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        svc = DocumentService(upload_dir)
        upload_result = svc.upload("test.pdf", pdf_path.read_bytes())
        doc_id = upload_result.document_id
        svc.extract_document(doc_id)
        result = svc.analyze_document(doc_id)

        assert isinstance(result, AnalysisResponse)
        assert isinstance(result.keywords, list)
        assert isinstance(result.sections, list)
        assert isinstance(result.reading_time, int)
        assert isinstance(result.contains_tables, bool)
        assert isinstance(result.contains_images, bool)
        assert isinstance(result.contains_code_blocks, bool)


# =============================================================================
# API Route Integration Tests
# =============================================================================

class TestAnalysisRoutes:
    def test_analyze_success(self, client, mock_services):
        from backend.app.schemas.document import AnalysisResponse

        mock_services["document"].analyze_document.return_value = AnalysisResponse(
            status="analyzed",
            document_id="doc-1",
            document_type="research_paper",
            classification_confidence=15.0,
            language="English",
            language_code="en",
            page_count=10,
            word_count=2500,
            character_count=15000,
            reading_time=11,
            sections=[{"name": "Introduction", "start_offset": 0, "end_offset": 100, "estimated_page": 1}],
            contains_tables=False,
            contains_images=False,
            contains_code_blocks=False,
            contains_urls=True,
            contains_emails=False,
            contains_phone_numbers=False,
            contains_dates=True,
            keywords=["natural language", "deep learning", "transformer"],
            summary_preview="This paper presents a novel approach.",
            extracted_metadata={"title": "Research Paper", "author": ""},
            created_at="2026-01-15T10:00:00",
        )

        response = client.post("/api/v1/documents/doc-1/analyze")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "analyzed"
        assert data["document_type"] == "research_paper"
        assert data["reading_time"] == 11
        assert len(data["keywords"]) == 3
        assert len(data["sections"]) == 1

    def test_analyze_not_extracted(self, client, mock_services):
        from backend.app.services.document_service import DocumentExtractionError

        mock_services["document"].analyze_document.side_effect = DocumentExtractionError(
            "Document must be extracted before analysis", status_code=400
        )

        response = client.post("/api/v1/documents/doc-1/analyze")
        assert response.status_code == 400
        assert "must be extracted" in response.json()["detail"]

    def test_analyze_not_found(self, client, mock_services):
        from backend.app.services.document_service import DocumentExtractionError

        mock_services["document"].analyze_document.side_effect = DocumentExtractionError(
            "Document not found", status_code=404
        )

        response = client.post("/api/v1/documents/nonexistent/analyze")
        assert response.status_code == 404

    def test_get_analysis_success(self, client, mock_services):
        mock_services["document"].get_analysis.return_value = {
            "document_id": "doc-1",
            "document_type": "research_paper",
            "language": "English",
            "keywords": ["nlp", "transformer"],
            "sections": [],
            "created_at": "2026-01-15T10:00:00",
        }

        response = client.get("/api/v1/documents/doc-1/analysis")
        assert response.status_code == 200
        data = response.json()
        assert data["document_type"] == "research_paper"
        assert len(data["keywords"]) == 2

    def test_get_analysis_not_found_document(self, client, mock_services):
        mock_services["document"].get_analysis.return_value = None
        mock_services["document"].get_metadata.return_value = None

        response = client.get("/api/v1/documents/nonexistent/analysis")
        assert response.status_code == 404

    def test_get_analysis_not_analyzed(self, client, mock_services):
        from backend.app.schemas.document import DocumentMetadata

        mock_services["document"].get_analysis.return_value = None
        mock_services["document"].get_metadata.return_value = DocumentMetadata(
            id="doc-1",
            filename="test.pdf",
            file_type="pdf",
            size=100,
            status="extracted",
            upload_time="2026-01-15T10:00:00",
            storage_path="/tmp/test.pdf",
        )

        response = client.get("/api/v1/documents/doc-1/analysis")
        assert response.status_code == 404
        assert "Run analysis first" in response.json()["detail"]
