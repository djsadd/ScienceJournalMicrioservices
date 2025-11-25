from sqlalchemy import Column, Integer, String, DateTime, Enum, Text
from sqlalchemy.sql import func
from app.database import Base
import enum


class TaskType(str, enum.Enum):
    metadata_extraction = "metadata_extraction"
    format_check = "format_check"
    plagiarism_check = "plagiarism_check"


class TaskStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class FileProcessingTask(Base):
    __tablename__ = "file_processing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, nullable=False)
    task_type = Column(Enum(TaskType), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending)
    result = Column(Text, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

