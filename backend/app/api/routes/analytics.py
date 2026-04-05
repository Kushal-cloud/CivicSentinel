from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.services.analytics_service import get_analytics_summary, get_heatmap, get_predictive_zones

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def summary(
    days: int = 30,
    session: AsyncSession = Depends(get_session),
):
    return await get_analytics_summary(session=session, days=days)


@router.get("/heatmap")
async def heatmap(
    days: int = 30,
    session: AsyncSession = Depends(get_session),
):
    return await get_heatmap(session=session, days=days)


@router.get("/predictive")
async def predictive(
    session: AsyncSession = Depends(get_session),
):
    return await get_predictive_zones(session=session)

