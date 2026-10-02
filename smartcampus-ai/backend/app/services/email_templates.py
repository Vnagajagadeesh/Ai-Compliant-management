"""
SmartCampus AI — Professional HTML Email Templates

Branded, mobile-friendly email templates for all complaint lifecycle events.
Uses Jinja2-style f-string placeholders for dynamic content.

Branding:
  - Product: SmartCampus AI
  - Tagline: "Smarter Complaints. Faster Resolution. Better Campus."
  - Primary: #2563EB (blue)
  - Gradient: #2563EB → #7C3AED (blue→purple)
  - Text: #0F1F3D (navy)
  - Background: #F6F8FB (soft gray)
"""

from dataclasses import dataclass


# ────────────────────────────────────────────────────────────
# Status colors for badges
# ────────────────────────────────────────────────────────────
STATUS_COLORS: dict[str, tuple[str, str]] = {
    "Pending":               ("#64748B", "#F1F5F9"),
    "Submitted":             ("#64748B", "#F1F5F9"),
    "Under Review":          ("#D97706", "#FEF3C7"),
    "Assigned":              ("#6366F1", "#EEF2FF"),
    "In Progress":           ("#2563EB", "#DBEAFE"),
    "Resolution Submitted":  ("#0D9488", "#CCFBF1"),
    "Resolved":              ("#059669", "#D1FAE5"),
    "Closed":                ("#94A3B8", "#F1F5F9"),
    "Escalated":             ("#E11D48", "#FFE4E6"),
}

PRIORITY_COLORS: dict[str, tuple[str, str]] = {
    "Critical": ("#FFFFFF", "#E11D48"),
    "High":     ("#FFFFFF", "#EA580C"),
    "Medium":   ("#78350F", "#FDE68A"),
    "Low":      ("#475569", "#E2E8F0"),
}


# ────────────────────────────────────────────────────────────
# Base layout — wraps all email content
# ────────────────────────────────────────────────────────────
def _base_layout(title: str, body_html: str) -> str:
    """
    Master email template with SmartCampus AI branding.
    Mobile-friendly, professional SaaS styling.
    """
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — SmartCampus AI</title>
<!--[if mso]>
<noscript>
<xml>
<o:OfficeDocumentSettings>
<o:PixelsPerInch>96</o:PixelsPerInch>
</o:OfficeDocumentSettings>
</xml>
</noscript>
<![endif]-->
<style>
  body {{ margin: 0; padding: 0; background: #F6F8FB; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, Helvetica, Arial, sans-serif; color: #0F1F3D; -webkit-text-size-adjust: 100%; }}
  .container {{ max-width: 600px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #2563EB 0%, #4F46E5 45%, #7C3AED 100%); padding: 32px 40px; text-align: center; }}
  .header-logo {{ font-size: 22px; font-weight: 800; color: #FFFFFF; letter-spacing: -0.02em; }}
  .header-tagline {{ font-size: 12px; color: rgba(255,255,255,0.75); letter-spacing: 0.08em; text-transform: uppercase; margin-top: 4px; font-weight: 600; }}
  .body {{ background: #FFFFFF; padding: 40px; border-left: 1px solid #E6EBF3; border-right: 1px solid #E6EBF3; }}
  .title {{ font-size: 22px; font-weight: 800; color: #0F1F3D; line-height: 1.3; margin: 0 0 8px 0; letter-spacing: -0.02em; }}
  .subtitle {{ font-size: 14px; color: #64748B; line-height: 1.5; margin: 0 0 24px 0; }}
  .info-grid {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
  .info-grid td {{ padding: 10px 16px; font-size: 13px; border-bottom: 1px solid #F1F5F9; vertical-align: top; }}
  .info-label {{ font-weight: 700; color: #94A3B8; text-transform: uppercase; font-size: 10px; letter-spacing: 0.08em; width: 140px; }}
  .info-value {{ font-weight: 600; color: #0F1F3D; }}
  .status-badge {{ display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }}
  .priority-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; letter-spacing: 0.04em; }}
  .card {{ background: #F8FAFC; border: 1px solid #E6EBF3; border-radius: 12px; padding: 20px; margin: 16px 0; }}
  .ai-card {{ background: linear-gradient(135deg, #EFF6FF 0%, #F5F3FF 60%, #EFF6FF 100%); border: 1px solid #DBEAFE; border-radius: 12px; padding: 20px; margin: 16px 0; }}
  .ai-label {{ font-size: 11px; font-weight: 800; color: #2563EB; text-transform: uppercase; letter-spacing: 0.06em; }}
  .btn-primary {{ display: inline-block; padding: 14px 32px; background: linear-gradient(135deg, #2563EB, #4F46E5); color: #FFFFFF !important; font-size: 14px; font-weight: 700; text-decoration: none; border-radius: 12px; text-align: center; }}
  .btn-ghost {{ display: inline-block; padding: 12px 28px; border: 2px solid #E2E8F0; color: #0F1F3D !important; font-size: 13px; font-weight: 700; text-decoration: none; border-radius: 12px; text-align: center; }}
  .divider {{ height: 1px; background: #E6EBF3; margin: 24px 0; }}
  .footer {{ background: #0B152E; padding: 32px 40px; text-align: center; }}
  .footer-text {{ font-size: 12px; color: #94A3B8; line-height: 1.6; }}
  .footer-brand {{ font-size: 15px; font-weight: 800; color: #FFFFFF; margin-bottom: 8px; }}
  .footer-link {{ color: #60A5FA; text-decoration: none; }}
  @media only screen and (max-width: 640px) {{
    .body {{ padding: 24px 20px !important; }}
    .header {{ padding: 24px 20px !important; }}
    .footer {{ padding: 24px 20px !important; }}
    .title {{ font-size: 20px !important; }}
  }}
</style>
</head>
<body>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#F6F8FB;">
<tr><td style="padding: 24px 16px;">
<div class="container">

  <!-- Header -->
  <div class="header" style="border-radius: 16px 16px 0 0;">
    <div class="header-logo">SmartCampus AI</div>
    <div class="header-tagline">Smarter Complaints &bull; Faster Resolution &bull; Better Campus</div>
  </div>

  <!-- Body -->
  <div class="body">
    {body_html}
  </div>

  <!-- Footer -->
  <div class="footer" style="border-radius: 0 0 16px 16px;">
    <div class="footer-brand">SmartCampus AI</div>
    <div class="footer-text">
      Smarter Complaints. Faster Resolution. Better Campus.<br>
      <a href="mailto:nagajagadeeshvakkalagadda@gmail.com" class="footer-link">Contact Support</a>
      &nbsp;&bull;&nbsp; <a href="#" class="footer-link">Privacy Policy</a>
      &nbsp;&bull;&nbsp; <a href="#" class="footer-link">Terms</a><br><br>
      &copy; 2026 SmartCampus AI. All rights reserved.<br>
      <span style="font-size:11px; color:#64748B;">You're receiving this because you're registered on SmartCampus AI.</span>
    </div>
  </div>

</div>
</td></tr>
</table>
</body>
</html>"""


# ────────────────────────────────────────────────────────────
# Helper: Status badge HTML
# ────────────────────────────────────────────────────────────
def _status_badge(status: str) -> str:
    fg, bg = STATUS_COLORS.get(status, ("#64748B", "#F1F5F9"))
    return f'<span class="status-badge" style="color:{fg};background:{bg};">{status}</span>'


def _priority_badge(priority: str) -> str:
    fg, bg = PRIORITY_COLORS.get(priority, ("#475569", "#E2E8F0"))
    return f'<span class="priority-badge" style="color:{fg};background:{bg};">{priority}</span>'


def _info_row(label: str, value: str) -> str:
    return f'<tr><td class="info-label">{label}</td><td class="info-value">{value}</td></tr>'


# ────────────────────────────────────────────────────────────
# Data class for email content
# ────────────────────────────────────────────────────────────
@dataclass
class EmailContent:
    subject: str
    html_body: str


# ================================================================
# EMAIL TEMPLATE BUILDERS
# ================================================================

def complaint_submitted_email(
    student_name: str,
    complaint_id: str,
    category: str,
    summary: str,
    status: str,
    priority: str,
    submitted_at: str,
    view_url: str = "#",
) -> EmailContent:
    """Email sent to student when their complaint is successfully submitted."""
    body = f"""\
    <h1 class="title">Your complaint has been submitted ✓</h1>
    <p class="subtitle">
      Hi {student_name}, your complaint has been received and AI is analyzing it now.
      We'll route it to the right team and keep you updated at every step.
    </p>

    <table class="info-grid">
      {_info_row("Complaint ID", f'<strong>{complaint_id}</strong>')}
      {_info_row("Category", category)}
      {_info_row("Priority", _priority_badge(priority))}
      {_info_row("Status", _status_badge(status))}
      {_info_row("Submitted", submitted_at)}
    </table>

    <div class="ai-card">
      <div class="ai-label">✦ AI Summary</div>
      <p style="margin:8px 0 0;font-size:13px;color:#334155;font-style:italic;">"{summary}"</p>
    </div>

    <div style="text-align:center; margin:28px 0 8px;">
      <a href="{view_url}" class="btn-primary">Track Your Complaint →</a>
    </div>
    <p style="text-align:center;font-size:12px;color:#94A3B8;margin-top:12px;">
      You'll receive updates at every status change.
    </p>"""
    return EmailContent(
        subject=f"[{complaint_id}] Complaint Submitted — {category}",
        html_body=_base_layout(f"Complaint Submitted — {complaint_id}", body),
    )


def complaint_assigned_email(
    recipient_name: str,
    complaint_id: str,
    title: str,
    category: str,
    priority: str,
    assigned_to: str,
    department: str,
    is_staff: bool,
    view_url: str = "#",
) -> EmailContent:
    """
    Email sent when a complaint is assigned.
    Sent to both the assigned staff member and the student.
    """
    if is_staff:
        heading = f"New complaint assigned to you"
        intro = (
            f"Hi {recipient_name}, a {priority.lower()}-priority {category.lower()} "
            f"complaint has been assigned to you. Please review and take action."
        )
        cta_text = "Review & Take Action →"
    else:
        heading = "Your complaint has been assigned"
        intro = (
            f"Hi {recipient_name}, your complaint has been assigned to "
            f"<strong>{assigned_to}</strong> in the <strong>{department}</strong> team. "
            f"They'll review it shortly."
        )
        cta_text = "Track Progress →"

    body = f"""\
    <h1 class="title">{heading}</h1>
    <p class="subtitle">{intro}</p>

    <div class="card">
      <table class="info-grid" style="margin:0;">
        {_info_row("Complaint ID", f'<strong>{complaint_id}</strong>')}
        {_info_row("Title", title)}
        {_info_row("Category", category)}
        {_info_row("Priority", _priority_badge(priority))}
        {_info_row("Department", department)}
        {_info_row("Assigned To", assigned_to)}
        {_info_row("Status", _status_badge("Assigned"))}
      </table>
    </div>

    <div style="text-align:center; margin:28px 0 8px;">
      <a href="{view_url}" class="btn-primary">{cta_text}</a>
    </div>"""
    return EmailContent(
        subject=f"[{complaint_id}] Complaint Assigned — {category} → {department}",
        html_body=_base_layout(f"Complaint Assigned — {complaint_id}", body),
    )


def status_update_email(
    student_name: str,
    complaint_id: str,
    title: str,
    old_status: str,
    new_status: str,
    update_note: str = "",
    view_url: str = "#",
) -> EmailContent:
    """Email sent to student when their complaint status changes."""
    body = f"""\
    <h1 class="title">Status Update on Your Complaint</h1>
    <p class="subtitle">
      Hi {student_name}, there's a new update on your complaint.
    </p>

    <div class="card">
      <table class="info-grid" style="margin:0;">
        {_info_row("Complaint ID", f'<strong>{complaint_id}</strong>')}
        {_info_row("Title", title)}
        {_info_row("Previous Status", _status_badge(old_status))}
        {_info_row("New Status", _status_badge(new_status))}
      </table>
    </div>

    {"<div class='ai-card'><div class='ai-label'>Update Details</div><p style=\"margin:8px 0 0;font-size:13px;color:#334155;\">" + update_note + "</p></div>" if update_note else ""}

    <div style="text-align:center; margin:28px 0 8px;">
      <a href="{view_url}" class="btn-primary">View Full Details →</a>
    </div>"""
    return EmailContent(
        subject=f"[{complaint_id}] Status: {old_status} → {new_status}",
        html_body=_base_layout(f"Status Update — {complaint_id}", body),
    )


def staff_response_email(
    student_name: str,
    complaint_id: str,
    title: str,
    staff_name: str,
    message: str,
    view_url: str = "#",
) -> EmailContent:
    """Email sent to student when staff responds to their complaint."""
    body = f"""\
    <h1 class="title">New response from {staff_name}</h1>
    <p class="subtitle">
      Hi {student_name}, {staff_name} has sent an update regarding your complaint.
    </p>

    <div class="card">
      <p style="font-size:13px;color:#334155;margin:0;"><strong>{complaint_id}</strong> — {title}</p>
    </div>

    <div class="ai-card">
      <div style="font-size:11px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.06em;">
        💬 Message from {staff_name}
      </div>
      <p style="margin:10px 0 0;font-size:14px;color:#0F1F3D;line-height:1.6;">{message}</p>
    </div>

    <div style="text-align:center; margin:28px 0 8px;">
      <a href="{view_url}" class="btn-primary">View & Reply →</a>
    </div>"""
    return EmailContent(
        subject=f"[{complaint_id}] New response from {staff_name}",
        html_body=_base_layout(f"Staff Response — {complaint_id}", body),
    )


def information_request_email(
    student_name: str,
    complaint_id: str,
    title: str,
    staff_name: str,
    request_message: str,
    view_url: str = "#",
) -> EmailContent:
    """Email sent when staff requests additional information from the student."""
    body = f"""\
    <h1 class="title">Additional information needed</h1>
    <p class="subtitle">
      Hi {student_name}, the team needs more information to resolve your complaint.
      Please respond at your earliest convenience.
    </p>

    <div class="card">
      <table class="info-grid" style="margin:0;">
        {_info_row("Complaint ID", f'<strong>{complaint_id}</strong>')}
        {_info_row("Title", title)}
        {_info_row("Requested By", staff_name)}
      </table>
    </div>

    <div style="background:#FEF3C7;border:1px solid #FDE68A;border-radius:12px;padding:20px;margin:16px 0;">
      <div style="font-size:11px;font-weight:700;color:#92400E;text-transform:uppercase;letter-spacing:0.06em;">
        ⚠ Information Requested
      </div>
      <p style="margin:10px 0 0;font-size:14px;color:#78350F;line-height:1.6;">{request_message}</p>
    </div>

    <div style="text-align:center; margin:28px 0 8px;">
      <a href="{view_url}" class="btn-primary">Provide Information →</a>
    </div>
    <p style="text-align:center;font-size:12px;color:#94A3B8;margin-top:12px;">
      Quick responses help us resolve your complaint faster.
    </p>"""
    return EmailContent(
        subject=f"[{complaint_id}] Action Required — Additional Information Needed",
        html_body=_base_layout(f"Info Request — {complaint_id}", body),
    )


def escalation_email(
    recipient_name: str,
    complaint_id: str,
    title: str,
    category: str,
    priority: str,
    escalated_by: str,
    reason: str = "",
    view_url: str = "#",
) -> EmailContent:
    """Email sent when a complaint is escalated to admin/senior staff."""
    body = f"""\
    <h1 class="title">🚨 Complaint Escalated</h1>
    <p class="subtitle">
      Hi {recipient_name}, a complaint has been escalated and requires your immediate attention.
    </p>

    <div style="background:#FFE4E6;border:1px solid #FECDD3;border-radius:12px;padding:20px;margin:16px 0;">
      <table class="info-grid" style="margin:0;">
        {_info_row("Complaint ID", f'<strong style="color:#E11D48;">{complaint_id}</strong>')}
        {_info_row("Title", title)}
        {_info_row("Category", category)}
        {_info_row("Priority", _priority_badge(priority))}
        {_info_row("Escalated By", escalated_by)}
        {_info_row("Status", _status_badge("Escalated"))}
      </table>
    </div>

    {"<div class='card'><div style='font-size:11px;font-weight:700;color:#92400E;text-transform:uppercase;letter-spacing:0.06em;'>Escalation Reason</div><p style=\"margin:8px 0 0;font-size:13px;color:#334155;\">" + reason + "</p></div>" if reason else ""}

    <div style="text-align:center; margin:28px 0 8px;">
      <a href="{view_url}" class="btn-primary" style="background:linear-gradient(135deg,#E11D48,#BE123C);">
        Handle Escalation Now →
      </a>
    </div>"""
    return EmailContent(
        subject=f"🚨 [{complaint_id}] ESCALATED — {category} — Immediate Attention Required",
        html_body=_base_layout(f"Escalation — {complaint_id}", body),
    )


def resolution_submitted_email(
    student_name: str,
    complaint_id: str,
    title: str,
    resolution_summary: str,
    resolved_at: str,
    feedback_url: str = "#",
    view_url: str = "#",
) -> EmailContent:
    """Email sent when a resolution is submitted for the student's complaint."""
    body = f"""\
    <h1 class="title">Your complaint has been resolved ✓</h1>
    <p class="subtitle">
      Hi {student_name}, great news — the team has submitted a resolution for your complaint.
      Please verify that the issue is actually fixed.
    </p>

    <div class="card">
      <table class="info-grid" style="margin:0;">
        {_info_row("Complaint ID", f'<strong>{complaint_id}</strong>')}
        {_info_row("Title", title)}
        {_info_row("Status", _status_badge("Resolved"))}
        {_info_row("Resolved On", resolved_at)}
      </table>
    </div>

    <div style="background:#D1FAE5;border:1px solid #A7F3D0;border-radius:12px;padding:20px;margin:16px 0;">
      <div style="font-size:11px;font-weight:700;color:#065F46;text-transform:uppercase;letter-spacing:0.06em;">
        ✓ Resolution Summary
      </div>
      <p style="margin:10px 0 0;font-size:14px;color:#064E3B;line-height:1.6;">{resolution_summary}</p>
    </div>

    <div style="text-align:center; margin:28px 0 8px;">
      <a href="{view_url}" class="btn-primary" style="background:linear-gradient(135deg,#059669,#047857);">
        Verify Resolution →
      </a>
    </div>
    <div style="text-align:center; margin:8px 0;">
      <a href="{feedback_url}" class="btn-ghost">Rate Your Experience ★</a>
    </div>
    <p style="text-align:center;font-size:12px;color:#94A3B8;margin-top:12px;">
      Your feedback helps us improve campus services for everyone.
    </p>"""
    return EmailContent(
        subject=f"[{complaint_id}] Resolved — Please Verify & Rate",
        html_body=_base_layout(f"Resolution — {complaint_id}", body),
    )


def feedback_request_email(
    student_name: str,
    complaint_id: str,
    title: str,
    resolved_by: str,
    feedback_url: str = "#",
) -> EmailContent:
    """Email requesting the student to rate their complaint resolution experience."""
    body = f"""\
    <h1 class="title">How did we do? ★</h1>
    <p class="subtitle">
      Hi {student_name}, your complaint <strong>{complaint_id}</strong> was resolved by
      <strong>{resolved_by}</strong>. We'd love to hear your feedback — it helps us
      improve and recognizes great staff work.
    </p>

    <div class="card">
      <p style="font-size:13px;color:#334155;margin:0;">{title}</p>
    </div>

    <div style="text-align:center; margin:20px 0;">
      <div style="font-size:36px;letter-spacing:8px;">★ ★ ★ ★ ★</div>
      <p style="font-size:12px;color:#94A3B8;margin-top:8px;">Tap a star to rate (1–5)</p>
    </div>

    <div style="text-align:center; margin:28px 0 8px;">
      <a href="{feedback_url}" class="btn-primary">Submit Feedback →</a>
    </div>
    <p style="text-align:center;font-size:12px;color:#94A3B8;margin-top:12px;">
      Takes less than 30 seconds. Your ratings train our AI.
    </p>"""
    return EmailContent(
        subject=f"[{complaint_id}] How was your experience? Rate us ★",
        html_body=_base_layout(f"Feedback — {complaint_id}", body),
    )
