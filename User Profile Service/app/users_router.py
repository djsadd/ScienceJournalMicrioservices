from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from app import models, schemas, database, security
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


@router.get("/{user_id}", response_model=schemas.UserProfileOut)
def get_profile(user_id: int, db: Session = Depends(get_db)):
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/me/roles", response_model=schemas.UserRolesOut)
async def get_user_roles(current=Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current["user_id"]
    profile = db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"user_id": user_id, "roles": profile.roles or []}
