"""
SmartCampus AI — Email API Routes

Endpoints for:
  - Checking email configuration status
  - Sending test emails
  - Viewing email logs
  - Retrying failed emails

Security:
  - Config status endpoint returns BOOLEAN flags, never actual credentials
  - Test endpoints use BackgroundTasks so API responses don't wait for SMTP
  - No endpoint ever returns SMTP_PASSWORD or any secret
"""

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings, Settings
from app.db.database import get_db
from app.schemas.email import (
    SendTestEmailRequest,
    RetryEmailRequest,
    EmailLogResponse,
    EmailStatusResponse,
    EmailConfigStatus,
)
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/email", tags=["Email"])


def _get_email_service(db: Session = Depends(get_db)) -> EmailService:
    return EmailService(db)


# ────────────────────────────────────────────────────────────
# Configuration status (no secrets exposed)
# ────────────────────────────────────────────────────────────

@router.get("/config-status", response_model=EmailConfigStatus)
def get_email_config_status(settings: Settings = Depends(get_settings)):
    """
    Returns whether email is configured.
    NEVER returns actual credentials — only boolean flags.
    """
    return EmailConfigStatus(
        email_enabled=settings.email_enabled,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        has_username=bool(settings.smtp_username),
        has_password=bool(settings.smtp_password),
        from_address_configured=bool(settings.email_from),
    )


# ────────────────────────────────────────────────────────────
# Test email sending (uses BackgroundTasks)
# ────────────────────────────────────────────────────────────

def _send_test_email_task(
    to_email: str,
    event_type: str,
    db: Session,
):
    """Background task that sends a test email."""
    service = EmailService(db)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Map event types to test method calls
    test_methods = {
        "complaint_submitted": lambda: service.send_complaint_submitted_email(
            to_email=to_email,
            student_name="Test Student",
            complaint_id="CMP-TEST-001",
            category="Electrical",
            summary="Test: Power outage in Block C Room 304 with burning smell from switchboard.",
            status="Submitted",
            priority="Critical",
            submitted_at=now,
            view_url="#",
        ),
        "complaint_assigned": lambda: service.send_complaint_assigned_email(
            to_email=to_email,
            recipient_name="Test Recipient",
            complaint_id="CMP-TEST-001",
            title="No power in Block C Room 304",
            category="Electrical",
            priority="Critical",
            assigned_to="Rahul Verma",
            department="Electrical Maintenance",
            is_staff=False,
            view_url="#",
        ),
        "status_update": lambda: service.send_status_update_email(
            to_email=to_email,
            student_name="Test Student",
            complaint_id="CMP-TEST-001",
            title="No power in Block C Room 304",
            old_status="Assigned",
            new_status="In Progress",
            update_note="Technician dispatched. Switchboard isolated, replacement in progress.",
            view_url="#",
        ),
        "staff_response": lambda: service.send_staff_response_email(
            to_email=to_email,
            student_name="Test Student",
            complaint_id="CMP-TEST-001",
            title="No power in Block C Room 304",
            staff_name="Rahul Verma",
            message="Hi, our team has started work on-site and isolated the issue. Expected resolution: ~6 hours.",
            view_url="#",
        ),
        "information_request": lambda: service.send_information_request_email(
            to_email=to_email,
            student_name="Test Student",
            complaint_id="CMP-TEST-001",
            title="No power in Block C Room 304",
            staff_name="Rahul Verma",
            request_message="Could you please confirm which switchboard is affected — the one near the door or near the window? A photo would help.",
            view_url="#",
        ),
        "escalation": lambda: service.send_escalation_email(
            to_email=to_email,
            recipient_name="Dr. Meera Nair",
            complaint_id="CMP-TEST-001",
            title="No power in Block C Room 304",
            category="Electrical",
            priority="Critical",
            escalated_by="Rahul Verma",
            reason="Burning smell from switchboard indicates potential fire risk. Needs immediate admin attention.",
            view_url="#",
        ),
        "resolution_submitted": lambda: service.send_resolution_submitted_email(
            to_email=to_email,
            student_name="Test Student",
            complaint_id="CMP-TEST-001",
            title="No power in Block C Room 304",
            resolution_summary="Faulty MCB replaced. Full wiring inspection completed. Power restored and tested safely.",
            resolved_at=now,
            feedback_url="#",
            view_url="#",
        ),
        "feedback_request": lambda: service.send_feedback_request_email(
            to_email=to_email,
            student_name="Test Student",
            complaint_id="CMP-TEST-001",
            title="No power in Block C Room 304",
            resolved_by="Rahul Verma",
            feedback_url="#",
        ),
    }

    send_func = test_methods.get(event_type)
    if send_func:
        send_func()


@router.post("/test", response_model=EmailStatusResponse)
def send_test_email(
    request: SendTestEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Send a test email in the background.
    The API responds immediately; email delivery happens asynchronously.
    """
    valid_events = [
        "complaint_submitted", "complaint_assigned", "status_update",
        "staff_response", "information_request", "escalation",
        "resolution_submitted", "feedback_request",
    ]
    if request.event_type not in valid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event_type. Must be one of: {', '.join(valid_events)}",
        )

    if not settings.is_email_configured:
        return EmailStatusResponse(
            success=False,
            message="Email is not configured. Set SMTP credentials in .env and EMAIL_ENABLED=true.",
        )

    # Queue the email send as a background task
    background_tasks.add_task(_send_test_email_task, request.to_email, request.event_type, db)

    return EmailStatusResponse(
        success=True,
        message=f"Test email ({request.event_type}) queued for delivery to {request.to_email}.",
    )


# ────────────────────────────────────────────────────────────
# Email logs
# ────────────────────────────────────────────────────────────

@router.get("/logs", response_model=list[EmailLogResponse])
def get_email_logs(
    complaint_id: str | None = None,
    event_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    service: EmailService = Depends(_get_email_service),
):
    """
    Retrieve email delivery logs.
    Supports filtering by complaint_id, event_type, and status.
    """
    return service.get_email_logs(
        complaint_id=complaint_id,
        event_type=event_type,
        status=status,
        limit=min(limit, 200),
    )


# ────────────────────────────────────────────────────────────
# Retry failed emails
# ────────────────────────────────────────────────────────────

@router.post("/retry", response_model=EmailStatusResponse)
def retry_failed_email(
    request: RetryEmailRequest,
    service: EmailService = Depends(_get_email_service),
):
    """Retry a previously failed email by its log ID."""
    success = service.retry_failed(request.log_id)
    if success:
        return EmailStatusResponse(
            success=True,
            message=f"Email log #{request.log_id} retried successfully.",
            log_id=request.log_id,
        )
    return EmailStatusResponse(
        success=False,
        message=f"Retry failed for email log #{request.log_id}. Check logs for details.",
        log_id=request.log_id,
    )
