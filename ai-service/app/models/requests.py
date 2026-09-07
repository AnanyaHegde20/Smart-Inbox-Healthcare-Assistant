from pydantic import BaseModel, Field
from typing import Optional


class EmailMetadata(BaseModel):
    """Optional email metadata associated with the document."""

    message_id: Optional[str] = Field(None, description="Email message ID")
    sender: Optional[str] = Field(None, description="Sender email address")
    recipients: Optional[list[str]] = Field(None, description="Recipient email addresses")
    subject: Optional[str] = Field(None, description="Email subject line")
    sent_at: Optional[str] = Field(None, description="ISO 8601 timestamp of when email was sent")
    thread_id: Optional[str] = Field(None, description="Email thread/conversation ID")


class ProcessDocumentRequest(BaseModel):
    """Request payload for document processing."""

    document: str = Field(
        ...,
        min_length=1,
        description="Raw document content (text, base64-encoded file, or HTML)",
    )
    filename: str = Field(
        ...,
        min_length=1,
        description="Original filename with extension (e.g. report.pdf)",
    )
    email_metadata: Optional[EmailMetadata] = Field(
        None,
        description="Optional email context if document was attached to an email",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document": "Patient discharge summary for John Doe...",
                    "filename": "discharge_summary.pdf",
                    "email_metadata": {
                        "sender": "dr.smith@hospital.org",
                        "subject": "Patient Discharge - John Doe",
                    },
                }
            ]
        }
    }
