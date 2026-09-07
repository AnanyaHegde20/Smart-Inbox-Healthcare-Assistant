"""LLM-enhanced document summarizer.

Uses LLM for high-quality summaries with fallback to rule-based summarization.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ..llm.provider import LLMProvider, LLMResponse
from ..llm.factory import create_llm_provider
from ..summarizer.models import DocumentSummary, SummarySentence

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a healthcare document summarizer. Generate a structured summary of 10-15 sentences.

Return a JSON object with:
{
  "sentences": [
    {"index": 1, "text": "sentence text", "section": "section_name"}
  ],
  "total_sentences": 10-15,
  "is_relevant": true/false,
  "relevance_confidence": 0.0-1.0,
  "key_topics": ["topic1", "topic2"],
  "document_purpose": "one-line purpose",
  "narrative": "full summary as plain text"
}

Section names: overview, case_info, missing_info, relevance, reasoning

Rules:
- Generate exactly 10-15 sentences
- NEVER invent patient information
- Describe what the document contains
- Identify relevant case information
- Mention missing important information
- State whether it appears relevant and explain why
- Use "Not stated" for missing information
- Include source references where appropriate"""


class LLMSummarizer:
    """Summarizer using LLM with rule-based fallback."""

    def __init__(self, llm_provider: LLMProvider | None = None):
        self._llm = llm_provider
        self._llm_available = True

    @property
    def llm(self) -> LLMProvider:
        if self._llm is None:
            self._llm = create_llm_provider()
        return self._llm

    def summarize(
        self,
        text: str,
        *,
        filename: str | None = None,
        classification_categories: list[str] | None = None,
        page_count: int | None = None,
    ) -> DocumentSummary:
        """Generate summary using LLM or fallback to rule-based."""
        if self._llm_available and self.llm.is_available():
            try:
                return self._summarize_with_llm(text, filename, classification_categories, page_count)
            except Exception as e:
                logger.warning("LLM summarization failed, falling back: %s", e)
                self._llm_available = False

        # Fallback to rule-based summarizer
        from ..summarizer.engine import DocumentSummarizer
        fallback = DocumentSummarizer()
        return fallback.summarize(text, filename=filename, classification_categories=classification_categories, page_count=page_count)

    def _summarize_with_llm(
        self,
        text: str,
        filename: str | None,
        classification_categories: list[str] | None,
        page_count: int | None,
    ) -> DocumentSummary:
        """Use LLM for summarization."""
        truncated = text[:10000] if len(text) > 10000 else text

        prompt = f"Summarize this healthcare document:"
        if filename:
            prompt += f"\nFilename: {filename}"
        if classification_categories:
            prompt += f"\nClassification: {', '.join(classification_categories)}"
        if page_count:
            prompt += f"\nPages: {page_count}"
        prompt += f"\n\n{truncated}"

        response: LLMResponse = self.llm.generate(
            prompt=prompt,
            system_prompt=_SYSTEM_PROMPT,
            response_format="json",
        )

        if not response.success or not response.structured_data:
            logger.warning("LLM summarization unsuccessful: %s", response.error)
            from ..summarizer.engine import DocumentSummarizer
            fallback = DocumentSummarizer()
            return fallback.summarize(text, filename=filename, classification_categories=classification_categories, page_count=page_count)

        return self._parse_response(response.structured_data)

    def _parse_response(self, data: dict[str, Any]) -> DocumentSummary:
        """Parse LLM response into DocumentSummary."""
        sentences = []
        for s in data.get("sentences", []):
            sentences.append(SummarySentence(
                index=s.get("index", len(sentences) + 1),
                text=s.get("text", ""),
                section=s.get("section", "overview"),
                source_ref=s.get("source_ref"),
            ))

        return DocumentSummary(
            sentences=sentences,
            total_sentences=data.get("total_sentences", len(sentences)),
            is_relevant=data.get("is_relevant", True),
            relevance_confidence=data.get("relevance_confidence", 0.5),
            key_topics=data.get("key_topics", []),
            document_purpose=data.get("document_purpose", "Healthcare document"),
        )
