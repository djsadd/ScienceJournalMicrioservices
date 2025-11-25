from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List
from jose import jwt, JWTError
from app import models, schemas, database, config

router = APIRouter(prefix="/articles", tags=["articles"])


def _file_id_to_url(file_id: str | None):
    if not file_id:
        return None
    return f"/files/{file_id}/download"


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


@router.get("/keywords", response_model=List[schemas.KeywordOut])
def list_keywords(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.query(models.Keyword).all()


@router.get("/keywords/{keyword_id}", response_model=schemas.KeywordOut)
def get_keyword(
    keyword_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    keyword = db.query(models.Keyword).filter(models.Keyword.id == keyword_id).first()
    if not keyword:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return keyword


@router.post("/keywords", response_model=schemas.KeywordOut)
def create_keyword(
    keyword: schemas.KeywordCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_author(current_user)
    new_keyword = models.Keyword(**keyword.dict())
    db.add(new_keyword)
    db.commit()
    db.refresh(new_keyword)
    return new_keyword


@router.get("/authors", response_model=List[schemas.AuthorOut])
def list_authors(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.query(models.Author).all()


@router.post("/authors", response_model=schemas.AuthorOut)
def create_author(
    author: schemas.AuthorCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_author(current_user)

    existing = db.query(models.Author).filter(models.Author.email == author.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Author with this email already exists")

    new_author = models.Author(**author.dict())
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return new_author


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


@router.post("/by_ids", response_model=schemas.ArticleOut)
def create_article_by_ids(
    article: schemas.ArticleCreateWithIds,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
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
        antiplagiarism_file_url=_file_id_to_url(article.antiplagiarism_file_id),
        not_published_elsewhere=article.not_published_elsewhere,
        plagiarism_free=article.plagiarism_free,
        authors_agree=article.authors_agree,
        generative_ai_info=article.generative_ai_info,
        manuscript_file_url=_file_id_to_url(article.manuscript_file_id),
        author_info_file_url=_file_id_to_url(article.author_info_file_id),
        cover_letter_file_url=_file_id_to_url(article.cover_letter_file_id),
    )
    db.add(new_article)
    db.flush()

    if article.author_ids:
        authors = db.query(models.Author).filter(models.Author.id.in_(article.author_ids)).all()
        if len(authors) != len(set(article.author_ids)):
            raise HTTPException(status_code=400, detail="One or more authors not found")
        for author in authors:
            db.execute(models.article_authors.insert().values(article_id=new_article.id, author_id=author.id))

    if article.keyword_ids:
        keywords = db.query(models.Keyword).filter(models.Keyword.id.in_(article.keyword_ids)).all()
        if len(keywords) != len(set(article.keyword_ids)):
            raise HTTPException(status_code=400, detail="One or more keywords not found")
        for keyword in keywords:
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
