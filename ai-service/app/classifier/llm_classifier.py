"""LLM-enhanced classifier.

Wraps the existing rule-based classifier and adds LLM-based classification
when an LLM provider is available. Falls back to rule-based when LLM is
unavailable or fails.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..llm.provider import LLMProvider, LLMResponse
from ..llm.factory import create_llm_provider
from .models import Category, CategoryResult, ClassificationResult
from .rules import classify as rule_classify

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a healthcare document classifier. Classify the document into one or more categories:
- SAFETY_REPORT: adverse events, incidents, patient harm, device recalls, near-misses
- QUALITY_COMPLAINT: product defects, service complaints, dissatisfaction, manufacturing issues
- INFO_REQUEST: questions, inquiries, information requests, guidance needed
- NOT_RELEVANT: spam, marketing, unrelated content

Return a JSON object with:
{
  "categories": [
    {"category": "CATEGORY_NAME", "confidence": 0.0-1.0, "reason": "brief explanation"}
  ],
  "primary_category": "MOST_LIKELY_CATEGORY",
  "primary_confidence": 0.0-1.0
}

Rules:
- A document can match multiple categories independently
- Sort categories by confidence descending
- Never invent information - use confidence below 0.5 when uncertain
- Always include at least one category"""


class LLMClassifier:
    """Classifier that uses LLM when available, with rule-based fallback."""

    def __init__(self, llm_provider: LLMProvider | None = None):
        self._llm = llm_provider
        self._llm_available = True  # Track if LLM has failed

    @property
    def llm(self) -> LLMProvider:
        if self._llm is None:
            self._llm = create_llm_provider()
        return self._llm

    def classify(self, text: str) -> ClassificationResult:
        """Classify text using LLM (preferred) or rules (fallback)."""
        # Try LLM classification
        if self._llm_available and self.llm.is_available():
            try:
                return self._classify_with_llm(text)
            except Exception as e:
                logger.warning("LLM classification failed, falling back to rules: %s", e)
                self._llm_available = False

        # Fallback to rule-based
        return rule_classify(text)

    def _classify_with_llm(self, text: str) -> ClassificationResult:
        """Use LLM for classification."""
        # Truncate long texts to fit in context
        truncated = text[:8000] if len(text) > 8000 else text

        response: LLMResponse = self.llm.generate(
            prompt=f"Classify this healthcare document:\n\n{truncated}",
            system_prompt=_SYSTEM_PROMPT,
            response_format="json",
        )

        if not response.success or not response.structured_data:
            logger.warning("LLM classification unsuccessful: %s", response.error)
            return rule_classify(text)

        data = response.structured_data
        categories_data = data.get("categories", [])

        if not categories_data:
            return rule_classify(text)

        # Convert to CategoryResult objects
        results = []
        for cat_data in categories_data:
            try:
                category = Category(cat_data["category"])
                confidence = float(cat_data.get("confidence", 0.5))
                reason = cat_data.get("reason", "LLM classification")
                results.append(CategoryResult(
                    category=category,
                    confidence=confidence,
                    reason=reason,
                ))
            except (ValueError, KeyError) as e:
                logger.warning("Invalid category from LLM: %s", e)
                continue

        if not results:
            return rule_classify(text)

        # Sort by confidence descending
        results.sort(key=lambda r: r.confidence, reverse=True)

        logger.info(
            "LLM classification: %d categories, primary=%s (%.2f)",
            len(results),
            results[0].category.value,
            results[0].confidence,
        )

        return ClassificationResult(categories=results)
