from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum


class NotificationStatus(str, enum.Enum):
    unread = "unread"
    read = "read"


class NotificationType(str, enum.Enum):
    system = "system"
    article_status = "article_status"
    review_assignment = "review_assignment"
    editorial = "editorial"
    custom = "custom"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    type = Column(Enum(NotificationType), default=NotificationType.system, nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    related_entity = Column(String, nullable=True)  # e.g. "article:123"
    status = Column(Enum(NotificationStatus), default=NotificationStatus.unread, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

