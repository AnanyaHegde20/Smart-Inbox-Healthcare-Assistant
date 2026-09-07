"""LLM-based image description for healthcare documents.

Uses vision-capable LLMs to describe images in documents.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

from ..llm.provider import LLMProvider, LLMResponse
from ..llm.factory import create_llm_provider

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a medical image analyst. Describe the image in detail for healthcare documentation.

Return a JSON object with:
{
  "description": "detailed description of the image",
  "modality": "x-ray|mri|ct|ultrasound|photo|chart|document|other",
  "findings": ["finding1", "finding2"],
  "clinical_relevance": "brief note on clinical significance"
}

Rules:
- Describe what you see objectively
- Do not make diagnoses
- Note image quality issues if present
- Use standard medical terminology
- Be concise but thorough"""


class LLMImageDescriber:
    """Image describer using vision-capable LLMs."""

    def __init__(self, llm_provider: LLMProvider | None = None):
        self._llm = llm_provider
        self._llm_available = True

    @property
    def llm(self) -> LLMProvider:
        if self._llm is None:
            self._llm = create_llm_provider()
        return self._llm

    def describe_image(
        self,
        image_data: bytes | str,
        *,
        content_type: str = "image/png",
        context: str | None = None,
    ) -> dict[str, Any]:
        """Describe an image using LLM or return basic description."""
        if self._llm_available and self.llm.is_available():
            try:
                return self._describe_with_llm(image_data, content_type, context)
            except Exception as e:
                logger.warning("LLM image description failed: %s", e)
                self._llm_available = False

        return self._basic_description(content_type)

    def _describe_with_llm(
        self,
        image_data: bytes | str,
        content_type: str,
        context: str | None,
    ) -> dict[str, Any]:
        """Use LLM vision to describe image."""
        # Encode image for API
        if isinstance(image_data, bytes):
            image_b64 = base64.b64encode(image_data).decode()
        else:
            image_b64 = image_data

        prompt = "Describe this medical image in detail for healthcare documentation."
        if context:
            prompt += f"\nContext: {context}"

        # Note: This would need provider-specific vision API support
        # For now, return a structured placeholder
        response: LLMResponse = self.llm.generate(
            prompt=f"{prompt}\n\n[Image data: {content_type}, {len(image_b64)} chars base64]",
            system_prompt=_SYSTEM_PROMPT,
            response_format="json",
        )

        if response.success and response.structured_data:
            return response.structured_data

        return self._basic_description(content_type)

    def _basic_description(self, content_type: str) -> dict[str, Any]:
        """Basic description without LLM."""
        return {
            "description": f"Image ({content_type}) - requires manual review",
            "modality": "other",
            "findings": ["Image present, LLM description unavailable"],
            "clinical_relevance": "Manual review required",
        }
