from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.models import WorkflowStatus


class EditorialTaskBase(BaseModel):
    article_id: int
    reviewer_ids: Optional[List[int]] = None


class EditorialTaskCreate(EditorialTaskBase):
    pass


class EditorialTaskUpdate(BaseModel):
    status: WorkflowStatus
    decision: Optional[str] = None
    decision_comment: Optional[str] = None
    reviewer_ids: Optional[List[int]] = None


class EditorialTaskOut(EditorialTaskBase):
    id: int
    editor_id: int
    status: WorkflowStatus
    decision: Optional[str] = None
    decision_comment: Optional[str] = None
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ReassignEditorRequest(BaseModel):
    new_editor_id: int
