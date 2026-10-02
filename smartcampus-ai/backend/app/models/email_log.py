"""
SmartCampus AI — Email Log Model

Records every email attempt for auditing and retry.
NEVER stores SMTP credentials — only delivery metadata.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from app.db.database import Base


class EmailLog(Base):
    """
    Audit trail for every email send attempt.

    Fields:
        recipient       — destination email address
        event_type      — e.g. complaint_submitted, status_update, escalation
        complaint_id    — associated complaint ID (nullable for system emails)
        subject         — email subject line
        status          — 'pending', 'sent', 'failed'
        failure_reason  — error message on failure (no credentials ever stored)
        retry_count     — number of retry attempts
        sent_at         — timestamp of successful delivery (or last attempt)
        created_at      — record creation timestamp
    """

    __tablename__ = "email_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    recipient = Column(String(255), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    complaint_id = Column(String(50), nullable=True, index=True)
    subject = Column(String(500), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending | sent | failed
    failure_reason = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<EmailLog(id={self.id}, recipient='{self.recipient}', "
            f"event='{self.event_type}', status='{self.status}')>"
        )
