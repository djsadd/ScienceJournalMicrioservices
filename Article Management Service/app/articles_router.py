from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from jose import jwt, JWTError
from app import models, schemas, database, config

router = APIRouter(prefix="/articles", tags=["articles"])


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


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


def ensure_author(user):
    if "author" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="You are not allowed to create articles")


def ensure_editor(user):
    if "editor" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Editor role required")


@router.post("/", response_model=schemas.ArticleOut)
def create_article(article: schemas.ArticleCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_author(current_user)

    new_article = models.Article(
        title_kz=article.title_kz,
        title_en=article.title_en,
        title_ru=article.title_ru,
        abstract_kz=article.abstract_kz,
        abstract_en=article.abstract_en,
        abstract_ru=article.abstract_ru,
        doi=article.doi,
        status=article.status,
        article_type=article.article_type,
        responsible_user_id=article.responsible_user_id,
        antiplagiarism_file_url=article.antiplagiarism_file_url,
        not_published_elsewhere=article.not_published_elsewhere,
        plagiarism_free=article.plagiarism_free,
        authors_agree=article.authors_agree,
        generative_ai_info=article.generative_ai_info,
        manuscript_file_url=article.manuscript_file_url,
        author_info_file_url=article.author_info_file_url,
        cover_letter_file_url=article.cover_letter_file_url,
    )
    db.add(new_article)
    db.flush()

    for author_payload in article.authors:
        author = models.Author(**author_payload.dict())
        db.add(author)
        db.flush()
        db.execute(models.article_authors.insert().values(article_id=new_article.id, author_id=author.id))

    for kw in article.keywords:
        keyword = models.Keyword(**kw.dict())
        db.add(keyword)
        db.flush()
        db.execute(models.article_keywords.insert().values(article_id=new_article.id, keyword_id=keyword.id))

    db.commit()
    db.refresh(new_article)
    return new_article


@router.post("/{article_id}/versions", response_model=schemas.ArticleVersionOut)
def add_version(article_id: int, version: schemas.ArticleVersionBase, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if current_user["user_id"] != article.responsible_user_id:
        raise HTTPException(status_code=403, detail="You are not the responsible user for this article")

    max_version = db.query(models.ArticleVersion).filter(models.ArticleVersion.article_id == article_id)\
                   .order_by(models.ArticleVersion.version_number.desc()).first()
    version_number = max_version.version_number + 1 if max_version else 1

    new_version = models.ArticleVersion(
        article_id=article_id,
        file_url=version.file_url,
        version_number=version_number
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)

    article.current_version_id = new_version.id
    db.commit()
    db.refresh(article)
    return new_version


@router.patch("/{article_id}/status")
def change_status(article_id: int, status: schemas.ArticleStatus, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_editor(current_user)
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    article.status = status
    db.commit()
    db.refresh(article)
    return {"id": article.id, "status": article.status}


@router.post("/{article_id}/assign_reviewers")
def assign_reviewers(article_id: int, reviewer_ids: List[int], db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_editor(current_user)
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    for uid in reviewer_ids:
        db.execute(models.article_reviewers.insert().values(article_id=article.id, user_id=uid))
    db.commit()
    return {"message": "Reviewers assigned successfully"}
