from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ReviewStatus(str, Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    resubmission = "resubmission"

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
    # Reviewer criteria fields (free-text answers)
    importance_applicability: Optional[str] = None
    novelty_application: Optional[str] = None
    originality: Optional[str] = None
    innovation_product: Optional[str] = None
    results_significance: Optional[str] = None
    coherence: Optional[str] = None
    style_quality: Optional[str] = None
    editorial_compliance: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass


class ReviewAction(str, Enum):
    """Действие фронтенда при PATCH обновлении рецензии."""
    save = "save"
    submit = "submit"


class ReviewUpdate(BaseModel):
    """Частичное обновление рецензии и действие: save/submit.

    Все поля необязательные, указывайте только изменяемые. Поле `action`
    показывает, что пользователь нажал: "Сохранить" или "Отправить".
    """
    comments: Optional[str] = None
    recommendation: Optional[Recommendation] = None
    status: Optional[ReviewStatus] = None
    importance_applicability: Optional[str] = None
    novelty_application: Optional[str] = None
    originality: Optional[str] = None
    innovation_product: Optional[str] = None
    results_significance: Optional[str] = None
    coherence: Optional[str] = None
    style_quality: Optional[str] = None
    editorial_compliance: Optional[str] = None
    action: ReviewAction


class AssignReviewerRequest(BaseModel):
    article_id: int
    reviewer_id: int
    deadline: Optional[datetime] = None


class ReviewOut(ReviewBase):
    id: int
    reviewer_id: int
    deadline: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class ReviewAssignmentOut(BaseModel):
    """Compact summary for article-level listing of reviewer assignments."""
    id: int
    article_id: int
    reviewer_id: int
    status: ReviewStatus
    recommendation: Optional[Recommendation] = None
    deadline: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    has_content: bool = False

    class Config:
        orm_mode = True


# Detailed schema for full review payload in detail endpoint
class ReviewDetail(ReviewOut):
    """Полная детальная схема рецензии (все поля модели)."""
    pass


# ----------------------------
# Editor actions
# ----------------------------
class RequestResubmission(BaseModel):
    """Запрос редактора на повторную рецензию.

    Можно (опционально) обновить дедлайн для рецензента.
    """
    deadline: Optional[datetime] = None
