"""
SmartCampus AI — Email Service Tests

Tests for:
  1. All 8 email event types (template generation)
  2. SMTP failure handling
  3. Email logging
  4. Credential sanitization
  5. Retry logic
  6. Provider abstraction

Run with:
  cd backend
  python -m pytest tests/test_email.py -v

These tests use a mock provider — no real SMTP connection needed.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.core.config import Settings
from app.models.email_log import EmailLog
from app.services.email_service import (
    EmailService,
    EmailProvider,
    GmailSMTPProvider,
    _sanitize_error,
)
from app.services.email_templates import (
    complaint_submitted_email,
    complaint_assigned_email,
    status_update_email,
    staff_response_email,
    information_request_email,
    escalation_email,
    resolution_submitted_email,
    feedback_request_email,
)


# ── Test Database ────────────────────────────────────────

@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


# ── Mock Provider ────────────────────────────────────────

class MockEmailProvider(EmailProvider):
    """Test provider that tracks calls and can simulate failures."""

    def __init__(self, should_fail: bool = False, fail_message: str = "Test SMTP error"):
        self.calls: list[dict] = []
        self.should_fail = should_fail
        self.fail_message = fail_message
        self._configured = True

    def is_configured(self) -> bool:
        return self._configured

    def send(self, to_email, subject, html_body, from_email, from_name) -> bool:
        self.calls.append({
            "to": to_email,
            "subject": subject,
            "from": from_email,
            "from_name": from_name,
        })
        if self.should_fail:
            raise Exception(self.fail_message)
        return True


@pytest.fixture
def mock_provider():
    return MockEmailProvider()


@pytest.fixture
def failing_provider():
    return MockEmailProvider(should_fail=True)


@pytest.fixture
def test_settings():
    return Settings(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="test@test.com",
        smtp_password="test-app-password",
        email_from="test@test.com",
        email_from_name="SmartCampus AI",
        email_enabled=True,
    )


# ════════════════════════════════════════════════════════════
# TEST 1: Template generation for all 8 event types
# ════════════════════════════════════════════════════════════

class TestEmailTemplates:
    """Verify all email templates generate valid HTML with correct subjects."""

    def test_complaint_submitted_template(self):
        result = complaint_submitted_email(
            student_name="Aarav Sharma",
            complaint_id="CMP-2026-0142",
            category="Electrical",
            summary="Power outage in Block C Room 304 with burning smell.",
            status="Submitted",
            priority="Critical",
            submitted_at="2026-10-01 21:40 UTC",
        )
        assert "CMP-2026-0142" in result.subject
        assert "SmartCampus AI" in result.html_body
        assert "Aarav Sharma" in result.html_body
        assert "Electrical" in result.html_body
        assert "Critical" in result.html_body
        assert "Power outage" in result.html_body
        assert "</html>" in result.html_body

    def test_complaint_assigned_template_student(self):
        result = complaint_assigned_email(
            recipient_name="Aarav Sharma",
            complaint_id="CMP-2026-0142",
            title="No power in Block C Room 304",
            category="Electrical",
            priority="Critical",
            assigned_to="Rahul Verma",
            department="Electrical Maintenance",
            is_staff=False,
        )
        assert "Assigned" in result.subject
        assert "Rahul Verma" in result.html_body
        assert "Track Progress" in result.html_body

    def test_complaint_assigned_template_staff(self):
        result = complaint_assigned_email(
            recipient_name="Rahul Verma",
            complaint_id="CMP-2026-0142",
            title="No power in Block C Room 304",
            category="Electrical",
            priority="Critical",
            assigned_to="Rahul Verma",
            department="Electrical Maintenance",
            is_staff=True,
        )
        assert "assigned to you" in result.html_body
        assert "Review & Take Action" in result.html_body

    def test_status_update_template(self):
        result = status_update_email(
            student_name="Aarav",
            complaint_id="CMP-2026-0142",
            title="No power in Block C",
            old_status="Assigned",
            new_status="In Progress",
            update_note="Technician dispatched.",
        )
        assert "Assigned" in result.html_body
        assert "In Progress" in result.html_body
        assert "Technician dispatched" in result.html_body

    def test_staff_response_template(self):
        result = staff_response_email(
            student_name="Aarav",
            complaint_id="CMP-2026-0142",
            title="No power in Block C",
            staff_name="Rahul Verma",
            message="We've started working on-site.",
        )
        assert "Rahul Verma" in result.html_body
        assert "started working" in result.html_body

    def test_information_request_template(self):
        result = information_request_email(
            student_name="Aarav",
            complaint_id="CMP-2026-0142",
            title="No power in Block C",
            staff_name="Rahul Verma",
            request_message="Could you send a photo of the switchboard?",
        )
        assert "Additional information" in result.html_body
        assert "photo of the switchboard" in result.html_body

    def test_escalation_template(self):
        result = escalation_email(
            recipient_name="Dr. Meera Nair",
            complaint_id="CMP-2026-0142",
            title="No power in Block C",
            category="Electrical",
            priority="Critical",
            escalated_by="Rahul Verma",
            reason="Burning smell indicates fire risk.",
        )
        assert "🚨" in result.subject
        assert "Escalated" in result.html_body
        assert "fire risk" in result.html_body

    def test_resolution_submitted_template(self):
        result = resolution_submitted_email(
            student_name="Aarav",
            complaint_id="CMP-2026-0142",
            title="No power in Block C",
            resolution_summary="MCB replaced and wiring inspected.",
            resolved_at="2026-10-02 14:30 UTC",
        )
        assert "resolved" in result.html_body.lower()
        assert "MCB replaced" in result.html_body
        assert "Verify Resolution" in result.html_body

    def test_feedback_request_template(self):
        result = feedback_request_email(
            student_name="Aarav",
            complaint_id="CMP-2026-0142",
            title="No power in Block C",
            resolved_by="Rahul Verma",
        )
        assert "★" in result.html_body
        assert "Submit Feedback" in result.html_body


# ════════════════════════════════════════════════════════════
# TEST 2: Email sending (success path)
# ════════════════════════════════════════════════════════════

class TestEmailServiceSuccess:
    """Test that emails are sent and logged correctly."""

    def test_complaint_submitted_email(self, db_session, mock_provider, test_settings):
        service = EmailService(db_session, provider=mock_provider, settings=test_settings)
        result = service.send_complaint_submitted_email(
            to_email="student@test.edu",
            student_name="Aarav",
            complaint_id="CMP-TEST-001",
            category="Electrical",
            summary="Power outage test.",
            status="Submitted",
            priority="High",
            submitted_at="2026-10-01",
        )
        assert result is True
        assert len(mock_provider.calls) == 1
        assert mock_provider.calls[0]["to"] == "student@test.edu"

        # Verify log entry
        logs = db_session.query(EmailLog).all()
        assert len(logs) == 1
        assert logs[0].status == "sent"
        assert logs[0].event_type == "complaint_submitted"
        assert logs[0].complaint_id == "CMP-TEST-001"

    def test_all_event_types_send(self, db_session, mock_provider, test_settings):
        """Verify every event type sends successfully."""
        service = EmailService(db_session, provider=mock_provider, settings=test_settings)

        service.send_complaint_submitted_email(
            "a@t.edu", "A", "C1", "E", "S", "Sub", "H", "now")
        service.send_complaint_assigned_email(
            "a@t.edu", "A", "C2", "T", "E", "H", "R", "D", False)
        service.send_status_update_email(
            "a@t.edu", "A", "C3", "T", "Old", "New")
        service.send_staff_response_email(
            "a@t.edu", "A", "C4", "T", "S", "M")
        service.send_information_request_email(
            "a@t.edu", "A", "C5", "T", "S", "Q")
        service.send_escalation_email(
            "a@t.edu", "A", "C6", "T", "E", "H", "S")
        service.send_resolution_submitted_email(
            "a@t.edu", "A", "C7", "T", "Fixed", "now")
        service.send_feedback_request_email(
            "a@t.edu", "A", "C8", "T", "R")

        assert len(mock_provider.calls) == 8
        logs = db_session.query(EmailLog).filter(EmailLog.status == "sent").count()
        assert logs == 8


# ════════════════════════════════════════════════════════════
# TEST 3: SMTP failure handling
# ════════════════════════════════════════════════════════════

class TestEmailServiceFailure:
    """Test that email failures are handled gracefully."""

    def test_failure_returns_false(self, db_session, failing_provider, test_settings):
        service = EmailService(db_session, provider=failing_provider, settings=test_settings)
        result = service.send_complaint_submitted_email(
            to_email="student@test.edu",
            student_name="Aarav",
            complaint_id="CMP-FAIL-001",
            category="Test",
            summary="Failure test.",
            status="Submitted",
            priority="Low",
            submitted_at="now",
        )
        # Must return False, NOT raise
        assert result is False

    def test_failure_logged(self, db_session, failing_provider, test_settings):
        service = EmailService(db_session, provider=failing_provider, settings=test_settings)
        service.send_complaint_submitted_email(
            "a@t.edu", "A", "CFAIL", "E", "S", "Sub", "H", "now")

        log = db_session.query(EmailLog).first()
        assert log.status == "failed"
        assert log.failure_reason is not None
        assert log.complaint_id == "CFAIL"

    def test_unconfigured_email_skipped(self, db_session):
        """When email is disabled, sends should be skipped, not fail."""
        settings = Settings(email_enabled=False, smtp_username="", smtp_password="")
        provider = MockEmailProvider()
        provider._configured = False
        service = EmailService(db_session, provider=provider, settings=settings)

        result = service.send_complaint_submitted_email(
            "a@t.edu", "A", "CSKIP", "E", "S", "Sub", "H", "now")

        assert result is False
        assert len(provider.calls) == 0
        log = db_session.query(EmailLog).first()
        assert log.status == "skipped"


# ════════════════════════════════════════════════════════════
# TEST 4: Credential sanitization
# ════════════════════════════════════════════════════════════

class TestCredentialSanitization:
    """Verify that no credentials leak into logs or error messages."""

    def test_sanitize_password_in_error(self):
        msg = _sanitize_error(Exception("AUTH failed for password=MyS3cretP@ss"))
        assert "MyS3cretP@ss" not in msg
        assert "REDACTED" in msg

    def test_sanitize_token_in_error(self):
        msg = _sanitize_error(Exception("token=abc123def456ghi789jkl012mno345"))
        assert "abc123def456" not in msg

    def test_sanitize_long_base64(self):
        b64 = "YWJjZGVmZ2hpamtsbW5vcHFyc3R1dnd4eXo="
        msg = _sanitize_error(Exception(f"Auth data: {b64}"))
        assert b64 not in msg

    def test_settings_repr_hides_secrets(self, test_settings):
        """Verify Settings.__repr__ doesn't expose smtp_password."""
        rep = repr(test_settings)
        assert "test-app-password" not in rep


# ════════════════════════════════════════════════════════════
# TEST 5: Email retry
# ════════════════════════════════════════════════════════════

class TestEmailRetry:

    def test_retry_failed_email(self, db_session, test_settings):
        """First fail, then retry with a working provider."""
        failing = MockEmailProvider(should_fail=True)
        service = EmailService(db_session, provider=failing, settings=test_settings)
        service.send_complaint_submitted_email(
            "a@t.edu", "A", "CRETRY", "E", "S", "Sub", "H", "now")

        log = db_session.query(EmailLog).first()
        assert log.status == "failed"

        # Swap to working provider and retry
        working = MockEmailProvider(should_fail=False)
        service2 = EmailService(db_session, provider=working, settings=test_settings)
        result = service2.retry_failed(log.id)
        assert result is True

        db_session.refresh(log)
        assert log.status == "sent"

    def test_retry_nonexistent_log(self, db_session, mock_provider, test_settings):
        service = EmailService(db_session, provider=mock_provider, settings=test_settings)
        result = service.retry_failed(99999)
        assert result is False


# ════════════════════════════════════════════════════════════
# TEST 6: Email log queries
# ════════════════════════════════════════════════════════════

class TestEmailLogs:

    def test_query_by_complaint_id(self, db_session, mock_provider, test_settings):
        service = EmailService(db_session, provider=mock_provider, settings=test_settings)
        service.send_complaint_submitted_email(
            "a@t.edu", "A", "C-LOG-1", "E", "S", "Sub", "H", "now")
        service.send_complaint_submitted_email(
            "b@t.edu", "B", "C-LOG-2", "E", "S", "Sub", "H", "now")

        logs = service.get_email_logs(complaint_id="C-LOG-1")
        assert len(logs) == 1
        assert logs[0].complaint_id == "C-LOG-1"

    def test_query_by_status(self, db_session, mock_provider, test_settings):
        service = EmailService(db_session, provider=mock_provider, settings=test_settings)
        service.send_complaint_submitted_email(
            "a@t.edu", "A", "C1", "E", "S", "Sub", "H", "now")

        sent = service.get_email_logs(status="sent")
        assert len(sent) == 1
        failed = service.get_email_logs(status="failed")
        assert len(failed) == 0
