from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    institution = Column(String, nullable=True)  # университет/лаборатория/институт
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="author")  # author, editor, reviewer, layout, admin
    is_active = Column(Boolean, default=True)
    accept_terms = Column(Boolean, default=False)
    notify_status = Column(Boolean, default=True)
