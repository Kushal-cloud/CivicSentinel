from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.pipeline import run_pipeline
from app.core.config import settings
from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus, LetterReviewStatus
from app.models.event import ComplaintEvent


def _tracking_id() -> str:
    now = datetime.now(timezone.utc)
    date_part = now.strftime("%Y%m%d")
    rand = uuid.uuid4().hex[:6].upper()
    return f"CS-{date_part}-{rand}"


async def process_uploaded_complaint(
    *,
    session: AsyncSession,
    image_path: str,
    image_bytes: bytes,
    reporter_user_id,
    reporter_name: str,
    reporter_email: str | None,
    reporter_phone: str | None,
    language: str,
    tone: str,
    manual_lat: float | None,
    manual_lon: float | None,
    manual_ward: str | None,
    manual_locality: str | None,
    citizen_description: str | None,
) -> Complaint:
    tracking_id = _tracking_id()

    complaint = Complaint(
        tracking_id=tracking_id,
        reporter_user_id=reporter_user_id,
        reporter_name=reporter_name,
        reporter_email=reporter_email,
        reporter_phone=reporter_phone,
        language=language,
        tone=tone,
        status=ComplaintStatus.received,
        letter_review_status=LetterReviewStatus.pending,
        image_path=image_path,
        citizen_description=citizen_description,
    )
    session.add(complaint)
    await session.flush()

    session.add(
        ComplaintEvent(
            complaint_id=complaint.id,
            event_type="uploaded",
            message="Image uploaded and stored",
            payload={"image_path": os.path.basename(image_path)},
        )
    )

    # Run the AI pipeline.
    pipeline_out = await run_pipeline(
        session,
        tracking_id=tracking_id,
        image_path=image_path,
        image_bytes=image_bytes,
        reporter_user_id=reporter_user_id,
        reporter_name=reporter_name,
        language=language,
        tone=tone,
        manual_lat=manual_lat,
        manual_lon=manual_lon,
        manual_ward=manual_ward,
        manual_locality=manual_locality,
        citizen_description=citizen_description,
    )

    complaint.issue_category = pipeline_out.issue_category
    complaint.department_name = pipeline_out.department_name
    complaint.jurisdiction = pipeline_out.jurisdiction
    complaint.ward = pipeline_out.ward
    complaint.locality = pipeline_out.locality
    complaint.latitude = pipeline_out.latitude
    complaint.longitude = pipeline_out.longitude

    complaint.detected_issues = {"detections": pipeline_out.detected_issues or []}
    complaint.severity_score = pipeline_out.severity_score
    complaint.priority = pipeline_out.priority

    complaint.fraud_flag = pipeline_out.fraud_flag
    complaint.duplicate_of_tracking_id = pipeline_out.duplicate_of_tracking_id
    complaint.image_phash = pipeline_out.image_phash

    complaint.letter_draft_subject = pipeline_out.letter_subject
    complaint.letter_draft_body = pipeline_out.letter_body
    complaint.language = language
    complaint.tone = tone

    if pipeline_out.fraud_flag:
        complaint.status = ComplaintStatus.flagged
    else:
        complaint.status = ComplaintStatus.review_pending
    complaint.letter_review_status = LetterReviewStatus.pending

    session.add(
        ComplaintEvent(
            complaint_id=complaint.id,
            event_type="ai_processed",
            message="Vision+location mapping+NLP letter generated",
            payload={
                "issue_category": complaint.issue_category,
                "department_name": complaint.department_name,
                "severity_score": complaint.severity_score,
                "priority": complaint.priority,
                "fraud_flag": complaint.fraud_flag,
                "duplicate_of": complaint.duplicate_of_tracking_id,
            },
        )
    )

    await session.commit()
    await session.refresh(complaint)
    return complaint


async def get_complaint_by_tracking_id(session: AsyncSession, *, tracking_id: str) -> Complaint | None:
    res = await session.execute(select(Complaint).where(Complaint.tracking_id == tracking_id))
    return res.scalar_one_or_none()


async def list_events_for_complaint(session: AsyncSession, *, complaint_id) -> list[ComplaintEvent]:
    res = await session.execute(
        select(ComplaintEvent)
        .where(ComplaintEvent.complaint_id == complaint_id)
        .order_by(ComplaintEvent.created_at.asc())
    )
    return res.scalars().all()


async def review_letter(
    *,
    session: AsyncSession,
    tracking_id: str,
    reviewer_user_id,
    approve: bool,
    letter_draft_subject: str | None,
    letter_draft_body: str | None,
    language: str | None,
    tone: str,
) -> Complaint:
    complaint = await get_complaint_by_tracking_id(session, tracking_id=tracking_id)
    if not complaint:
        raise ValueError("Complaint not found")

    complaint.letter_draft_subject = letter_draft_subject or complaint.letter_draft_subject
    complaint.letter_draft_body = letter_draft_body or complaint.letter_draft_body
    complaint.language = language or complaint.language
    complaint.tone = tone

    if approve and not complaint.fraud_flag:
        complaint.letter_review_status = LetterReviewStatus.approved
        complaint.status = ComplaintStatus.ready_for_submission
        session.add(
            ComplaintEvent(
                complaint_id=complaint.id,
                event_type="review_approved",
                message="Citizen approved complaint draft",
            )
        )
    else:
        complaint.letter_review_status = LetterReviewStatus.pending
        complaint.status = ComplaintStatus.review_pending
        session.add(
            ComplaintEvent(
                complaint_id=complaint.id,
                event_type="review_pending",
                message="Citizen updated complaint draft",
            )
        )

    await session.commit()
    await session.refresh(complaint)
    return complaint


async def regenerate_letter(
    *,
    session: AsyncSession,
    tracking_id: str,
    requester_user_id,
    language: str,
    tone: str,
) -> Complaint:
    complaint = await get_complaint_by_tracking_id(session, tracking_id=tracking_id)
    if not complaint:
        raise ValueError("Complaint not found")

    # Regenerate using stored image+derived fields. For MVP, we reuse the latest detected_issues/fields.
    # If you want strict regeneration from the raw image, re-run the full pipeline.
    # (We keep MVP fast and deterministic.)

    from app.agents.nlp_agent import generate_letter
    from app.agents.recommendation_engine import recommend

    rec = recommend(complaint.issue_category, severity_score=complaint.severity_score)
    letter = generate_letter(
        tracking_id=complaint.tracking_id,
        language=language,
        tone=tone,
        issue_category=complaint.issue_category,
        department_name=complaint.department_name,
        ward=complaint.ward,
        locality=complaint.locality,
        jurisdiction=complaint.jurisdiction,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        severity_score=complaint.severity_score,
        priority=complaint.priority,
        citizen_description=complaint.citizen_description,
        recommendations=(rec.recommendations + rec.preventive_actions)[:6],
        reporter_name=complaint.reporter_name,
        detected_issues=complaint.detected_issues.get("detections") if getattr(complaint, "detected_issues") else None,
    )

    complaint.language = language
    complaint.tone = tone
    complaint.letter_draft_subject = letter.subject
    complaint.letter_draft_body = letter.body
    complaint.letter_review_status = LetterReviewStatus.pending
    complaint.status = ComplaintStatus.review_pending

    session.add(
        ComplaintEvent(
            complaint_id=complaint.id,
            event_type="letter_regenerated",
            message="NLP complaint letter regenerated with new language/tone",
            payload={"language": language, "tone": tone},
        )
    )

    await session.commit()
    await session.refresh(complaint)
    return complaint


async def submit_complaint(
    *,
    session: AsyncSession,
    tracking_id: str,
    requester_user_id,
) -> tuple[Complaint, bool]:
    complaint = await get_complaint_by_tracking_id(session, tracking_id=tracking_id)
    if not complaint:
        raise ValueError("Complaint not found")

    if complaint.fraud_flag:
        raise ValueError("Complaint flagged for review; submit blocked for MVP")

    if complaint.letter_review_status != LetterReviewStatus.approved or complaint.status != ComplaintStatus.ready_for_submission:
        raise ValueError("Complaint not approved for submission")

    # Dispatch through submission agent (email + stubs).
    from app.services.submission_service import dispatch_complaint

    dispatched = await dispatch_complaint(complaint=complaint)

    complaint.status = ComplaintStatus.submitted
    complaint.submitted_at = datetime.now(timezone.utc)

    session.add(
        ComplaintEvent(
            complaint_id=complaint.id,
            event_type="submitted",
            message="Complaint submitted to mapped authority",
            payload={"dispatched": dispatched},
        )
    )

    await session.commit()
    await session.refresh(complaint)

    # Best-effort citizen notification.
    try:
        from app.services.notification_service import notify_status_change

        await notify_status_change(complaint=complaint, new_status=complaint.status.value)
    except Exception:
        pass

    return complaint, dispatched


async def update_complaint_status(
    *,
    session: AsyncSession,
    tracking_id: str,
    new_status: ComplaintStatus,
    department_name: str | None = None,
    message: str | None = None,
) -> Complaint | None:
    complaint = await get_complaint_by_tracking_id(session, tracking_id=tracking_id)
    if not complaint:
        return None

    complaint.status = new_status
    if department_name:
        complaint.department_name = department_name

    now = datetime.now(timezone.utc)
    if new_status == ComplaintStatus.resolved:
        complaint.resolved_at = now
    if new_status == ComplaintStatus.escalated:
        complaint.escalated_at = now

    session.add(
        ComplaintEvent(
            complaint_id=complaint.id,
            event_type="status_updated",
            message=message or f"Status updated to {new_status.value}",
            payload={"new_status": new_status.value, "department_name": complaint.department_name},
        )
    )
    await session.commit()
    await session.refresh(complaint)

    # Best-effort citizen notification.
    try:
        from app.services.notification_service import notify_status_change

        await notify_status_change(complaint=complaint, new_status=new_status.value)
    except Exception:
        pass

    return complaint

async def upvote_complaint(
    *,
    session: AsyncSession,
    tracking_id: str,
) -> Complaint:
    complaint = await get_complaint_by_tracking_id(session, tracking_id=tracking_id)
    if not complaint:
        raise ValueError("Complaint not found")
    
    complaint.upvotes = (complaint.upvotes or 0) + 1
    await session.commit()
    await session.refresh(complaint)
    return complaint


async def follow_up_complaint(
    *,
    session: AsyncSession,
    tracking_id: str,
    requester_user_id,
) -> Complaint:
    complaint = await get_complaint_by_tracking_id(session, tracking_id=tracking_id)
    if not complaint:
        raise ValueError("Complaint not found")
    
    complaint.follow_up_count = (complaint.follow_up_count or 0) + 1
    
    # Generate urgent letter
    from app.agents.nlp_agent import generate_letter
    from app.agents.recommendation_engine import recommend

    rec = recommend(complaint.issue_category, severity_score=complaint.severity_score)
    letter = generate_letter(
        tracking_id=complaint.tracking_id,
        language=complaint.language or "en",
        tone="urgent",
        issue_category=complaint.issue_category,
        department_name=complaint.department_name,
        ward=complaint.ward,
        locality=complaint.locality,
        jurisdiction=complaint.jurisdiction,
        latitude=complaint.latitude,
        longitude=complaint.longitude,
        severity_score=complaint.severity_score,
        priority=complaint.priority,
        citizen_description=complaint.citizen_description,
        recommendations=(rec.recommendations + rec.preventive_actions)[:6],
        reporter_name=complaint.reporter_name,
        detected_issues=complaint.detected_issues.get("detections") if getattr(complaint, "detected_issues") else None,
    )
    complaint.letter_draft_subject = letter.subject
    complaint.letter_draft_body = letter.body
    
    session.add(
        ComplaintEvent(
            complaint_id=complaint.id,
            event_type="follow_up_sent",
            message=f"Urgent follow up generated. Follow up count: {complaint.follow_up_count}",
        )
    )
    await session.commit()
    await session.refresh(complaint)
    return complaint

async def fetch_gallery_complaints(session: AsyncSession) -> list[Complaint]:
    res = await session.execute(
        select(Complaint)
        .where(Complaint.status == ComplaintStatus.resolved)
        .order_by(Complaint.updated_at.desc())
        .limit(50)
    )
    return res.scalars().all()
