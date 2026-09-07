"""Structured document summary models.

Every summary is broken into sentences with provenance, so a human
reviewer can verify each claim against the source document.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SummarySentence(BaseModel):
    """A single sentence in the summary with source traceability."""

    index: int = Field(..., description="Sentence position in the summary (1-indexed)")
    text: str = Field(..., description="The sentence content")
    section: str = Field(
        ...,
        description="Which part of the summary this belongs to: "
        "'overview', 'case_info', 'missing_info', 'relevance', 'reasoning'",
    )
    source_ref: dict | None = Field(
        None,
        description="Source location when the sentence references specific document content",
    )


class DocumentSummary(BaseModel):
    """Structured summary of a document.

    Contains 10-15 sentences organized by section:
    - overview: what the document is about
    - case_info: identified case/relevant information
    - missing_info: important information that is absent
    - relevance: whether the document is relevant
    - reasoning: explanation of the relevance assessment
    """

    sentences: list[SummarySentence] = Field(
        ..., min_length=1, description="Summary sentences in order"
    )
    total_sentences: int = Field(..., description="Total sentence count")
    is_relevant: bool = Field(..., description="Whether the document appears relevant")
    relevance_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence in relevance assessment"
    )
    key_topics: list[str] = Field(
        default_factory=list, description="Main topics identified in the document"
    )
    document_purpose: str = Field(
        ..., description="One-line description of the document's purpose"
    )

    @property
    def overview_sentences(self) -> list[SummarySentence]:
        return [s for s in self.sentences if s.section == "overview"]

    @property
    def case_info_sentences(self) -> list[SummarySentence]:
        return [s for s in self.sentences if s.section == "case_info"]

    @property
    def missing_info_sentences(self) -> list[SummarySentence]:
        return [s for s in self.sentences if s.section == "missing_info"]

    @property
    def relevance_sentences(self) -> list[SummarySentence]:
        return [s for s in self.sentences if s.section == "relevance"]

    @property
    def reasoning_sentences(self) -> list[SummarySentence]:
        return [s for s in self.sentences if s.section == "reasoning"]

    def to_narrative(self) -> str:
        """Convert to a plain-text narrative summary."""
        return " ".join(s.text for s in self.sentences)
