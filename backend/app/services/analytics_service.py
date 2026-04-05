from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.schemas.analytics import AnalyticsHeatmap, AnalyticsSummary, PredictiveAnalyticsOut, PredictiveRiskZone


async def get_analytics_summary(*, session: AsyncSession, days: int = 30) -> AnalyticsSummary:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    res_total = await session.execute(select(func.count()).select_from(Complaint).where(Complaint.created_at >= cutoff))
    total = int(res_total.scalar_one() or 0)

    res_status = await session.execute(
        select(Complaint.status, func.count()).where(Complaint.created_at >= cutoff).group_by(Complaint.status)
    )
    by_status = {str(k.value): int(v) for k, v in res_status.all() if hasattr(k, "value")}

    res_issue = await session.execute(
        select(Complaint.issue_category, func.count()).where(Complaint.created_at >= cutoff).group_by(Complaint.issue_category)
    )
    by_issue = {str(k or "unknown"): int(v) for k, v in res_issue.all()}

    res_dept = await session.execute(
        select(Complaint.department_name, func.count()).where(Complaint.created_at >= cutoff).group_by(Complaint.department_name)
    )
    by_dept = {str(k or "unknown"): int(v) for k, v in res_dept.all()}

    res_sev = await session.execute(select(func.avg(Complaint.severity_score)).where(Complaint.created_at >= cutoff))
    severity_avg = res_sev.scalar_one()

    # Resolution time: submitted/ready -> resolved not tracked separately; use created_at -> resolved_at.
    res_times = await session.execute(
        select(func.extract("epoch", Complaint.resolved_at - Complaint.created_at) / 60.0).where(
            Complaint.resolved_at.is_not(None), Complaint.created_at >= cutoff
        )
    )
    times = [float(x[0]) for x in res_times.all() if x[0] is not None]
    times.sort()
    p50 = times[int(len(times) * 0.5)] if times else None
    p90 = times[int(len(times) * 0.9) - 1] if times and len(times) > 1 else None

    return AnalyticsSummary(
        total_complaints=total,
        by_status=by_status,
        by_issue_category=by_issue,
        by_department=by_dept,
        severity_average=float(severity_avg) if severity_avg is not None else None,
        resolution_times_minutes_p50=round(p50, 2) if p50 is not None else None,
        resolution_times_minutes_p90=round(p90, 2) if p90 is not None else None,
    )


async def get_heatmap(*, session: AsyncSession, days: int = 30, grid_size_degrees: float = 0.05) -> AnalyticsHeatmap:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # MVP: do grid binning in Python (simpler). Scale by adding a DB aggregation later.
    res = await session.execute(
        select(Complaint.latitude, Complaint.longitude).where(
            Complaint.created_at >= cutoff, Complaint.latitude.is_not(None), Complaint.longitude.is_not(None)
        )
    )
    points = [(float(lat), float(lon)) for lat, lon in res.all() if lat is not None and lon is not None]

    cells: dict[tuple[float, float], int] = {}
    for lat, lon in points:
        lat_bin = round(lat / grid_size_degrees) * grid_size_degrees
        lon_bin = round(lon / grid_size_degrees) * grid_size_degrees
        key = (lat_bin, lon_bin)
        cells[key] = cells.get(key, 0) + 1

    out_cells = [
        {"lat_bin": float(k[0]), "lon_bin": float(k[1]), "count": int(v)} for k, v in sorted(cells.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return AnalyticsHeatmap(grid_size_degrees=grid_size_degrees, cells=[{"lat_bin": c["lat_bin"], "lon_bin": c["lon_bin"], "count": c["count"]} for c in out_cells])


async def get_predictive_zones(*, session: AsyncSession) -> PredictiveAnalyticsOut:
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(days=30)
    prev_cutoff = now - timedelta(days=60)

    # Use ward-level as zone key (MVP). Replace with grid-based zones when you have more scale data.
    res_recent = await session.execute(
        select(Complaint.ward, func.count()).where(Complaint.created_at >= recent_cutoff).group_by(Complaint.ward)
    )
    res_prev = await session.execute(
        select(Complaint.ward, func.count()).where(Complaint.created_at >= prev_cutoff, Complaint.created_at < recent_cutoff).group_by(Complaint.ward)
    )

    recent = {str(k or "unknown"): int(v) for k, v in res_recent.all()}
    prev = {str(k or "unknown"): int(v) for k, v in res_prev.all()}

    zones: list[PredictiveRiskZone] = []
    keys = set(recent.keys()) | set(prev.keys())
    for ward in keys:
        r = recent.get(ward, 0)
        p = prev.get(ward, 0)
        if r == 0 and p == 0:
            continue
        prev_count = max(1, p)
        risk_score = (r / prev_count) if p > 0 else (1.5 if r > 0 else 0.0)
        zones.append(
            PredictiveRiskZone(
                ward=None if ward == "unknown" else ward,
                grid_key=ward,
                risk_score=round(float(risk_score), 3),
                recent_count=r,
                previous_count=p,
            )
        )

    zones.sort(key=lambda z: z.risk_score, reverse=True)
    return PredictiveAnalyticsOut(zones=zones[:20])

