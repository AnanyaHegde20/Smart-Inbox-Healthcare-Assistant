"""Main PDF processing orchestrator.

Coordinates scanner detection, text extraction, OCR, table
extraction, image detection, and language detection into a single
``PDFProcessingResult``.

For scanned PDFs, a two-pass OCR strategy is used when the initial
English pass detects a non-English language:
    1. OCR with English to get a text sample
    2. Detect language from that sample
    3. Re-run OCR with the detected language (if Tesseract data is available)
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from .scanner_detector import ScanDetectionResult, detect_scanned
from .text_extractor import ExtractionResult, extract_text
from .ocr_service import OCRService, OCRServiceResult
from .language_detector import detect_language
from .table_extractor import ExtractedTable, extract_tables
from .image_detector import DetectedImage, detect_images

logger = logging.getLogger(__name__)

# Map langdetect BCP-47 codes (ISO 639-1) to Tesseract language codes (ISO 639-2)
_LANGDETECT_TO_TESSERACT: dict[str, str] = {
    "en": "eng",
    "fr": "fra",
    "de": "deu",
    "es": "spa",
    "it": "ita",
    "pt": "por",
    "nl": "nld",
    "ru": "rus",
    "ja": "jpn",
    "zh": "chi_sim",
    "ko": "kor",
    "ar": "ara",
    "hi": "hin",
    "th": "tha",
    "vi": "vie",
    "pl": "pol",
    "sv": "swe",
    "da": "dan",
    "no": "nor",
    "fi": "fin",
    "cs": "ces",
    "el": "grc",
    "hu": "hun",
    "ro": "ron",
    "tr": "tur",
    "uk": "ukr",
}


def _has_tesseract_lang(tess_lang: str) -> bool:
    """Check if a Tesseract language data file is installed."""
    try:
        import pytesseract
        return tess_lang in pytesseract.get_languages()
    except Exception:
        return False


def _map_lang_to_tesseract(langdetect_code: str) -> str | None:
    """Map a langdetect code to a Tesseract language code, or None if unmapped."""
    return _LANGDETECT_TO_TESSERACT.get(langdetect_code)


@dataclass
class SourceRef:
    filename: str
    page: int | None = None
    section: str | None = None


@dataclass
class PDFProcessingResult:
    extracted_text: str
    language: str
    is_scanned: bool
    scan_reason: str
    total_pages: int
    tables: list[ExtractedTable] = field(default_factory=list)
    images: list[DetectedImage] = field(default_factory=list)
    source_references: list[SourceRef] = field(default_factory=list)
    ocr_result: OCRServiceResult | None = None
    processing_time_ms: float = 0.0


class PDFProcessor:
    """High-level interface for processing a single PDF file.

    Accepts an optional ``OCRService`` to handle scanned PDFs.  When no
    service is provided, scanned PDFs are flagged but not OCR'd.
    """

    def __init__(self, ocr_service: OCRService | None = None) -> None:
        self.ocr_service = ocr_service

    def process(
        self,
        pdf_path: str,
        *,
        run_ocr: bool = True,
    ) -> PDFProcessingResult:
        start = time.perf_counter()
        filename = Path(pdf_path).name

        # 1 -- Detect if scanned
        scan = detect_scanned(pdf_path)

        # 2 -- Extract text (will be empty/low for scanned PDFs)
        extraction = extract_text(pdf_path)

        # 3 -- OCR (only if scanned, service available, and requested)
        ocr_result: OCRServiceResult | None = None
        if scan.is_scanned and run_ocr and self.ocr_service is not None:
            ocr_result = self.ocr_service.process(pdf_path)

            # 3a -- Two-pass OCR: detect language from first pass,
            #       re-run with correct language if non-English
            if ocr_result and ocr_result.full_text.strip():
                initial_lang = detect_language(ocr_result.full_text)
                tess_lang = _map_lang_to_tesseract(initial_lang)

                if (
                    tess_lang
                    and tess_lang != "eng"
                    and _has_tesseract_lang(tess_lang)
                ):
                    logger.info(
                        "Two-pass OCR: detected '%s' from English pass, "
                        "re-running with Tesseract lang '%s'",
                        initial_lang,
                        tess_lang,
                    )
                    from app.ocr import TesseractProvider

                    re_provider = TesseractProvider(lang=tess_lang)
                    re_service = OCRService(provider=re_provider)
                    ocr_result = re_service.process(pdf_path)

        # 4 -- Language detection
        # Use OCR text if available, otherwise raw extraction
        text_for_lang = ocr_result.full_text if ocr_result else extraction.full_text
        language = detect_language(text_for_lang)

        # 5 -- Table extraction (only for digital PDFs with text)
        tables: list[ExtractedTable] = []
        if not scan.is_scanned:
            tables = extract_tables(pdf_path)

        # 6 -- Image detection
        images = detect_images(pdf_path)

        # 7 -- Build source references per page
        source_refs = [
            SourceRef(filename=filename, page=pg.page_number)
            for pg in extraction.pages
            if pg.char_count > 0
        ]

        # If OCR produced text, add page-level refs from OCR pages
        if ocr_result:
            existing_pages = {ref.page for ref in source_refs}
            for page_out in ocr_result.pages:
                if page_out.page_number not in existing_pages and page_out.raw_text.strip():
                    source_refs.append(
                        SourceRef(filename=filename, page=page_out.page_number, section="OCR")
                    )

        # Use OCR text as the primary extracted text when available
        final_text = ocr_result.full_text if ocr_result else extraction.full_text

        elapsed_ms = (time.perf_counter() - start) * 1000

        result = PDFProcessingResult(
            extracted_text=final_text,
            language=language,
            is_scanned=scan.is_scanned,
            scan_reason=scan.reason,
            total_pages=extraction.total_pages,
            tables=tables,
            images=images,
            source_references=source_refs,
            ocr_result=ocr_result,
            processing_time_ms=round(elapsed_ms, 2),
        )

        logger.info(
            "PDF processed: %s | pages=%d | scanned=%s | ocr=%s | lang=%s | %.1fms",
            filename,
            result.total_pages,
            result.is_scanned,
            ocr_result is not None,
            result.language,
            elapsed_ms,
        )
        return result
