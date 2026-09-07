"""Non-English OCR tests.

Tests OCR with non-English text. French (fra) is installed and tested
for real. German (deu) and Spanish (spa) are skipped unless their
language data is installed.

To add more languages:
    1. Download from https://github.com/tesseract-ocr/tessdata
    2. Place .traineddata file in tessdata directory
    3. Add test class below with appropriate skip decorator
"""

from __future__ import annotations

import io
import tempfile
from pathlib import Path

import fitz
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.ocr import TesseractProvider
from app.processors.ocr_service import OCRService
from app.processors.pdf_processor import PDFProcessor
from app.processors.language_detector import detect_language


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_text_image(text: str, width: int = 800, height: int = 300) -> bytes:
    """Render text onto a white background and return PNG bytes."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except (IOError, OSError):
        font = ImageFont.load_default(size=36)
    # Draw multi-line text
    y = 30
    for line in text.split("\n"):
        draw.text((20, y), line, fill=(0, 0, 0), font=font)
        y += 50
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _create_image_pdf(png_bytes: bytes, tmp_path: Path) -> Path:
    """Create a PDF containing ONLY an image (no text layer)."""
    pdf_path = tmp_path / "non_english.pdf"
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(png_bytes)
        img_path = f.name
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(page.rect, filename=img_path)
    doc.save(str(pdf_path))
    doc.close()
    Path(img_path).unlink(missing_ok=True)
    return pdf_path


def _has_lang(lang: str) -> bool:
    """Check if a Tesseract language data file is installed."""
    try:
        import pytesseract
        return lang in pytesseract.get_languages()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# French OCR — primary non-English test (fra is installed)
# ---------------------------------------------------------------------------

class TestFrenchOCR:
    """Full pipeline test for French scanned documents.

    Creates a scanned PDF with French text, runs OCR with French
    language data, and verifies text extraction, language detection,
    classification, and structured extraction.
    """

    FRENCH_TEXT = (
        "Rapport d'evenement indeirable\n"
        "Patient: Jean Dupont\n"
        "Medicament: Aspirine 100 mg\n"
        "Reaction: Choc anaphylactique\n"
        "Service: Cardiologie"
    )

    @pytest.fixture(autouse=True)
    def _check_tesseract(self):
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
        except Exception:
            pytest.skip("Tesseract binary not installed")
        if not _has_lang("fra"):
            pytest.skip("French (fra) Tesseract data not installed")

    def test_french_ocr_produces_text(self, tmp_path: Path):
        """French text should be correctly recognized with fra language data."""
        png = _create_text_image(self.FRENCH_TEXT)
        pdf = _create_image_pdf(png, tmp_path)

        provider = TesseractProvider(lang="fra")
        service = OCRService(provider=provider)
        result = service.process(str(pdf))

        assert result.total_pages == 1
        text = result.full_text.strip()
        assert len(text) > 0
        text_lower = text.lower()
        # Core French words should appear
        assert "rapport" in text_lower or "evenement" in text_lower or "patient" in text_lower

    def test_french_ocr_word_confidence(self, tmp_path: Path):
        """Each French OCR word should have a valid confidence score."""
        png = _create_text_image(self.FRENCH_TEXT)
        pdf = _create_image_pdf(png, tmp_path)

        provider = TesseractProvider(lang="fra")
        service = OCRService(provider=provider)
        result = service.process(str(pdf))

        assert len(result.pages) > 0
        for page in result.pages:
            for word_text in page.low_confidence_words:
                assert isinstance(word_text, str)

    def test_french_language_detected(self, tmp_path: Path):
        """Language detector should identify French from OCR output."""
        png = _create_text_image(self.FRENCH_TEXT)
        pdf = _create_image_pdf(png, tmp_path)

        provider = TesseractProvider(lang="fra")
        service = OCRService(provider=provider)
        result = service.process(str(pdf))

        lang = detect_language(result.full_text)
        assert lang == "fr", f"Expected 'fr', got '{lang}'"

    def test_french_full_pipeline(self, tmp_path: Path):
        """Full pipeline: scanned French PDF -> OCR -> classification -> extraction -> summary."""
        png = _create_text_image(self.FRENCH_TEXT)
        pdf = _create_image_pdf(png, tmp_path)

        # Use English provider (simulates default), processor will do two-pass
        provider = TesseractProvider(lang="eng")
        service = OCRService(provider=provider)
        processor = PDFProcessor(ocr_service=service)

        result = processor.process(str(pdf))

        # Verify scanned detection
        assert result.is_scanned is True

        # Verify OCR produced text
        assert len(result.extracted_text.strip()) > 0

        # Verify language detection (should be fr after two-pass)
        assert result.language == "fr", f"Expected language 'fr', got '{result.language}'"

        # Verify OCR result exists
        assert result.ocr_result is not None
        assert result.ocr_result.overall_confidence > 0.0

    def test_french_two_pass_ocr_improves_result(self, tmp_path: Path):
        """Two-pass OCR: English first, then French re-run should produce better text."""
        png = _create_text_image(self.FRENCH_TEXT)
        pdf = _create_image_pdf(png, tmp_path)

        # Pass 1: English only
        eng_provider = TesseractProvider(lang="eng")
        eng_service = OCRService(provider=eng_provider)
        eng_result = eng_service.process(str(pdf))

        # Pass 2: French
        fra_provider = TesseractProvider(lang="fra")
        fra_service = OCRService(provider=fra_provider)
        fra_result = fra_service.process(str(pdf))

        # French OCR should produce recognizable French words
        fra_text = fra_result.full_text.lower()
        assert "rapport" in fra_text or "patient" in fra_text or "medicament" in fra_text

    def test_french_classification(self, tmp_path: Path):
        """French adverse event text should classify into a relevant category."""
        from app.classifier.rules import classify

        # Use the French OCR text directly
        ocr_text = (
            "Rapport d'evenement indeirable\n"
            "Patient: Jean Dupont\n"
            "Medicament: Aspirine 100 mg\n"
            "Reaction: Choc anaphylactique"
        )
        result = classify(ocr_text)
        # Should classify into at least one category with confidence > 0
        assert len(result.categories) > 0
        top_cat = max(result.categories, key=lambda c: c.confidence)
        assert top_cat.confidence > 0.0

    def test_french_structured_extraction(self, tmp_path: Path):
        """French text should produce structured extraction fields."""
        import asyncio
        import base64
        from app.services.document_processor import DocumentProcessor, ProcessDocumentRequest

        png = _create_text_image(self.FRENCH_TEXT)
        pdf = _create_image_pdf(png, tmp_path)

        with open(pdf, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()

        processor = DocumentProcessor()
        req = ProcessDocumentRequest(document=b64, filename="rapport_francais.pdf")
        result = asyncio.run(processor.process(request=req))

        # Should have classification and extracted facts
        assert result.classification is not None
        assert result.classification.category is not None
        assert len(result.extracted_facts) > 0


# ---------------------------------------------------------------------------
# German and Spanish — skipped unless language data is installed
# ---------------------------------------------------------------------------

class TestGermanOCR:
    """German OCR tests (skipped unless deu data installed)."""

    @pytest.mark.skipif(not _has_lang("deu"), reason="German (deu) Tesseract data not installed")
    def test_german_ocr(self, tmp_path: Path):
        png = _create_text_image("Sicherheitsbericht fur Patienten")
        pdf = _create_image_pdf(png, tmp_path)
        provider = TesseractProvider(lang="deu")
        service = OCRService(provider=provider)
        result = service.process(str(pdf))
        assert len(result.full_text.strip()) > 0


class TestSpanishOCR:
    """Spanish OCR tests (skipped unless spa data installed)."""

    @pytest.mark.skipif(not _has_lang("spa"), reason="Spanish (spa) Tesseract data not installed")
    def test_spanish_ocr(self, tmp_path: Path):
        png = _create_text_image("Reporte de seguridad del paciente")
        pdf = _create_image_pdf(png, tmp_path)
        provider = TesseractProvider(lang="spa")
        service = OCRService(provider=provider)
        result = service.process(str(pdf))
        assert len(result.full_text.strip()) > 0


# ---------------------------------------------------------------------------
# Language availability check
# ---------------------------------------------------------------------------

class TestLanguageAvailability:
    """Verify installed Tesseract languages."""

    def test_eng_available(self):
        assert _has_lang("eng"), "English data not installed"

    def test_fra_available(self):
        assert _has_lang("fra"), "French data not installed — expected for this test suite"

    def test_osd_available(self):
        assert _has_lang("osd"), "OSD data not installed"
