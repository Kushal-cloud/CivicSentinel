from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, require_roles
from app.core.db import get_session
from app.models.complaint import Complaint
from app.models.enums import ComplaintStatus, UserRole
from app.services.complaints_service import update_complaint_status

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminStatusUpdate(BaseModel):
    status: Literal[
        "in_progress",
        "resolved",
        "escalated",
        "rejected",
        "flagged",
        "submitted",
    ] = "in_progress"
    department_name: str | None = Field(default=None, max_length=128)
    message: str | None = Field(default=None, max_length=1024)


@router.get("/complaints")
async def list_complaints(
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_roles(UserRole.admin)),
):
    res = await session.execute(select(Complaint).order_by(Complaint.created_at.desc()).limit(limit).offset(offset))
    items = res.scalars().all()
    return [
        {
            "tracking_id": c.tracking_id,
            "status": c.status.value,
            "issue_category": c.issue_category,
            "department_name": c.department_name,
            "severity_score": c.severity_score,
            "priority": c.priority,
            "ward": c.ward,
            "locality": c.locality,
            "fraud_flag": c.fraud_flag,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in items
    ]


@router.patch("/complaints/{tracking_id}/status")
async def admin_update_status(
    tracking_id: str,
    payload: AdminStatusUpdate,
    session: AsyncSession = Depends(get_session),
    user=Depends(require_roles(UserRole.admin)),
):
    c = await update_complaint_status(
        session=session,
        tracking_id=tracking_id,
        new_status=ComplaintStatus(payload.status),
        department_name=payload.department_name,
        message=payload.message,
    )
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return {"tracking_id": c.tracking_id, "status": c.status.value}

