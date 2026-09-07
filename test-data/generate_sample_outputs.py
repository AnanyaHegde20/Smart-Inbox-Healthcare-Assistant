#!/usr/bin/env python3
"""
Generate sample extracted JSON outputs for every test document.

Processes all emails (.txt) and PDFs through the DocumentProcessor
and saves the full ProcessDocumentResponse as individual JSON files.

Usage:
    python test-data/generate_sample_outputs.py
"""

import asyncio
import base64
import json
import sys
import time
from pathlib import Path

# Add ai-service to path
AI_SERVICE_DIR = Path(__file__).resolve().parent.parent / "ai-service"
sys.path.insert(0, str(AI_SERVICE_DIR))

from app.services.document_processor import DocumentProcessor
from app.models.requests import ProcessDocumentRequest

TEST_DATA_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = TEST_DATA_DIR / "sample-outputs"


def _collect_email_files() -> list[Path]:
    """Collect all .txt email files."""
    email_dir = TEST_DATA_DIR / "emails"
    return sorted(email_dir.glob("email-*.txt"))


def _collect_pdf_files() -> list[Path]:
    """Collect all .pdf files from test-data/pdfs/."""
    pdf_dir = TEST_DATA_DIR / "pdfs"
    return sorted(pdf_dir.rglob("*.pdf"))


async def process_text_file(
    processor: DocumentProcessor, file_path: Path
) -> dict:
    """Process a text file and return the full response as dict."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    request = ProcessDocumentRequest(document=text, filename=file_path.name)
    response = await processor.process(request)
    return response.model_dump()


async def process_pdf_file(
    processor: DocumentProcessor, file_path: Path
) -> dict:
    """Process a PDF file (base64-encoded) and return the full response as dict."""
    pdf_bytes = file_path.read_bytes()
    b64_content = base64.b64encode(pdf_bytes).decode("utf-8")
    request = ProcessDocumentRequest(document=b64_content, filename=file_path.name)
    response = await processor.process(request)
    return response.model_dump()


def _make_output_name(file_path: Path, base_dir: Path) -> str:
    """Create a clean output filename from the source file path."""
    rel = file_path.relative_to(base_dir)
    # Replace path separators with underscores, keep extension
    name = str(rel).replace("\\", "_").replace("/", "_")
    # Remove .txt extension for emails, keep .pdf name
    if name.endswith(".txt"):
        name = name[:-4]
    elif name.endswith(".pdf"):
        name = name[:-4]  # Remove .pdf, we'll add .json
    return name + ".json"


async def main():
    print("=" * 60)
    print("SAMPLE OUTPUT GENERATOR")
    print("Smart Inbox Assistant Healthcare")
    print("=" * 60)
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("ALL DATA IS SYNTHETIC.\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    processor = DocumentProcessor()

    # Collect all files
    email_files = _collect_email_files()
    pdf_files = _collect_pdf_files()
    all_files = [(f, "email") for f in email_files] + [(f, "pdf") for f in pdf_files]

    print(f"Found {len(email_files)} email files and {len(pdf_files)} PDF files")
    print(f"Total: {len(all_files)} documents to process\n")

    results_summary = []
    start_time = time.perf_counter()

    for i, (file_path, doc_type) in enumerate(all_files, 1):
        rel_name = file_path.relative_to(TEST_DATA_DIR)
        print(f"[{i}/{len(all_files)}] Processing {rel_name}...", end=" ", flush=True)

        try:
            t0 = time.perf_counter()
            if doc_type == "email":
                output_data = await process_text_file(processor, file_path)
            else:
                output_data = await process_pdf_file(processor, file_path)
            elapsed = (time.perf_counter() - t0) * 1000

            # Save JSON
            output_name = _make_output_name(file_path, TEST_DATA_DIR)
            output_path = OUTPUT_DIR / output_name
            output_path.write_text(
                json.dumps(output_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

            category = output_data.get("classification", {}).get("category", "?")
            confidence = output_data.get("classification", {}).get("confidence", 0)
            facts_count = len(output_data.get("extracted_facts", []))
            summary_sentences = 0
            if output_data.get("document_summary"):
                summary_sentences = output_data["document_summary"].get("total_sentences", 0)

            print(f"OK ({elapsed:.0f}ms) -> {category} ({confidence:.2f}) | {facts_count} facts | {summary_sentences} summary sentences")

            results_summary.append({
                "file": str(rel_name),
                "output": output_name,
                "category": category,
                "confidence": round(confidence, 4),
                "facts_count": facts_count,
                "summary_sentences": summary_sentences,
                "processing_ms": round(elapsed, 2),
                "success": True,
            })

        except Exception as exc:
            print(f"FAILED: {exc}")
            results_summary.append({
                "file": str(rel_name),
                "output": None,
                "category": "ERROR",
                "confidence": 0,
                "facts_count": 0,
                "summary_sentences": 0,
                "processing_ms": 0,
                "success": False,
                "error": str(exc),
            })

    total_elapsed = (time.perf_counter() - start_time) * 1000

    # Save summary index
    summary_index = {
        "description": "Sample extracted JSON outputs for all test documents",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_documents": len(all_files),
        "successful": sum(1 for r in results_summary if r["success"]),
        "failed": sum(1 for r in results_summary if not r["success"]),
        "total_processing_ms": round(total_elapsed, 2),
        "documents": results_summary,
    }
    index_path = OUTPUT_DIR / "_index.json"
    index_path.write_text(
        json.dumps(summary_index, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n{'=' * 60}")
    print(f"COMPLETE: {summary_index['successful']}/{len(all_files)} documents processed")
    print(f"Total time: {total_elapsed:.0f}ms")
    print(f"Outputs saved to: {OUTPUT_DIR}")
    print(f"Index file: {index_path}")
    print(f"{'=' * 60}")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
