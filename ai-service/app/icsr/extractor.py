"""ICSr field extraction engine.

Extracts structured safety report fields from text using pattern matching.
Never invents patient information — returns "Not stated" when a field
cannot be reliably extracted.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from .models import (
    FieldValue,
    ICSRReport,
    Narrative,
    Patient,
    Product,
    Reaction,
    Reporter,
    Severity,
    SourceRef,
)

logger = logging.getLogger(__name__)

_NOT_STATED = FieldValue(
    value="Not stated",
    confidence=0.0,
    source_ref=SourceRef(document_type="unknown"),
)

_NOT_STATED_EMAIL = FieldValue(
    value="Not stated",
    confidence=0.0,
    source_ref=SourceRef(document_type="email"),
)

_NOT_STATED_PDF = FieldValue(
    value="Not stated",
    confidence=0.0,
    source_ref=SourceRef(document_type="pdf"),
)


def _src(doc_type: str, filename: str | None = None, page: int | None = None) -> SourceRef:
    return SourceRef(document_type=doc_type, filename=filename, page=page)


def _field(value: str, confidence: float, src: SourceRef) -> FieldValue:
    return FieldValue(value=value, confidence=confidence, source_ref=src)


def _not_stated(src: SourceRef) -> FieldValue:
    return FieldValue(value="Not stated", confidence=0.0, source_ref=src)


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

@dataclass
class _Pattern:
    regex: str
    group: int = 1
    confidence: float = 0.8


# Patient patterns
_PAT_PATTERNS = {
    "name": [
        _Pattern(r"(?:patient\s+name|patient)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
        _Pattern(r"(?:name)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.60),
    ],
    "age": [
        _Pattern(r"(?:age|patient\s+age)\s*[:=]\s*(\d{1,3})", 1, 0.90),
        _Pattern(r"(\d{1,3})\s*(?:year|yr)s?\s*(?:old|of\s+age)", 1, 0.85),
        _Pattern(r"\bage[:\s]+(\d{1,3})", 1, 0.85),
    ],
    "sex": [
        _Pattern(r"(?:sex|gender)\s*[:=]\s*(male|female|m|f|other)", 1, 0.90),
        _Pattern(r"\b(male|female)\b", 1, 0.70),
    ],
    "weight": [
        _Pattern(r"(?:weight|wt)\s*[:=]\s*([\d.]+)\s*(kg|lbs?|pounds?)?", 1, 0.80),
        _Pattern(r"([\d.]+)\s*(kg|lbs?)\b", 1, 0.70),
    ],
    "height": [
        _Pattern(r"height\s*[:=]\s*([\d.]+)\s*(cm|in|ft|inches)?(?:\s|$)", 1, 0.85),
        _Pattern(r"ht\s*[:=]\s*([\d.]+)\s*(cm|in|ft|inches)?(?:\s|$)", 1, 0.80),
    ],
    "medical_history": [
        _Pattern(r"(?:medical\s+history|history)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.75),
        _Pattern(r"(?:pmh|past\s+medical)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.75),
    ],
}

# Reporter patterns
_RPT_PATTERNS = {
    "name": [
        _Pattern(r"(?:reporter\s*name|reported\s+by|notify|notified\s+by)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
        _Pattern(r"(?:reporter)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.70),
        _Pattern(r"(?:from)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.50),
    ],
    "role": [
        _Pattern(r"(?:role|title|position)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
        _Pattern(r"\b(physician|doctor|nurse|pharmacist|patient|consumer|other\s+health\s+professional)\b", 1, 0.70),
    ],
    "organization": [
        _Pattern(r"(?:organization|org|institution|hospital|clinic)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    ],
    "contact": [
        _Pattern(r"(?:contact|email|phone)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
        _Pattern(r"([\w.-]+@[\w.-]+\.\w+)", 1, 0.90),
    ],
}

# Product patterns
_PRD_PATTERNS = {
    "name": [
        _Pattern(r"(?:product|drug|medication|medicine|device)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
        _Pattern(r"(?:suspected\s+product)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
        _Pattern(r"(?:brand|trade\s+name)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    ],
    "manufacturer": [
        _Pattern(r"(?:manufacturer|mfr|manufacturer\s+name)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    ],
    "lot_number": [
        _Pattern(r"(?:lot|batch|lot\s+number|batch\s+number)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.90),
    ],
    "expiry_date": [
        _Pattern(r"(?:expir|exp|expiry\s+date|expiration)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    ],
    "dosage": [
        _Pattern(r"(?:dosage|dose|dosing)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
        _Pattern(r"(\d+\s*(?:mg|ml|g|mcg|units?)(?:\s*/\s*(?:day|dose|week))?)", 1, 0.75),
    ],
    "route": [
        _Pattern(r"(?:route|route\s+of\s+admin)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
        _Pattern(r"\b(oral|intravenous|iv|im|subcutaneous|topical|inhalation|rectal|sublingual)\b", 1, 0.75),
    ],
    "indication": [
        _Pattern(r"(?:indication|indicated\s+for|reason\s+for\s+use)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    ],
}

# Reaction patterns
_RXN_PATTERNS = {
    "description": [
        _Pattern(r"(?:reaction|adverse\s+event|event|reaction\s+description)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.85),
        _Pattern(r"(?:what\s+happened|description\s+of\s+event)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.80),
    ],
    "onset_date": [
        _Pattern(r"(?:onset\s*date|date\s+of\s+onset|when\s+started|onset)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    ],
    "outcome": [
        _Pattern(r"(?:outcome|patient\s+outcome|result)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
        _Pattern(r"\b(recovered|recovering|not\s+recovered|fatal|death|resolved|ongoing|sequelae)\b", 1, 0.70),
    ],
    "seriousness": [
        _Pattern(r"(?:seriousness|serious|severity)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    ],
}

# Severity patterns
_SEV_PATTERNS = {
    "grade": [
        _Pattern(r"(?:grade|ctcae\s+grade|severity\s+grade)\s*[:=]\s*(\d)", 1, 0.85),
        _Pattern(r"(?:grade)\s*[:=]\s*(mild|moderate|severe|grade\s+\d)", 1, 0.80),
    ],
    "description": [
        _Pattern(r"(?:severity|severity\s+description)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    ],
    "hospitalization": [
        _Pattern(r"(?:hospitalization|hospitalized|required\s+hospitalization)\s*[:=]?\s*(yes|no|true|false)", 1, 0.85),
        _Pattern(r"\b(hospitalized|hospitalization\s+required)\b", 1, 0.80),
    ],
    "life_threatening": [
        _Pattern(r"(?:life[\s-]threatening|life\s+threat)\s*[:=]?\s*(yes|no|true|false)", 1, 0.85),
        _Pattern(r"\b(life[\s-]threatening)\b", 1, 0.80),
    ],
    "death": [
        _Pattern(r"(?:death|fatal|died|resulted\s+in\s+death)\s*[:=]?\s*(yes|no|true|false)?", 1, 0.85),
        _Pattern(r"\b(fatal|resulted\s+in\s+death|patient\s+died)\b", 1, 0.80),
    ],
    "disability": [
        _Pattern(r"(?:disability|disabled|permanent\s+damage)\s*[:=]?\s*(yes|no|true|false)", 1, 0.85),
    ],
    "congenital_anomaly": [
        _Pattern(r"(?:congenital|birth\s+defect|congenital\s+anomaly)\s*[:=]?\s*(yes|no|true|false)", 1, 0.85),
    ],
    "other_significant": [
        _Pattern(r"(?:other\s+significant|medically\s+significant)\s*[:=]?\s*(yes|no|true|false)", 1, 0.85),
    ],
}

# Narrative patterns
_NAR_PATTERNS = {
    "summary": [
        _Pattern(r"(?:summary|case\s+summary)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.85),
        _Pattern(r"(?:narrative)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.80),
    ],
    "causality_assessment": [
        _Pattern(r"(?:causality|assessment|relationship|relatedness)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
        _Pattern(r"\b(certain|probable|possible|unlikely|unrelated|conditional|unassessable)\b", 1, 0.75),
    ],
    "action_taken": [
        _Pattern(r"(?:action\s+taken|action)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    ],
    "additional_information": [
        _Pattern(r"(?:additional|other\s+info|comments|notes)\s*[:=]\s*(.+?)(?:\n\n|\Z)", 1, 0.75),
    ],
}

# Report-level patterns
_RPT_ID_PATTERNS = [
    _Pattern(r"(?:report\s*(?:id|number|no|#))\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.90),
    _Pattern(r"(?:case\s*(?:id|number|no|#))\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    _Pattern(r"\b(SR-[\w-]+)\b", 1, 0.80),
]

_RPT_DATE_PATTERNS = [
    _Pattern(r"(?:report\s*date|date\s+of\s+report|dated)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    _Pattern(r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", 1, 0.60),
]

_RPT_TYPE_PATTERNS = [
    _Pattern(r"(?:report\s*type|type)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
    _Pattern(r"\b(initial|follow[\s-]up|final|initial\s+report)\b", 1, 0.70),
]


# ---------------------------------------------------------------------------
# Extraction engine
# ---------------------------------------------------------------------------

def _extract_field(
    text: str,
    patterns: list[_Pattern],
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


def _extract_bool_field(
    text: str,
    patterns: list[_Pattern],
    src: SourceRef,
) -> FieldValue:
    """Extract a boolean-ish field, normalising to Yes/No."""
    for pat in patterns:
        m = re.search(pat.regex, text, re.IGNORECASE | re.DOTALL)
        if m:
            raw = m.group(pat.group).strip().lower()
            if raw in ("yes", "true", "1"):
                return _field("Yes", pat.confidence, src)
            elif raw in ("no", "false", "0"):
                return _field("No", pat.confidence, src)
            else:
                return _field(raw.title(), pat.confidence, src)
    return _not_stated(src)


def _detect_source(text: str, filename: str | None) -> tuple[str, int | None]:
    """Infer document type and page from context."""
    if filename:
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return "pdf", None
        if lower.endswith((".eml", ".msg")):
            return "email", None
    # Default heuristic
    return "text", None


class ICSRExtractor:
    """Extract ICSR fields from text.

    Usage::

        extractor = ICSRExtractor()
        report = extractor.extract(text, filename="report.pdf", page=1)
    """

    def extract(
        self,
        text: str,
        *,
        filename: str | None = None,
        page: int | None = None,
    ) -> ICSRReport:
        doc_type, _ = _detect_source(text, filename)
        src = _src(doc_type, filename, page)

        logger.info(
            "Extracting ICSR from %s (doc_type=%s, page=%s, length=%d)",
            filename or "unknown",
            doc_type,
            page,
            len(text),
        )

        return ICSRReport(
            report_id=_extract_field(text, _RPT_ID_PATTERNS, src),
            report_date=_extract_field(text, _RPT_DATE_PATTERNS, src),
            report_type=_extract_field(text, _RPT_TYPE_PATTERNS, src),
            patient=Patient(
                name=_extract_field(text, _PAT_PATTERNS["name"], src),
                age=_extract_field(text, _PAT_PATTERNS["age"], src),
                sex=_extract_field(text, _PAT_PATTERNS["sex"], src),
                weight=_extract_field(text, _PAT_PATTERNS["weight"], src),
                height=_extract_field(text, _PAT_PATTERNS["height"], src),
                medical_history=_extract_field(text, _PAT_PATTERNS["medical_history"], src),
            ),
            reporter=Reporter(
                name=_extract_field(text, _RPT_PATTERNS["name"], src),
                role=_extract_field(text, _RPT_PATTERNS["role"], src),
                organization=_extract_field(text, _RPT_PATTERNS["organization"], src),
                contact=_extract_field(text, _RPT_PATTERNS["contact"], src),
            ),
            product=Product(
                name=_extract_field(text, _PRD_PATTERNS["name"], src),
                manufacturer=_extract_field(text, _PRD_PATTERNS["manufacturer"], src),
                lot_number=_extract_field(text, _PRD_PATTERNS["lot_number"], src),
                expiry_date=_extract_field(text, _PRD_PATTERNS["expiry_date"], src),
                dosage=_extract_field(text, _PRD_PATTERNS["dosage"], src),
                route=_extract_field(text, _PRD_PATTERNS["route"], src),
                indication=_extract_field(text, _PRD_PATTERNS["indication"], src),
            ),
            reaction=Reaction(
                description=_extract_field(text, _RXN_PATTERNS["description"], src),
                onset_date=_extract_field(text, _RXN_PATTERNS["onset_date"], src),
                outcome=_extract_field(text, _RXN_PATTERNS["outcome"], src),
                seriousness=_extract_field(text, _RXN_PATTERNS["seriousness"], src),
            ),
            severity=Severity(
                grade=_extract_field(text, _SEV_PATTERNS["grade"], src),
                description=_extract_field(text, _SEV_PATTERNS["description"], src),
                hospitalization=_extract_bool_field(text, _SEV_PATTERNS["hospitalization"], src),
                life_threatening=_extract_bool_field(text, _SEV_PATTERNS["life_threatening"], src),
                death=_extract_bool_field(text, _SEV_PATTERNS["death"], src),
                disability=_extract_bool_field(text, _SEV_PATTERNS["disability"], src),
                congenital_anomaly=_extract_bool_field(text, _SEV_PATTERNS["congenital_anomaly"], src),
                other_significant=_extract_bool_field(text, _SEV_PATTERNS["other_significant"], src),
            ),
            narrative=Narrative(
                summary=_extract_field(text, _NAR_PATTERNS["summary"], src),
                causality_assessment=_extract_field(text, _NAR_PATTERNS["causality_assessment"], src),
                action_taken=_extract_field(text, _NAR_PATTERNS["action_taken"], src),
                additional_information=_extract_field(text, _NAR_PATTERNS["additional_information"], src),
            ),
        )
