from pydantic import BaseModel
from typing import List


class UserProfileBase(BaseModel):
    full_name: str
    phone: str | None = None
    organization: str | None = None
    roles: List[str] = ["author"]


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
