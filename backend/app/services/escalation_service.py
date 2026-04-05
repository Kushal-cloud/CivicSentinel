from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.core.config import settings
from app.core.db import AsyncSessionLocal
from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus
from app.models.event import ComplaintEvent


def start_escalation_scheduler() -> None:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(check_escalation_sla, "interval", minutes=5, max_instances=1, coalesce=True)
    scheduler.start()


async def check_escalation_sla() -> None:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=settings.escalation_hours)

    async with AsyncSessionLocal() as session:
        statuses = [
            ComplaintStatus.received,
            ComplaintStatus.review_pending,
            ComplaintStatus.ready_for_submission,
            ComplaintStatus.submitted,
            ComplaintStatus.in_progress,
            ComplaintStatus.flagged,
        ]

        res = await session.execute(
            select(Complaint).where(
                Complaint.updated_at <= cutoff,
                Complaint.status.in_(statuses),
                Complaint.resolved_at.is_(None),
                Complaint.escalated_at.is_(None),
            )
        )
        complaints = res.scalars().all()
        if not complaints:
            return

        for c in complaints:
            c.status = ComplaintStatus.escalated
            c.escalated_at = now
            session.add(
                ComplaintEvent(
                    complaint_id=c.id,
                    event_type="escalated",
                    message="Escalated due to SLA breach",
                )
            )

        await session.commit()

        # Best-effort notifications to citizens.
        try:
            from app.services.notification_service import notify_status_change

            for c in complaints:
                await notify_status_change(complaint=c, new_status=ComplaintStatus.escalated.value)
        except Exception:
            pass

