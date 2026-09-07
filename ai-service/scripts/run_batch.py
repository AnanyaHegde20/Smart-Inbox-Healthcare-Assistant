"""
Standalone batch processing script.
Processes all synthetic documents from test-data/ and generates a report.

Usage:
    python scripts/run_batch.py [--max N]

Output:
    sample-output/batch-processing-report.json
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.batch_processor import run_batch_processing, save_report


async def main():
    max_docs = None
    if len(sys.argv) > 2 and sys.argv[1] == "--max":
        max_docs = int(sys.argv[2])

    print(f"Starting batch processing{' (max: ' + str(max_docs) + ')' if max_docs else ''}...")
    report = await run_batch_processing(max_documents=max_docs)
    path = save_report(report)

    print(f"\n{'=' * 60}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Total documents:    {report.total_documents}")
    print(f"Successful:         {report.successful_documents}")
    print(f"Failed:             {report.failed_documents}")
    print(f"Avg time:           {report.average_processing_time_ms:.1f}ms")
    print(f"Min time:           {report.minimum_processing_time_ms:.1f}ms")
    print(f"Max time:           {report.maximum_processing_time_ms:.1f}ms")
    print(f"Total time:         {report.total_processing_time_ms:.1f}ms")
    print(f"Report saved to:    {path}")
    print(f"{'=' * 60}")

    print(f"\nPer-document results:")
    print(f"{'Filename':<55} {'Status':<10} {'Category':<20} {'Conf':<6} {'Time(ms)':<10}")
    print("-" * 101)
    for doc in report.documents:
        status = "OK" if doc.success else "FAIL"
        print(f"{doc.filename:<55} {status:<10} {doc.classification:<20} {doc.confidence:<6.2f} {doc.processing_duration_ms:<10.1f}")


if __name__ == "__main__":
    asyncio.run(main())
