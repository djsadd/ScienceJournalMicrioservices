from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str
    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    organization: str | None = None
    institution: str | None = None
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = "author"
    accept_terms: bool = False
    notify_status: bool = True


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    organization: str | None = None
    institution: str | None = None
    email: EmailStr
    role: str
    is_active: bool
    accept_terms: bool
    notify_status: bool

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None


class UserFullInfo(BaseModel):
    """Complete user information from Auth and User Profile services"""
    # From Auth Service
    id: int
    username: str
    full_name: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    organization: str | None = None
    institution: str | None = None
    email: EmailStr
    role: str
    is_active: bool = True
    accept_terms: bool
    notify_status: bool
    # From User Profile Service
    profile_id: int | None = None
    phone: str | None = None
    roles: list[str] = []

    class Config:
        orm_mode = True


class UserActivationUpdate(BaseModel):
    is_active: bool
