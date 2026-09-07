"""NOT_RELEVANT extraction models and engine."""

from __future__ import annotations

import logging
import re

from pydantic import BaseModel, Field

from app.icsr.models import FieldValue, SourceRef
from .base import Pattern, detect_source, extract_field, NOT_STATED, _not_stated, _src

logger = logging.getLogger(__name__)


class NotRelevantResult(BaseModel):
    """Extracted fields for a not-relevant document."""

    reason: FieldValue
    detected_category: FieldValue
    sender: FieldValue
    subject: FieldValue
    date_received: FieldValue
    is_spam: FieldValue
    language: FieldValue


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

_REASON_PATTERNS = [
    Pattern(r"(?:reason|because|rational|explanation)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
]

_DETECTED_CATEGORY_PATTERNS = [
    Pattern(r"(?:type|category|classification)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    Pattern(r"\b(spam|marketing|newsletter|promotion|advertisement|phishing|scam|personal|unrelated|off[\s-]topic|auto[\s-]reply|out\s+of\s+office)\b", 1, 0.70),
]

_SENDER_PATTERNS = [
    Pattern(r"(?:from|sender|author)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
    Pattern(r"([\w.-]+@[\w.-]+\.\w+)", 1, 0.75),
]

_SUBJECT_PATTERNS = [
    Pattern(r"(?:subject|re|regarding|topic)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.85),
]

_DATE_RECEIVED_PATTERNS = [
    Pattern(r"(?:date|received|sent)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.75),
    Pattern(r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})", 1, 0.60),
]

_SPAM_PATTERNS = [
    Pattern(r"\b(unsubscribe|opt[\s-]out|click\s+here|buy\s+now|limited\s+time\s+offer|act\s+now|congratulations|you\s+have\s+been\s+selected|viagra|cialis|discount|free\s+gift|winner|lottery)\b", 1, 0.80),
]

_LANGUAGE_PATTERNS = [
    Pattern(r"(?:language|lang)\s*[:=]\s*(.+?)(?:\n|$)", 1, 0.80),
]


class NotRelevantExtractor:
    """Extract structured fields from a not-relevant document."""

    def extract(
        self,
        text: str,
        *,
        filename: str | None = None,
        page: int | None = None,
    ) -> NotRelevantResult:
        doc_type, _ = detect_source(text, filename)
        src = _src(doc_type, filename, page)

        logger.info(
            "Extracting NOT_RELEVANT from %s (length=%d)",
            filename or "unknown",
            len(text),
        )

        # Special handling for spam detection
        is_spam = self._detect_spam(text, src)

        # Special handling for reason — use detected category if available
        reason = self._extract_reason(text, src)

        return NotRelevantResult(
            reason=reason,
            detected_category=extract_field(text, _DETECTED_CATEGORY_PATTERNS, src),
            sender=extract_field(text, _SENDER_PATTERNS, src),
            subject=extract_field(text, _SUBJECT_PATTERNS, src),
            date_received=extract_field(text, _DATE_RECEIVED_PATTERNS, src),
            is_spam=is_spam,
            language=extract_field(text, _LANGUAGE_PATTERNS, src),
        )

    def _detect_spam(self, text: str, src: SourceRef) -> FieldValue:
        """Detect if the document is spam based on common indicators."""
        lower = text.lower()

        spam_score = 0
        spam_signals = []

        for pat in _SPAM_PATTERNS:
            matches = re.findall(pat.regex, lower)
            if matches:
                spam_score += len(matches)
                spam_signals.extend(matches[:2])

        if spam_score >= 3:
            return FieldValue(
                value="Yes",
                confidence=0.90,
                source_ref=src,
            )
        elif spam_score >= 1:
            return FieldValue(
                value="Likely",
                confidence=0.65,
                source_ref=src,
            )
        else:
            return _not_stated(src)

    def _extract_reason(self, text: str, src: SourceRef) -> FieldValue:
        """Extract or infer the reason why this is not relevant."""
        lower = text.lower()

        # Try explicit reason pattern first
        for pat in _REASON_PATTERNS:
            m = re.search(pat.regex, text, re.IGNORECASE | re.DOTALL)
            if m:
                value = m.group(pat.group).strip()
                if value:
                    return FieldValue(value=value, confidence=pat.confidence, source_ref=src)

        # Infer reason from detected signals
        reasons = []

        if re.search(r"\b(unsubscribe|opt[\s-]out|newsletter|digest)\b", lower):
            reasons.append("Marketing/newsletter content")
        if re.search(r"\b(viagra|cialis|pharmacy|discount\s+medication)\b", lower):
            reasons.append("Pharmaceutical spam")
        if re.search(r"\b(congratulations|winner|lottery|prize|free\s+gift)\b", lower):
            reasons.append("Scam/chain letter")
        if re.search(r"\b(dear\s+(friend|valued|customer|user))\b", lower):
            reasons.append("Mass-distributed greeting")
        if re.search(r"\b(click\s+here|buy\s+now|limited\s+time|act\s+now)\b", lower):
            reasons.append("Promotional content")
        if re.search(r"\b(out\s+of\s+office|auto[\s-]reply|automatic\s+response)\b", lower):
            reasons.append("Automated response")
        if re.search(r"\b(weather|sports|recipe|entertainment|movie)\b", lower):
            reasons.append("Unrelated personal content")

        if reasons:
            combined = "; ".join(reasons[:3])
            return FieldValue(value=combined, confidence=0.75, source_ref=src)

        # Generic fallback
        return FieldValue(
            value="Content does not match any healthcare safety, quality, or inquiry category",
            confidence=0.50,
            source_ref=src,
        )
