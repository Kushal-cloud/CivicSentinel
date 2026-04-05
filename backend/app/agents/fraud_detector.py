from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint


@dataclass
class FraudResult:
    fraud_flag: bool
    fraud_score: float
    reasons: list[str]


async def assess_fraud(
    session: AsyncSession,
    *,
    reporter_user_id,
    image_phash_hex: str | None,
    detected_issues: list[dict[str, Any]] | None,
    latitude: float | None,
    longitude: float | None,
) -> FraudResult:
    reasons: list[str] = []
    detected_issues = detected_issues or []
    max_conf = 0.0
    for d in detected_issues:
        try:
            max_conf = max(max_conf, float(d.get("confidence") or 0.0))
        except Exception:
            pass

    score = 0.0
    # Low confidence + no geo often correlates with low-quality spam.
    if max_conf < 0.18 and (latitude is None or longitude is None):
        score += 0.5
        reasons.append("Low model confidence and missing location")

    if reporter_user_id and image_phash_hex:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        res = await session.execute(
            select(func.count(Complaint.id)).where(Complaint.reporter_user_id == reporter_user_id)
            .where(Complaint.image_phash == image_phash_hex)
            .where(Complaint.created_at >= cutoff)
        )
        cnt = int(res.scalar_one() or 0)
        if cnt >= 3:
            score += 0.5
            reasons.append("Repeated submissions with similar image")

    if reporter_user_id:
        cutoff_day = datetime.now(timezone.utc) - timedelta(days=1)
        res2 = await session.execute(
            select(func.count(Complaint.id)).where(Complaint.reporter_user_id == reporter_user_id).where(Complaint.created_at >= cutoff_day)
        )
        daily_cnt = int(res2.scalar_one() or 0)
        if daily_cnt >= 8:
            score += 0.4
            reasons.append("Unusually high submission volume")

    fraud_score = min(1.0, round(score, 2))
    fraud_flag = fraud_score >= 0.6
    return FraudResult(fraud_flag=fraud_flag, fraud_score=fraud_score, reasons=reasons)

