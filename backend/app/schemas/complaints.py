from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    complaint_id: uuid.UUID
    tracking_id: str
    status: str
    department_name: str | None = None
    issue_category: str | None = None
    severity_score: float | None = None
    priority: int | None = None
    ward: str | None = None
    locality: str | None = None
    jurisdiction: str | None = None

    letter_draft_subject: str | None = None
    letter_draft_body: str | None = None
    letter_review_status: str | None = None


class ComplaintReviewOut(BaseModel):
    complaint_id: uuid.UUID
    tracking_id: str
    status: str
    letter_review_status: str
    language: str
    tone: str

    issue_category: str | None = None
    department_name: str | None = None
    severity_score: float | None = None
    priority: int | None = None

    ward: str | None = None
    locality: str | None = None
    jurisdiction: str | None = None

    letter_draft_subject: str | None = None
    letter_draft_body: str | None = None


class ReviewUpdateRequest(BaseModel):
    approve: bool = True
    letter_draft_subject: str | None = Field(default=None, max_length=240)
    letter_draft_body: str | None = Field(default=None)
    language: str | None = Field(default=None, max_length=16)
    tone: Literal["formal", "urgent", "escalated"] = "formal"


class RegenerateRequest(BaseModel):
    language: str = "en"
    tone: Literal["formal", "urgent", "escalated"] = "formal"


class SubmitResponse(BaseModel):
    tracking_id: str
    status: str
    dispatched: bool = True

