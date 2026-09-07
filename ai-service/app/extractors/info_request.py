"""INFO_REQUEST extraction models and engine."""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from app.icsr.models import FieldValue, SourceRef
from .base import Pattern, detect_source, extract_field, NOT_STATED, _not_stated, _src

logger = logging.getLogger(__name__)


class InfoRequestResult(BaseModel):
    """Extracted fields for an information request."""

    questions: FieldValue
    product_topic: FieldValue
    urgency: FieldValue
    requester_name: FieldValue
    requester_contact: FieldValue
    date_submitted: FieldValue
    preferred_response_format: FieldValue


# ---------------------------------------------------------------------------
# Pattern definitions — questions
# ---------------------------------------------------------------------------

_QUESTIONS_PATTERNS = [
    Pattern(r"(?:question|inquiry|request|what\s+i\s+need)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.85),
    Pattern(r"(?:please\s+(?:tell|explain|clarify|provide|advise))\s*[:=]?\s*(.+?)(?:\n\n|\Z)", 1, 0.80),
    Pattern(r"(.+\?)", 1, 0.65),  # Any sentence ending with ?
]

_PRODUCT_TOPIC_PATTERNS = [
    Pattern(r"(?:product|topic|subject|re|regarding|about)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    Pattern(r"(?:regarding|about|re:)\s+(.+?)(?:\n|\.|$)", 1, 0.75),
]

_URGENCY_PATTERNS = [
    Pattern(r"(?:urgency|priority|urgent|asap|immediately|time[\s-]sensitive)\s*[:=]?\s*(high|medium|low|urgent|critical)?", 1, 0.80),
    Pattern(r"\b(urgent|asap|immediately|time[\s-]sensitive|critical|emergency)\b", 1, 0.75),
    Pattern(r"\b(routine|normal|standard|no\s+rush)\b", 1, 0.65),
]

_REQUESTER_NAME_PATTERNS = [
    Pattern(r"(?:requester|from|name|sender|requested\s+by)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
]

_REQUESTER_CONTACT_PATTERNS = [
    Pattern(r"(?:contact|email|phone|reply\s+to)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    Pattern(r"([\w.-]+@[\w.-]+\.\w+)", 1, 0.90),
    Pattern(r"(\+?\d[\d\s\-()]{7,})", 1, 0.75),
]

_DATE_SUBMITTED_PATTERNS = [
    Pattern(r"(?:date|submitted|sent|received)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.75),
    Pattern(r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", 1, 0.60),
]

_RESPONSE_FORMAT_PATTERNS = [
    Pattern(r"(?:format|preferred\s+format|response\s+format|reply\s+format)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    Pattern(r"\b(email|phone|mail|fax|written|verbal)\b", 1, 0.65),
]


class InfoRequestExtractor:
    """Extract structured fields from an information request document."""

    def extract(
        self,
        text: str,
        *,
        filename: str | None = None,
        page: int | None = None,
    ) -> InfoRequestResult:
        doc_type, _ = detect_source(text, filename)
        src = _src(doc_type, filename, page)

        logger.info(
            "Extracting INFO_REQUEST from %s (length=%d)",
            filename or "unknown",
            len(text),
        )

        # Special handling for questions — collect all question sentences
        questions_field = self._extract_questions(text, src)

        return InfoRequestResult(
            questions=questions_field,
            product_topic=extract_field(text, _PRODUCT_TOPIC_PATTERNS, src),
            urgency=extract_field(text, _URGENCY_PATTERNS, src),
            requester_name=extract_field(text, _REQUESTER_NAME_PATTERNS, src),
            requester_contact=extract_field(text, _REQUESTER_CONTACT_PATTERNS, src),
            date_submitted=extract_field(text, _DATE_SUBMITTED_PATTERNS, src),
            preferred_response_format=extract_field(text, _RESPONSE_FORMAT_PATTERNS, src),
        )

    def _extract_questions(self, text: str, src: SourceRef) -> FieldValue:
        """Collect all sentences ending with '?' as questions."""
        # First try structured patterns
        for pat in _QUESTIONS_PATTERNS[:2]:
            m = re.search(pat.regex, text, re.IGNORECASE | re.DOTALL)
            if m:
                value = m.group(pat.group).strip()
                if value:
                    return FieldValue(value=value, confidence=pat.confidence, source_ref=src)

        # Fallback: collect all question sentences
        sentences = re.findall(r"(.+?\?)", text)
        if sentences:
            combined = " | ".join(s.strip() for s in sentences[:5])  # cap at 5 questions
            return FieldValue(value=combined, confidence=0.70, source_ref=src)

        return _not_stated(src)
