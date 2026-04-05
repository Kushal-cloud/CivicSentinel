from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.models.complaint import Complaint


DEPARTMENT_CONTACT_EMAILS = {
    "Road Maintenance": "road-maintenance@example.gov",
    "Sanitation & Solid Waste": "sanitation@example.gov",
    "Electricity & Street Lighting": "electricity@example.gov",
    "Water Supply & Sewerage": "water@example.gov",
    "Public Works (General)": "public-works@example.gov",
}


async def dispatch_complaint(*, complaint: Complaint) -> bool:
    """
    MVP dispatcher.
    - If SMTP is configured, sends the generated letter via email.
    - Otherwise returns False and logs a no-op.
    """
    if not settings.smtp_host or not settings.smtp_user:
        # No email configured in this environment.
        return False

    to_email = DEPARTMENT_CONTACT_EMAILS.get(complaint.department_name or "", settings.smtp_user)
    if not to_email:
        return False

    msg = EmailMessage()
    msg["Subject"] = complaint.letter_draft_subject or f"CivicSentinel Complaint {complaint.tracking_id}"
    msg["From"] = settings.smtp_user
    msg["To"] = to_email

    body = complaint.letter_draft_body or ""
    msg.set_content(body)

    # Attach image as proof when possible (optional).
    try:
        if complaint.image_path and os.path.exists(complaint.image_path):
            with open(complaint.image_path, "rb") as f:
                img_bytes = f.read()
            maintype = "image"
            subtype = "jpeg"
            msg.add_attachment(img_bytes, maintype=maintype, subtype=subtype, filename=os.path.basename(complaint.image_path))
    except Exception:
        # Attachments are best-effort only.
        pass

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            if settings.smtp_pass:
                smtp.starttls()
                smtp.login(settings.smtp_user, settings.smtp_pass)
            smtp.send_message(msg)
        return True
    except Exception:
        return False

