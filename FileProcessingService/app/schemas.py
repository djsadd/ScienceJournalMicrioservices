from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskType(str, Enum):
    metadata_extraction = "metadata_extraction"
    format_check = "format_check"
    plagiarism_check = "plagiarism_check"


class TaskStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class TaskCreate(BaseModel):
    file_id: str
    task_type: TaskType


class TaskOut(BaseModel):
    id: int
    file_id: str
    task_type: TaskType
    status: TaskStatus
    result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

