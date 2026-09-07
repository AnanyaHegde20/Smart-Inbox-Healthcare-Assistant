from fastapi import APIRouter, HTTPException

from app.models.requests import ProcessDocumentRequest
from app.models.responses import ProcessDocumentResponse
from app.services import DocumentProcessor

router = APIRouter()

_processor = DocumentProcessor()


@router.post("/process-document", response_model=ProcessDocumentResponse)
async def process_document(request: ProcessDocumentRequest):
    """Accept a document and return extracted, classified, summarised results."""
    try:
        return await _processor.process(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
