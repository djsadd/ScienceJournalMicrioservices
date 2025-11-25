from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
from app import models, schemas, database, security, config

router = APIRouter(prefix="/auth", tags=["auth"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter((models.User.username == user.username) | (models.User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    hashed_password = security.hash_password(user.password)
    new_user = models.User(
        username=user.username,
        full_name=user.full_name,
        first_name=user.first_name,
        last_name=user.last_name,
        organization=user.organization,
        institution=user.institution,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        accept_terms=user.accept_terms,
        notify_status=user.notify_status,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create profile in User Profile Service
    try:
        profile_payload = {
            "user_id": new_user.id,
            "full_name": new_user.full_name or new_user.username,
            "roles": [new_user.role],
            "organization": new_user.organization,
            "phone": None,
        }
        with httpx.Client(timeout=5.0) as client:
            # Call users service with trailing slash to avoid FastAPI 307 redirect
            client.post(f"{config.USER_SERVICE_URL}/users/", json=profile_payload)
    except Exception:
        # Fail-soft: auth registration succeeds even if profile call fails
        pass

    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    # JWT spec expects `sub` to be a string; cast user.id accordingly
    access_token = security.create_access_token({"sub": str(user.id), "roles": [user.role]})
    refresh_token = security.create_refresh_token({"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
