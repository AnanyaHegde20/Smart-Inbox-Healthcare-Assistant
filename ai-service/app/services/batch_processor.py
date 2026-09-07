from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.models.requests import ProcessDocumentRequest
from app.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)

TEST_DATA_ROOT = Path(__file__).resolve().parents[3] / "test-data"
OUTPUT_DIR = Path(__file__).resolve().parents[3] / "sample-output"
REPORT_FILENAME = "batch-processing-report.json"


@dataclass
class DocumentResult:
    filename: str
    start_time: str
    end_time: str
    processing_duration_ms: float
    classification: str
    all_categories: list[str]
    confidence: float
    success: bool
    error: Optional[str] = None


@dataclass
class BatchReport:
    total_documents: int
    successful_documents: int
    failed_documents: int
    average_processing_time_ms: float
    minimum_processing_time_ms: float
    maximum_processing_time_ms: float
    processing_start_time: str
    processing_end_time: str
    total_processing_time_ms: float
    documents: list[DocumentResult] = field(default_factory=list)


def _collect_text_files() -> list[Path]:
    """Collect all .txt files from test-data/ directory tree."""
    if not TEST_DATA_ROOT.exists():
        return []
    return sorted(TEST_DATA_ROOT.rglob("*.txt"))


def _parse_manifest() -> dict[str, dict]:
    """Load manifest.json and build a lookup by filename."""
    manifest_path = TEST_DATA_ROOT / "manifest.json"
    if not manifest_path.exists():
        return {}
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    lookup: dict[str, dict] = {}
    for entry in manifest.get("emails", []):
        lookup[entry["filename"]] = entry
    for category_list in manifest.get("pdfs", {}).values():
        for entry in category_list:
            lookup[entry["filename"]] = entry
    return lookup


async def process_single_document(
    processor: DocumentProcessor,
    file_path: Path,
    manifest_lookup: dict[str, dict],
) -> DocumentResult:
    """Process a single document and return its result."""
    relative_name = str(file_path.relative_to(TEST_DATA_ROOT)).replace("\\", "/")
    start_iso = datetime.now(timezone.utc).isoformat()
    t0 = time.perf_counter()

    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            raise ValueError("Document is empty")

        request = ProcessDocumentRequest(document=text, filename=file_path.name)
        response = await processor.process(request)

        elapsed_ms = (time.perf_counter() - t0) * 1000
        end_iso = datetime.now(timezone.utc).isoformat()

        primary_cat = response.classification.category
        all_cats = [c.category for c in response.classification_output.categories]
        confidence = response.classification.confidence

        return DocumentResult(
            filename=relative_name,
            start_time=start_iso,
            end_time=end_iso,
            processing_duration_ms=round(elapsed_ms, 2),
            classification=primary_cat,
            all_categories=all_cats,
            confidence=round(confidence, 4),
            success=True,
        )

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        end_iso = datetime.now(timezone.utc).isoformat()
        logger.error("Failed to process %s: %s", relative_name, exc)
        return DocumentResult(
            filename=relative_name,
            start_time=start_iso,
            end_time=end_iso,
            processing_duration_ms=round(elapsed_ms, 2),
            classification="ERROR",
            all_categories=[],
            confidence=0.0,
            success=False,
            error=str(exc),
        )


async def run_batch_processing(
    max_documents: Optional[int] = None,
) -> BatchReport:
    """Process all (or up to max_documents) synthetic documents and return a report."""
    processor = DocumentProcessor()
    files = _collect_text_files()
    manifest_lookup = _parse_manifest()

    if max_documents:
        files = files[:max_documents]

    batch_start = datetime.now(timezone.utc).isoformat()
    t_batch_start = time.perf_counter()

    results: list[DocumentResult] = []
    for file_path in files:
        result = await process_single_document(processor, file_path, manifest_lookup)
        results.append(result)
        logger.info(
            "[%d/%d] %s -> %s (%.1fms)",
            len(results),
            len(files),
            result.filename,
            result.classification,
            result.processing_duration_ms,
        )

    t_batch_end = time.perf_counter()
    batch_end = datetime.now(timezone.utc).isoformat()
    total_ms = (t_batch_end - t_batch_start) * 1000

    successful = [r for r in results if r.success]
    failed = [r for r in results if not r.success]
    durations = [r.processing_duration_ms for r in results]

    report = BatchReport(
        total_documents=len(results),
        successful_documents=len(successful),
        failed_documents=len(failed),
        average_processing_time_ms=round(sum(durations) / len(durations), 2) if durations else 0,
        minimum_processing_time_ms=round(min(durations), 2) if durations else 0,
        maximum_processing_time_ms=round(max(durations), 2) if durations else 0,
        processing_start_time=batch_start,
        processing_end_time=batch_end,
        total_processing_time_ms=round(total_ms, 2),
        documents=results,
    )

    return report


def save_report(report: BatchReport, output_path: Optional[Path] = None) -> Path:
    """Serialize the batch report to JSON and save it."""
    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / REPORT_FILENAME

    data = {
        "total_documents": report.total_documents,
        "successful_documents": report.successful_documents,
        "failed_documents": report.failed_documents,
        "average_processing_time_ms": report.average_processing_time_ms,
        "minimum_processing_time_ms": report.minimum_processing_time_ms,
        "maximum_processing_time_ms": report.maximum_processing_time_ms,
        "processing_start_time": report.processing_start_time,
        "processing_end_time": report.processing_end_time,
        "total_processing_time_ms": report.total_processing_time_ms,
        "documents": [
            {
                "filename": d.filename,
                "start_time": d.start_time,
                "end_time": d.end_time,
                "processing_duration_ms": d.processing_duration_ms,
                "classification": d.classification,
                "all_categories": d.all_categories,
                "confidence": d.confidence,
                "success": d.success,
                "error": d.error,
            }
            for d in report.documents
        ],
    }

    output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Report saved to %s", output_path)
    return output_path
