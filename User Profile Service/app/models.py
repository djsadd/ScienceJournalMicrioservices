from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from app.database import Base
import enum

roles = ["author", "reviewer", "editor", "layout"]


class Language(str, enum.Enum):
    kz = "kz"
    ru = "ru"
    en = "en"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)  # id из Auth
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    # Предпочтительный язык пользователя (для подбора рецензентов / локализации)
    preferred_language = Column(String, nullable=False, default=Language.en.value)

    # связи
    articles = relationship("ArticleLink", back_populates="user")
    reviews = relationship("ReviewLink", back_populates="user")

    roles = Column(ARRAY(String), default=["author"])


class ArticleLink(Base):
    __tablename__ = "user_articles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    article_id = Column(Integer, nullable=False)
    role = Column(String, default="author")  # author, reviewer, editor

    user = relationship("UserProfile", back_populates="articles")


class ReviewLink(Base):
    __tablename__ = "user_reviews"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"))
    review_id = Column(Integer, nullable=False)

    user = relationship("UserProfile", back_populates="reviews")
