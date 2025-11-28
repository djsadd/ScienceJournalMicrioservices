from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
import httpx
from jose import jwt, JWTError
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
    
    # Editors and reviewers require approval - set is_active to False
    is_active = user.role not in ["editor", "reviewer"]
    
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
        is_active=is_active,
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
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=403, 
            detail="Account is pending approval. Please wait for administrator confirmation."
        )
    
    # JWT spec expects `sub` to be a string; cast user.id accordingly
    access_token = security.create_access_token({"sub": str(user.id), "roles": [user.role]})
    refresh_token = security.create_refresh_token({"sub": str(user.id)})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def get_current_user_id(authorization: str = Header(None)) -> int:
    """Extract user_id from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = parts[1]
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return int(user_id)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_active_user(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)) -> models.User:
    """Get current user and verify they are active"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive. Please contact administrator."
        )
    return user


@router.get("/me", response_model=schemas.UserFullInfo)
def get_user_full_info(
    user: models.User = Depends(get_current_active_user)
):
    """Get complete user information from Auth and User Profile services"""
    # User is already fetched and validated by get_current_active_user
    
    # Prepare response with auth data
    user_info = {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "organization": user.organization,
        "institution": user.institution,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "accept_terms": user.accept_terms,
        "notify_status": user.notify_status,
        "profile_id": None,
        "phone": None,
        "roles": [user.role],
    }
    
    # Try to get profile from User Profile Service
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{config.USER_SERVICE_URL}/users/{user.id}")
            if response.status_code == 200:
                profile_data = response.json()
                user_info["profile_id"] = profile_data.get("id")
                user_info["phone"] = profile_data.get("phone")
                user_info["roles"] = profile_data.get("roles", [user.role])
                # Update organization from profile if it's more recent
                if profile_data.get("organization"):
                    user_info["organization"] = profile_data.get("organization")
    except Exception:
        # Fail-soft: return auth data even if profile service is unavailable
        pass
    
    return user_info


@router.get("/users/{user_id}", response_model=schemas.UserOut)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Получить информацию о пользователе по ID.
    Внутренний эндпоинт для межсервисного взаимодействия.
    """
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Admin endpoints
def require_admin(user: models.User = Depends(get_current_active_user)) -> models.User:
    """Verify that current user has admin role"""
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return user


@router.get("/admin/pending-users", response_model=list[schemas.UserOut])
def get_pending_users(
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get all users waiting for activation (editors and reviewers)"""
    pending_users = db.query(models.User).filter(
        models.User.is_active == False,
        models.User.role.in_(["editor", "reviewer"])
    ).all()
    return pending_users


@router.patch("/admin/users/{user_id}/activate", response_model=schemas.UserOut)
def activate_user(
    user_id: int,
    activation: schemas.UserActivationUpdate,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a user account"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = activation.is_active
    db.commit()
    db.refresh(user)
    return user
