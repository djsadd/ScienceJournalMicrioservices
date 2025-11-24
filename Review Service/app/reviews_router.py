from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from jose import jwt, JWTError
from app import models, schemas, database, config

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
def get_current_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    token = authorization.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        user_id = payload.get("sub")
        roles = payload.get("roles", ["author"])
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": int(user_id), "roles": roles}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ----------------------------
# CREATE REVIEW (только reviewer)
# ----------------------------
@router.post("/", response_model=schemas.ReviewOut)
def create_review(review: schemas.ReviewCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if "reviewer" not in current_user["roles"]:
        raise HTTPException(status_code=403, detail="You are not allowed to create reviews")
    
    new_review = models.Review(
        article_id=review.article_id,
        reviewer_id=current_user["user_id"],
        comments=review.comments,
        recommendation=review.recommendation,
        status=review.status
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

# ----------------------------
# GET REVIEWS FOR ARTICLE
# ----------------------------
@router.get("/article/{article_id}", response_model=List[schemas.ReviewOut])
def get_reviews(article_id: int, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).filter(models.Review.article_id == article_id).all()
    return reviews

# ----------------------------
# UPDATE REVIEW (только автор рецензии)
# ----------------------------
@router.patch("/{review_id}", response_model=schemas.ReviewOut)
def update_review(review_id: int, review: schemas.ReviewBase, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    db_review = db.query(models.Review).filter(models.Review.id == review_id).first()
    if not db_review:
        raise HTTPException(status_code=404, detail="Review not found")
    if db_review.reviewer_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only edit your own reviews")
    
    db_review.comments = review.comments
    db_review.recommendation = review.recommendation
    db_review.status = review.status
    db.commit()
    db.refresh(db_review)
    return db_review
