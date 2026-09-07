"""Extract tables from PDF pages using PyMuPDF's built-in table finder."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTable:
    page_number: int
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    bbox: tuple[float, float, float, float] | None = None


def extract_tables(pdf_path: str) -> list[ExtractedTable]:
    """Scan every page for tabular structures and return them as data.

    PyMuPDF's ``page.find_tables()`` uses heuristic line/rect detection.
    It works well for digitally-born tables.  Scanned PDFs should be OCR'd
    first and have tables detected in the resulting text instead.
    """
    doc = fitz.open(pdf_path)
    all_tables: list[ExtractedTable] = []

    for page_idx in range(doc.page_count):
        page = doc.load_page(page_idx)
        tab_finder = page.find_tables()

        for tab in tab_finder.tables:
            data = tab.extract()
            if not data:
                continue

            # First row becomes headers; remaining rows are data
            headers = [str(cell) if cell is not None else "" for cell in data[0]]
            rows = []
            for row in data[1:]:
                rows.append([str(cell) if cell is not None else "" for cell in row])

            all_tables.append(
                ExtractedTable(
                    page_number=page_idx + 1,
                    headers=headers,
                    rows=rows,
                    bbox=tab.bbox,
                )
            )
            logger.debug(
                "Found table on page %d: %d cols x %d rows",
                page_idx + 1,
                len(headers),
                len(rows),
            )

    doc.close()
    logger.info("Extracted %d tables from %s", len(all_tables), pdf_path)
    return all_tables
