from pydantic import BaseModel
from typing import List
from enum import Enum


class Language(str, Enum):
    kz = "kz"
    ru = "ru"
    en = "en"


class UserProfileBase(BaseModel):
    full_name: str
    phone: str | None = None
    organization: str | None = None
    roles: List[str] = ["author"]
    preferred_language: Language = Language.en


class UserProfileCreate(UserProfileBase):
    user_id: int


class UserProfileOut(UserProfileBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True


class UserRolesOut(BaseModel):
    user_id: int
    roles: List[str]
    preferred_language: Language | None = None


class ArticleLinkBase(BaseModel):
    article_id: int
    role: str


class ArticleLinkOut(ArticleLinkBase):
    id: int

    class Config:
        orm_mode = True


class ReviewLinkBase(BaseModel):
    review_id: int


class ReviewLinkOut(ReviewLinkBase):
    id: int

    class Config:
        orm_mode = True


class ReviewerFullInfo(BaseModel):
    """Reviewer information for frontend (enriched)"""
    # From User Profile Service
    id: int
    user_id: int
    full_name: str
    phone: str | None = None
    organization: str | None = None
    roles: List[str] = []
    preferred_language: Language
    is_active: bool | None = None

    # From Auth - Identity Service
    username: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    institution: str | None = None

    class Config:
        orm_mode = True
