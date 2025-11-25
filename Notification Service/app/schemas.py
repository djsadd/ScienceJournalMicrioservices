from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class NotificationStatus(str, Enum):
    unread = "unread"
    read = "read"


class NotificationType(str, Enum):
    system = "system"
    article_status = "article_status"
    review_assignment = "review_assignment"
    editorial = "editorial"
    custom = "custom"


class NotificationBase(BaseModel):
    user_id: int
    type: NotificationType = NotificationType.system
    title: str
    message: str
    related_entity: Optional[str] = None


class NotificationCreate(NotificationBase):
    pass


class NotificationUpdateStatus(BaseModel):
    status: NotificationStatus


class NotificationOut(NotificationBase):
    id: int
    status: NotificationStatus
    created_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        orm_mode = True

