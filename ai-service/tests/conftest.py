"""Shared fixtures for PDF processor tests."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
import pytest
from PIL import Image as PILImage
import io
import tempfile

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FIXTURES_DIR.mkdir(exist_ok=True)


@pytest.fixture()
def digital_pdf(tmp_path: Path) -> Path:
    """Create a simple digital PDF with known text content."""
    pdf_path = tmp_path / "digital.pdf"
    doc = fitz.open()

    page = doc.new_page()
    lines = [
        "Patient Discharge Summary",
        "",
        "Patient Name: John Doe",
        "Date of Admission: 2025-01-10",
        "Date of Discharge: 2025-01-15",
        "Diagnosis: Community-acquired pneumonia",
        "",
        "The patient was admitted with fever and cough.",
        "Chest X-ray confirmed right lower lobe infiltrate.",
        "Treatment with IV antibiotics was initiated.",
        "Patient improved and was discharged in stable condition.",
        "Follow-up with Dr. Smith in 2 weeks.",
    ]
    text = "\n".join(lines)
    page.insert_text((72, 72), text, fontsize=11)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture()
def multi_page_pdf(tmp_path: Path) -> Path:
    """Create a multi-page digital PDF."""
    pdf_path = tmp_path / "multipage.pdf"
    doc = fitz.open()

    for i in range(1, 4):
        page = doc.new_page()
        page.insert_text(
            (72, 72),
            f"Page {i} content.\nThis is line two on page {i}.\nAnd line three.",
            fontsize=11,
        )

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture()
def pdf_with_table(tmp_path: Path) -> Path:
    """Create a PDF containing a table drawn with rectangles and text."""
    pdf_path = tmp_path / "table.pdf"
    doc = fitz.open()
    page = doc.new_page()

    x0, y0 = 72, 72
    col_w = 150
    row_h = 30
    headers = ["Name", "Amount", "Date"]
    rows = [
        ["Alice", "$100.00", "2025-01-01"],
        ["Bob", "$250.50", "2025-02-15"],
    ]

    for col_idx, header in enumerate(headers):
        rect = fitz.Rect(x0 + col_idx * col_w, y0, x0 + (col_idx + 1) * col_w, y0 + row_h)
        page.draw_rect(rect, color=(0, 0, 0), width=0.5)
        page.insert_text((x0 + col_idx * col_w + 5, y0 + 20), header, fontsize=10)

    for row_idx, row in enumerate(rows):
        for col_idx, cell in enumerate(row):
            ry = y0 + (row_idx + 1) * row_h
            rect = fitz.Rect(x0 + col_idx * col_w, ry, x0 + (col_idx + 1) * col_w, ry + row_h)
            page.draw_rect(rect, color=(0, 0, 0), width=0.5)
            page.insert_text((x0 + col_idx * col_w + 5, ry + 20), cell, fontsize=10)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture()
def scanned_pdf(tmp_path: Path) -> Path:
    """Create a scanned-style PDF: image-only, minimal text."""
    pdf_path = tmp_path / "scanned.pdf"

    # Create a large PNG image first (simulating a scanned page)
    width, height = 612, 792
    img = PILImage.new("RGB", (width, height), color=(240, 240, 240))
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(img_bytes.getvalue())
        img_path = f.name

    # Create PDF from the image
    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    page.insert_image(page.rect, filename=img_path)

    # Add minimal text (below threshold)
    page.insert_text((72, 72), "Scanned doc", fontsize=8)

    doc.save(str(pdf_path))
    doc.close()

    Path(img_path).unlink(missing_ok=True)
    return pdf_path
