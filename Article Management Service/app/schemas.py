from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class ArticleStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    editor_check = "editor_check"
    reviewer_check = "reviewer_check"
    sent_for_revision = "sent_for_revision"
    accepted = "accepted"
    rejected = "rejected"
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


class ArticleVersionOut(BaseModel):
    id: int
    article_id: int
    version_number: int
    version_code: Optional[str] = None
    
    # Полный снимок статьи
    title_kz: str
    title_en: str
    title_ru: str
    abstract_kz: Optional[str] = None
    abstract_en: Optional[str] = None
    abstract_ru: Optional[str] = None
    doi: Optional[str] = None
    article_type: ArticleType
    
    # Файлы
    manuscript_file_url: Optional[str] = None
    antiplagiarism_file_url: Optional[str] = None
    author_info_file_url: Optional[str] = None
    cover_letter_file_url: Optional[str] = None
    
    # Дополнительная информация
    not_published_elsewhere: bool
    plagiarism_free: bool
    authors_agree: bool
    generative_ai_info: Optional[str] = None
    
    # Legacy поле для обратной совместимости
    file_url: Optional[str] = None
    
    created_at: datetime
    is_published: bool
    
    # Авторы и ключевые слова на момент создания версии
    authors: List[AuthorOut] = Field(default_factory=list)
    keywords: List[KeywordOut] = Field(default_factory=list)

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
    assigned_editor_id: int | None = None
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


class AssignedEditorUpdate(BaseModel):
    editor_id: int | None = None


class AssignReviewerRequest(BaseModel):
    reviewer_ids: List[int] = Field(..., min_items=1, description="List of reviewer user IDs to assign")
    deadline: Optional[datetime] = None


class ArticleStatusUpdate(BaseModel):
    status: ArticleStatus


class VolumeBase(BaseModel):
    year: int
    number: int
    month: int | None = Field(default=None, ge=1, le=12, description="Month number 1-12")
    title_kz: str | None = None
    title_en: str | None = None
    title_ru: str | None = None
    description: str | None = None
    is_active: bool = True


class VolumeCreate(VolumeBase):
    article_ids: List[int] = Field(default_factory=list, description="IDs of published articles to include")


class VolumeUpdate(BaseModel):
    year: int | None = None
    number: int | None = None
    month: int | None = Field(default=None, ge=1, le=12)
    title_kz: str | None = None
    title_en: str | None = None
    title_ru: str | None = None
    description: str | None = None
    is_active: bool | None = None
    article_ids: List[int] | None = Field(default=None, description="Override list of article IDs in volume")


class VolumeOut(VolumeBase):
    id: int
    published_at: datetime
    articles: List[ArticleOut] = Field(default_factory=list)

    class Config:
        orm_mode = True
