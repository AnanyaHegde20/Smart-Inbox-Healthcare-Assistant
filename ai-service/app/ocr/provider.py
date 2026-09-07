"""OCR provider interface.

Every OCR backend must implement ``OCRProvider``.  The interface is
intentionally minimal so that swapping Tesseract for a cloud vision API
only requires writing a new concrete class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class OCRWord:
    """A single word with confidence."""

    text: str
    confidence: float  # 0.0 – 1.0


@dataclass
class OCRPageResult:
    """Result of OCR on a single page."""

    page_number: int
    full_text: str
    words: list[OCRWord] = field(default_factory=list)
    mean_confidence: float = 0.0
    low_confidence_count: int = 0  # words below threshold


@dataclass
class OCRResult:
    """Aggregated OCR result across all processed pages."""

    pages: list[OCRPageResult] = field(default_factory=list)
    total_pages: int = 0
    overall_mean_confidence: float = 0.0


class OCRProvider(ABC):
    """Abstract base class for OCR providers.

    Implement ``_run_ocr`` for each backend.  The public ``ocr`` method
    handles the common loop over pages.
    """

    @abstractmethod
    def _run_ocr(self, image_bytes: bytes, page_number: int) -> OCRPageResult:
        """Run OCR on a single page image and return the result."""
        ...

    def ocr(self, pages: list[tuple[int, bytes]]) -> OCRResult:
        """Run OCR over a list of (page_number, image_bytes) tuples.

        ``_run_ocr`` is called for each page and results are aggregated.
        """
        results: list[OCRPageResult] = []
        for page_number, image_bytes in pages:
            page_result = self._run_ocr(image_bytes, page_number)
            results.append(page_result)

        total = len(results)
        if total == 0:
            return OCRResult(pages=[], total_pages=0, overall_mean_confidence=0.0)

        overall_confidence = sum(r.mean_confidence for r in results) / total

        return OCRResult(
            pages=results,
            total_pages=total,
            overall_mean_confidence=round(overall_confidence, 4),
        )
