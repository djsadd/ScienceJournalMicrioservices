from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ReviewStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"

class Recommendation(str, Enum):
    accept = "accept"
    minor_revision = "minor_revision"
    major_revision = "major_revision"
    reject = "reject"

class ReviewBase(BaseModel):
    article_id: int
    comments: Optional[str] = None
    recommendation: Optional[Recommendation] = None
    status: ReviewStatus = ReviewStatus.pending

class ReviewCreate(ReviewBase):
    pass

class ReviewOut(ReviewBase):
    id: int
    reviewer_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
