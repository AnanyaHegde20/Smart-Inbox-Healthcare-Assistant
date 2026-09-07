"""Shared extraction models and helpers.

Re-exports SourceRef and FieldValue from the ICSR models so all
extractors use the same provenance types.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.icsr.models import FieldValue, SourceRef

NOT_STATED = "Not stated"

__all__ = ["FieldValue", "SourceRef", "NOT_STATED", "Pattern", "extract_field"]


@dataclass
class Pattern:
    """A single regex pattern with confidence score."""

    regex: str
    group: int = 1
    confidence: float = 0.8


def _src(doc_type: str, filename: str | None = None, page: int | None = None) -> SourceRef:
    return SourceRef(document_type=doc_type, filename=filename, page=page)


def _field(value: str, confidence: float, src: SourceRef) -> FieldValue:
    return FieldValue(value=value, confidence=confidence, source_ref=src)


def _not_stated(src: SourceRef) -> FieldValue:
    return FieldValue(value=NOT_STATED, confidence=0.0, source_ref=src)


def extract_field(
    text: str,
    patterns: list[Pattern],
    src: SourceRef,
) -> FieldValue:
    """Try each pattern in order; return first match or 'Not stated'."""
    for pat in patterns:
        m = re.search(pat.regex, text, re.IGNORECASE | re.DOTALL)
        if m:
            value = m.group(pat.group).strip()
            if value:
                return _field(value, pat.confidence, src)
    return _not_stated(src)


def detect_source(text: str, filename: str | None) -> tuple[str, int | None]:
    """Infer document type and page from context."""
    if filename:
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return "pdf", None
        if lower.endswith((".eml", ".msg")):
            return "email", None
    return "text", None
