"""ICSr (Individual Case Safety Report) data models.

Every field follows the pattern:
    value        – extracted text or "Not stated"
    confidence   – 0.0 to 1.0
    source_ref   – where the value came from (document type + page)

The extractor must NEVER invent patient information.  When a field
cannot be found, value is set to "Not stated" with confidence 0.0.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    """Identifies where a field value was extracted from."""

    document_type: str = Field(
        ...,
        description="Source document type: 'email', 'pdf', 'text', etc.",
    )
    filename: str | None = Field(
        None,
        description="Original filename when available",
    )
    page: int | None = Field(
        None,
        description="Page number (PDF only, 1-indexed). None for emails/text.",
    )
    offset: int | None = Field(
        None,
        description="Character offset in extracted text when applicable",
    )


class FieldValue(BaseModel):
    """A single extracted value with provenance."""

    value: str = Field(
        ...,
        description="Extracted value or 'Not stated' if not found",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score 0-1. 0.0 when value is 'Not stated'",
    )
    source_ref: SourceRef = Field(
        ...,
        description="Source location for this value",
    )


class Patient(BaseModel):
    """Patient demographics extracted from the safety report."""

    name: FieldValue
    age: FieldValue
    sex: FieldValue
    weight: FieldValue
    height: FieldValue
    medical_history: FieldValue


class Reporter(BaseModel):
    """Person reporting the adverse event."""

    name: FieldValue
    role: FieldValue
    organization: FieldValue
    contact: FieldValue


class Product(BaseModel):
    """Suspected product / drug / device involved."""

    name: FieldValue
    manufacturer: FieldValue
    lot_number: FieldValue
    expiry_date: FieldValue
    dosage: FieldValue
    route: FieldValue
    indication: FieldValue


class Reaction(BaseModel):
    """Adverse reaction / event description."""

    description: FieldValue
    onset_date: FieldValue
    outcome: FieldValue
    seriousness: FieldValue


class Severity(BaseModel):
    """Severity assessment of the event."""

    grade: FieldValue
    description: FieldValue
    hospitalization: FieldValue
    life_threatening: FieldValue
    death: FieldValue
    disability: FieldValue
    congenital_anomaly: FieldValue
    other_significant: FieldValue


class Narrative(BaseModel):
    """Free-text narrative section of the safety report."""

    summary: FieldValue
    causality_assessment: FieldValue
    action_taken: FieldValue
    additional_information: FieldValue


class ICSRReport(BaseModel):
    """Complete ICSR extraction result.

    Structured JSON output with every field containing value,
    confidence, and source_reference.  Missing fields default to
    "Not stated" with confidence 0.0.
    """

    patient: Patient
    reporter: Reporter
    product: Product
    reaction: Reaction
    severity: Severity
    narrative: Narrative
    report_id: FieldValue
    report_date: FieldValue
    report_type: FieldValue

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "report_id": {"value": "SR-2025-001", "confidence": 0.95, "source_ref": {"document_type": "email", "filename": "report.eml"}},
                    "patient": {
                        "name": {"value": "Not stated", "confidence": 0.0, "source_ref": {"document_type": "email"}},
                        "age": {"value": "45", "confidence": 0.9, "source_ref": {"document_type": "pdf", "page": 1}},
                        "sex": {"value": "Male", "confidence": 0.85, "source_ref": {"document_type": "pdf", "page": 1}},
                    },
                }
            ]
        }
    }
