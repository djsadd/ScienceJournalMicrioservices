from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class ReviewStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    resubmission = "resubmission"

class Recommendation(str, enum.Enum):
    accept = "accept"
    minor_revision = "minor_revision"
    major_revision = "major_revision"
    reject = "reject"

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, nullable=False)   # article_id из Articles
    reviewer_id = Column(Integer, nullable=False)  # user_id из Users
    comments = Column(String, nullable=True)
    recommendation = Column(Enum(Recommendation), nullable=True)
    status = Column(Enum(ReviewStatus), default=ReviewStatus.pending)
    deadline = Column(DateTime(timezone=True), nullable=True)
    # Reviewer criteria fields (free-text answers)
    importance_applicability = Column(Text, nullable=True)
    novelty_application = Column(Text, nullable=True)
    originality = Column(Text, nullable=True)
    innovation_product = Column(Text, nullable=True)
    results_significance = Column(Text, nullable=True)
    coherence = Column(Text, nullable=True)
    style_quality = Column(Text, nullable=True)
    editorial_compliance = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
