"""Comprehensive tests for PDF extraction pipeline: digital and scanned."""

from __future__ import annotations

import base64
import tempfile
from pathlib import Path

import fitz
import pytest
from PIL import Image as PILImage

from app.processors.scanner_detector import detect_scanned, ScanDetectionResult
from app.processors.text_extractor import extract_text, ExtractionResult
from app.processors.table_extractor import extract_tables, ExtractedTable
from app.processors.image_detector import detect_images, DetectedImage
from app.processors.language_detector import detect_language
from app.processors.pdf_processor import PDFProcessor
from app.processors.ocr_service import OCRService
from app.ocr import TesseractProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def digital_pdf_with_safety_content(tmp_path: Path) -> Path:
    """Digital PDF containing safety report content."""
    pdf_path = tmp_path / "safety.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), (
        "ADVERSE EVENT REPORT\n\n"
        "Patient: Jane Smith, Age 67, Female\n"
        "Drug: Metformin 500mg\n"
        "Event: Severe hypoglycemia requiring hospitalization\n"
        "Onset: 2025-03-15\n"
        "Outcome: Recovered\n"
        "Reporter: Dr. John Lee, Cardiologist\n"
        "Causality: Probable\n\n"
        "The patient experienced dizziness, confusion, and loss of consciousness "
        "30 minutes after taking Metformin. EpiPen was administered in the ER. "
        "Patient was hospitalized for 24-hour observation."
    ), fontsize=11)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture()
def digital_pdf_with_quality_content(tmp_path: Path) -> Path:
    """Digital PDF containing quality complaint content."""
    pdf_path = tmp_path / "quality.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), (
        "QUALITY COMPLAINT REPORT\n\n"
        "Product: Acetaminophen 500mg Tablets\n"
        "Lot Number: PC-2025-9999\n"
        "Complaint: Inconsistent tablet coating observed\n"
        "Affected Quantity: 10,000 tablets\n"
        "Reported by: QA Department\n"
        "Date: 2025-06-01\n\n"
        "Visual inspection revealed patchy coating on 15% of tablets. "
        "Dissolution testing confirmed failure to meet specification. "
        "Root cause analysis is underway."
    ), fontsize=11)
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture()
def scanned_pdf_with_text(tmp_path: Path) -> Path:
    """Scanned-style PDF with text content via image."""
    pdf_path = tmp_path / "scanned_text.pdf"

    width, height = 612, 792
    img = PILImage.new("RGB", (width, height), color=(255, 255, 255))

    import tempfile, io
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(img_bytes.getvalue())
        img_path = f.name

    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    page.insert_image(page.rect, filename=img_path)
    page.insert_text((72, 72), "A", fontsize=8)
    doc.save(str(pdf_path))
    doc.close()

    Path(img_path).unlink(missing_ok=True)
    return pdf_path


# ---------------------------------------------------------------------------
# Digital PDF Extraction Tests
# ---------------------------------------------------------------------------

class TestDigitalPDFExtraction:
    """Tests for digital PDF text extraction."""

    def test_extracts_full_text(self, digital_pdf_with_safety_content):
        result = extract_text(str(digital_pdf_with_safety_content))
        assert "ADVERSE EVENT REPORT" in result.full_text
        assert "Metformin" in result.full_text
        assert len(result.pages) >= 1

    def test_page_count_matches(self, digital_pdf_with_safety_content):
        result = extract_text(str(digital_pdf_with_safety_content))
        assert result.total_pages == 1

    def test_page_numbers_are_1_indexed(self, multi_page_pdf):
        result = extract_text(str(multi_page_pdf))
        page_nums = [p.page_number for p in result.pages]
        assert page_nums == [1, 2, 3]

    def test_per_page_text_non_empty(self, multi_page_pdf):
        result = extract_text(str(multi_page_pdf))
        for page in result.pages:
            assert len(page.text.strip()) > 0

    def test_scanner_detector_digital(self, digital_pdf_with_safety_content):
        result = detect_scanned(str(digital_pdf_with_safety_content))
        assert result.is_scanned is False

    def test_scanner_detector_scanned(self, scanned_pdf_with_text):
        result = detect_scanned(str(scanned_pdf_with_text))
        assert result.is_scanned is True

    def test_language_detection_english(self):
        text = "This is a patient safety report about adverse events."
        lang = detect_language(text)
        assert lang == "en"

    def test_language_detection_empty(self):
        lang = detect_language("")
        assert lang == "unknown"

    def test_language_detection_short(self):
        lang = detect_language("Hi")
        assert lang in ("unknown", "en")

    def test_table_extractor_finds_tables(self, pdf_with_table):
        tables = extract_tables(str(pdf_with_table))
        assert len(tables) >= 1
        assert len(tables[0].headers) == 3

    def test_image_detector_digital(self, digital_pdf_with_safety_content):
        images = detect_images(str(digital_pdf_with_safety_content))
        assert isinstance(images, list)

    def test_image_detector_scanned(self, scanned_pdf_with_text):
        images = detect_images(str(scanned_pdf_with_text))
        assert len(images) >= 1

    def test_full_pdf_processor_digital(self, digital_pdf_with_safety_content):
        processor = PDFProcessor()
        result = processor.process(str(digital_pdf_with_safety_content))
        assert len(result.extracted_text.strip()) > 0
        assert result.is_scanned is False
        assert result.total_pages == 1
        assert result.language in ("en", "unknown")

    def test_full_pdf_processor_multipage(self, multi_page_pdf):
        processor = PDFProcessor()
        result = processor.process(str(multi_page_pdf))
        assert result.total_pages == 3
        assert "Page 1" in result.extracted_text
        assert "Page 3" in result.extracted_text

    def test_source_references_generated(self, digital_pdf_with_safety_content):
        processor = PDFProcessor()
        result = processor.process(str(digital_pdf_with_safety_content))
        assert len(result.source_references) >= 1
        assert result.source_references[0].page >= 1


# ---------------------------------------------------------------------------
# Scanned PDF OCR Tests
# ---------------------------------------------------------------------------

class TestScannedPDFExtraction:
    """Tests for scanned PDF processing with OCR."""

    def test_scanned_detected_correctly(self, scanned_pdf_with_text):
        result = detect_scanned(str(scanned_pdf_with_text))
        assert result.is_scanned is True
        assert result.chars_per_page < 50

    def test_scanned_pdf_low_text_content(self, scanned_pdf_with_text):
        result = extract_text(str(scanned_pdf_with_text))
        assert len(result.full_text.strip()) < 50

    def test_scanned_pdf_with_ocr_disabled(self, scanned_pdf_with_text):
        processor = PDFProcessor(ocr_service=None)
        result = processor.process(str(scanned_pdf_with_text))
        assert result.ocr_result is None

    def test_scanned_pdf_ocr_service_interface(self):
        service = OCRService(provider=TesseractProvider())
        assert service is not None

    def test_scanned_pdf_still_returns_valid_result(self, scanned_pdf_with_text):
        processor = PDFProcessor()
        result = processor.process(str(scanned_pdf_with_text))
        assert result.extracted_text is not None
        assert result.is_scanned is True
        assert result.total_pages >= 1


# ---------------------------------------------------------------------------
# Multi-page and Source Reference Tests
# ---------------------------------------------------------------------------

class TestMultiPageProcessing:
    """Tests for multi-page PDF handling."""

    def test_multipage_source_refs_cover_all_pages(self, multi_page_pdf):
        processor = PDFProcessor()
        result = processor.process(str(multi_page_pdf))
        pages_with_refs = {ref.page for ref in result.source_references}
        assert len(pages_with_refs) == 3

    def test_multipage_text_concatenation(self, multi_page_pdf):
        processor = PDFProcessor()
        result = processor.process(str(multi_page_pdf))
        assert "Page 1" in result.extracted_text
        assert "Page 2" in result.extracted_text
        assert "Page 3" in result.extracted_text

    def test_table_pdf_extracts_tables(self, pdf_with_table):
        processor = PDFProcessor()
        result = processor.process(str(pdf_with_table))
        assert len(result.tables) >= 1

    def test_digital_pdf_no_ocr_result(self, digital_pdf_with_safety_content):
        processor = PDFProcessor()
        result = processor.process(str(digital_pdf_with_safety_content))
        assert result.ocr_result is None


# ---------------------------------------------------------------------------
# Encoding and Edge Case Tests
# ---------------------------------------------------------------------------

class TestPDFEdgeCases:
    """Tests for edge cases in PDF processing."""

    def test_empty_pdf(self, tmp_path):
        pdf_path = tmp_path / "empty.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        processor = PDFProcessor()
        result = processor.process(str(pdf_path))
        assert result.extracted_text.strip() == "" or len(result.extracted_text.strip()) < 10

    def test_nonexistent_file(self):
        processor = PDFProcessor()
        with pytest.raises(Exception):
            processor.process("/nonexistent/file.pdf")

    def test_detector_returns_page_count(self, digital_pdf_with_safety_content):
        result = detect_scanned(str(digital_pdf_with_safety_content))
        assert result.page_count >= 1
