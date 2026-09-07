"""Extract text from digital PDFs while preserving useful structure."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class PageText:
    page_number: int
    text: str
    char_count: int


@dataclass
class ExtractionResult:
    full_text: str
    pages: list[PageText] = field(default_factory=list)
    total_pages: int = 0


def extract_text(pdf_path: str) -> ExtractionResult:
    """Extract text from every page of a digital PDF.

    Returns the concatenated full text plus per-page breakdown so callers
    can reconstruct page-level source references.
    """
    doc = fitz.open(pdf_path)
    pages: list[PageText] = []
    parts: list[str] = []

    for page_idx in range(doc.page_count):
        page = doc.load_page(page_idx)
        text = page.get_text("text")
        stripped = text.strip()
        pages.append(
            PageText(
                page_number=page_idx + 1,
                text=stripped,
                char_count=len(stripped),
            )
        )
        parts.append(stripped)

    doc.close()

    full_text = "\n\n".join(parts)
    logger.info(
        "Extracted %d chars across %d pages from %s",
        len(full_text),
        len(pages),
        pdf_path,
    )
    return ExtractionResult(
        full_text=full_text,
        pages=pages,
        total_pages=len(pages),
    )
