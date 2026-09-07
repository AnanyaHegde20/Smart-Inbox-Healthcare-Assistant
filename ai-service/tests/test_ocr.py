"""Tests for OCR processing of scanned PDFs.

Uses a mock OCR provider so tests run without Tesseract installed.
All test documents contain synthetic data — no real patient info.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ocr.provider import OCRPageResult, OCRProvider, OCRResult, OCRWord
from app.processors.ocr_service import OCRService, _mark_uncertain
from app.processors.pdf_processor import PDFProcessor


# ---------------------------------------------------------------------------
# Mock OCR provider for deterministic testing
# ---------------------------------------------------------------------------

class StubOCRProvider(OCRProvider):
    """Returns deterministic OCR results without running real OCR."""

    def __init__(self, pages: dict[int, str] | None = None, confidences: dict[int, float] | None = None):
        """Args:
            pages: {page_number: text} mapping.
            confidences: {page_number: mean_confidence} — defaults to 0.95.
        """
        self._pages = pages or {}
        self._confidences = confidences or {}

    def _run_ocr(self, image_bytes: bytes, page_number: int) -> OCRPageResult:
        text = self._pages.get(page_number, f"OCR text for page {page_number}")
        conf = self._confidences.get(page_number, 0.95)

        # Build word list with some low-confidence words if confidence < 0.9
        words: list[OCRWord] = []
        for token in text.split():
            if conf < 0.5:
                words.append(OCRWord(text=token, confidence=0.3))
            elif conf < 0.8:
                words.append(OCRWord(text=token, confidence=0.65))
            else:
                words.append(OCRWord(text=token, confidence=conf))

        low_count = sum(1 for w in words if w.confidence < 0.6)

        return OCRPageResult(
            page_number=page_number,
            full_text=text,
            words=words,
            mean_confidence=conf,
            low_confidence_count=low_count,
        )


class AlwaysFailOCRProvider(OCRProvider):
    """Simulates an OCR provider that returns empty/zero-confidence results."""

    def _run_ocr(self, image_bytes: bytes, page_number: int) -> OCRPageResult:
        return OCRPageResult(
            page_number=page_number,
            full_text="",
            words=[],
            mean_confidence=0.0,
            low_confidence_count=0,
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def scanned_pdf(tmp_path: Path) -> Path:
    """Create a synthetic scanned PDF (image-only, minimal text)."""
    from PIL import Image as PILImage
    import fitz
    import io, tempfile

    pdf_path = tmp_path / "scanned.pdf"
    width, height = 612, 792

    img = PILImage.new("RGB", (width, height), color=(240, 240, 240))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(buf.getvalue())
        img_path = f.name

    doc = fitz.open()
    page = doc.new_page(width=width, height=height)
    page.insert_image(page.rect, filename=img_path)
    page.insert_text((72, 72), "Scanned document", fontsize=8)

    doc.save(str(pdf_path))
    doc.close()
    Path(img_path).unlink(missing_ok=True)
    return pdf_path


@pytest.fixture()
def multi_page_scanned_pdf(tmp_path: Path) -> Path:
    """Create a 3-page synthetic scanned PDF."""
    from PIL import Image as PILImage
    import fitz
    import io, tempfile

    pdf_path = tmp_path / "scanned_multi.pdf"
    doc = fitz.open()

    for page_num in range(1, 4):
        width, height = 612, 792
        img = PILImage.new("RGB", (width, height), color=(235, 235, 235))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(buf.getvalue())
            img_path = f.name

        page = doc.new_page(width=width, height=height)
        page.insert_image(page.rect, filename=img_path)
        page.insert_text((72, 72), f"Page {page_num} scanned text", fontsize=8)

        Path(img_path).unlink(missing_ok=True)

    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


# ---------------------------------------------------------------------------
# Tests: _mark_uncertain helper
# ---------------------------------------------------------------------------

class TestMarkUncertain:
    def test_no_words_returns_original(self):
        assert _mark_uncertain("hello world", []) == "hello world"

    def test_high_confidence_not_marked(self):
        words = [OCRWord(text="hello", confidence=0.95)]
        result = _mark_uncertain("hello world", words)
        assert "[uncertain]" not in result

    def test_low_confidence_marked(self):
        words = [OCRWord(text="unclear", confidence=0.3)]
        result = _mark_uncertain("this is unclear text", words)
        assert "[uncertain]unclear[/uncertain]" in result

    def test_empty_text_not_marked(self):
        words = [OCRWord(text="", confidence=0.1)]
        result = _mark_uncertain("hello", words)
        assert "[uncertain]" not in result


# ---------------------------------------------------------------------------
# Tests: OCRService with StubOCRProvider
# ---------------------------------------------------------------------------

class TestOCRService:
    def test_scanned_pdf_ocr_produces_text(self, scanned_pdf: Path):
        provider = StubOCRProvider(pages={1: "Patient chart shows normal vitals"})
        service = OCRService(provider=provider)
        result = service.process(str(scanned_pdf))

        assert result.total_pages == 1
        assert "Patient chart shows normal vitals" in result.full_text
        assert result.overall_confidence == 0.95

    def test_multi_page_ocr(self, multi_page_scanned_pdf: Path):
        provider = StubOCRProvider(
            pages={1: "Page one text", 2: "Page two text", 3: "Page three text"}
        )
        service = OCRService(provider=provider)
        result = service.process(str(multi_page_scanned_pdf))

        assert result.total_pages == 3
        assert "Page one text" in result.full_text
        assert "Page two text" in result.full_text
        assert "Page three text" in result.full_text

    def test_page_numbers_preserved(self, multi_page_scanned_pdf: Path):
        provider = StubOCRProvider(
            pages={1: "First", 2: "Second", 3: "Third"}
        )
        service = OCRService(provider=provider)
        result = service.process(str(multi_page_scanned_pdf))

        page_numbers = [p.page_number for p in result.pages]
        assert page_numbers == [1, 2, 3]

    def test_confidence_returned(self, scanned_pdf: Path):
        provider = StubOCRProvider(
            pages={1: "Some text"},
            confidences={1: 0.87},
        )
        service = OCRService(provider=provider)
        result = service.process(str(scanned_pdf))

        assert result.overall_confidence == 0.87
        assert result.pages[0].mean_confidence == 0.87

    def test_low_confidence_marks_uncertain(self, scanned_pdf: Path):
        provider = StubOCRProvider(
            pages={1: "This is unclear"},
            confidences={1: 0.4},
        )
        service = OCRService(provider=provider)
        result = service.process(str(scanned_pdf))

        assert result.needs_review is True
        assert "[uncertain]" in result.marked_text
        assert len(result.pages[0].low_confidence_words) > 0

    def test_high_confidence_no_uncertain_markers(self, scanned_pdf: Path):
        provider = StubOCRProvider(
            pages={1: "Clear readable text"},
            confidences={1: 0.98},
        )
        service = OCRService(provider=provider)
        result = service.process(str(scanned_pdf))

        assert result.needs_review is False
        assert "[uncertain]" not in result.marked_text

    def test_empty_ocr_result(self, scanned_pdf: Path):
        provider = AlwaysFailOCRProvider()
        service = OCRService(provider=provider)
        result = service.process(str(scanned_pdf))

        assert result.total_pages >= 1
        assert result.full_text == ""
        assert result.overall_confidence == 0.0


# ---------------------------------------------------------------------------
# Tests: PDFProcessor with OCR integration
# ---------------------------------------------------------------------------

class TestPDFProcessorWithOCR:
    def test_scanned_pdf_gets_ocr_text(self, scanned_pdf: Path):
        provider = StubOCRProvider(
            pages={1: "Synthetic test document for unit testing"}
        )
        ocr_service = OCRService(provider=provider)
        processor = PDFProcessor(ocr_service=ocr_service)

        result = processor.process(str(scanned_pdf))

        assert result.is_scanned is True
        assert result.ocr_result is not None
        assert "Synthetic test document" in result.extracted_text

    def test_scanned_pdf_without_ocr_service(self, scanned_pdf: Path):
        processor = PDFProcessor(ocr_service=None)
        result = processor.process(str(scanned_pdf), run_ocr=True)

        assert result.is_scanned is True
        assert result.ocr_result is None

    def test_scanned_pdf_with_ocr_disabled(self, scanned_pdf: Path):
        provider = StubOCRProvider(pages={1: "Should not appear"})
        ocr_service = OCRService(provider=provider)
        processor = PDFProcessor(ocr_service=ocr_service)

        result = processor.process(str(scanned_pdf), run_ocr=False)

        assert result.ocr_result is None

    def test_scanned_pdf_source_refs_cover_ocr_pages(self, scanned_pdf: Path):
        provider = StubOCRProvider(pages={1: "OCR content"})
        ocr_service = OCRService(provider=provider)
        processor = PDFProcessor(ocr_service=ocr_service)

        result = processor.process(str(scanned_pdf))

        # OCR ran and produced output
        assert result.ocr_result is not None
        assert result.ocr_result.total_pages == 1

        # Source refs should include page 1 (from text extraction or OCR)
        page1_refs = [r for r in result.source_references if r.page == 1]
        assert len(page1_refs) >= 1


# ---------------------------------------------------------------------------
# Tests: OCRProvider interface contract
# ---------------------------------------------------------------------------

class TestOCRProviderInterface:
    def test_provider_ocr_method_aggregates(self):
        provider = StubOCRProvider(
            pages={1: "Page one", 2: "Page two"},
            confidences={1: 0.9, 2: 0.8},
        )
        result = provider.ocr([(1, b"img1"), (2, b"img2")])

        assert isinstance(result, OCRResult)
        assert result.total_pages == 2
        assert len(result.pages) == 2
        assert result.overall_mean_confidence == pytest.approx(0.85, abs=0.01)

    def test_provider_empty_input(self):
        provider = StubOCRProvider()
        result = provider.ocr([])

        assert result.total_pages == 0
        assert result.overall_mean_confidence == 0.0
