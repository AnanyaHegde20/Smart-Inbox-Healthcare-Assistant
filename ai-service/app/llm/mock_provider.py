"""Mock LLM provider for testing.

Returns predictable responses without making API calls.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from .provider import LLMConfig, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class MockLLMProvider(LLMProvider):
    """Mock LLM provider that returns rule-based responses.

    Used for testing and development without API keys.
    """

    def __init__(self, config: LLMConfig | None = None):
        self.config = config or LLMConfig(provider="mock")
        self._call_count = 0

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        response_format: str | None = None,
    ) -> LLMResponse:
        self._call_count += 1
        lower = prompt.lower()
        sys_lower = (system_prompt or "").lower()

        # Classification: detect from system prompt or explicit keywords
        if ("classif" in sys_lower or "categoriz" in sys_lower or
                "classif" in lower or "categoriz" in lower or "category" in lower):
            return self._classify(prompt, response_format)

        # Extraction: detect from system prompt or explicit keywords
        if ("extractor" in sys_lower or "extract" in sys_lower or "field" in lower):
            return self._extract(prompt, response_format)

        # Summary: detect from system prompt or explicit keywords
        if "summariz" in sys_lower or "summar" in lower:
            return self._summarize(prompt, response_format)

        # Image description: detect from system prompt or explicit keywords
        if "image" in sys_lower or "image" in lower or "describe" in lower:
            return self._describe_image(prompt, response_format)

        # Content-based fallback: detect healthcare classification patterns
        safety_words = ["fell", "fall", "adverse", "incident", "recall", "injury", "harm", "anaphylaxis"]
        complaint_words = ["complaint", "defect", "malfunction", "error", "quality"]
        request_words = ["question", "request", "inquiry", "provide", "information"]
        spam_words = ["won", "free", "click", "unsubscribe", "marketing", "offer", "congratulations"]

        if any(w in lower for w in safety_words):
            return self._classify(prompt, response_format)
        if any(w in lower for w in complaint_words):
            return self._classify(prompt, response_format)
        if any(w in lower for w in request_words):
            return self._classify(prompt, response_format)
        if any(w in lower for w in spam_words):
            return self._classify(prompt, response_format)

        # Content-based fallback: detect extraction patterns
        if re.search(r"patient|medication|lot|reporter|date", lower):
            return self._extract(prompt, response_format)

        # Default response
        return LLMResponse(
            content="Mock response for: " + prompt[:100],
            model="mock-model",
            usage={"prompt_tokens": 50, "completion_tokens": 20},
        )

    def is_available(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "mock"

    @property
    def call_count(self) -> int:
        return self._call_count

    def _classify(self, prompt: str, response_format: str | None) -> LLMResponse:
        lower = prompt.lower()

        # Determine categories based on content
        categories = []
        if any(w in lower for w in ["fall", "adverse", "safety", "incident", "recall", "anaphylaxis"]):
            categories.append({"category": "SAFETY_REPORT", "confidence": 0.90, "reason": "Safety-related content detected"})
        if any(w in lower for w in ["complaint", "quality", "defect", "malfunction", "error"]):
            categories.append({"category": "QUALITY_COMPLAINT", "confidence": 0.85, "reason": "Quality issue detected"})
        if any(w in lower for w in ["question", "request", "inquiry", "information", "storage"]):
            categories.append({"category": "INFO_REQUEST", "confidence": 0.80, "reason": "Information request detected"})
        if any(w in lower for w in ["spam", "marketing", "unsubscribe", "promotion", "offer"]):
            categories.append({"category": "NOT_RELEVANT", "confidence": 0.92, "reason": "Marketing/spam content"})

        if not categories:
            categories.append({"category": "NOT_RELEVANT", "confidence": 0.50, "reason": "No clear healthcare category match"})

        # Sort by confidence descending
        categories.sort(key=lambda c: c["confidence"], reverse=True)

        result = {
            "categories": categories,
            "primary_category": categories[0]["category"],
            "primary_confidence": categories[0]["confidence"],
        }

        if response_format == "json":
            return LLMResponse(
                content=json.dumps(result),
                structured_data=result,
                model="mock-model",
                usage={"prompt_tokens": 100, "completion_tokens": 50},
            )

        return LLMResponse(
            content=str(result),
            structured_data=result,
            model="mock-model",
            usage={"prompt_tokens": 100, "completion_tokens": 50},
        )

    def _extract(self, prompt: str, response_format: str | None) -> LLMResponse:
        # Build defaults for all standard fields
        fields = {
            "patient_name": {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"},
            "date": {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"},
            "product": {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"},
            "lot_number": {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"},
            "reporter": {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"},
        }

        # Patient info - multiple patterns
        patient_match = re.search(r"patient[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)", prompt)
        if not patient_match:
            patient_match = re.search(r"(?:patient|subject|individual)\s+([A-Z][a-z]+ [A-Z][a-z]+)", prompt, re.IGNORECASE)
        if patient_match:
            fields["patient_name"] = {"value": patient_match.group(1), "confidence": 0.85, "source_ref": "document_text"}

        # Dates
        date_match = re.search(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", prompt)
        if date_match:
            fields["date"] = {"value": date_match.group(), "confidence": 0.90, "source_ref": "document_text"}

        # Product/medication - multiple patterns
        product_match = re.search(r"(?:medication|drug|product)[:\s]+(\w[\w\s]+?)(?:\n|,|\.|$)", prompt, re.IGNORECASE)
        if not product_match:
            product_match = re.search(r"medication:\s*(\w[\w\s]*?)(?:\.|$)", prompt, re.IGNORECASE)
        if product_match:
            fields["product"] = {"value": product_match.group(1).strip(), "confidence": 0.80, "source_ref": "document_text"}

        # Lot number - multiple patterns
        lot_match = re.search(r"(?:lot|batch)[:\s#]+([A-Z0-9\-]+)", prompt, re.IGNORECASE)
        if not lot_match:
            lot_match = re.search(r"lot:\s*([A-Z0-9\-]+)", prompt, re.IGNORECASE)
        if lot_match:
            fields["lot_number"] = {"value": lot_match.group(1), "confidence": 0.88, "source_ref": "document_text"}

        # Reporter (excluding generic 'from' to avoid false matches in prompts)
        reporter_match = re.search(r"(?:reporter|author|reported by)[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)", prompt, re.IGNORECASE)
        if reporter_match:
            fields["reporter"] = {"value": reporter_match.group(1), "confidence": 0.82, "source_ref": "document_text"}

        result = {"extracted_fields": fields, "extraction_type": "llm"}

        if response_format == "json":
            return LLMResponse(
                content=json.dumps(result),
                structured_data=result,
                model="mock-model",
                usage={"prompt_tokens": 150, "completion_tokens": 80},
            )

        return LLMResponse(
            content=str(result),
            structured_data=result,
            model="mock-model",
            usage={"prompt_tokens": 150, "completion_tokens": 80},
        )

    def _summarize(self, prompt: str, response_format: str | None) -> LLMResponse:
        # Generate a mock summary
        sentences = [
            "This document contains healthcare-related information.",
            "The content appears to be relevant to patient safety or quality management.",
            "Key entities and dates have been identified in the text.",
            "The document includes specific details that may require follow-up.",
            "No critical gaps in essential information were detected.",
            "The overall tone suggests a formal healthcare communication.",
            "Source references are available for verification of key claims.",
            "The document follows standard healthcare documentation practices.",
            "Additional context may be needed for complete assessment.",
            "The information presented is consistent with clinical reporting standards.",
        ]

        result = {
            "sentences": [{"index": i + 1, "text": s, "section": "overview"} for i, s in enumerate(sentences)],
            "total_sentences": len(sentences),
            "is_relevant": True,
            "relevance_confidence": 0.75,
            "key_topics": ["healthcare", "documentation"],
            "document_purpose": "Healthcare document requiring review",
            "narrative": " ".join(sentences),
        }

        if response_format == "json":
            return LLMResponse(
                content=json.dumps(result),
                structured_data=result,
                model="mock-model",
                usage={"prompt_tokens": 200, "completion_tokens": 150},
            )

        return LLMResponse(
            content=result["narrative"],
            structured_data=result,
            model="mock-model",
            usage={"prompt_tokens": 200, "completion_tokens": 150},
        )

    def _describe_image(self, prompt: str, response_format: str | None) -> LLMResponse:
        result = {
            "description": "Medical image showing relevant clinical information.",
            "modality": "clinical_image",
            "findings": ["Image content analyzed", "No critical findings identified"],
        }

        if response_format == "json":
            return LLMResponse(
                content=json.dumps(result),
                structured_data=result,
                model="mock-model",
                usage={"prompt_tokens": 100, "completion_tokens": 30},
            )

        return LLMResponse(
            content=result["description"],
            structured_data=result,
            model="mock-model",
            usage={"prompt_tokens": 100, "completion_tokens": 30},
        )
