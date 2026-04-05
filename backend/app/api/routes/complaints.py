from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.db import get_session
from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus, LetterReviewStatus, UserRole
from app.schemas.complaints import (
    RegenerateRequest,
    ReviewUpdateRequest,
    SubmitResponse,
    UploadResponse,
)

from app.services.complaints_service import (
    get_complaint_by_tracking_id,
    list_events_for_complaint,
    process_uploaded_complaint,
    regenerate_letter,
    review_letter,
    submit_complaint,
    upvote_complaint,
    follow_up_complaint,
    fetch_gallery_complaints,
)

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.get("/my", response_model=list[dict])
async def my_complaints(
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> list[dict]:
    from sqlalchemy import desc
    result = await session.execute(
        select(Complaint)
        .where(Complaint.reporter_user_id == user.id)
        .order_by(desc(Complaint.created_at))
    )
    complaints = result.scalars().all()
    return [
        {
            "tracking_id": c.tracking_id,
            "status": c.status.value,
            "issue_category": c.issue_category,
            "ward": c.ward,
            "locality": c.locality,
            "fraud_flag": c.fraud_flag,
            "upvotes": c.upvotes or 0,
            "follow_up_count": c.follow_up_count or 0,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in complaints
    ]


@router.post("/upload", response_model=UploadResponse)
async def upload_complaint(
    image: UploadFile = File(...),
    lat: float | None = Form(default=None),
    lon: float | None = Form(default=None),
    language: str = Form(default="en"),
    tone: str = Form(default="formal"),
    manual_ward: str | None = Form(default=None),
    manual_locality: str | None = Form(default=None),
    citizen_description: str | None = Form(default=None, max_length=2000),
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> UploadResponse:
    # Validate upload size early.
    content = await image.read()
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image too large")
    if not image.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    # Ensure user is the reporter.
    reporter_name = user.name
    reporter_email = user.email
    if not reporter_name or not reporter_name.strip():
        reporter_name = reporter_email.split('@')[0].replace('.', ' ').title() if reporter_email else "Concerned Citizen"
    reporter_phone = user.phone

    # Store image
    os.makedirs(settings.storage_dir, exist_ok=True)
    extension = os.path.splitext(image.filename)[1].lower() or ".jpg"
    stored_name = f"{uuid.uuid4().hex}{extension}"
    image_path = os.path.join(settings.storage_dir, stored_name)
    with open(image_path, "wb") as f:
        f.write(content)

    complaint = await process_uploaded_complaint(
        session=session,
        image_path=image_path,
        image_bytes=content,
        reporter_user_id=user.id,
        reporter_name=reporter_name,
        reporter_email=reporter_email,
        reporter_phone=reporter_phone,
        language=language,
        tone=tone,
        manual_lat=lat,
        manual_lon=lon,
        manual_ward=manual_ward,
        manual_locality=manual_locality,
        citizen_description=citizen_description,
    )

    return UploadResponse(
        complaint_id=complaint.id,
        tracking_id=complaint.tracking_id,
        status=complaint.status.value,
        department_name=complaint.department_name,
        issue_category=complaint.issue_category,
        severity_score=complaint.severity_score,
        priority=complaint.priority,
        ward=complaint.ward,
        locality=complaint.locality,
        jurisdiction=complaint.jurisdiction,
        letter_draft_subject=complaint.letter_draft_subject,
        letter_draft_body=complaint.letter_draft_body,
        letter_review_status=complaint.letter_review_status.value if complaint.letter_review_status else None,
    )


@router.get("/public/gallery", response_model=list[dict])
async def gallery(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    complaints = await fetch_gallery_complaints(session=session)
    return [
        {
            "tracking_id": c.tracking_id,
            "issue_category": c.issue_category,
            "ward": c.ward,
            "locality": c.locality,
            "upvotes": c.upvotes,
            "image_path": c.image_path,
            "resolved_image_path": c.resolved_image_path,
        }
        for c in complaints
    ]


@router.get("/{tracking_id}", response_model=dict)
async def get_review(
    tracking_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> JSONResponse:
    complaint = await get_complaint_by_tracking_id(session=session, tracking_id=tracking_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.reporter_user_id and complaint.reporter_user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    return JSONResponse(
        {
            "complaint_id": str(complaint.id),
            "tracking_id": complaint.tracking_id,
            "status": complaint.status.value,
            "letter_review_status": complaint.letter_review_status.value,
            "language": complaint.language,
            "tone": complaint.tone,
            "issue_category": complaint.issue_category,
            "department_name": complaint.department_name,
            "severity_score": complaint.severity_score,
            "priority": complaint.priority,
            "ward": complaint.ward,
            "locality": complaint.locality,
            "jurisdiction": complaint.jurisdiction,
            "letter_draft_subject": complaint.letter_draft_subject,
            "letter_draft_body": complaint.letter_draft_body,
            "detected_issues": complaint.detected_issues,
            "duplicate_of_tracking_id": complaint.duplicate_of_tracking_id,
            "image_path": complaint.image_path,
            "fraud_flag": complaint.fraud_flag,
            "reporter_name": complaint.reporter_name,
            "created_at": complaint.created_at.isoformat() if complaint.created_at else None,
            "upvotes": complaint.upvotes or 0,
            "follow_up_count": complaint.follow_up_count or 0,
        }
    )


@router.put("/{tracking_id}/review", response_model=dict)
async def review(
    tracking_id: str,
    payload: ReviewUpdateRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> JSONResponse:
    complaint = await get_complaint_by_tracking_id(session=session, tracking_id=tracking_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.reporter_user_id and complaint.reporter_user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    complaint = await review_letter(
        session=session,
        tracking_id=tracking_id,
        reviewer_user_id=user.id,
        approve=payload.approve,
        letter_draft_subject=payload.letter_draft_subject,
        letter_draft_body=payload.letter_draft_body,
        language=payload.language,
        tone=payload.tone,
    )
    return JSONResponse({"tracking_id": complaint.tracking_id, "status": complaint.status.value, "letter_review_status": complaint.letter_review_status.value})


@router.post("/{tracking_id}/regenerate", response_model=dict)
async def regenerate(
    tracking_id: str,
    payload: RegenerateRequest,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> JSONResponse:
    complaint = await get_complaint_by_tracking_id(session=session, tracking_id=tracking_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.reporter_user_id and complaint.reporter_user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    complaint = await regenerate_letter(
        session=session,
        tracking_id=tracking_id,
        requester_user_id=user.id,
        language=payload.language,
        tone=payload.tone,
    )
    return JSONResponse(
        {
            "tracking_id": complaint.tracking_id,
            "status": complaint.status.value,
            "letter_review_status": complaint.letter_review_status.value,
            "letter_draft_subject": complaint.letter_draft_subject,
            "letter_draft_body": complaint.letter_draft_body,
        }
    )


@router.post("/{tracking_id}/submit", response_model=SubmitResponse)
async def submit(
    tracking_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> SubmitResponse:
    complaint = await get_complaint_by_tracking_id(session=session, tracking_id=tracking_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.reporter_user_id and complaint.reporter_user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    complaint, dispatched = await submit_complaint(
        session=session,
        tracking_id=tracking_id,
        requester_user_id=user.id,
    )
    return SubmitResponse(tracking_id=complaint.tracking_id, status=complaint.status.value, dispatched=dispatched)


@router.get("/citizen/{tracking_id}/events", response_model=list[dict])
async def events(
    tracking_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> list[dict]:
    complaint = await get_complaint_by_tracking_id(session=session, tracking_id=tracking_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    if complaint.reporter_user_id and complaint.reporter_user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Not allowed")

    events = await list_events_for_complaint(session=session, complaint_id=complaint.id)
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "message": e.message,
            "payload": e.payload,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.post("/{tracking_id}/upvote", response_model=dict)
async def upvote(
    tracking_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> JSONResponse:
    complaint = await upvote_complaint(session=session, tracking_id=tracking_id)
    return JSONResponse({"tracking_id": complaint.tracking_id, "upvotes": complaint.upvotes})


@router.post("/{tracking_id}/follow-up", response_model=dict)
async def follow_up(
    tracking_id: str,
    session: AsyncSession = Depends(get_session),
    user=Depends(get_current_user),
) -> JSONResponse:
    complaint = await follow_up_complaint(session=session, tracking_id=tracking_id, requester_user_id=user.id)
    return JSONResponse({
        "tracking_id": complaint.tracking_id, 
        "follow_up_count": complaint.follow_up_count,
        "letter_draft_subject": complaint.letter_draft_subject,
        "letter_draft_body": complaint.letter_draft_body
    })

