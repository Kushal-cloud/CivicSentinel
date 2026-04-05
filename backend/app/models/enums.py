import enum


class UserRole(str, enum.Enum):
    citizen = "citizen"
    admin = "admin"


class ComplaintStatus(str, enum.Enum):
    received = "received"  # image uploaded + processed, awaiting user review
    review_pending = "review_pending"  # citizen can edit/approve/regenerate
    ready_for_submission = "ready_for_submission"
    submitted = "submitted"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"
    rejected = "rejected"
    flagged = "flagged"  # suspected spam/fraud; requires admin action


class LetterReviewStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"

