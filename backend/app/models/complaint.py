import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.enums import ComplaintStatus, LetterReviewStatus


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tracking_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    reporter_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reporter_name: Mapped[str] = mapped_column(String(120))
    reporter_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reporter_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    language: Mapped[str] = mapped_column(String(16), default="en")
    tone: Mapped[str] = mapped_column(String(32), default="formal")

    status: Mapped[ComplaintStatus] = mapped_column(Enum(ComplaintStatus), default=ComplaintStatus.received, index=True)
    letter_review_status: Mapped[LetterReviewStatus] = mapped_column(
        Enum(LetterReviewStatus), default=LetterReviewStatus.pending, index=True
    )

    issue_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    department_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    jurisdiction: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ward: Mapped[str | None] = mapped_column(String(128), nullable=True)
    locality: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # Vision/NLP derived
    severity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fraud_flag: Mapped[bool] = mapped_column(Boolean, default=False)

    detected_issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Image + duplicate detection
    image_path: Mapped[str] = mapped_column(Text)
    image_phash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duplicate_of_tracking_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)

    # Draft complaint letter
    letter_draft_subject: Mapped[str | None] = mapped_column(Text, nullable=True)
    letter_draft_body: Mapped[str | None] = mapped_column(Text, nullable=True)

    citizen_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Added features
    upvotes: Mapped[int] = mapped_column(Integer, default=0)
    resolved_image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_count: Mapped[int] = mapped_column(Integer, default=0)

    events = relationship("ComplaintEvent", back_populates="complaint", cascade="all, delete-orphan")

