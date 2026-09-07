"""OCR service: converts scanned PDF pages to images and runs OCR.

This module provides ``OCRService`` which combines page rendering
(PDF → image) with provider-based OCR (image → text).  It marks
low-confidence words so downstream consumers never have to guess
what the OCR engine was unsure about.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF

from app.ocr.provider import OCRPageResult, OCRProvider, OCRResult

logger = logging.getLogger(__name__)

# Words with confidence below this are wrapped in [uncertain] markers
_UNCERTAINTY_THRESHOLD = 0.6


@dataclass
class PageImage:
    """A rendered PDF page."""

    page_number: int
    image_bytes: bytes
    width: int
    height: int
    dpi: int = 300


@dataclass
class OCRPageOutput:
    """Per-page OCR output with marked uncertain text."""

    page_number: int
    raw_text: str
    marked_text: str  # text with [uncertain] wrappers
    mean_confidence: float
    low_confidence_words: list[str] = field(default_factory=list)


@dataclass
class OCRServiceResult:
    """Full OCR service output."""

    pages: list[OCRPageOutput] = field(default_factory=list)
    full_text: str = ""
    marked_text: str = ""  # full text with uncertainty markers
    overall_confidence: float = 0.0
    total_pages: int = 0
    needs_review: bool = False  # True if any page has low confidence


def _render_pages(pdf_path: str, dpi: int = 300) -> list[PageImage]:
    """Render every PDF page to a PNG image."""
    doc = fitz.open(pdf_path)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pages: list[PageImage] = []

    for page_idx in range(doc.page_count):
        page = doc.load_page(page_idx)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        pages.append(
            PageImage(
                page_number=page_idx + 1,
                image_bytes=pix.tobytes("png"),
                width=pix.width,
                height=pix.height,
                dpi=dpi,
            )
        )

    doc.close()
    return pages


def _mark_uncertain(full_text: str, words: list) -> str:
    """Wrap low-confidence words in [uncertain] markers.

    Never invents text — only marks what the OCR engine returned
    with low confidence.
    """
    if not words:
        return full_text

    marked = full_text
    for word in words:
        if hasattr(word, "confidence") and hasattr(word, "text"):
            if word.confidence < _UNCERTAINTY_THRESHOLD and word.text.strip():
                # Only mark the first occurrence to avoid double-marking
                marked = marked.replace(word.text, f"[uncertain]{word.text}[/uncertain]", 1)

    return marked


class OCRService:
    """Orchestrates page rendering + provider-based OCR.

    Usage::

        from app.ocr import TesseractProvider
        service = OCRService(provider=TesseractProvider())
        result = service.process("scanned.pdf")
    """

    def __init__(self, provider: OCRProvider, dpi: int = 300) -> None:
        self.provider = provider
        self.dpi = dpi

    def process(self, pdf_path: str) -> OCRServiceResult:
        """Render pages, run OCR, and return marked results."""
        page_images = _render_pages(pdf_path, dpi=self.dpi)

        if not page_images:
            return OCRServiceResult(total_pages=0)

        # Convert to (page_number, image_bytes) tuples for the provider
        page_tuples = [(p.page_number, p.image_bytes) for p in page_images]
        ocr_result: OCRResult = self.provider.ocr(page_tuples)

        # Build per-page outputs with uncertainty markers
        page_outputs: list[OCRPageOutput] = []
        all_raw: list[str] = []
        all_marked: list[str] = []
        needs_review = False

        for page_ocr in ocr_result.pages:
            marked = _mark_uncertain(page_ocr.full_text, page_ocr.words)
            low_words = [w.text for w in page_ocr.words if w.confidence < _UNCERTAINTY_THRESHOLD]

            if low_words:
                needs_review = True

            page_outputs.append(
                OCRPageOutput(
                    page_number=page_ocr.page_number,
                    raw_text=page_ocr.full_text,
                    marked_text=marked,
                    mean_confidence=page_ocr.mean_confidence,
                    low_confidence_words=low_words,
                )
            )
            all_raw.append(page_ocr.full_text)
            all_marked.append(marked)

        full_text = "\n\n".join(all_raw)
        marked_text = "\n\n".join(all_marked)

        result = OCRServiceResult(
            pages=page_outputs,
            full_text=full_text,
            marked_text=marked_text,
            overall_confidence=ocr_result.overall_mean_confidence,
            total_pages=ocr_result.total_pages,
            needs_review=needs_review,
        )

        logger.info(
            "OCR complete: %d pages, confidence %.2f, needs_review=%s",
            result.total_pages,
            result.overall_confidence,
            result.needs_review,
        )
        return result
