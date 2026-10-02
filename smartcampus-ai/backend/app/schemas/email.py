"""
SmartCampus AI — Email-related Pydantic Schemas

Used for API request/response validation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ── Request Schemas ──────────────────────────────────────

class SendTestEmailRequest(BaseModel):
    """Request body for the test email endpoint."""
    to_email: EmailStr
    event_type: str = Field(
        default="complaint_submitted",
        description="One of: complaint_submitted, complaint_assigned, status_update, "
                    "staff_response, information_request, escalation, resolution_submitted, feedback_request",
    )


class RetryEmailRequest(BaseModel):
    """Request to retry a specific failed email."""
    log_id: int


# ── Response Schemas ─────────────────────────────────────

class EmailLogResponse(BaseModel):
    """Email log entry — returned from the API."""
    id: int
    recipient: str
    event_type: str
    complaint_id: Optional[str] = None
    subject: str
    status: str
    failure_reason: Optional[str] = None
    retry_count: int
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmailStatusResponse(BaseModel):
    """Simple response for email operations."""
    success: bool
    message: str
    log_id: Optional[int] = None


class EmailConfigStatus(BaseModel):
    """
    Returns email configuration status WITHOUT exposing credentials.
    Only indicates whether email is configured, not what the credentials are.
    """
    email_enabled: bool
    smtp_host: str
    smtp_port: int
    has_username: bool  # True if SMTP_USERNAME is set, never the value itself
    has_password: bool  # True if SMTP_PASSWORD is set, never the value itself
    from_address_configured: bool  # True if EMAIL_FROM is set
