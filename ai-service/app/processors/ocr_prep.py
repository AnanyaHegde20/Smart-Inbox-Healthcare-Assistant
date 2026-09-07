"""Prepare scanned PDFs for OCR processing.

This module is a placeholder that converts each page to an image and
exposes the data in a format ready for any OCR backend (Tesseract,
cloud vision API, etc.).  The actual OCR call is intentionally left
abstract so providers can be swapped without touching this layer.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class PageImage:
    page_number: int
    image_bytes: bytes
    width: int
    height: int
    dpi: int = 300


@dataclass
class OCRPrepResult:
    pages: list[PageImage] = field(default_factory=list)
    total_pages: int = 0


def prepare_for_ocr(pdf_path: str, dpi: int = 300) -> OCRPrepResult:
    """Render each page to a PNG image for downstream OCR.

    The returned ``image_bytes`` can be fed to any OCR provider:
    - ``pytesseract.image_to_string()``
    - Google Cloud Vision API
    - AWS Textract
    - Azure Computer Vision

    This function does NOT run OCR itself.
    """
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
        logger.debug(
            "Rendered page %d at %dx%d (%d dpi)",
            page_idx + 1,
            pix.width,
            pix.height,
            dpi,
        )

    doc.close()
    logger.info("Rendered %d pages for OCR from %s", len(pages), pdf_path)
    return OCRPrepResult(pages=pages, total_pages=len(pages))
