from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from jose import jwt, JWTError
import httpx
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


def _create_article_version_snapshot(db: Session, article: models.Article, version_number: int, version_code: str) -> models.ArticleVersion:
    """
    Создает полный снимок статьи в виде версии.
    Сохраняет все данные статьи, включая авторов и ключевые слова.
    """
    new_version = models.ArticleVersion(
        article_id=article.id,
        version_number=version_number,
        version_code=version_code,
        # Полный снимок данных статьи
        title_kz=article.title_kz,
        title_en=article.title_en,
        title_ru=article.title_ru,
        abstract_kz=article.abstract_kz,
        abstract_en=article.abstract_en,
        abstract_ru=article.abstract_ru,
        doi=article.doi,
        article_type=article.article_type,
        manuscript_file_url=article.manuscript_file_url,
        antiplagiarism_file_url=article.antiplagiarism_file_url,
        author_info_file_url=article.author_info_file_url,
        cover_letter_file_url=article.cover_letter_file_url,
        not_published_elsewhere=article.not_published_elsewhere,
        plagiarism_free=article.plagiarism_free,
        authors_agree=article.authors_agree,
        generative_ai_info=article.generative_ai_info,
        # Legacy поле для обратной совместимости
        file_url=article.manuscript_file_url,
    )
    db.add(new_version)
    db.flush()
    
    # Копируем авторов
    for author in article.authors:
        db.execute(
            models.article_version_authors.insert().values(
                version_id=new_version.id,
                author_id=author.id
            )
        )
    
    # Копируем ключевые слова
    for keyword in article.keywords:
        db.execute(
            models.article_version_keywords.insert().values(
                version_id=new_version.id,
                keyword_id=keyword.id
            )
        )
    
    return new_version


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


@router.get("/unassigned")
def list_unassigned_articles(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    # Фильтры
    status: str = None,
    author_name: str = None,
    year: int = None,
    article_type: str = None,
    keywords: str = None,
    search: str = None,
    # Пагинация
    page: int = 1,
    page_size: int = 10,
):
    """
    Список неназначенных статей для редактора с фильтрацией и пагинацией.
    
    Параметры фильтрации:
    - status: Статус статьи (submitted, under_review, accepted, published, withdrawn, draft)
    - author_name: Поиск по имени автора (частичное совпадение)
    - year: Год создания статьи
    - article_type: Тип статьи (original, review)
    - keywords: Ключевые слова через запятую (поиск по любому из них)
    - search: Общий поиск по заголовку и аннотации (на всех языках)
    
    Параметры пагинации:
    - page: Номер страницы (начиная с 1)
    - page_size: Количество элементов на странице (по умолчанию 10)
    
    Возвращает статьи со статусом 'submitted' по умолчанию.
    Доступно только для пользователей с ролью 'editor'.
    """
    ensure_editor(current_user)
    
    from sqlalchemy.orm import joinedload
    from sqlalchemy import extract, or_, and_
    
    # Базовый запрос
    query = (
        db.query(models.Article)
        .options(
            joinedload(models.Article.authors),
            joinedload(models.Article.keywords)
        )
    )
    
    # Фильтр по статусу (по умолчанию только submitted)
    if status:
        try:
            status_enum = models.ArticleStatus(status)
            query = query.filter(models.Article.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    else:
        # По умолчанию показываем только submitted статьи
        query = query.filter(models.Article.status == models.ArticleStatus.submitted)
    
    # Фильтр по автору
    if author_name:
        query = query.join(models.Article.authors).filter(
            or_(
                models.Author.first_name.ilike(f"%{author_name}%"),
                models.Author.last_name.ilike(f"%{author_name}%"),
                models.Author.patronymic.ilike(f"%{author_name}%")
            )
        )
    
    # Фильтр по году
    if year:
        query = query.filter(extract('year', models.Article.created_at) == year)
    
    # Фильтр по типу статьи
    if article_type:
        try:
            type_enum = models.ArticleType(article_type)
            query = query.filter(models.Article.article_type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid article type: {article_type}")
    
    # Фильтр по ключевым словам
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        if keyword_list:
            keyword_filters = []
            for keyword_text in keyword_list:
                keyword_filters.append(
                    or_(
                        models.Keyword.title_kz.ilike(f"%{keyword_text}%"),
                        models.Keyword.title_en.ilike(f"%{keyword_text}%"),
                        models.Keyword.title_ru.ilike(f"%{keyword_text}%")
                    )
                )
            query = query.join(models.Article.keywords).filter(or_(*keyword_filters))
    
    # Общий поиск по заголовку и аннотации
    if search:
        search_filter = or_(
            models.Article.title_kz.ilike(f"%{search}%"),
            models.Article.title_en.ilike(f"%{search}%"),
            models.Article.title_ru.ilike(f"%{search}%"),
            models.Article.abstract_kz.ilike(f"%{search}%"),
            models.Article.abstract_en.ilike(f"%{search}%"),
            models.Article.abstract_ru.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Подсчет общего количества записей
    total_count = query.distinct().count()
    
    # Применяем сортировку и пагинацию
    query = query.distinct().order_by(models.Article.created_at.desc())
    
    # Валидация параметров пагинации
    if page < 1:
        raise HTTPException(status_code=400, detail="Page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Page size must be between 1 and 100")
    
    offset = (page - 1) * page_size
    articles = query.offset(offset).limit(page_size).all()
    
    # Рассчитываем информацию о пагинации
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
    
    return {
        "items": articles,
        "pagination": {
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


@router.get("/editor/{article_id}", response_model=schemas.ArticleOut)
def get_article_detail_for_editor(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Детальная страница рукописи для редактора.
    Доступна только пользователям с ролью 'editor'.
    Возвращает полную информацию о статье, включая авторов, ключевые слова и версии.
    """
    ensure_editor(current_user)
    
    from sqlalchemy.orm import joinedload
    article = (
        db.query(models.Article)
        .options(
            joinedload(models.Article.authors),
            joinedload(models.Article.keywords),
            joinedload(models.Article.versions).joinedload(models.ArticleVersion.authors),
            joinedload(models.Article.versions).joinedload(models.ArticleVersion.keywords)
        )
        .filter(models.Article.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return article


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


@router.get("/my/{article_id}/file")
async def get_article_manuscript(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Получение ссылки на файл рукописи статьи.
    Доступна только ответственному пользователю (responsible_user_id).
    Делает запрос к микросервису FileProcessing для получения ссылки на скачивание.
    """
    article = (
        db.query(models.Article)
        .filter(models.Article.id == article_id)
        .first()
    )
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article.responsible_user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You are not the responsible user for this article")
    
    if not article.manuscript_file_url:
        raise HTTPException(status_code=404, detail="Manuscript file not found")
    
    # Извлекаем file_id из manuscript_file_url (формат: /files/{file_id}/download)
    try:
        file_id = article.manuscript_file_url.split("/files/")[1].split("/download")[0]
    except (IndexError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid manuscript file URL")
    
    # Запрос к микросервису FileProcessing для получения ссылки на файл
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{config.FILE_SERVICE_URL}/files/{file_id}",
                timeout=10.0
            )
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="File not found in storage")
            elif response.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to retrieve file from storage service")
            
            file_data = response.json()
            
            return {
                "article_id": article_id,
                "file_id": file_id,
                "download_url": f"{config.API_GATEWAY_URL}/files/{file_id}/download",
                "filename": file_data.get("filename"),
                "file_size": file_data.get("file_size"),
                "content_type": file_data.get("content_type"),
                "uploaded_at": file_data.get("uploaded_at")
            }
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="File service timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to connect to file service: {str(e)}")


@router.get("/my/{article_id}/file/download")
async def download_article_manuscript(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Прямое скачивание файла рукописи статьи.
    Доступна только ответственному пользователю (responsible_user_id).
    Проксирует файл из микросервиса FileProcessing.
    """
    article = (
        db.query(models.Article)
        .filter(models.Article.id == article_id)
        .first()
    )
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    if article.responsible_user_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You are not the responsible user for this article")
    
    if not article.manuscript_file_url:
        raise HTTPException(status_code=404, detail="Manuscript file not found")
    
    # Извлекаем file_id из manuscript_file_url
    try:
        file_id = article.manuscript_file_url.split("/files/")[1].split("/download")[0]
    except (IndexError, AttributeError):
        raise HTTPException(status_code=400, detail="Invalid manuscript file URL")
    
    # Запрос к микросервису FileProcessing для скачивания файла
    try:
        async with httpx.AsyncClient() as client:
            # Сначала получаем метаданные файла
            metadata_response = await client.get(
                f"{config.FILE_SERVICE_URL}/files/{file_id}",
                timeout=10.0
            )
            
            if metadata_response.status_code == 404:
                raise HTTPException(status_code=404, detail="File not found in storage")
            elif metadata_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to retrieve file metadata")
            
            file_data = metadata_response.json()
            filename = file_data.get("filename", "manuscript.pdf")
            content_type = file_data.get("content_type", "application/octet-stream")
            
            # Теперь скачиваем сам файл
            download_response = await client.get(
                f"{config.FILE_SERVICE_URL}/files/{file_id}/download",
                timeout=30.0
            )
            
            if download_response.status_code != 200:
                raise HTTPException(status_code=502, detail="Failed to download file from storage service")
            
            # Возвращаем файл с правильными заголовками
            return StreamingResponse(
                iter([download_response.content]),
                media_type=content_type,
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Length": str(len(download_response.content))
                }
            )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="File service timeout")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Failed to connect to file service: {str(e)}")


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
    
    # Создаем полный снимок статьи
    new_version = _create_article_version_snapshot(
        db=db,
        article=existing_article,
        version_number=version_number,
        version_code=version_code
    )
    
    # Обновляем ссылку на текущую версию
    existing_article.current_version_id = new_version.id
    
    db.commit()
    db.refresh(existing_article)
    
    return existing_article


@router.post("/{article_id}/versions", response_model=schemas.ArticleVersionOut)
def add_version(article_id: int, version: schemas.ArticleVersionBase, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    """
    Создание новой версии статьи.
    Доступна только ответственному пользователю (responsible_user_id).
    Создает полный снимок статьи на текущий момент.
    """
    from sqlalchemy.orm import joinedload
    
    article = (
        db.query(models.Article)
        .options(
            joinedload(models.Article.authors),
            joinedload(models.Article.keywords)
        )
        .filter(models.Article.id == article_id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    if current_user["user_id"] != article.responsible_user_id:
        raise HTTPException(status_code=403, detail="You are not the responsible user for this article")

    max_version = db.query(models.ArticleVersion).filter(models.ArticleVersion.article_id == article_id)\
                   .order_by(models.ArticleVersion.version_number.desc()).first()
    version_number = max_version.version_number + 1 if max_version else 1
    version_code = f"TAU-V{version_number}"

    # Создаем полный снимок статьи
    new_version = _create_article_version_snapshot(
        db=db,
        article=article,
        version_number=version_number,
        version_code=version_code
    )

    article.current_version_id = new_version.id
    db.commit()
    db.refresh(new_version)
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
async def assign_reviewers(
    article_id: int, 
    request: schemas.AssignReviewerRequest,
    db: Session = Depends(get_db), 
    current_user: dict = Depends(get_current_user)
):
    """
    Назначение рецензентов на статью (только для редакторов).
    Создает записи в таблице article_reviewers и отправляет запрос в Review Service для создания Review записей.
    """
    ensure_editor(current_user)
    
    # Проверяем существование статьи
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Сохраняем связь article-reviewers в Article Management Service
    for reviewer_id in request.reviewer_ids:
        # Проверяем, не назначен ли уже этот рецензент
        existing = db.execute(
            models.article_reviewers.select().where(
                models.article_reviewers.c.article_id == article_id,
                models.article_reviewers.c.user_id == reviewer_id
            )
        ).first()
        
        if not existing:
            db.execute(
                models.article_reviewers.insert().values(
                    article_id=article.id, 
                    user_id=reviewer_id
                )
            )
    
    db.commit()
    
    # Отправляем запрос в Review Service для создания Review записей
    review_service_url = config.REVIEW_SERVICE_URL if hasattr(config, 'REVIEW_SERVICE_URL') else "http://reviews:8000"
    
    async with httpx.AsyncClient() as client:
        try:
            for reviewer_id in request.reviewer_ids:
                payload = {
                    "article_id": article_id,
                    "reviewer_id": reviewer_id
                }
                if request.deadline is not None:
                    try:
                        payload["deadline"] = request.deadline.isoformat()
                    except Exception:
                        payload["deadline"] = str(request.deadline)

                response = await client.post(
                    f"{review_service_url}/reviews/assign",
                    json=payload,
                    timeout=10.0
                )
                if response.status_code != 200 and response.status_code != 201:
                    print(f"Warning: Failed to create review in Review Service for reviewer {reviewer_id}: {response.text}")
        except Exception as e:
            print(f"Error communicating with Review Service: {e}")
            # Продолжаем работу, даже если Review Service недоступен
    
    return {"message": "Reviewers assigned successfully", "article_id": article_id, "reviewer_ids": request.reviewer_ids}


@router.get("/{article_id}/reviewers")
def get_article_reviewers(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Получение списка рецензентов, назначенных на статью.
    Доступно редакторам и авторам статьи.
    """
    # Проверяем существование статьи
    article = db.query(models.Article).filter(models.Article.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Проверка прав доступа
    is_editor = "editor" in current_user.get("roles", [])
    is_article_author = article.responsible_user_id == current_user["user_id"]
    
    if not (is_editor or is_article_author):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Получаем список reviewer_ids
    reviewer_records = db.execute(
        models.article_reviewers.select().where(
            models.article_reviewers.c.article_id == article_id
        )
    ).fetchall()
    
    reviewer_ids = [record.user_id for record in reviewer_records]

    # Пытаемся обогатить данные информацией о дедлайне из Review Service
    review_service_url = config.REVIEW_SERVICE_URL if hasattr(config, 'REVIEW_SERVICE_URL') else "http://reviews:8000"
    deadlines_by_reviewer: dict[int, str | None] = {}
    try:
        import httpx
        resp = httpx.get(f"{review_service_url}/reviews/article/{article_id}", timeout=5.0)
        if resp.status_code == 200:
            data = resp.json() or []
            for item in data:
                rid = item.get("reviewer_id")
                if rid in reviewer_ids and rid is not None:
                    deadlines_by_reviewer[int(rid)] = item.get("deadline")
    except Exception:
        pass

    # Обогащаем информацией о рецензентах из User Profile и Auth сервисов
    reviewers_out = []
    api_gateway_url = getattr(config, 'API_GATEWAY_URL', 'http://localhost:8000')
    try:
        import httpx
        with httpx.Client(timeout=5.0) as client:
            for rid in reviewer_ids:
                profile = None
                auth_info = None
                try:
                    prof_resp = client.get(f"{api_gateway_url}/users/{rid}")
                    if prof_resp.status_code == 200:
                        profile = prof_resp.json()
                except Exception:
                    profile = None
                try:
                    auth_resp = client.get(f"{api_gateway_url}/auth/users/{rid}")
                    if auth_resp.status_code == 200:
                        auth_info = auth_resp.json()
                except Exception:
                    auth_info = None

                item = {
                    # From User Profile Service
                    "id": (profile or {}).get("id"),
                    "user_id": rid,
                    "full_name": (profile or {}).get("full_name"),
                    "phone": (profile or {}).get("phone"),
                    "organization": (profile or {}).get("organization"),
                    "roles": (profile or {}).get("roles", []) or [],
                    "preferred_language": (profile or {}).get("preferred_language"),
                    "is_active": (profile or {}).get("is_active"),
                    # From Auth - Identity Service
                    "username": (auth_info or {}).get("username"),
                    "email": (auth_info or {}).get("email"),
                    "first_name": (auth_info or {}).get("first_name"),
                    "last_name": (auth_info or {}).get("last_name"),
                    "institution": (auth_info or {}).get("institution"),
                    # Aggregated
                    "deadline": deadlines_by_reviewer.get(rid)
                }

                # prefer is_active from auth if present
                if auth_info and auth_info.get("is_active") is not None:
                    item["is_active"] = auth_info.get("is_active")

                reviewers_out.append(item)
    except Exception:
        # Фоллбек: только идентификаторы и дедлайны
        reviewers_out = [
            {
                "id": None,
                "user_id": rid,
                "full_name": None,
                "phone": None,
                "organization": None,
                "roles": [],
                "preferred_language": None,
                "is_active": None,
                "username": None,
                "email": None,
                "first_name": None,
                "last_name": None,
                "institution": None,
                "deadline": deadlines_by_reviewer.get(rid),
            }
            for rid in reviewer_ids
        ]

    return {"article_id": article_id, "reviews": reviewers_out}


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
