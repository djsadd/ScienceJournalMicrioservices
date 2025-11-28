from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# Association tables
article_authors = Table(
    "article_authors",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

article_reviewers = Table(
    "article_reviewers",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("user_id", Integer, nullable=False),
)

article_keywords = Table(
    "article_keywords",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id"), primary_key=True),
    Column("keyword_id", Integer, ForeignKey("keywords.id"), primary_key=True),
)

# Association tables for article versions
article_version_authors = Table(
    "article_version_authors",
    Base.metadata,
    Column("version_id", Integer, ForeignKey("article_versions.id"), primary_key=True),
    Column("author_id", Integer, ForeignKey("authors.id"), primary_key=True),
)

article_version_keywords = Table(
    "article_version_keywords",
    Base.metadata,
    Column("version_id", Integer, ForeignKey("article_versions.id"), primary_key=True),
    Column("keyword_id", Integer, ForeignKey("keywords.id"), primary_key=True),
)


class ArticleStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    under_review = "under_review"
    accepted = "accepted"
    published = "published"
    withdrawn = "withdrawn"


class ArticleType(str, enum.Enum):
    original = "original"
    review = "review"


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, nullable=False, unique=True)
    prefix = Column(String, nullable=True)
    first_name = Column(String, nullable=False)
    patronymic = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    country = Column(String, nullable=False)
    affiliation1 = Column(String, nullable=False)
    affiliation2 = Column(String, nullable=True)
    affiliation3 = Column(String, nullable=True)
    is_corresponding = Column(Boolean, default=False)
    orcid = Column(String, nullable=True)
    scopus_author_id = Column(String, nullable=True)
    researcher_id = Column(String, nullable=True)

    articles = relationship("Article", secondary=article_authors, back_populates="authors")


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    title_kz = Column(String, nullable=False)
    title_en = Column(String, nullable=False)
    title_ru = Column(String, nullable=False)

    articles = relationship("Article", secondary=article_keywords, back_populates="keywords")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title_kz = Column(String, nullable=False)
    title_en = Column(String, nullable=False)
    title_ru = Column(String, nullable=False)
    abstract_kz = Column(String, nullable=True)
    abstract_en = Column(String, nullable=True)
    abstract_ru = Column(String, nullable=True)
    doi = Column(String, nullable=True)
    status = Column(Enum(ArticleStatus), default=ArticleStatus.draft)
    article_type = Column(Enum(ArticleType), nullable=False, default=ArticleType.original)
    responsible_user_id = Column(Integer, nullable=False)
    antiplagiarism_file_url = Column(String, nullable=True)
    not_published_elsewhere = Column(Boolean, default=False)
    plagiarism_free = Column(Boolean, default=False)
    authors_agree = Column(Boolean, default=False)
    generative_ai_info = Column(String, nullable=True)
    manuscript_file_url = Column(String, nullable=True)
    author_info_file_url = Column(String, nullable=True)
    cover_letter_file_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    current_version_id = Column(Integer, ForeignKey("article_versions.id"), nullable=True)

    # Explicit foreign_keys to avoid ambiguity with current_version_id
    versions = relationship(
        "ArticleVersion",
        back_populates="article",
        foreign_keys="ArticleVersion.article_id",
    )
    authors = relationship("Author", secondary=article_authors, back_populates="articles")
    keywords = relationship("Keyword", secondary=article_keywords, back_populates="articles")


class ArticleVersion(Base):
    __tablename__ = "article_versions"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    version_number = Column(Integer, nullable=False)
    version_code = Column(String, nullable=True)
    
    # Полный снимок статьи на момент создания версии
    title_kz = Column(String, nullable=False)
    title_en = Column(String, nullable=False)
    title_ru = Column(String, nullable=False)
    abstract_kz = Column(String, nullable=True)
    abstract_en = Column(String, nullable=True)
    abstract_ru = Column(String, nullable=True)
    doi = Column(String, nullable=True)
    article_type = Column(Enum(ArticleType), nullable=False)
    
    # Файлы
    manuscript_file_url = Column(String, nullable=True)
    antiplagiarism_file_url = Column(String, nullable=True)
    author_info_file_url = Column(String, nullable=True)
    cover_letter_file_url = Column(String, nullable=True)
    
    # Дополнительная информация
    not_published_elsewhere = Column(Boolean, default=False)
    plagiarism_free = Column(Boolean, default=False)
    authors_agree = Column(Boolean, default=False)
    generative_ai_info = Column(String, nullable=True)
    
    # Legacy поле для обратной совместимости (можно удалить позже)
    file_url = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_published = Column(Boolean, default=False)

    # Relationships
    article = relationship(
        "Article",
        back_populates="versions",
        foreign_keys=[article_id],
    )
    authors = relationship("Author", secondary=article_version_authors)
    keywords = relationship("Keyword", secondary=article_version_keywords)
