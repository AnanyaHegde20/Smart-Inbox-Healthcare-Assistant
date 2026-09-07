"""Tests for digital PDF processing."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.processors.pdf_processor import PDFProcessor
from app.processors.scanner_detector import detect_scanned
from app.processors.text_extractor import extract_text
from app.processors.language_detector import detect_language
from app.processors.table_extractor import extract_tables
from app.processors.image_detector import detect_images


class TestScannerDetector:
    def test_digital_pdf_not_scanned(self, digital_pdf: Path):
        result = detect_scanned(str(digital_pdf))
        assert result.is_scanned is False
        assert result.page_count == 1
        assert result.chars_per_page > 50

    def test_scanned_pdf_detected(self, scanned_pdf: Path):
        result = detect_scanned(str(scanned_pdf))
        assert result.is_scanned is True
        assert result.page_count == 1


class TestTextExtractor:
    def test_extracts_full_text(self, digital_pdf: Path):
        result = extract_text(str(digital_pdf))
        assert "Patient Discharge Summary" in result.full_text
        assert "John Doe" in result.full_text
        assert "Dr. Smith" in result.full_text

    def test_page_count(self, digital_pdf: Path):
        result = extract_text(str(digital_pdf))
        assert result.total_pages == 1
        assert len(result.pages) == 1

    def test_multi_page_text(self, multi_page_pdf: Path):
        result = extract_text(str(multi_page_pdf))
        assert result.total_pages == 3
        assert "Page 1 content" in result.full_text
        assert "Page 2 content" in result.full_text
        assert "Page 3 content" in result.full_text

    def test_page_numbers_are_1_indexed(self, multi_page_pdf: Path):
        result = extract_text(str(multi_page_pdf))
        page_numbers = [p.page_number for p in result.pages]
        assert page_numbers == [1, 2, 3]

    def test_per_page_char_count(self, digital_pdf: Path):
        result = extract_text(str(digital_pdf))
        assert result.pages[0].char_count > 0
        assert result.pages[0].char_count == len(result.pages[0].text)


class TestLanguageDetector:
    def test_english_detected(self, digital_pdf: Path):
        text = extract_text(str(digital_pdf)).full_text
        lang = detect_language(text)
        assert lang == "en"

    def test_short_text_returns_unknown(self):
        assert detect_language("hi") == "unknown"

    def test_empty_text_returns_unknown(self):
        assert detect_language("") == "unknown"


class TestTableExtractor:
    def test_extracts_tables(self, pdf_with_table: Path):
        tables = extract_tables(str(pdf_with_table))
        # We drew a table with 2 rows and 3 columns
        assert len(tables) >= 1
        first_table = tables[0]
        assert len(first_table.headers) == 3
        assert len(first_table.rows) == 2
        assert "Alice" in first_table.rows[0]
        assert "$250.50" in first_table.rows[1]

    def test_page_number_recorded(self, pdf_with_table: Path):
        tables = extract_tables(str(pdf_with_table))
        assert tables[0].page_number == 1


class TestImageDetector:
    def test_digital_pdf_no_large_images(self, digital_pdf: Path):
        images = detect_images(str(digital_pdf))
        assert images == []

    def test_scanned_pdf_has_images(self, scanned_pdf: Path):
        images = detect_images(str(scanned_pdf))
        assert len(images) >= 1


class TestPDFProcessorIntegration:
    def test_digital_pdf_full_processing(self, digital_pdf: Path):
        processor = PDFProcessor()
        result = processor.process(str(digital_pdf))

        assert result.is_scanned is False
        assert result.language == "en"
        assert "Patient Discharge Summary" in result.extracted_text
        assert result.total_pages == 1
        assert len(result.source_references) >= 1
        assert result.source_references[0].filename == "digital.pdf"
        assert result.source_references[0].page == 1
        assert result.processing_time_ms > 0

    def test_scanned_pdf_no_ocr_when_no_service(self, scanned_pdf: Path):
        processor = PDFProcessor()
        result = processor.process(str(scanned_pdf))

        assert result.is_scanned is True
        # No OCR service configured, so ocr_result is None
        assert result.ocr_result is None

    def test_no_ocr_when_disabled(self, scanned_pdf: Path):
        from app.ocr import TesseractProvider
        from app.processors.ocr_service import OCRService

        ocr_service = OCRService(provider=TesseractProvider())
        processor = PDFProcessor(ocr_service=ocr_service)
        result = processor.process(str(scanned_pdf), run_ocr=False)

        assert result.ocr_result is None

    def test_multi_page_source_refs(self, multi_page_pdf: Path):
        processor = PDFProcessor()
        result = processor.process(str(multi_page_pdf))

        assert result.total_pages == 3
        refs = result.source_references
        assert len(refs) == 3
        assert [r.page for r in refs] == [1, 2, 3]
        assert all(r.filename == "multipage.pdf" for r in refs)


class TestDocumentProcessorPDF:
    """Test the DocumentProcessor service with PDF input."""

    @pytest.mark.asyncio
    async def test_process_pdf_request(self, digital_pdf: Path):
        import base64

        from app.services.document_processor import DocumentProcessor
        from app.models.requests import ProcessDocumentRequest

        pdf_bytes = digital_pdf.read_bytes()
        b64 = base64.b64encode(pdf_bytes).decode()

        request = ProcessDocumentRequest(
            document=b64,
            filename="test_discharge.pdf",
        )

        processor = DocumentProcessor()
        response = await processor.process(request)

        assert response.document_type == "pdf"
        assert "Patient Discharge Summary" in response.extracted_text
        assert response.language == "en"
        assert len(response.source_references) >= 1
        assert response.processing_time_ms > 0
