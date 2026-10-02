"""
SmartCampus AI — Email Service

Secure, abstracted email service that:
  1. Uses a provider abstraction (swap Gmail for any provider without changing business logic)
  2. Logs every send attempt to the email_logs table
  3. Never fails complaint operations — email errors are caught and logged
  4. Supports background task execution so API requests don't wait on SMTP
  5. Never exposes SMTP credentials in logs, responses, or error messages

Provider hierarchy:
  EmailProvider (abstract)  ←  GmailSMTPProvider (concrete)
  EmailService             →   uses whichever provider is configured

Security:
  - SMTP credentials are read from Settings (env vars only)
  - Settings fields use repr=False — credentials never appear in repr/str
  - Failure logs sanitize error messages to remove any credential fragments
  - send_email() catches ALL exceptions to protect calling code
"""

from __future__ import annotations

import logging
import re
import smtplib
import ssl
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.email_log import EmailLog
from app.services.email_templates import (
    EmailContent,
    complaint_submitted_email,
    complaint_assigned_email,
    status_update_email,
    staff_response_email,
    information_request_email,
    escalation_email,
    resolution_submitted_email,
    feedback_request_email,
)

logger = logging.getLogger("smartcampus.email")

# Maximum retries for transient failures
MAX_RETRIES = 3


# ════════════════════════════════════════════════════════════
# PROVIDER ABSTRACTION
# ════════════════════════════════════════════════════════════

class EmailProvider(ABC):
    """
    Abstract base class for email delivery providers.
    Swap the concrete implementation to change from Gmail to
    SendGrid, SES, Mailgun, etc. without touching business logic.
    """

    @abstractmethod
    def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        from_email: str,
        from_name: str,
    ) -> bool:
        """
        Send a single email. Returns True on success, raises on failure.
        Implementations must NEVER log credentials.
        """
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check whether this provider has valid configuration."""
        ...


class GmailSMTPProvider(EmailProvider):
    """
    Gmail SMTP provider using STARTTLS on port 587.
    Requires a Gmail App Password (not the account password).
    Credentials are read from Settings and never stored in this class.
    """

    def __init__(self, settings: Settings):
        self._settings = settings

    def is_configured(self) -> bool:
        return self._settings.is_email_configured

    def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        from_email: str,
        from_name: str,
    ) -> bool:
        """Send via Gmail SMTP with STARTTLS. Raises on failure."""
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["X-Mailer"] = "SmartCampus AI Notification Service"

        # Attach HTML body
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Plain-text fallback
        plain = f"{subject}\n\nView this email in HTML for full formatting.\n— SmartCampus AI"
        msg.attach(MIMEText(plain, "plain", "utf-8"))

        context = ssl.create_default_context()

        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            # Credentials read from settings — never logged
            server.login(self._settings.smtp_username, self._settings.smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())

        return True


# ════════════════════════════════════════════════════════════
# EMAIL SERVICE
# ════════════════════════════════════════════════════════════

def _sanitize_error(error: Exception) -> str:
    """
    Strip any potential credential fragments from error messages
    before they are logged or stored.
    """
    msg = str(error)
    # Remove anything that looks like a password or token
    msg = re.sub(r'(password|passwd|pwd|token|secret|key)\s*[:=]\s*\S+',
                 r'\1=***REDACTED***', msg, flags=re.IGNORECASE)
    # Remove base64 auth strings
    msg = re.sub(r'[A-Za-z0-9+/]{20,}={0,2}', '***REDACTED***', msg)
    return msg[:500]  # Cap length


class EmailService:
    """
    High-level email service for SmartCampus AI.

    Usage:
        service = EmailService(db_session)
        success = service.send_complaint_submitted_email(...)

    Key design decisions:
      - Every send attempt is logged to email_logs
      - Failures never propagate — callers always get True/False
      - Retry logic for transient SMTP errors
      - Provider can be swapped via constructor injection
    """

    def __init__(
        self,
        db: Session,
        provider: Optional[EmailProvider] = None,
        settings: Optional[Settings] = None,
    ):
        self._db = db
        self._settings = settings or get_settings()
        self._provider = provider or GmailSMTPProvider(self._settings)

    # ────────────────────────────────────────────────────────
    # Core send method
    # ────────────────────────────────────────────────────────

    def send_email(
        self,
        to_email: str,
        content: EmailContent,
        event_type: str,
        complaint_id: Optional[str] = None,
    ) -> bool:
        """
        Send an email and log the result.

        Returns True on success, False on failure.
        NEVER raises — complaint operations must not break because of email.
        """
        # Create log entry first (status = 'pending')
        log_entry = EmailLog(
            recipient=to_email,
            event_type=event_type,
            complaint_id=complaint_id,
            subject=content.subject,
            status="pending",
            retry_count=0,
        )
        self._db.add(log_entry)
        self._db.commit()
        self._db.refresh(log_entry)

        # Check if email is actually configured
        if not self._provider.is_configured():
            log_entry.status = "skipped"
            log_entry.failure_reason = "Email is not configured (EMAIL_ENABLED=false or missing SMTP credentials)"
            self._db.commit()
            logger.info(
                "Email skipped (not configured): event=%s, recipient=%s, complaint=%s",
                event_type, to_email, complaint_id,
            )
            return False

        # Attempt delivery with retries
        last_error = ""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                self._provider.send(
                    to_email=to_email,
                    subject=content.subject,
                    html_body=content.html_body,
                    from_email=self._settings.email_from,
                    from_name=self._settings.email_from_name,
                )
                # Success
                log_entry.status = "sent"
                log_entry.sent_at = datetime.now(timezone.utc)
                log_entry.retry_count = attempt - 1
                self._db.commit()
                logger.info(
                    "Email sent: event=%s, recipient=%s, complaint=%s, attempt=%d",
                    event_type, to_email, complaint_id, attempt,
                )
                return True

            except smtplib.SMTPAuthenticationError:
                # Auth errors won't be fixed by retrying
                last_error = "SMTP authentication failed — check APP_PASSWORD configuration"
                logger.error(
                    "SMTP auth error (no retry): event=%s, recipient=%s",
                    event_type, to_email,
                )
                break

            except (smtplib.SMTPException, OSError, TimeoutError) as exc:
                last_error = _sanitize_error(exc)
                logger.warning(
                    "Email attempt %d/%d failed: event=%s, recipient=%s, error=%s",
                    attempt, MAX_RETRIES, event_type, to_email, last_error,
                )

            except Exception as exc:
                # Catch absolutely everything — emails must never crash the app
                last_error = _sanitize_error(exc)
                logger.error(
                    "Unexpected email error: event=%s, recipient=%s, error=%s",
                    event_type, to_email, last_error,
                )
                break

        # All attempts failed
        log_entry.status = "failed"
        log_entry.failure_reason = last_error
        log_entry.retry_count = min(MAX_RETRIES, log_entry.retry_count + 1)
        self._db.commit()
        return False

    # ────────────────────────────────────────────────────────
    # Event-specific send methods
    # ────────────────────────────────────────────────────────

    def send_complaint_submitted_email(
        self,
        to_email: str,
        student_name: str,
        complaint_id: str,
        category: str,
        summary: str,
        status: str,
        priority: str,
        submitted_at: str,
        view_url: str = "#",
    ) -> bool:
        """Notify student that their complaint was submitted."""
        content = complaint_submitted_email(
            student_name=student_name,
            complaint_id=complaint_id,
            category=category,
            summary=summary,
            status=status,
            priority=priority,
            submitted_at=submitted_at,
            view_url=view_url,
        )
        return self.send_email(to_email, content, "complaint_submitted", complaint_id)

    def send_complaint_assigned_email(
        self,
        to_email: str,
        recipient_name: str,
        complaint_id: str,
        title: str,
        category: str,
        priority: str,
        assigned_to: str,
        department: str,
        is_staff: bool,
        view_url: str = "#",
    ) -> bool:
        """Notify student/staff that a complaint was assigned."""
        content = complaint_assigned_email(
            recipient_name=recipient_name,
            complaint_id=complaint_id,
            title=title,
            category=category,
            priority=priority,
            assigned_to=assigned_to,
            department=department,
            is_staff=is_staff,
            view_url=view_url,
        )
        return self.send_email(to_email, content, "complaint_assigned", complaint_id)

    def send_status_update_email(
        self,
        to_email: str,
        student_name: str,
        complaint_id: str,
        title: str,
        old_status: str,
        new_status: str,
        update_note: str = "",
        view_url: str = "#",
    ) -> bool:
        """Notify student of a complaint status change."""
        content = status_update_email(
            student_name=student_name,
            complaint_id=complaint_id,
            title=title,
            old_status=old_status,
            new_status=new_status,
            update_note=update_note,
            view_url=view_url,
        )
        return self.send_email(to_email, content, "status_update", complaint_id)

    def send_staff_response_email(
        self,
        to_email: str,
        student_name: str,
        complaint_id: str,
        title: str,
        staff_name: str,
        message: str,
        view_url: str = "#",
    ) -> bool:
        """Notify student that staff has responded."""
        content = staff_response_email(
            student_name=student_name,
            complaint_id=complaint_id,
            title=title,
            staff_name=staff_name,
            message=message,
            view_url=view_url,
        )
        return self.send_email(to_email, content, "staff_response", complaint_id)

    def send_information_request_email(
        self,
        to_email: str,
        student_name: str,
        complaint_id: str,
        title: str,
        staff_name: str,
        request_message: str,
        view_url: str = "#",
    ) -> bool:
        """Notify student that additional information is needed."""
        content = information_request_email(
            student_name=student_name,
            complaint_id=complaint_id,
            title=title,
            staff_name=staff_name,
            request_message=request_message,
            view_url=view_url,
        )
        return self.send_email(to_email, content, "information_request", complaint_id)

    def send_escalation_email(
        self,
        to_email: str,
        recipient_name: str,
        complaint_id: str,
        title: str,
        category: str,
        priority: str,
        escalated_by: str,
        reason: str = "",
        view_url: str = "#",
    ) -> bool:
        """Notify admin/senior staff of an escalated complaint."""
        content = escalation_email(
            recipient_name=recipient_name,
            complaint_id=complaint_id,
            title=title,
            category=category,
            priority=priority,
            escalated_by=escalated_by,
            reason=reason,
            view_url=view_url,
        )
        return self.send_email(to_email, content, "escalation", complaint_id)

    def send_resolution_submitted_email(
        self,
        to_email: str,
        student_name: str,
        complaint_id: str,
        title: str,
        resolution_summary: str,
        resolved_at: str,
        feedback_url: str = "#",
        view_url: str = "#",
    ) -> bool:
        """Notify student that their complaint has been resolved."""
        content = resolution_submitted_email(
            student_name=student_name,
            complaint_id=complaint_id,
            title=title,
            resolution_summary=resolution_summary,
            resolved_at=resolved_at,
            feedback_url=feedback_url,
            view_url=view_url,
        )
        return self.send_email(to_email, content, "resolution_submitted", complaint_id)

    def send_feedback_request_email(
        self,
        to_email: str,
        student_name: str,
        complaint_id: str,
        title: str,
        resolved_by: str,
        feedback_url: str = "#",
    ) -> bool:
        """Request the student to rate their resolution experience."""
        content = feedback_request_email(
            student_name=student_name,
            complaint_id=complaint_id,
            title=title,
            resolved_by=resolved_by,
            feedback_url=feedback_url,
        )
        return self.send_email(to_email, content, "feedback_request", complaint_id)

    # ────────────────────────────────────────────────────────
    # Utility methods
    # ────────────────────────────────────────────────────────

    def get_email_logs(
        self,
        complaint_id: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[EmailLog]:
        """Query email logs with optional filters."""
        query = self._db.query(EmailLog)
        if complaint_id:
            query = query.filter(EmailLog.complaint_id == complaint_id)
        if event_type:
            query = query.filter(EmailLog.event_type == event_type)
        if status:
            query = query.filter(EmailLog.status == status)
        return query.order_by(EmailLog.created_at.desc()).limit(limit).all()

    def retry_failed(self, log_id: int) -> bool:
        """
        Retry a previously failed email by its log ID.
        Returns True if the retry succeeded.
        """
        log_entry = self._db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if not log_entry or log_entry.status != "failed":
            return False

        # Look up the original template data — for retry, we resend with
        # a simple notification since we don't store the full HTML body
        content = EmailContent(
            subject=f"[Retry] {log_entry.subject}",
            html_body=f"<p>This is a retry of a previously failed notification for {log_entry.complaint_id}.</p>",
        )

        # Attempt resend
        try:
            if self._provider.is_configured():
                self._provider.send(
                    to_email=log_entry.recipient,
                    subject=content.subject,
                    html_body=content.html_body,
                    from_email=self._settings.email_from,
                    from_name=self._settings.email_from_name,
                )
                log_entry.status = "sent"
                log_entry.sent_at = datetime.now(timezone.utc)
                log_entry.retry_count += 1
                self._db.commit()
                return True
        except Exception as exc:
            log_entry.failure_reason = _sanitize_error(exc)
            log_entry.retry_count += 1
            self._db.commit()

        return False
