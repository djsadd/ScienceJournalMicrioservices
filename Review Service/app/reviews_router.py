from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from jose import jwt, JWTError
from app import models, schemas, database, config
import httpx

router = APIRouter(prefix="/reviews", tags=["reviews"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----------------------------
# JWT dependency
# ----------------------------
def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_user_roles: Optional[str] = Header(default=None, alias="X-User-Roles"),
):
    # Prefer JWT from Authorization if provided
    if authorization:
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")
        token = authorization.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
            user_id = payload.get("sub")
            roles = payload.get("roles")
            # Normalize roles to a list
            if isinstance(roles, str):
                roles = [r.strip() for r in roles.split(",") if r.strip()] or ["author"]
            elif isinstance(roles, list):
                roles = [str(r).strip() for r in roles if str(r).strip()] or ["author"]
            else:
                roles = ["author"]
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid token")
            return {"user_id": int(user_id), "roles": roles}
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")

    # Fallback: trust identity forwarded by API Gateway
    if x_user_id:
        roles = [r.strip() for r in (x_user_roles or "").split(",") if r.strip()] or ["author"]
        try:
            return {"user_id": int(x_user_id), "roles": roles}
        except ValueError:
            raise HTTPException(status_code=401, detail="Invalid forwarded user id")

    # If neither provided, return 401 (not 422)
    raise HTTPException(status_code=401, detail="Missing Authorization header")

# ----------------------------
# CREATE REVIEW (только reviewer)
# ----------------------------
@router.post("/", response_model=schemas.ReviewOut)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    
    new_review = models.Review(
        article_id=review.article_id,
        reviewer_id=current_user["user_id"],
        comments=review.comments,
        recommendation=review.recommendation,
        status=review.status,
        importance_applicability=review.importance_applicability,
        novelty_application=review.novelty_application,
        originality=review.originality,
        innovation_product=review.innovation_product,
        results_significance=review.results_significance,
        coherence=review.coherence,
        style_quality=review.style_quality,
        editorial_compliance=review.editorial_compliance,
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review


# ----------------------------
# ASSIGN REVIEWER (вызывается Article Service)
# ----------------------------
@router.post("/assign", response_model=schemas.ReviewOut)
def assign_reviewer(request: schemas.AssignReviewerRequest, db: Session = Depends(get_db)):
    """
    Создание записи Review при назначении рецензента редактором.
    Этот эндпоинт вызывается из Article Management Service.
    """
    # Проверяем, не существует ли уже Review для этой статьи и рецензента
    existing_review = db.query(models.Review).filter(
        models.Review.article_id == request.article_id,
        models.Review.reviewer_id == request.reviewer_id
    ).first()
    
    if existing_review:
        # Если уже существует, возвращаем существующую запись
        return existing_review
    
    # Создаем новую запись Review со статусом pending
    new_review = models.Review(
        article_id=request.article_id,
        reviewer_id=request.reviewer_id,
        deadline=request.deadline,
        status=models.ReviewStatus.pending
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

# ----------------------------
# GET REVIEWS FOR ARTICLE (compact summary)
# ----------------------------
@router.get("/article/{article_id}", response_model=List[schemas.ReviewAssignmentOut])
def get_reviews(article_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).filter(models.Review.article_id == article_id).all()
    result = []
    for r in reviews:
        has_content = any([
            r.comments,
            r.importance_applicability,
            r.novelty_application,
            r.originality,
            r.innovation_product,
            r.results_significance,
            r.coherence,
            r.style_quality,
            r.editorial_compliance,
        ])
        result.append({
            "id": r.id,
            "article_id": r.article_id,
            "reviewer_id": r.reviewer_id,
            "status": r.status,
            "recommendation": r.recommendation,
            "deadline": r.deadline,
            "updated_at": r.updated_at,
            "has_content": bool(has_content),
        })
    return result

# ----------------------------
# UPDATE REVIEW (только автор рецензии)
# ----------------------------
@router.patch("/{review_id}", response_model=schemas.ReviewOut)
def update_review(review_id: int, review: schemas.ReviewUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.reviewer_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only edit your own reviews")
    # Prevent edits if already submitted (completed)
    if db_review.status == models.ReviewStatus.completed:
        raise HTTPException(status_code=400, detail="Submitted reviews cannot be edited")
    
    # Apply partial updates only for provided fields
    if review.comments is not None:
        db_review.comments = review.comments
    if review.recommendation is not None:
        db_review.recommendation = review.recommendation
    if review.status is not None:
        db_review.status = review.status
    if review.importance_applicability is not None:
        db_review.importance_applicability = review.importance_applicability
    if review.novelty_application is not None:
        db_review.novelty_application = review.novelty_application
    if review.originality is not None:
        db_review.originality = review.originality
    if review.innovation_product is not None:
        db_review.innovation_product = review.innovation_product
    if review.results_significance is not None:
        db_review.results_significance = review.results_significance
    if review.coherence is not None:
        db_review.coherence = review.coherence
    if review.style_quality is not None:
        db_review.style_quality = review.style_quality
    if review.editorial_compliance is not None:
        db_review.editorial_compliance = review.editorial_compliance

    # Handle action: save -> in_progress, submit -> completed
    if review.action == schemas.ReviewAction.save:
        db_review.status = models.ReviewStatus.in_progress
    elif review.action == schemas.ReviewAction.submit:
        db_review.status = models.ReviewStatus.completed
    db.commit()
    db.refresh(db_review)
    # Если отправлено, уведомляем Article Management Service
    try:
        if db_review.status == models.ReviewStatus.completed:
            api_gateway = getattr(config, 'API_GATEWAY_URL', 'http://localhost:8000')
            shared_secret = getattr(config, 'SHARED_SERVICE_SECRET', 'service-shared-secret')
            with httpx.Client(timeout=5.0) as client:
                client.patch(
                    f"{api_gateway}/articles/internal/{db_review.article_id}/review-submitted",
                    headers={"X-Service-Secret": shared_secret}
                )
    except Exception:
        # Не блокируем ответ рецензенту, если межсервисный вызов не удался
        pass
    return db_review


# ----------------------------
# REQUEST RESUBMISSION (только редактор)
# ----------------------------
@router.patch("/{review_id}/request-resubmission", response_model=schemas.ReviewOut)
def request_resubmission(
    review_id: int,
    payload: Optional[schemas.RequestResubmission] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    roles = current_user.get("roles", [])
    if "editor" not in roles:
        raise HTTPException(status_code=403, detail="Editor role required")

    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")

    if payload and payload.deadline is not None:
        db_review.deadline = payload.deadline

    db_review.status = models.ReviewStatus.resubmission
    db.commit()
    db.refresh(db_review)
    return db_review


# ----------------------------
# GET REVIEWS BY REVIEWER (рецензент видит свои задания)
# ----------------------------
@router.get("/my-reviews", response_model=List[schemas.ReviewOut])
def get_my_reviews(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Получение списка всех рецензий, назначенных текущему пользователю.
    Роли не проверяются; фильтрация только по идентификатору пользователя.
    """
    
    reviews = db.query(models.Review).filter(
        models.Review.reviewer_id == current_user["user_id"]
    ).all()
    
    return reviews


# ----------------------------
# GET SINGLE REVIEW (рецензент или редактор)
# Полный ответ по всем полям модели
# ----------------------------
@router.get(
    "/{review_id}",
    response_model=schemas.ReviewDetail,
    response_model_exclude_none=False,
)
def get_review(review_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    roles = current_user.get("roles", [])
    if ("editor" not in roles) and (db_review.reviewer_id != current_user["user_id"]):
        raise HTTPException(status_code=403, detail="Not allowed to view this review")
    return db_review


# ----------------------------
# GET DETAILED REVIEW (только назначенный рецензент)
# ----------------------------
@router.get(
    "/{review_id}/detail",
    response_model=schemas.ReviewDetail,
)
def get_review_detail(review_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """Детальный просмотр рецензии без проверки роли, но только для назначенного рецензента.

    Возвращаются ключевые поля, которые заполняет рецензент:
    comments, recommendation, status, deadline, importance_applicability,
    novelty_application, originality, innovation_product, results_significance,
    coherence, style_quality, editorial_compliance (и базовые служебные поля схемы).
    """
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.reviewer_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only view your assigned reviews")
    return db_review
