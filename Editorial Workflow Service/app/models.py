import enum
from sqlalchemy import Column, Integer, String, Enum, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class WorkflowStatus(str, enum.Enum):
    submitted = "submitted"
    under_review = "under_review"
    decision_pending = "decision_pending"
    accepted = "accepted"
    rejected = "rejected"


class EditorialTask(Base):
    __tablename__ = "editorial_tasks"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False, index=True)
    editor_id = Column(Integer, nullable=False, index=True)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.submitted)
    decision = Column(String, nullable=True)
    decision_comment = Column(String, nullable=True)
    reviewer_ids = Column(JSON, nullable=True)  # list of ints
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
