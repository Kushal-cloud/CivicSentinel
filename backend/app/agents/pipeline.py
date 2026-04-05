from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.authority_mapping import map_department
from app.agents.duplicate_detector import compute_image_phash, find_duplicate
from app.agents.fraud_detector import assess_fraud
from app.agents.image_preprocessing import preprocess_image_for_detection, validate_image_bytes
from app.agents.location_agent import detect_location
from app.agents.nlp_agent import generate_letter
from app.agents.recommendation_engine import recommend
from app.agents.severity_engine import estimate_severity
from app.agents.vision_agent import detect_issues


@dataclass
class PipelineOutput:
    issue_category: str | None
    department_name: str | None
    jurisdiction: str | None
    ward: str | None
    locality: str | None
    latitude: float | None
    longitude: float | None
    detected_issues: list[dict[str, Any]] | None
    severity_score: float | None
    priority: int | None
    fraud_flag: bool
    duplicate_of_tracking_id: str | None
    image_phash: str | None
    letter_subject: str | None
    letter_body: str | None
    language: str
    tone: str


async def _compute_ward_risk_factor(session: AsyncSession, ward: str | None) -> float:
    if not ward:
        return 1.0
    now = datetime.now(timezone.utc)
    last_cutoff = now - timedelta(days=30)
    prev_cutoff = now - timedelta(days=60)

    from app.models.complaint import Complaint

    res_last = await session.execute(
        select(func.count()).select_from(Complaint).where(Complaint.ward == ward, Complaint.created_at >= last_cutoff)
    )
    last_count = int(res_last.scalar_one() or 0)

    res_prev = await session.execute(
        select(func.count()).select_from(Complaint).where(
            Complaint.ward == ward,
            Complaint.created_at >= prev_cutoff,
            Complaint.created_at < last_cutoff,
        )
    )
    prev_count = int(res_prev.scalar_one() or 0)

    if prev_count <= 0 and last_count > 0:
        return 1.25
    if prev_count > 0:
        delta = last_count - prev_count
        if delta > 0:
            return 1.0 + min(0.5, delta / max(1, prev_count) * 0.25)
    return 1.0


async def run_pipeline(
    session: AsyncSession,
    *,
    tracking_id: str,
    image_path: str,
    image_bytes: bytes,
    reporter_user_id,
    reporter_name: str | None,
    language: str,
    tone: str,
    manual_lat: float | None,
    manual_lon: float | None,
    manual_ward: str | None,
    manual_locality: str | None,
    citizen_description: str | None,
) -> PipelineOutput:
    # 1) Validate + preprocess.
    validate_image_bytes(image_bytes, filename=image_path)
    prep = preprocess_image_for_detection(image_bytes)
    pil_image = prep["pil_image"]

    # 2) Compute perceptual hash for duplicate detection.
    img_phash = compute_image_phash(pil_image)

    # 3) Vision detection.
    vision = detect_issues(pil_image, image_bytes=image_bytes)

    # 4) Severity estimation (needs contextual risk factor).
    # 5) Location detection (EXIF or manual) + reverse geocode.
    loc = detect_location(image_bytes=image_bytes, manual_lat=manual_lat, manual_lon=manual_lon)

    ward = manual_ward or loc.ward
    locality = manual_locality or loc.locality
    jurisdiction = loc.jurisdiction

    risk_factor = await _compute_ward_risk_factor(session, ward)
    severity = estimate_severity(
        issue_category=vision.issue_category,
        detected_issues=vision.detected_issues,
        risk_factor=risk_factor,
    )

    # 6) Authority mapping.
    authority = map_department(vision.issue_category, detected_issues=vision.detected_issues)

    # 7) Duplicate detection.
    dup = await find_duplicate(
        session,
        image_phash_hex=img_phash,
        latitude=loc.latitude,
        longitude=loc.longitude,
    )

    # 8) Fraud/spam detection.
    fraud = await assess_fraud(
        session,
        reporter_user_id=reporter_user_id,
        image_phash_hex=img_phash,
        detected_issues=vision.detected_issues,
        latitude=loc.latitude,
        longitude=loc.longitude,
    )

    # 9) Recommendation engine.
    rec = recommend(authority.mapped_issue_category or vision.issue_category, severity_score=severity.severity_score)

    # 10) NLP complaint letter generation.
    letter = generate_letter(
        tracking_id=tracking_id,
        language=language,
        tone=tone,
        issue_category=authority.mapped_issue_category or vision.issue_category,
        department_name=authority.department_name,
        ward=ward,
        locality=locality,
        jurisdiction=jurisdiction,
        latitude=loc.latitude,
        longitude=loc.longitude,
        severity_score=severity.severity_score,
        priority=severity.priority,
        citizen_description=citizen_description,
        recommendations=(rec.recommendations + rec.preventive_actions)[:6],
        reporter_name=reporter_name,
        detected_issues=vision.detected_issues,
    )

    return PipelineOutput(
        issue_category=authority.mapped_issue_category or vision.issue_category,
        department_name=authority.department_name,
        jurisdiction=jurisdiction,
        ward=ward,
        locality=locality,
        latitude=loc.latitude,
        longitude=loc.longitude,
        detected_issues=vision.detected_issues,
        severity_score=severity.severity_score,
        priority=severity.priority,
        fraud_flag=fraud.fraud_flag,
        duplicate_of_tracking_id=dup.duplicate_of_tracking_id,
        image_phash=img_phash,
        letter_subject=letter.subject,
        letter_body=letter.body,
        language=language,
        tone=tone,
    )

