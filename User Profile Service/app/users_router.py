from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from app import models, schemas, database, security
from app import config
import httpx

router = APIRouter(prefix="/users", tags=["users"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(request: Request, authorization: str = Header(None)):
    """Resolve current user using data forwarded by API gateway.

    Gateway is expected to validate JWT and pass X-User-Id / X-User-Roles headers.
    For direct calls (e.g. local testing), fall back to JWT decoding from Authorization.
    """
    # Preferred path: trust identity forwarded by API gateway
    forwarded_user_id = request.headers.get("X-User-Id")
    if forwarded_user_id:
        roles_header = request.headers.get("X-User-Roles", "")
        roles = [r for r in roles_header.split(",") if r] if roles_header else []
        try:
            return {"user_id": int(forwarded_user_id), "roles": roles}
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid forwarded user id")

    # Fallback: decode JWT locally for direct access (non-gateway)
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")

    parts = authorization.split()
    if len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    scheme, token = parts
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization scheme")

    from app.config import SECRET_KEY, ALGORITHM
    from jose import jwt, JWTError

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        roles = payload.get("roles", [])
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": int(user_id), "roles": roles}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/", response_model=schemas.UserProfileOut)
def create_profile(profile: schemas.UserProfileCreate, db: Session = Depends(get_db)):
    db_profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == profile.user_id).first()
    if db_profile:
        raise HTTPException(status_code=400, detail="Profile already exists")
    new_profile = models.UserProfile(**profile.dict())
    db.add(new_profile)
    db.commit()
    db.refresh(new_profile)
    return new_profile


@router.get("/me/roles", response_model=schemas.UserRolesOut)
async def get_user_roles(current=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current["user_id"]
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"user_id": user_id, "roles": profile.roles or [], "preferred_language": profile.preferred_language}


@router.patch("/me/language", response_model=schemas.UserProfileOut)
async def update_language(preferred_language: schemas.Language, current=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current["user_id"]
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile.preferred_language = preferred_language.value
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/reviewers", response_model=list[schemas.ReviewerFullInfo])
def get_reviewers(
    db: Session = Depends(get_db),
    language: str | None = None,
    current=Depends(get_current_user),
):
    """
    Получить список всех рецензентов (пользователей с ролью 'reviewer').
    Возвращает полную информацию, обогащённую данными из Auth-сервиса.
    Опциональная фильтрация по предпочитаемому языку.
    Доступно только для роли 'editor'.
    """
    # Проверка роли
    roles = current.get("roles", [])
    if "editor" not in roles:
        raise HTTPException(status_code=403, detail="Editor role required")

    query = db.query(models.UserProfile).filter(
        models.UserProfile.roles.contains(["reviewer"]) 
    )

    if language:
        query = query.filter(models.UserProfile.preferred_language == language)

    reviewers = query.all()

    enriched: list[dict] = []
    with httpx.Client(timeout=5.0) as client:
        for reviewer in reviewers:
            item = {
                "id": reviewer.id,
                "user_id": reviewer.user_id,
                "full_name": reviewer.full_name,
                "phone": reviewer.phone,
                "organization": reviewer.organization,
                "roles": reviewer.roles or [],
                "preferred_language": reviewer.preferred_language,
                "is_active": reviewer.is_active,
                # defaults for auth data
                "username": None,
                "email": None,
                "first_name": None,
                "last_name": None,
                "institution": None,
            }
            try:
                auth_resp = client.get(f"{config.AUTH_SERVICE_URL}/auth/users/{reviewer.user_id}")
                if auth_resp.status_code == 200:
                    auth_data = auth_resp.json()
                    item.update({
                        "username": auth_data.get("username"),
                        "email": auth_data.get("email"),
                        "first_name": auth_data.get("first_name"),
                        "last_name": auth_data.get("last_name"),
                        "institution": auth_data.get("institution"),
                        # prefer is_active from auth if present
                        "is_active": auth_data.get("is_active", item["is_active"]),
                    })
                    # если в профиле нет organization, возьмём из auth
                    if not item.get("organization") and auth_data.get("organization"):
                        item["organization"] = auth_data.get("organization")
            except Exception:
                # fail-soft: отдаём профиль без auth-данных
                pass
            enriched.append(item)

    return enriched


@router.get("/{user_id}", response_model=schemas.UserProfileOut)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
