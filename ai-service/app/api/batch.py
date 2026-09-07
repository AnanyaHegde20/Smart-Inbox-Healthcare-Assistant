from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.batch_processor import run_batch_processing, save_report

router = APIRouter()


class BatchProcessRequest(BaseModel):
    max_documents: int | None = None


class BatchProcessResponse(BaseModel):
    message: str
    total_documents: int
    successful_documents: int
    failed_documents: int
    average_processing_time_ms: float
    report_path: str


@router.post("/batch-process", response_model=BatchProcessResponse)
async def batch_process_documents(request: BatchProcessRequest | None = None):
    """Process all synthetic documents from test-data/ and generate a report."""
    try:
        max_docs = request.max_documents if request else None
        report = await run_batch_processing(max_documents=max_docs)
        path = save_report(report)
        return BatchProcessResponse(
            message=f"Batch processing completed. {report.successful_documents}/{report.total_documents} documents processed successfully.",
            total_documents=report.total_documents,
            successful_documents=report.successful_documents,
            failed_documents=report.failed_documents,
            average_processing_time_ms=report.average_processing_time_ms,
            report_path=str(path),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
