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


@router.get("/my", response_model=List[schemas.ArticleOut])
def list_my_articles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Список статей текущего пользователя-автора.
    Фильтр по responsible_user_id == current_user["user_id"].
    """
    from sqlalchemy.orm import joinedload
    articles = (
        db.query(models.Article)
        .options(
            joinedload(models.Article.authors),
            joinedload(models.Article.keywords)
        )
        .filter(models.Article.responsible_user_id == current_user["user_id"])
        .order_by(models.Article.created_at.desc())
        .all()
    )
    return articles


@router.get("/my/{article_id}", response_model=schemas.ArticleOut)
def get_article_detail(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Детальная страница статьи для автора.
    Доступна только ответственному пользователю (responsible_user_id).
    """
    from sqlalchemy.orm import joinedload
    article = (
        db.query(models.Article)
        .options(
            joinedload(models.Article.authors),
            joinedload(models.Article.keywords),
            joinedload(models.Article.versions)
        )
        .filter(models.Article.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    if article.responsible_user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You are not the responsible user for this article")
    return article


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
def create_article(article: schemas.ArticleCreateWithIds, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_author(current_user)

    new_article = models.Article(
        title_kz=article.title_kz,
        title_en=article.title_en,
        title_ru=article.title_ru,
        abstract_kz=article.abstract_kz,
        abstract_en=article.abstract_en,
        abstract_ru=article.abstract_ru,
        doi=article.doi,
        status=models.ArticleStatus.submitted,
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


@router.put("/{article_id}", response_model=schemas.ArticleOut)
def update_article(
    article_id: int,
    article: schemas.ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Обновление статьи с автоматическим созданием новой версии.
    Может обновить только responsible user (ответственный автор).
    При каждом обновлении создается новая версия с кодом TAU-V{номер}.
    """
    from sqlalchemy.orm import joinedload
    
    # Получаем статью
    existing_article = (
        db.query(models.Article)
        .options(
            joinedload(models.Article.authors),
            joinedload(models.Article.keywords),
            joinedload(models.Article.versions)
        )
        .filter(models.Article.id == article_id)
        .first()
    )
    
    if not existing_article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Проверка, что текущий пользователь - ответственный автор
    if existing_article.responsible_user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Only the responsible author can update this article"
        )
    
    # Обновляем только переданные поля
    update_data = article.dict(exclude_unset=True)
    
    # Обрабатываем file_id -> file_url конвертацию
    if "antiplagiarism_file_id" in update_data:
        existing_article.antiplagiarism_file_url = _file_id_to_url(update_data.pop("antiplagiarism_file_id"))
    if "manuscript_file_id" in update_data:
        existing_article.manuscript_file_url = _file_id_to_url(update_data.pop("manuscript_file_id"))
    if "author_info_file_id" in update_data:
        existing_article.author_info_file_url = _file_id_to_url(update_data.pop("author_info_file_id"))
    if "cover_letter_file_id" in update_data:
        existing_article.cover_letter_file_url = _file_id_to_url(update_data.pop("cover_letter_file_id"))
    
    # Обновляем авторов
    if "author_ids" in update_data:
        author_ids = update_data.pop("author_ids")
        # Удаляем старые связи
        db.execute(
            models.article_authors.delete().where(models.article_authors.c.article_id == article_id)
        )
        # Добавляем новые связи
        if author_ids:
            authors = db.query(models.Author).filter(models.Author.id.in_(author_ids)).all()
            if len(authors) != len(set(author_ids)):
                raise HTTPException(status_code=400, detail="One or more authors not found")
            for author in authors:
                db.execute(
                    models.article_authors.insert().values(article_id=article_id, author_id=author.id)
                )
    
    # Обновляем ключевые слова
    if "keyword_ids" in update_data:
        keyword_ids = update_data.pop("keyword_ids")
        # Удаляем старые связи
        db.execute(
            models.article_keywords.delete().where(models.article_keywords.c.article_id == article_id)
        )
        # Добавляем новые связи
        if keyword_ids:
            keywords = db.query(models.Keyword).filter(models.Keyword.id.in_(keyword_ids)).all()
            if len(keywords) != len(set(keyword_ids)):
                raise HTTPException(status_code=400, detail="One or more keywords not found")
            for keyword in keywords:
                db.execute(
                    models.article_keywords.insert().values(article_id=article_id, keyword_id=keyword.id)
                )
    
    # Обновляем остальные поля статьи
    for field, value in update_data.items():
        setattr(existing_article, field, value)
    
    # При обновлении статья автоматически получает статус "submitted"
    # (отправлено), если она не опубликована и не отозвана
    if existing_article.status not in [models.ArticleStatus.published]:
        existing_article.status = models.ArticleStatus.submitted
    
    # Создаем новую версию с префиксом TAU-V{номер}
    max_version = (
        db.query(models.ArticleVersion)
        .filter(models.ArticleVersion.article_id == article_id)
        .order_by(models.ArticleVersion.version_number.desc())
        .first()
    )
    version_number = max_version.version_number + 1 if max_version else 1
    version_code = f"TAU-V{version_number}"
    
    new_version = models.ArticleVersion(
        article_id=article_id,
        version_number=version_number,
        version_code=version_code,
        file_url=existing_article.manuscript_file_url
    )
    db.add(new_version)
    db.flush()
    
    # Обновляем ссылку на текущую версию
    existing_article.current_version_id = new_version.id
    
    db.commit()
    db.refresh(existing_article)
    
    return existing_article


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
    version_code = f"TAU-V{version_number}"

    new_version = models.ArticleVersion(
        article_id=article_id,
        file_url=version.file_url,
        version_number=version_number,
        version_code=version_code
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


@router.post("/{article_id}/withdraw")
def withdraw_article(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Отзыв статьи автором.
    Может отозвать только responsible user (ответственный автор).
    Статья переводится в статус 'withdrawn'.
    """
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Проверка, что текущий пользователь - ответственный автор
    if article.responsible_user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=403,
            detail="Only the responsible author can withdraw this article"
        )
    
    # Проверка, что статья не опубликована (опубликованные статьи нельзя отозвать)
    if article.status == models.ArticleStatus.published:
        raise HTTPException(
            status_code=400,
            detail="Published articles cannot be withdrawn"
        )
    
    # Проверка, что статья уже не отозвана
    if article.status == models.ArticleStatus.withdrawn:
        raise HTTPException(
            status_code=400,
            detail="Article is already withdrawn"
        )
    
    # Отзыв статьи
    article.status = models.ArticleStatus.withdrawn
    db.commit()
    db.refresh(article)
    
    return {
        "id": article.id,
        "status": article.status,
        "message": "Article has been successfully withdrawn"
    }
