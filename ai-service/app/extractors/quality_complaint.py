"""QUALITY_COMPLAINT extraction models and engine."""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from app.icsr.models import FieldValue, SourceRef
from .base import Pattern, detect_source, extract_field, NOT_STATED, _not_stated, _src

logger = logging.getLogger(__name__)


class QualityComplaintResult(BaseModel):
    """Extracted fields for a quality complaint."""

    product: FieldValue
    batch_lot_number: FieldValue
    complaint_description: FieldValue
    photo_mentioned: FieldValue
    complaint_category: FieldValue
    complainant_name: FieldValue
    complainant_contact: FieldValue
    date_received: FieldValue
    expected_resolution: FieldValue


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

_PRODUCT_PATTERNS = [
    Pattern(r"(?:product|item|device|drug|medication)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    Pattern(r"(?:complaint\s+about|issue\s+with|problem\s+with)\s+(.+?)(?:\n|\.|$)", 1, 0.75),
    Pattern(r"(?:product|item)\s+name\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
]

_LOT_PATTERNS = [
    Pattern(r"(?:lot|batch|lot\s+number|batch\s+number|lot\s*#|batch\s*#)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.90),
    Pattern(r"(?:lot|batch)\s*[:=]\s*(\S+)", 1, 0.85),
]

_DESCRIPTION_PATTERNS = [
    Pattern(r"(?:complaint|description|issue|problem|details)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.85),
    Pattern(r"(?:what\s+happened|what\s+is\s+the\s+issue)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.80),
    Pattern(r"(?:customer|patient|user)\s+(?:reported|stated|said)\s*[:=]?\s*(.+?)(?:\n\n|\Z)", 1, 0.75),
]

_PHOTO_PATTERNS = [
    Pattern(r"(?:photo|image|picture|attachment|attached|enclosed|see\s+attached)\s+(?:included|attached|enclosed|provided|available)", 1, 0.85),
    Pattern(r"(?:photo|image|picture)\s*[:=]?\s*(yes|no|included|attached|none)", 1, 0.80),
    Pattern(r"\b(photo|image|picture|screenshot)\b", 1, 0.60),
]

_CATEGORY_PATTERNS = [
    Pattern(r"(?:complaint\s+type|category|classification)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    Pattern(r"\b(product\s+quality|packaging|labeling|delivery|service|performance|safety)\b", 1, 0.70),
]

_COMPLAINANT_NAME_PATTERNS = [
    Pattern(r"(?:complainant|reported\s+by|from|name)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    Pattern(r"(?:patient|customer|user)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.70),
]

_COMPLAINANT_CONTACT_PATTERNS = [
    Pattern(r"(?:contact|email|phone|mobile)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    Pattern(r"([\w.-]+@[\w.-]+\.\w+)", 1, 0.90),
    Pattern(r"(\+?\d[\d\s\-()]{7,})", 1, 0.75),
]

_DATE_RECEIVED_PATTERNS = [
    Pattern(r"(?:date\s+received|received\s+on|complaint\s+date|date\s+of\s+complaint)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    Pattern(r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", 1, 0.60),
]

_RESOLUTION_PATTERNS = [
    Pattern(r"(?:expected\s+resolution|resolution|action\s+requested|what\s+do\s+you\s+want)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    Pattern(r"(?:refund|replacement|repair|investigation|apology)\b", 1, 0.65),
]


class QualityComplaintExtractor:
    """Extract structured fields from a quality complaint document."""

    def extract(
        self,
        text: str,
        *,
        filename: str | None = None,
        page: int | None = None,
    ) -> QualityComplaintResult:
        doc_type, _ = detect_source(text, filename)
        src = _src(doc_type, filename, page)

        logger.info(
            "Extracting QUALITY_COMPLAINT from %s (length=%d)",
            filename or "unknown",
            len(text),
        )

        # Photo detection needs special handling — check for "no photo" negation
        photo_field = self._extract_photo(text, src)

        return QualityComplaintResult(
            product=extract_field(text, _PRODUCT_PATTERNS, src),
            batch_lot_number=extract_field(text, _LOT_PATTERNS, src),
            complaint_description=extract_field(text, _DESCRIPTION_PATTERNS, src),
            photo_mentioned=photo_field,
            complaint_category=extract_field(text, _CATEGORY_PATTERNS, src),
            complainant_name=extract_field(text, _COMPLAINANT_NAME_PATTERNS, src),
            complainant_contact=extract_field(text, _COMPLAINANT_CONTACT_PATTERNS, src),
            date_received=extract_field(text, _DATE_RECEIVED_PATTERNS, src),
            expected_resolution=extract_field(text, _RESOLUTION_PATTERNS, src),
        )

    def _extract_photo(self, text: str, src: SourceRef) -> FieldValue:
        """Detect whether a photo/image was mentioned, with negation check."""
        lower = text.lower()

        # Check for explicit "no photo" / "no image" / "none"
        if re.search(r"\b(no\s+photo|no\s+image|no\s+picture|photo[:\s]+none|image[:\s]+none)\b", lower):
            return FieldValue(value="No", confidence=0.85, source_ref=src)

        # Check for positive photo mentions
        for pat in _PHOTO_PATTERNS:
            m = re.search(pat.regex, text, re.IGNORECASE | re.DOTALL)
            if m:
                raw = m.group(pat.group).strip()
                if raw.lower() in ("yes", "included", "attached", "provided", "available"):
                    return FieldValue(value="Yes", confidence=pat.confidence, source_ref=src)
                elif raw.lower() in ("no", "none"):
                    return FieldValue(value="No", confidence=pat.confidence, source_ref=src)
                else:
                    # Generic mention — likely a photo exists
                    return FieldValue(value="Yes", confidence=0.60, source_ref=src)

        return _not_stated(src)
