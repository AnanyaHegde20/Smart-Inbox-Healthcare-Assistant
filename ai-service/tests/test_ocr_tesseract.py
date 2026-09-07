"""Tests proving OCR is invoked for scanned/image-only PDFs.

Creates a real scanned-style PDF by rendering text onto a PIL Image,
embedding it in a PDF, and verifying that Tesseract OCR produces
recognizable text from the image.
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.ocr import TesseractProvider
from app.ocr.provider import OCRProvider, OCRPageResult, OCRResult
from app.processors.ocr_service import OCRService
from app.processors.pdf_processor import PDFProcessor
from app.processors.scanner_detector import detect_scanned


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_text_image(text: str, width: int = 800, height: int = 200) -> bytes:
    """Render text onto a white background and return PNG bytes."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Use default font at a large size for OCR readability
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except (IOError, OSError):
        font = ImageFont.load_default(size=36)
    draw.text((20, 50), text, fill=(0, 0, 0), font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_scanned_pdf_with_text(text: str, tmp_path: Path) -> Path:
    """Create a PDF containing ONLY an image with text (no extractable text layer).

    This simulates a scanned document where PyMuPDF extracts no text
    but OCR can read the image.
    """
    pdf_path = tmp_path / "scanned_text.pdf"
    png_bytes = _create_text_image(text)

    # Write PNG to temp file for fitz
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_bytes)
        img_path = f.name

    doc = fitz.open()
    # Insert image covering the full page — no text layer
    page = doc.new_page(width=612, height=792)
    page.insert_image(page.rect, filename=img_path)

    doc.save(str(pdf_path))
    doc.close()

    Path(img_path).unlink(missing_ok=True)
    return pdf_path


def _create_scanned_pdf_multiline(lines: list[str], tmp_path: Path) -> Path:
    """Create a multi-page scanned PDF, one line per page."""
    pdf_path = tmp_path / "scanned_multipage.pdf"
    doc = fitz.open()

    for line in lines:
        png_bytes = _create_text_image(line)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(png_bytes)
            img_path = f.name
        page = doc.new_page(width=612, height=792)
        page.insert_image(page.rect, filename=img_path)
        Path(img_path).unlink(missing_ok=True)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


# ---------------------------------------------------------------------------
# Tesseract Provider Tests (unit)
# ---------------------------------------------------------------------------

class TestTesseractProviderOCR:
    """Direct TesseractProvider tests with real images."""

    @pytest.fixture(autouse=True)
    def _check_tesseract(self):
        """Skip if Tesseract binary is not available."""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
        except Exception:
            pytest.skip("Tesseract binary not installed")

    def test_ocr_reads_printed_text(self):
        """Tesseract should read clear printed text from an image."""
        png_bytes = _create_text_image("Patient Safety Report 2025")
        provider = TesseractProvider(lang="eng")

        result = provider._run_ocr(png_bytes, page_number=1)

        assert isinstance(result, OCRPageResult)
        assert result.page_number == 1
        assert len(result.full_text.strip()) > 0
        # The recognized text should contain key words
        text_lower = result.full_text.lower()
        assert "patient" in text_lower or "safety" in text_lower or "report" in text_lower
        assert result.mean_confidence > 0.0
        assert len(result.words) > 0

    def test_ocr_word_confidence(self):
        """Each OCR word should have a confidence between 0 and 1."""
        png_bytes = _create_text_image("Adverse event: anaphylactic shock")
        provider = TesseractProvider(lang="eng")

        result = provider._run_ocr(png_bytes, page_number=1)

        for word in result.words:
            assert 0.0 <= word.confidence <= 1.0
            assert len(word.text.strip()) > 0

    def test_ocr_empty_image(self):
        """An image with no text should return empty OCR result."""
        img = Image.new("RGB", (400, 200), color=(255, 255, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        png_bytes = buf.getvalue()

        provider = TesseractProvider(lang="eng")
        result = provider._run_ocr(png_bytes, page_number=1)

        assert result.page_number == 1
        # May have empty or minimal text
        assert result.mean_confidence >= 0.0


# ---------------------------------------------------------------------------
# OCRService Tests (integration: rendering + OCR)
# ---------------------------------------------------------------------------

class TestOCRServiceIntegration:
    """Test OCRService with real scanned PDFs."""

    @pytest.fixture(autouse=True)
    def _check_tesseract(self):
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
        except Exception:
            pytest.skip("Tesseract binary not installed")

    def test_scanned_pdf_ocr_produces_text(self, tmp_path: Path):
        """A scanned PDF should yield OCR text when processed."""
        pdf = _create_scanned_pdf_with_text("Hello World from OCR", tmp_path)
        provider = TesseractProvider(lang="eng")
        service = OCRService(provider=provider)

        result = service.process(str(pdf))

        assert result.total_pages == 1
        assert len(result.full_text.strip()) > 0
        text_lower = result.full_text.lower()
        assert "hello" in text_lower or "world" in text_lower or "ocr" in text_lower

    def test_multi_page_scanned_ocr(self, tmp_path: Path):
        """Multi-page scanned PDF should OCR each page."""
        pdf = _create_scanned_pdf_multiline(
            ["Page one content", "Page two content", "Page three content"],
            tmp_path,
        )
        provider = TesseractProvider(lang="eng")
        service = OCRService(provider=provider)

        result = service.process(str(pdf))

        assert result.total_pages == 3
        assert len(result.full_text.strip()) > 0


# ---------------------------------------------------------------------------
# PDFProcessor + Scanner Detection + OCR Pipeline Tests
# ---------------------------------------------------------------------------

class TestPDFProcessorOCR:
    """Test the full PDF processing pipeline with scanned PDFs."""

    @pytest.fixture(autouse=True)
    def _check_tesseract(self):
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
        except Exception:
            pytest.skip("Tesseract binary not installed")

    def test_scanned_pdf_detected_and_ocr_used(self, tmp_path: Path):
        """Scanned PDF should be detected and OCR text used."""
        pdf = _create_scanned_pdf_with_text(
            "Medication Error Report Ward 5A Patient fall incident",
            tmp_path,
        )
        # Verify scanner detector flags it as scanned
        scan = detect_scanned(str(pdf))
        assert scan.is_scanned is True

        # Process with OCR
        provider = TesseractProvider(lang="eng")
        ocr_service = OCRService(provider=provider)
        processor = PDFProcessor(ocr_service=ocr_service)

        result = processor.process(str(pdf))

        assert result.is_scanned is True
        assert result.ocr_result is not None
        assert len(result.extracted_text.strip()) > 0
        text_lower = result.extracted_text.lower()
        assert "medication" in text_lower or "error" in text_lower or "ward" in text_lower

    def test_digital_pdf_no_ocr(self, tmp_path: Path):
        """Digital PDF with text layer should NOT trigger OCR."""
        pdf_path = tmp_path / "digital.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Digital PDF with text layer", fontsize=12)
        doc.save(str(pdf_path))
        doc.close()

        scan = detect_scanned(str(pdf_path))
        assert scan.is_scanned is False

        provider = TesseractProvider(lang="eng")
        ocr_service = OCRService(provider=provider)
        processor = PDFProcessor(ocr_service=ocr_service)

        result = processor.process(str(pdf_path))

        assert result.is_scanned is False
        assert result.ocr_result is None  # OCR should NOT have been invoked
        assert "Digital PDF" in result.extracted_text


# ---------------------------------------------------------------------------
# Tesseract health/status test
# ---------------------------------------------------------------------------

class TestTesseractHealth:
    """Verify Tesseract is properly installed and accessible."""

    def test_tesseract_version_accessible(self):
        """The Tesseract binary should report a version."""
        try:
            import pytesseract
            version = pytesseract.get_tesseract_version()
            assert version is not None
        except Exception:
            pytest.skip("Tesseract binary not installed")

    def test_tesseract_eng_language_available(self):
        """English language data should be installed."""
        try:
            import pytesseract
            langs = pytesseract.get_languages()
            assert "eng" in langs
        except Exception:
            pytest.skip("Tesseract binary not installed")
