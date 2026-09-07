from pydantic import BaseModel, Field
from typing import Optional


class ExtractedFact(BaseModel):
    """A single fact extracted from the document."""

    key: str = Field(..., description="Fact label (e.g. 'patient_name')")
    value: str = Field(..., description="Fact value")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")


class SourceReference(BaseModel):
    """Reference to a source location within the document."""

    page: Optional[int] = Field(None, description="Page number")
    section: Optional[str] = Field(None, description="Section heading")
    offset: Optional[int] = Field(None, description="Character offset in text")


class TableData(BaseModel):
    """Extracted table data."""

    headers: list[str] = Field(default_factory=list)
    rows: list[list[str]] = Field(default_factory=list)
    page: Optional[int] = None


class ImageDescription(BaseModel):
    """Description of an image found in the document."""

    description: str
    page: Optional[int] = None
    image_index: Optional[int] = None


class Classification(BaseModel):
    """Legacy single-category classification result (backward compat)."""

    category: str = Field(..., description="Primary category")
    subcategory: Optional[str] = Field(None, description="Subcategory")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class CategoryOutput(BaseModel):
    """Single category result in structured JSON output."""

    category: str = Field(..., description="Category label (e.g. SAFETY_REPORT)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence 0-1")
    reason: str = Field(..., description="One-line reason")


class ClassificationOutput(BaseModel):
    """Multi-category classification output.

    Contains all matched categories sorted by confidence descending.
    A document can match zero, one, or more categories.
    """

    categories: list[CategoryOutput] = Field(
        ..., min_length=1, description="Matched categories, highest confidence first"
    )

    @property
    def primary_category(self) -> str:
        return self.categories[0].category

    @property
    def primary_confidence(self) -> float:
        return self.categories[0].confidence


class SummarySentenceOutput(BaseModel):
    """A single sentence in the structured summary."""

    index: int = Field(..., description="Sentence position in the summary (1-indexed)")
    text: str = Field(..., description="The sentence content")
    section: str = Field(
        ...,
        description="Which part of the summary: 'overview', 'case_info', 'missing_info', 'relevance', 'reasoning'",
    )
    source_ref: Optional[dict] = Field(
        None,
        description="Source location when the sentence references specific document content",
    )


class DocumentSummaryOutput(BaseModel):
    """Structured summary of a document for human review.

    Contains 10-15 sentences organized by section with source traceability.
    """

    sentences: list[SummarySentenceOutput] = Field(
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
    narrative: str = Field(
        ..., description="Full summary as a plain-text narrative"
    )


class ProcessDocumentResponse(BaseModel):
    """Response payload for document processing."""

    document_type: str = Field(..., description="Detected document type (e.g. 'pdf', 'email', 'report')")
    extracted_text: str = Field(..., description="Full extracted text content")
    language: str = Field(..., description="Detected language code (e.g. 'en')")
    translated_text: Optional[str] = Field(None, description="Translated text if source language differs from target")
    summary: str = Field(..., description="Legacy plain-text summary (backward compat)")
    classification: Classification
    classification_output: Optional[ClassificationOutput] = Field(
        None, description="Multi-category classification result"
    )
    extracted_facts: list[ExtractedFact] = Field(default_factory=list)
    source_references: list[SourceReference] = Field(default_factory=list)
    tables: list[TableData] = Field(default_factory=list)
    image_descriptions: list[ImageDescription] = Field(default_factory=list)
    processing_time_ms: float = Field(..., description="Total processing time in milliseconds")
    document_summary: Optional[DocumentSummaryOutput] = Field(
        None, description="Structured summary for human review (10-15 sentences)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document_type": "pdf",
                    "extracted_text": "Patient adverse event report...",
                    "language": "en",
                    "translated_text": None,
                    "summary": "Adverse event report for patient...",
                    "classification": {
                        "category": "SAFETY_REPORT",
                        "confidence": 0.92,
                        "reasons": ["Contains safety terminology"],
                    },
                    "classification_output": {
                        "categories": [
                            {"category": "SAFETY_REPORT", "confidence": 0.92, "reason": "Matched: adverse event, patient fall"},
                            {"category": "QUALITY_COMPLAINT", "confidence": 0.25, "reason": "Matched: complaint"},
                        ]
                    },
                    "extracted_facts": [],
                    "source_references": [{"page": 1}],
                    "tables": [],
                    "image_descriptions": [],
                    "processing_time_ms": 150.0,
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    service: str = "ai-service"
    version: str = "0.1.0"
