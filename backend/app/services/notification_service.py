from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.models.complaint import Complaint


async def notify_status_change(*, complaint: Complaint, new_status: str) -> None:
    """
    MVP: email notification to the citizen when SMTP is configured.
    For SMS/WhatsApp/push, add channel adapters (Twilio, Firebase, etc).
    """
    if not settings.smtp_host or not settings.smtp_user:
        return
    if not complaint.reporter_email:
        return

    msg = EmailMessage()
    msg["Subject"] = f"CivicSentinel update: {new_status}"
    msg["From"] = settings.smtp_user
    msg["To"] = complaint.reporter_email
    msg.set_content(
        f"Hello {complaint.reporter_name},\n\n"
        f"Your complaint (Tracking ID: {complaint.tracking_id}) has status: {new_status}.\n\n"
        f"Regards,\nCivicSentinel"
    )

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            if settings.smtp_pass:
                smtp.starttls()
                smtp.login(settings.smtp_user, settings.smtp_pass)
            smtp.send_message(msg)
    except Exception:
        # Best-effort only.
        return

