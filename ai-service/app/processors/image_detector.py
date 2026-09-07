"""Detect meaningful images in a PDF and prepare placeholder descriptions.

Large images (above a configurable pixel-size threshold) are considered
"meaningful" -- charts, photos, diagrams -- and returned with metadata.
Small images (icons, bullets, decorative lines) are filtered out.

The actual description generation is left as an async hook so it can be
wired to an LLM or vision API later.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# Images smaller than this (in total pixels) are considered decorative
_MIN_PIXELS = 10_000  # e.g. 100x100


@dataclass
class DetectedImage:
    page_number: int
    image_index: int
    width: int
    height: int
    pixel_count: int
    ext: str
    description: str  # placeholder until LLM is wired in


def detect_images(pdf_path: str) -> list[DetectedImage]:
    """Scan every page for images above the minimum size threshold."""
    doc = fitz.open(pdf_path)
    results: list[DetectedImage] = []
    image_counter = 0

    for page_idx in range(doc.page_count):
        page = doc.load_page(page_idx)
        images = page.get_images(full=True)

        for img_idx, img_info in enumerate(images):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            w = base_image["width"]
            h = base_image["height"]
            ext = base_image["ext"]
            pixel_count = w * h

            if pixel_count < _MIN_PIXELS:
                continue

            image_counter += 1
            results.append(
                DetectedImage(
                    page_number=page_idx + 1,
                    image_index=image_counter,
                    width=w,
                    height=h,
                    pixel_count=pixel_count,
                    ext=ext,
                    description=(
                        f"Image #{image_counter} on page {page_idx + 1}: "
                        f"{w}x{h} {ext} image (description pending LLM)"
                    ),
                )
            )

    total_pages = doc.page_count
    doc.close()
    logger.info(
        "Detected %d meaningful images across %d pages from %s",
        len(results),
        total_pages,
        pdf_path,
    )
    return results
