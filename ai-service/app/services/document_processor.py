from __future__ import annotations

import base64
import logging
import tempfile
import time
from pathlib import Path, PurePosixPath

from app.classifier import classify
from app.classifier.models import ClassificationResult
from app.icsr.extractor import ICSRExtractor
from app.icsr.models import ICSRReport
from app.extractors.quality_complaint import QualityComplaintExtractor, QualityComplaintResult
from app.extractors.info_request import InfoRequestExtractor, InfoRequestResult
from app.extractors.not_relevant import NotRelevantExtractor, NotRelevantResult
from app.models.requests import ProcessDocumentRequest
from app.models.responses import (
    CategoryOutput,
    Classification,
    ClassificationOutput,
    DocumentSummaryOutput,
    ExtractedFact,
    ImageDescription,
    ProcessDocumentResponse,
    SourceReference,
    SummarySentenceOutput,
    TableData,
)
from app.ocr import TesseractProvider
from app.processors.ocr_service import OCRService
from app.processors.pdf_processor import PDFProcessor
from app.summarizer import DocumentSummarizer

logger = logging.getLogger(__name__)

_PDF_EXTENSIONS = {".pdf"}

# Non-PDF document type labels
_EXTENSIONS = {
    ".doc": "doc",
    ".docx": "docx",
    ".txt": "text",
    ".html": "html",
    ".htm": "html",
    ".eml": "email",
    ".msg": "email",
    ".csv": "csv",
    ".xlsx": "spreadsheet",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}

# Wire up services
_ocr_service = OCRService(provider=TesseractProvider(lang="eng"))
_pdf_processor = PDFProcessor(ocr_service=_ocr_service)
_summarizer = DocumentSummarizer()

# Category-specific extractors
_icsr_extractor = ICSRExtractor()
_quality_extractor = QualityComplaintExtractor()
_info_extractor = InfoRequestExtractor()
_not_relevant_extractor = NotRelevantExtractor()


def _detect_document_type(filename: str) -> str:
    ext = PurePosixPath(filename).suffix.lower()
    if ext in _PDF_EXTENSIONS:
        return "pdf"
    return _EXTENSIONS.get(ext, "unknown")


def _build_summary(text: str, max_sentences: int = 3) -> str:
    """Legacy: returns first N sentences as a plain-text summary."""
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    if not sentences:
        return ""
    return ". ".join(sentences[:max_sentences]) + "."


def _to_summary_output(result) -> DocumentSummaryOutput:
    """Convert DocumentSummary to response model."""
    return DocumentSummaryOutput(
        sentences=[
            SummarySentenceOutput(
                index=s.index,
                text=s.text,
                section=s.section,
                source_ref=s.source_ref,
            )
            for s in result.sentences
        ],
        total_sentences=result.total_sentences,
        is_relevant=result.is_relevant,
        relevance_confidence=result.relevance_confidence,
        key_topics=result.key_topics,
        document_purpose=result.document_purpose,
        narrative=result.to_narrative(),
    )


def _to_classification_output(result: ClassificationResult) -> ClassificationOutput:
    """Convert classifier result to response model."""
    return ClassificationOutput(
        categories=[
            CategoryOutput(
                category=c.category.value,
                confidence=c.confidence,
                reason=c.reason,
            )
            for c in result.categories
        ]
    )


def _to_legacy_classification(result: ClassificationResult) -> Classification:
    """Convert classifier result to legacy single-category format (backward compat)."""
    primary = result.primary
    return Classification(
        category=primary.category.value,
        subcategory=None,
        confidence=primary.confidence,
        reasons=[c.reason for c in result.categories],
    )


def _extract_facts_stub(filename: str, text: str) -> list[dict]:
    """Stub: returns basic filename-derived facts."""
    return [
        {"key": "filename", "value": filename, "confidence": 1.0},
        {"key": "word_count", "value": str(len(text.split())), "confidence": 1.0},
    ]


def _field_value_to_fact(key: str, fv) -> dict:
    """Convert a FieldValue to an ExtractedFact dict."""
    return {"key": key, "value": fv.value, "confidence": fv.confidence}


def _flatten_icsr(report: ICSRReport) -> list[dict]:
    """Flatten a nested ICSRReport into a list of ExtractedFact dicts."""
    facts = []
    # Report-level
    for key in ("report_id", "report_date", "report_type"):
        fv = getattr(report, key)
        facts.append(_field_value_to_fact(key, fv))
    # Patient
    for key in ("name", "age", "sex", "weight", "height", "medical_history"):
        facts.append(_field_value_to_fact(f"patient_{key}", getattr(report.patient, key)))
    # Reporter
    for key in ("name", "role", "organization", "contact"):
        facts.append(_field_value_to_fact(f"reporter_{key}", getattr(report.reporter, key)))
    # Product
    for key in ("name", "manufacturer", "lot_number", "expiry_date", "dosage", "route", "indication"):
        facts.append(_field_value_to_fact(f"product_{key}", getattr(report.product, key)))
    # Reaction
    for key in ("description", "onset_date", "outcome", "seriousness"):
        facts.append(_field_value_to_fact(f"reaction_{key}", getattr(report.reaction, key)))
    # Severity
    for key in ("grade", "description", "hospitalization", "life_threatening", "death", "disability", "congenital_anomaly", "other_significant"):
        facts.append(_field_value_to_fact(f"severity_{key}", getattr(report.severity, key)))
    # Narrative
    for key in ("summary", "causality_assessment", "action_taken", "additional_information"):
        facts.append(_field_value_to_fact(f"narrative_{key}", getattr(report.narrative, key)))
    return facts


def _flatten_model(model, prefix: str = "") -> list[dict]:
    """Flatten a Pydantic model with FieldValue fields into ExtractedFact dicts."""
    facts = []
    for field_name, field_val in model.model_dump().items():
        if isinstance(field_val, dict) and "value" in field_val:
            key = f"{prefix}{field_name}" if prefix else field_name
            facts.append({"key": key, "value": field_val["value"], "confidence": field_val["confidence"]})
    return facts


def _extract_category_facts(text: str, primary_category: str, filename: str | None = None) -> list[dict]:
    """Run the appropriate category-specific extractor and return facts."""
    try:
        if primary_category == "SAFETY_REPORT":
            report = _icsr_extractor.extract(text, filename=filename)
            return _flatten_icsr(report)
        elif primary_category == "QUALITY_COMPLAINT":
            result = _quality_extractor.extract(text, filename=filename)
            return _flatten_model(result)
        elif primary_category == "INFO_REQUEST":
            result = _info_extractor.extract(text, filename=filename)
            return _flatten_model(result)
        elif primary_category == "NOT_RELEVANT":
            result = _not_relevant_extractor.extract(text, filename=filename)
            return _flatten_model(result)
    except Exception:
        logger.exception("Category-specific extraction failed for %s", primary_category)
    # Fallback: return empty list (not the stub)
    return []


class DocumentProcessor:
    """Core service responsible for orchestrating document processing."""

    async def process(self, request: ProcessDocumentRequest) -> ProcessDocumentResponse:
        start = time.perf_counter()

        document_type = _detect_document_type(request.filename)

        # ---------- PDF branch: use real PDF processor ----------
        if document_type == "pdf":
            return await self._process_pdf(request, start)

        # ---------- Non-PDF: use raw document field as text ----------
        extracted_text = request.document
        language = "en"

        # Run multi-category classifier
        class_result = classify(extracted_text)
        classification = _to_legacy_classification(class_result)
        classification_output = _to_classification_output(class_result)

        # Run category-specific extractor
        primary_cat = class_result.primary.category.value
        extracted_facts = _extract_category_facts(extracted_text, primary_cat, request.filename)

        # Generate structured summary
        summary_result = _summarizer.summarize(
            extracted_text,
            filename=request.filename,
            classification_categories=[c.category.value for c in class_result.categories],
        )
        summary_output = _to_summary_output(summary_result)
        legacy_summary = _build_summary(extracted_text)

        elapsed_ms = (time.perf_counter() - start) * 1000

        return ProcessDocumentResponse(
            document_type=document_type,
            extracted_text=extracted_text,
            language=language,
            translated_text=None,
            summary=legacy_summary,
            classification=classification,
            classification_output=classification_output,
            extracted_facts=extracted_facts,
            source_references=[],
            tables=[],
            image_descriptions=[],
            processing_time_ms=round(elapsed_ms, 2),
            document_summary=summary_output,
        )

    async def _process_pdf(
        self, request: ProcessDocumentRequest, start: float
    ) -> ProcessDocumentResponse:
        """Process a PDF: decode base64, run PDFProcessor, map to response."""
        pdf_bytes = base64.b64decode(request.document)
        suffix = PurePosixPath(request.filename).suffix or ".pdf"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        try:
            result = _pdf_processor.process(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        # Map PDF results to response models
        tables = [
            TableData(headers=t.headers, rows=t.rows, page=t.page_number)
            for t in result.tables
        ]

        images = [
            ImageDescription(
                description=img.description,
                page=img.page_number,
                image_index=img.image_index,
            )
            for img in result.images
        ]

        source_references = [
            SourceReference(page=ref.page, section=ref.section)
            for ref in result.source_references
        ]

        # Run multi-category classifier
        class_result = classify(result.extracted_text)
        classification = _to_legacy_classification(class_result)
        classification_output = _to_classification_output(class_result)

        # Run category-specific extractor
        primary_cat = class_result.primary.category.value
        extracted_facts = _extract_category_facts(result.extracted_text, primary_cat, request.filename)

        # Generate structured summary
        summary_result = _summarizer.summarize(
            result.extracted_text,
            filename=request.filename,
            classification_categories=[c.category.value for c in class_result.categories],
            page_count=result.total_pages,
        )
        summary_output = _to_summary_output(summary_result)
        legacy_summary = _build_summary(result.extracted_text)

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "PDF processed: %s | scanned=%s | ocr=%s | lang=%s | pages=%d | cats=%s | summary=%d sentences | %.1fms",
            request.filename,
            result.is_scanned,
            result.ocr_result is not None,
            result.language,
            result.total_pages,
            [c.category.value for c in class_result.categories],
            summary_result.total_sentences,
            elapsed_ms,
        )

        return ProcessDocumentResponse(
            document_type="pdf",
            extracted_text=result.extracted_text,
            language=result.language,
            translated_text=None,
            summary=legacy_summary,
            classification=classification,
            classification_output=classification_output,
            extracted_facts=extracted_facts,
            source_references=source_references,
            tables=tables,
            image_descriptions=images,
            processing_time_ms=round(elapsed_ms, 2),
            document_summary=summary_output,
        )
