from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class FileOut(BaseModel):
    id: str
    original_name: str
    content_type: Optional[str] = None
    size_bytes: int
    url: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
