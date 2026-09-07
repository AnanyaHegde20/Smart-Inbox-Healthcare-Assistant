"""Tests for LLM integration.

All tests use the MockLLMProvider to avoid real API calls.
"""

from __future__ import annotations

import json

import pytest

from app.llm import (
    LLMConfig,
    LLMExtractor,
    LLMImageDescriber,
    LLMResponse,
    LLMSummarizer,
    MockLLMProvider,
    create_llm_provider,
)
from app.llm.llm_extractor import LLMExtractor
from app.classifier import LLMClassifier


class TestMockLLMProvider:
    """Tests for the mock LLM provider."""

    def test_is_always_available(self):
        provider = MockLLMProvider()
        assert provider.is_available() is True

    def test_provider_name(self):
        provider = MockLLMProvider()
        assert provider.get_provider_name() == "mock"

    def test_classify_safety_content(self):
        provider = MockLLMProvider()
        response = provider.generate(
            "Patient fell in hospital room. Adverse event report.",
            response_format="json",
        )
        assert response.success is True
        assert response.structured_data is not None
        assert "categories" in response.structured_data
        cats = response.structured_data["categories"]
        assert any(c["category"] == "SAFETY_REPORT" for c in cats)

    def test_classify_complaint_content(self):
        provider = MockLLMProvider()
        response = provider.generate(
            "Quality complaint about defective product batch.",
            response_format="json",
        )
        assert response.success is True
        cats = response.structured_data["categories"]
        assert any(c["category"] == "QUALITY_COMPLAINT" for c in cats)

    def test_classify_request_content(self):
        provider = MockLLMProvider()
        response = provider.generate(
            "Please provide information about storage requirements.",
            response_format="json",
        )
        assert response.success is True
        cats = response.structured_data["categories"]
        assert any(c["category"] == "INFO_REQUEST" for c in cats)

    def test_classify_spam_content(self):
        provider = MockLLMProvider()
        response = provider.generate(
            "You won a free vacation! Click here to claim.",
            response_format="json",
        )
        assert response.success is True
        cats = response.structured_data["categories"]
        assert any(c["category"] == "NOT_RELEVANT" for c in cats)

    def test_extract_fields(self):
        provider = MockLLMProvider()
        response = provider.generate(
            "Patient John Smith. Medication: Aspirin. Lot: ABC-123.",
            response_format="json",
        )
        assert response.success is True
        assert "extracted_fields" in response.structured_data
        fields = response.structured_data["extracted_fields"]
        assert "patient_name" in fields
        assert fields["patient_name"]["value"] == "John Smith"

    def test_summarize(self):
        provider = MockLLMProvider()
        response = provider.generate(
            "Summarize this healthcare document about patient safety.",
            response_format="json",
        )
        assert response.success is True
        assert "sentences" in response.structured_data
        assert response.structured_data["total_sentences"] >= 10

    def test_describe_image(self):
        provider = MockLLMProvider()
        response = provider.generate(
            "Describe this medical image.",
            response_format="json",
        )
        assert response.success is True
        assert "description" in response.structured_data

    def test_call_count_increments(self):
        provider = MockLLMProvider()
        assert provider.call_count == 0
        provider.generate("test")
        assert provider.call_count == 1
        provider.generate("test2")
        assert provider.call_count == 2


class TestLLMFactory:
    """Tests for the provider factory."""

    def test_mock_provider_creation(self):
        provider = create_llm_provider()
        assert isinstance(provider, MockLLMProvider)


class TestLLMClassifier:
    """Tests for the LLM-enhanced classifier."""

    def test_classify_safety_text(self):
        classifier = LLMClassifier(llm_provider=MockLLMProvider())
        result = classifier.classify("Patient fall incident report. Adverse event documented.")
        assert len(result.categories) > 0
        assert result.primary.category.value == "SAFETY_REPORT"

    def test_classify_complaint_text(self):
        classifier = LLMClassifier(llm_provider=MockLLMProvider())
        result = classifier.classify("Quality complaint about defective tablet coating.")
        assert len(result.categories) > 0
        assert result.primary.category.value == "QUALITY_COMPLAINT"

    def test_classify_request_text(self):
        classifier = LLMClassifier(llm_provider=MockLLMProvider())
        result = classifier.classify("Please provide information about storage guidelines.")
        assert len(result.categories) > 0
        assert result.primary.category.value == "INFO_REQUEST"

    def test_classify_spam_text(self):
        classifier = LLMClassifier(llm_provider=MockLLMProvider())
        result = classifier.classify("You won a free vacation! Click here now!")
        assert len(result.categories) > 0
        assert result.primary.category.value == "NOT_RELEVANT"


class TestLLMExtractor:
    """Tests for the LLM-enhanced extractor."""

    def test_extract_patient_info(self):
        extractor = LLMExtractor(llm_provider=MockLLMProvider())
        result = extractor.extract("Patient Jane Doe. DOB: 01/15/1980.")
        assert "extracted_fields" in result
        fields = result["extracted_fields"]
        assert "patient_name" in fields
        assert fields["patient_name"]["value"] == "Jane Doe"

    def test_extract_medication_info(self):
        extractor = LLMExtractor(llm_provider=MockLLMProvider())
        result = extractor.extract("Medication: Aspirin 100mg. Lot: ASP-2025-001.")
        assert "extracted_fields" in result
        fields = result["extracted_fields"]
        assert "product" in fields
        assert "lot_number" in fields

    def test_extract_missing_info(self):
        extractor = LLMExtractor(llm_provider=MockLLMProvider())
        result = extractor.extract("Short document with minimal content.")
        assert "extracted_fields" in result
        # Should have "Not stated" for missing fields
        fields = result["extracted_fields"]
        assert any(v["value"] == "Not stated" for v in fields.values())


class TestLLMSummarizer:
    """Tests for the LLM-enhanced summarizer."""

    def test_summarize_generates_sentences(self):
        summarizer = LLMSummarizer(llm_provider=MockLLMProvider())
        result = summarizer.summarize("Patient safety incident report with detailed information about a fall event.")
        assert result.total_sentences >= 10
        assert len(result.sentences) >= 10

    def test_summarize_has_sections(self):
        summarizer = LLMSummarizer(llm_provider=MockLLMProvider())
        result = summarizer.summarize("Healthcare document content for summarization.")
        sections = {s.section for s in result.sentences}
        assert "overview" in sections

    def test_summarize_with_filename(self):
        summarizer = LLMSummarizer(llm_provider=MockLLMProvider())
        result = summarizer.summarize("Document content.", filename="report.pdf")
        assert result.document_purpose != ""


class TestLLMImageDescriber:
    """Tests for the LLM image describer."""

    def test_describe_image_returns_structure(self):
        describer = LLMImageDescriber(llm_provider=MockLLMProvider())
        result = describer.describe_image(b"fake image data", content_type="image/png")
        assert "description" in result
        assert "modality" in result
        assert "findings" in result


class TestLLMResponse:
    """Tests for the LLMResponse dataclass."""

    def test_successful_response(self):
        resp = LLMResponse(content="test", success=True, model="test-model")
        assert resp.success is True
        assert resp.error is None

    def test_error_response(self):
        resp = LLMResponse(content="", success=False, error="API error")
        assert resp.success is False
        assert resp.error == "API error"

    def test_structured_data(self):
        data = {"key": "value"}
        resp = LLMResponse(content="test", structured_data=data)
        assert resp.structured_data == data


class TestLLMConfig:
    """Tests for the LLMConfig dataclass."""

    def test_default_config(self):
        config = LLMConfig()
        assert config.provider == "mock"
        assert config.temperature == 0.3
        assert config.max_tokens == 4096

    def test_custom_config(self):
        config = LLMConfig(provider="openai", model="gpt-4", api_key="test-key")
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key == "test-key"
