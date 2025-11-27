from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ArticleStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    accepted = "accepted"
    published = "published"
    withdrawn = "withdrawn"


class ArticleType(str, Enum):
    original = "original"
    review = "review"


class KeywordCreate(BaseModel):
    title_kz: str
    title_en: str
    title_ru: str


class KeywordOut(KeywordCreate):
    id: int

    class Config:
        orm_mode = True


class AuthorCreate(BaseModel):
    email: str
    prefix: Optional[str] = None
    first_name: str
    patronymic: Optional[str] = None
    last_name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    country: str
    affiliation1: str
    affiliation2: Optional[str] = None
    affiliation3: Optional[str] = None
    is_corresponding: bool = False
    orcid: Optional[str] = None
    scopus_author_id: Optional[str] = None
    researcher_id: Optional[str] = None


class AuthorOut(AuthorCreate):
    id: int

    class Config:
        orm_mode = True


class ArticleVersionBase(BaseModel):
    file_url: str
    version_number: int


class ArticleVersionOut(ArticleVersionBase):
    id: int
    version_code: Optional[str] = None
    created_at: datetime
    is_published: bool

    class Config:
        orm_mode = True


class ArticleCreate(BaseModel):
    title_kz: str
    title_en: str
    title_ru: str
    abstract_kz: Optional[str] = None
    abstract_en: Optional[str] = None
    abstract_ru: Optional[str] = None
    doi: Optional[str] = None
    status: ArticleStatus = ArticleStatus.draft
    article_type: ArticleType = ArticleType.original
    responsible_user_id: int
    antiplagiarism_file_url: Optional[str] = None
    not_published_elsewhere: bool = False
    plagiarism_free: bool = False
    authors_agree: bool = False
    generative_ai_info: Optional[str] = None
    manuscript_file_url: Optional[str] = None
    author_info_file_url: Optional[str] = None
    cover_letter_file_url: Optional[str] = None
    keywords: List[KeywordCreate] = Field(default_factory=list)
    authors: List[AuthorCreate] = Field(default_factory=list)


class ArticleCreateWithIds(BaseModel):
    title_kz: str
    title_en: str
    title_ru: str
    abstract_kz: Optional[str] = None
    abstract_en: Optional[str] = None
    abstract_ru: Optional[str] = None
    doi: Optional[str] = None
    status: ArticleStatus = ArticleStatus.draft
    article_type: ArticleType = ArticleType.original
    responsible_user_id: int
    antiplagiarism_file_id: Optional[str] = None
    not_published_elsewhere: bool = False
    plagiarism_free: bool = False
    authors_agree: bool = False
    generative_ai_info: Optional[str] = None
    manuscript_file_id: Optional[str] = None
    author_info_file_id: Optional[str] = None
    cover_letter_file_id: Optional[str] = None
    keyword_ids: List[int] = Field(default_factory=list)
    author_ids: List[int] = Field(default_factory=list)


class ArticleUpdate(BaseModel):
    title_kz: Optional[str] = None
    title_en: Optional[str] = None
    title_ru: Optional[str] = None
    abstract_kz: Optional[str] = None
    abstract_en: Optional[str] = None
    abstract_ru: Optional[str] = None
    doi: Optional[str] = None
    article_type: Optional[ArticleType] = None
    antiplagiarism_file_id: Optional[str] = None
    not_published_elsewhere: Optional[bool] = None
    plagiarism_free: Optional[bool] = None
    authors_agree: Optional[bool] = None
    generative_ai_info: Optional[str] = None
    manuscript_file_id: Optional[str] = None
    author_info_file_id: Optional[str] = None
    cover_letter_file_id: Optional[str] = None
    keyword_ids: Optional[List[int]] = None
    author_ids: Optional[List[int]] = None


class ArticleOut(BaseModel):
    id: int
    title_kz: str
    title_en: str
    title_ru: str
    abstract_kz: Optional[str] = None
    abstract_en: Optional[str] = None
    abstract_ru: Optional[str] = None
    doi: Optional[str] = None
    status: ArticleStatus
    article_type: ArticleType
    responsible_user_id: int
    antiplagiarism_file_url: Optional[str] = None
    not_published_elsewhere: bool
    plagiarism_free: bool
    authors_agree: bool
    generative_ai_info: Optional[str] = None
    manuscript_file_url: Optional[str] = None
    author_info_file_url: Optional[str] = None
    cover_letter_file_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    versions: List[ArticleVersionOut] = Field(default_factory=list)
    keywords: List[KeywordOut] = Field(default_factory=list)
    authors: List[AuthorOut] = Field(default_factory=list)

    class Config:
        orm_mode = True
