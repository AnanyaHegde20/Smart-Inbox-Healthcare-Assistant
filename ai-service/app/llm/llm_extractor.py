"""LLM-enhanced extraction engine.

Uses LLM for structured information extraction from healthcare documents.
Falls back to regex-based extraction when LLM is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..llm.provider import LLMProvider, LLMResponse
from ..llm.factory import create_llm_provider

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a healthcare document information extractor. Extract structured information from the document.

Return a JSON object with:
{
  "extracted_fields": {
    "field_name": {
      "value": "extracted value or 'Not stated'",
      "confidence": 0.0-1.0,
      "source_ref": "where in document this was found"
    }
  },
  "extraction_type": "ICSR|QUALITY_COMPLAINT|INFO_REQUEST|GENERAL",
  "missing_fields": ["list of important fields not found"]
}

Rules:
- NEVER invent patient information - use "Not stated" with confidence 0.0
- For dates, use the format found in the document
- For source_ref, indicate page or section if available
- Include ALL extracted fields, even with low confidence
- Mark fields as "Not stated" if not found in the document
- extraction_type should match the document's primary purpose"""


class LLMExtractor:
    """Information extractor using LLM with fallback to regex patterns."""

    def __init__(self, llm_provider: LLMProvider | None = None):
        self._llm = llm_provider
        self._llm_available = True

    @property
    def llm(self) -> LLMProvider:
        if self._llm is None:
            self._llm = create_llm_provider()
        return self._llm

    def extract(self, text: str, extraction_type: str | None = None) -> dict[str, Any]:
        """Extract information using LLM or fallback to basic extraction."""
        if self._llm_available and self.llm.is_available():
            try:
                return self._extract_with_llm(text, extraction_type)
            except Exception as e:
                logger.warning("LLM extraction failed, falling back: %s", e)
                self._llm_available = False

        return self._extract_basic(text, extraction_type)

    def _extract_with_llm(self, text: str, extraction_type: str | None) -> dict[str, Any]:
        """Use LLM for structured extraction."""
        truncated = text[:8000] if len(text) > 8000 else text

        prompt = f"Extract information from this healthcare document:"
        if extraction_type:
            prompt += f"\nDocument type: {extraction_type}"
        prompt += f"\n\n{truncated}"

        response: LLMResponse = self.llm.generate(
            prompt=prompt,
            system_prompt=_SYSTEM_PROMPT,
            response_format="json",
        )

        if not response.success or not response.structured_data:
            logger.warning("LLM extraction unsuccessful: %s", response.error)
            return self._extract_basic(text, extraction_type)

        return response.structured_data

    def _extract_basic(self, text: str, extraction_type: str | None) -> dict[str, Any]:
        """Basic regex-based extraction as fallback."""
        import re

        extracted = {}

        # Patient name
        patient_match = re.search(r"(?:patient|subject|individual)\s*[:=]?\s*([A-Z][a-z]+ [A-Z][a-z]+)", text, re.IGNORECASE)
        if patient_match:
            extracted["patient_name"] = {"value": patient_match.group(1), "confidence": 0.75, "source_ref": "document_text"}
        else:
            extracted["patient_name"] = {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"}

        # Date
        date_match = re.search(r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b", text)
        if date_match:
            extracted["date"] = {"value": date_match.group(), "confidence": 0.85, "source_ref": "document_text"}
        else:
            extracted["date"] = {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"}

        # Product/medication
        product_match = re.search(r"(?:medication|drug|product|device)\s*[:=]?\s*(\w[\w\s]+?)(?:\n|,|\.|$)", text, re.IGNORECASE)
        if product_match:
            extracted["product"] = {"value": product_match.group(1).strip(), "confidence": 0.70, "source_ref": "document_text"}
        else:
            extracted["product"] = {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"}

        # Lot number
        lot_match = re.search(r"(?:lot|batch|lot number)\s*[:= #]*([A-Z0-9\-]+)", text, re.IGNORECASE)
        if lot_match:
            extracted["lot_number"] = {"value": lot_match.group(1), "confidence": 0.80, "source_ref": "document_text"}
        else:
            extracted["lot_number"] = {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"}

        # Reporter
        reporter_match = re.search(r"(?:reporter|author|reported by|from)\s*[:=]?\s*([A-Z][a-z]+ [A-Z][a-z]+)", text, re.IGNORECASE)
        if reporter_match:
            extracted["reporter"] = {"value": reporter_match.group(1), "confidence": 0.72, "source_ref": "document_text"}
        else:
            extracted["reporter"] = {"value": "Not stated", "confidence": 0.0, "source_ref": "not_found"}

        return {
            "extracted_fields": extracted,
            "extraction_type": extraction_type or "GENERAL",
            "missing_fields": [k for k, v in extracted.items() if v["value"] == "Not stated"],
        }
