"""Document summarization engine.

Generates a 10-15 sentence structured summary from extracted text.
The summarizer NEVER invents facts — it only reports what is present
or explicitly absent in the source text.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from .models import DocumentSummary, SummarySentence

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, stripping whitespace."""
    raw = re.split(r'(?<=[.!?])\s+', text.replace("\n", " ").strip())
    return [s.strip() for s in raw if s.strip() and len(s.strip()) > 5]


def _count_words(text: str) -> int:
    return len(text.split())


def _detect_topics(text: str) -> list[str]:
    """Identify main topics from keywords in the text."""
    topics: list[str] = []
    lower = text.lower()

    topic_signals = {
        "patient safety": ["patient", "safety", "fall", "incident"],
        "medication": ["medication", "drug", "dose", "prescription", "pharmacy"],
        "quality complaint": ["complaint", "dissatisfied", "poor service", "unprofessional"],
        "adverse event": ["adverse event", "side effect", "reaction", "allergic"],
        "information request": ["question", "inquiry", "request", "information"],
        "clinical documentation": ["diagnosis", "treatment", "clinical", "medical record"],
        "billing": ["bill", "charge", "payment", "invoice", "cost"],
        "infection control": ["infection", "contamination", "hygiene", "sterile"],
        "equipment": ["device", "equipment", "malfunction", "failure"],
        "personnel": ["staff", "nurse", "doctor", "physician", "employee"],
    }

    for topic, keywords in topic_signals.items():
        matches = sum(1 for kw in keywords if kw in lower)
        if matches >= 2:
            topics.append(topic)
        elif matches == 1 and topic in lower:
            topics.append(topic)

    return topics[:5]  # cap at 5 topics


def _detect_missing_info(text: str) -> list[str]:
    """Identify important information that is absent from the text."""
    missing: list[str] = []
    lower = text.lower()

    # Check for common missing elements
    if not re.search(r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b', text):
        missing.append("no specific dates mentioned")

    if not re.search(r'\b(patient|name|individual)\b', lower):
        missing.append("no patient or subject identified")

    if not re.search(r'\b(product|drug|device|medication)\b', lower):
        missing.append("no specific product or device identified")

    if not re.search(r'\b(report|incident|event)\b', lower):
        missing.append("no formal incident or report reference")

    if not re.search(r'\b(outcome|resolved|improved|worsened|died)\b', lower):
        missing.append("no outcome information provided")

    if not re.search(r'\b(recommend|suggest|action|follow[\s-]up)\b', lower):
        missing.append("no recommended actions or follow-up stated")

    if _count_words(text) < 50:
        missing.append("document is very brief with limited detail")

    return missing[:5]  # cap at 5


def _assess_relevance(text: str, classification_categories: list[str] | None = None) -> tuple[bool, float, str]:
    """Assess whether the document appears relevant to healthcare operations.

    Returns (is_relevant, confidence, reason).
    """
    lower = text.lower()
    relevant_score = 0
    irrelevant_score = 0
    reasons: list[str] = []

    # Positive relevance signals
    relevant_patterns = [
        (r'\b(patient|clinical|medical|healthcare)\b', 2, "contains healthcare terminology"),
        (r'\b(adverse|incident|safety|complaint)\b', 2, "mentions safety or quality concerns"),
        (r'\b(diagnosis|treatment|medication|prescription)\b', 1, "references clinical care"),
        (r'\b(report|document|record|form)\b', 1, "appears to be a formal document"),
    ]

    for pattern, weight, reason in relevant_patterns:
        if re.search(pattern, lower):
            relevant_score += weight
            if reason not in reasons:
                reasons.append(reason)

    # Negative relevance signals
    irrelevant_patterns = [
        (r'\b(spam|unsubscribe|click here|buy now)\b', 3, "appears to be spam or marketing"),
        (r'\b(congratulations|winner|lottery|free gift)\b', 3, "appears to be a scam"),
        (r'\b(out of office|auto[\s-]reply)\b', 2, "appears to be an automated response"),
        (r'\b(weather|recipe|sports|entertainment)\b', 2, "content is unrelated to healthcare"),
    ]

    for pattern, weight, reason in irrelevant_patterns:
        if re.search(pattern, lower):
            irrelevant_score += weight
            if reason not in reasons:
                reasons.append(reason)

    # Boost if classification categories are provided
    if classification_categories:
        healthcare_cats = {"SAFETY_REPORT", "QUALITY_COMPLAINT", "INFO_REQUEST"}
        if any(c in healthcare_cats for c in classification_categories):
            relevant_score += 3
            reasons.append("classified into a healthcare category")

    # Calculate final assessment
    total = relevant_score + irrelevant_score
    if total == 0:
        return False, 0.3, "insufficient signals to determine relevance"

    if relevant_score > irrelevant_score:
        confidence = min(relevant_score / max(total, 1), 0.95)
        return True, round(confidence, 2), "; ".join(reasons[:3])
    else:
        confidence = min(irrelevant_score / max(total, 1), 0.95)
        return False, round(confidence, 2), "; ".join(reasons[:3])


# ---------------------------------------------------------------------------
# Summarizer
# ---------------------------------------------------------------------------

class DocumentSummarizer:
    """Generate structured summaries from extracted document text.

    Produces 10-15 sentences organized into sections:
    overview, case_info, missing_info, relevance, reasoning.
    """

    def summarize(
        self,
        text: str,
        *,
        filename: str | None = None,
        classification_categories: list[str] | None = None,
        page_count: int | None = None,
    ) -> DocumentSummary:
        if not text or not text.strip():
            return self._empty_summary(filename)

        sentences = _split_sentences(text)
        word_count = _count_words(text)
        topics = _detect_topics(text)
        missing = _detect_missing_info(text)
        is_relevant, relevance_conf, relevance_reason = _assess_relevance(
            text, classification_categories
        )

        summary_sentences: list[SummarySentence] = []
        idx = 0

        # --- Overview (2-3 sentences) ---
        idx, summary_sentences = self._add_overview(
            summary_sentences, idx, text, sentences, filename, word_count, page_count
        )

        # --- Case Information (3-4 sentences) ---
        idx, summary_sentences = self._add_case_info(
            summary_sentences, idx, text, sentences, topics
        )

        # --- Missing Information (2-3 sentences) ---
        idx, summary_sentences = self._add_missing_info(
            summary_sentences, idx, missing
        )

        # --- Relevance Assessment (1-2 sentences) ---
        idx, summary_sentences = self._add_relevance(
            summary_sentences, idx, is_relevant, relevance_conf, relevance_reason
        )

        # --- Reasoning (1-2 sentences) ---
        idx, summary_sentences = self._add_reasoning(
            summary_sentences, idx, text, classification_categories, topics
        )

        # Determine document purpose
        purpose = self._determine_purpose(text, topics, classification_categories)

        total = len(summary_sentences)

        logger.info(
            "Generated %d-sentence summary for %s (relevant=%s, topics=%d)",
            total,
            filename or "unknown",
            is_relevant,
            len(topics),
        )

        return DocumentSummary(
            sentences=summary_sentences,
            total_sentences=total,
            is_relevant=is_relevant,
            relevance_confidence=relevance_conf,
            key_topics=topics,
            document_purpose=purpose,
        )

    def _empty_summary(self, filename: str | None) -> DocumentSummary:
        """Return a minimal summary for empty documents."""
        return DocumentSummary(
            sentences=[
                SummarySentence(
                    index=1,
                    text=f"The document '{filename or 'unknown'}' appears to be empty or contains no extractable text.",
                    section="overview",
                    source_ref=None,
                ),
            ],
            total_sentences=1,
            is_relevant=False,
            relevance_confidence=0.1,
            key_topics=[],
            document_purpose="Empty or unreadable document",
        )

    def _add_overview(
        self,
        existing: list[SummarySentence],
        start_idx: int,
        text: str,
        sentences: list[str],
        filename: str | None,
        word_count: int,
        page_count: int | None,
    ) -> tuple[int, list[SummarySentence]]:
        idx = start_idx

        # Sentence 1: Document type and size
        doc_desc = f"The document '{filename or 'unknown'}' contains approximately {word_count} words"
        if page_count:
            doc_desc += f" across {page_count} pages"
        doc_desc += "."
        idx += 1
        existing.append(SummarySentence(index=idx, text=doc_desc, section="overview"))

        # Sentence 2: First meaningful sentence from the document
        if sentences:
            first = sentences[0]
            if len(first) > 20:
                idx += 1
                existing.append(SummarySentence(
                    index=idx,
                    text=f"The document opens with the following content: \"{first[:200]}\"",
                    section="overview",
                ))

        # Sentence 3: General content description
        if sentences and len(sentences) > 2:
            mid = len(sentences) // 2
            mid_sentence = sentences[mid]
            if len(mid_sentence) > 15:
                idx += 1
                existing.append(SummarySentence(
                    index=idx,
                    text=f"Additional content includes: \"{mid_sentence[:200]}\"",
                    section="overview",
                ))

        return idx, existing

    def _add_case_info(
        self,
        existing: list[SummarySentence],
        start_idx: int,
        text: str,
        sentences: list[str],
        topics: list[str],
    ) -> tuple[int, list[SummarySentence]]:
        idx = start_idx
        lower = text.lower()

        # Identify case-related information
        if topics:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text=f"The document relates to the following topics: {', '.join(topics)}.",
                section="case_info",
            ))

        # Look for specific entities
        entities_found = []

        # Patient/subject references
        patient_match = re.search(r'(?:patient|subject|individual)\s*[:=]?\s*(\w[\w\s]*?)(?:\n|,|\.|$)', text, re.IGNORECASE)
        if patient_match:
            entities_found.append(f"patient/subject reference: '{patient_match.group(1).strip()}'")

        # Product references
        product_match = re.search(r'(?:product|drug|device|medication)\s*[:=]?\s*(\w[\w\s]*?)(?:\n|,|\.|$)', text, re.IGNORECASE)
        if product_match:
            entities_found.append(f"product/device reference: '{product_match.group(1).strip()}'")

        # Date references
        dates = re.findall(r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b', text)
        if dates:
            entities_found.append(f"dates mentioned: {', '.join(dates[:3])}")

        # Reporter/author
        reporter_match = re.search(r'(?:reporter|author|from|reported by)\s*[:=]?\s*(\w[\w\s]*?)(?:\n|,|\.|$)', text, re.IGNORECASE)
        if reporter_match:
            entities_found.append(f"reporter/author: '{reporter_match.group(1).strip()}'")

        if entities_found:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text=f"Key entities identified in the document include: {'; '.join(entities_found[:4])}.",
                section="case_info",
            ))

        # Extract key sentences that contain case information
        case_keywords = ["patient", "incident", "adverse", "complaint", "report", "event", "error", "fall", "reaction"]
        case_sentences = []
        for s in sentences:
            if any(kw in s.lower() for kw in case_keywords):
                case_sentences.append(s)
                if len(case_sentences) >= 2:
                    break

        for cs in case_sentences:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text=f"Relevant case detail: \"{cs[:200]}\"",
                section="case_info",
            ))

        return idx, existing

    def _add_missing_info(
        self,
        existing: list[SummarySentence],
        start_idx: int,
        missing: list[str],
    ) -> tuple[int, list[SummarySentence]]:
        idx = start_idx

        if missing:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text=f"The following important information is missing or not clearly stated: {'; '.join(missing[:3])}.",
                section="missing_info",
            ))

            if len(missing) > 3:
                idx += 1
                existing.append(SummarySentence(
                    index=idx,
                    text=f"Additional gaps include: {'; '.join(missing[3:5])}.",
                    section="missing_info",
                ))

            # Recommendation about completeness
            if len(missing) >= 4:
                idx += 1
                existing.append(SummarySentence(
                    index=idx,
                    text="Due to the number of missing fields, this document may be incomplete and could benefit from additional detail.",
                    section="missing_info",
                ))

        return idx, existing

    def _add_relevance(
        self,
        existing: list[SummarySentence],
        start_idx: int,
        is_relevant: bool,
        confidence: float,
        reason: str,
    ) -> tuple[int, list[SummarySentence]]:
        idx = start_idx

        if is_relevant:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text=f"This document appears to be relevant to healthcare operations with {confidence:.0%} confidence.",
                section="relevance",
            ))
        else:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text=f"This document does not appear to be directly relevant to healthcare safety, quality, or information requests (confidence: {confidence:.0%}).",
                section="relevance",
            ))

        return idx, existing

    def _add_reasoning(
        self,
        existing: list[SummarySentence],
        start_idx: int,
        text: str,
        classification_categories: list[str] | None,
        topics: list[str],
    ) -> tuple[int, list[SummarySentence]]:
        idx = start_idx

        if classification_categories:
            cats_str = ", ".join(classification_categories[:3])
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text=f"The document was classified into the following categories: {cats_str}, which supports its relevance to the review process.",
                section="reasoning",
            ))

        if topics:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text=f"The identified topics ({', '.join(topics[:3])}) are within the scope of healthcare document review.",
                section="reasoning",
            ))

        # Content density reasoning
        word_count = _count_words(text)
        if word_count < 50:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text="The document is very brief, which limits the ability to extract comprehensive information.",
                section="reasoning",
            ))
        elif word_count > 500:
            idx += 1
            existing.append(SummarySentence(
                index=idx,
                text="The document contains substantial detail, providing a good basis for review.",
                section="reasoning",
            ))

        return idx, existing

    def _determine_purpose(
        self,
        text: str,
        topics: list[str],
        classification_categories: list[str] | None,
    ) -> str:
        """Determine the one-line purpose of the document."""
        lower = text.lower()

        if classification_categories:
            if "SAFETY_REPORT" in classification_categories:
                return "Safety report or adverse event documentation"
            if "QUALITY_COMPLAINT" in classification_categories:
                return "Quality complaint or service issue report"
            if "INFO_REQUEST" in classification_categories:
                return "Information request or inquiry"

        if "adverse" in lower or "incident" in lower or "safety" in lower:
            return "Safety-related documentation"
        if "complaint" in lower or "dissatisfied" in lower:
            return "Quality complaint documentation"
        if "question" in lower or "inquiry" in lower:
            return "Information request or inquiry"
        if "report" in lower or "record" in lower:
            return "Healthcare report or record"
        if topics:
            return f"Document related to {topics[0]}"

        return "General healthcare document"
