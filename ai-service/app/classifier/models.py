"""Classification data models.

Defines the four assignment categories and structured output format.
"""

from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class Category(str, Enum):
    """Allowed classification categories."""

    SAFETY_REPORT = "SAFETY_REPORT"
    QUALITY_COMPLAINT = "QUALITY_COMPLAINT"
    INFO_REQUEST = "INFO_REQUEST"
    NOT_RELEVANT = "NOT_RELEVANT"


class CategoryResult(BaseModel):
    """Result for a single category evaluation."""

    category: Category
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reason: str = Field(..., description="One-line reason for this classification")

    model_config = {"json_schema_extra": {"examples": [
        {
            "category": "SAFETY_REPORT",
            "confidence": 0.92,
            "reason": "Document mentions patient fall incident and adverse event",
        }
    ]}}


class ClassificationResult(BaseModel):
    """Full classification output — one or more categories."""

    categories: list[CategoryResult] = Field(
        ..., min_length=1, description="All matching categories, sorted by confidence desc"
    )

    @property
    def primary(self) -> CategoryResult:
        """Highest-confidence category."""
        return self.categories[0]

    def has_category(self, cat: Category) -> bool:
        return any(c.category == cat for c in self.categories)

    def get(self, cat: Category) -> CategoryResult | None:
        for c in self.categories:
            if c.category == cat:
                return c
        return None
