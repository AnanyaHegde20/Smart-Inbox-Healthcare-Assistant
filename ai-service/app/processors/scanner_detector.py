"""Detect whether a PDF is digitally born or scanned/image-based."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# If average characters per page is below this, treat as scanned
_CHAR_THRESHOLD = 50

# If the ratio of images to pages exceeds this, lean toward scanned
_IMAGE_RATIO_THRESHOLD = 0.8


@dataclass
class ScanDetectionResult:
    is_scanned: bool
    reason: str
    chars_per_page: float
    image_count: int
    page_count: int


def detect_scanned(pdf_path: str) -> ScanDetectionResult:
    """Open a PDF and decide if it is scanned/image-based."""
    doc = fitz.open(pdf_path)
    page_count = doc.page_count

    total_chars = 0
    total_images = 0

    for page in doc:
        text = page.get_text("text")
        total_chars += len(text.strip())
        total_images += len(page.get_images(full=True))

    doc.close()

    chars_per_page = total_chars / max(page_count, 1)
    image_ratio = total_images / max(page_count, 1)

    if chars_per_page < _CHAR_THRESHOLD and image_ratio >= _IMAGE_RATIO_THRESHOLD:
        reason = (
            f"Low text density ({chars_per_page:.0f} chars/page) "
            f"and high image ratio ({image_ratio:.1f})"
        )
        logger.info("PDF detected as scanned: %s", reason)
        return ScanDetectionResult(
            is_scanned=True,
            reason=reason,
            chars_per_page=chars_per_page,
            image_count=total_images,
            page_count=page_count,
        )

    reason = (
        f"Text density {chars_per_page:.0f} chars/page, "
        f"image ratio {image_ratio:.1f}"
    )
    logger.debug("PDF detected as digital: %s", reason)
    return ScanDetectionResult(
        is_scanned=False,
        reason=reason,
        chars_per_page=chars_per_page,
        image_count=total_images,
        page_count=page_count,
    )
