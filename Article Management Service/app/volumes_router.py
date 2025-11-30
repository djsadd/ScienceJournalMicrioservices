from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session, joinedload
from typing import List
from jose import jwt, JWTError
from app import models, schemas, database, config

router = APIRouter(prefix="/volumes", tags=["volumes"])


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


def ensure_editor(user):
    if "editor" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Editor role required")


@router.get("/", response_model=List[schemas.VolumeOut])
def list_volumes(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    year: int | None = None,
    number: int | None = None,
    month: int | None = None,
    active_only: bool = True,
):
    query = db.query(models.Volume).options(
        joinedload(models.Volume.articles).joinedload(models.Article.authors),
        joinedload(models.Volume.articles).joinedload(models.Article.keywords),
    )
    if year is not None:
        query = query.filter(models.Volume.year == year)
    if number is not None:
        query = query.filter(models.Volume.number == number)
    if month is not None:
        query = query.filter(models.Volume.month == month)
    if active_only:
        query = query.filter(models.Volume.is_active.is_(True))
    # Порядок новее раньше
    volumes = query.order_by(models.Volume.year.desc(), models.Volume.number.desc()).all()
    return volumes


@router.get("/{volume_id}", response_model=schemas.VolumeOut)
def get_volume(
    volume_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    volume = (
        db.query(models.Volume)
        .options(
            joinedload(models.Volume.articles).joinedload(models.Article.authors),
            joinedload(models.Volume.articles).joinedload(models.Article.keywords),
        )
        .filter(models.Volume.id == volume_id)
        .first()
    )
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    return volume


@router.post("/", response_model=schemas.VolumeOut, status_code=201)
def create_volume(
    payload: schemas.VolumeCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_editor(current_user)

    # Проверка уникальности (год+номер)
    existing = db.query(models.Volume).filter(
        models.Volume.year == payload.year,
        models.Volume.number == payload.number,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Volume with this year and number already exists")

    volume = models.Volume(
        year=payload.year,
        number=payload.number,
        month=payload.month,
        title_kz=payload.title_kz,
        title_en=payload.title_en,
        title_ru=payload.title_ru,
        description=payload.description,
        is_active=payload.is_active,
    )
    db.add(volume)
    db.flush()

    # Привязка статей (только опубликованные)
    if payload.article_ids:
        articles = db.query(models.Article).filter(models.Article.id.in_(payload.article_ids)).all()
        found_ids = {a.id for a in articles}
        missing = [aid for aid in payload.article_ids if aid not in found_ids]
        if missing:
            raise HTTPException(status_code=400, detail=f"Articles not found: {missing}")
        # Проверяем статусы
        not_published = [a.id for a in articles if a.status != models.ArticleStatus.published]
        if not_published:
            raise HTTPException(status_code=400, detail=f"Articles not published: {not_published}")
        for article in articles:
            db.execute(models.volume_articles.insert().values(volume_id=volume.id, article_id=article.id))

    db.commit()
    db.refresh(volume)
    return volume


@router.put("/{volume_id}", response_model=schemas.VolumeOut)
@router.patch("/{volume_id}", response_model=schemas.VolumeOut)
def update_volume(
    volume_id: int,
    payload: schemas.VolumeUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_editor(current_user)
    volume = db.query(models.Volume).filter(models.Volume.id == volume_id).first()
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")

    update_data = payload.dict(exclude_unset=True)

    # Если меняется год/номер нужно проверить уникальность
    if ("year" in update_data or "number" in update_data):
        new_year = update_data.get("year", volume.year)
        new_number = update_data.get("number", volume.number)
        exists = db.query(models.Volume).filter(
            models.Volume.year == new_year,
            models.Volume.number == new_number,
            models.Volume.id != volume_id,
        ).first()
        if exists:
            raise HTTPException(status_code=400, detail="Another volume with this year and number exists")

    # Обновляем простые поля
    for field in ["year", "number", "month", "title_kz", "title_en", "title_ru", "description", "is_active"]:
        if field in update_data:
            setattr(volume, field, update_data[field])

    # Полная замена списка статей если передан article_ids
    if "article_ids" in update_data and update_data["article_ids"] is not None:
        article_ids = update_data["article_ids"]
        db.execute(models.volume_articles.delete().where(models.volume_articles.c.volume_id == volume_id))
        if article_ids:
            articles = db.query(models.Article).filter(models.Article.id.in_(article_ids)).all()
            found_ids = {a.id for a in articles}
            missing = [aid for aid in article_ids if aid not in found_ids]
            if missing:
                raise HTTPException(status_code=400, detail=f"Articles not found: {missing}")
            not_published = [a.id for a in articles if a.status != models.ArticleStatus.published]
            if not_published:
                raise HTTPException(status_code=400, detail=f"Articles not published: {not_published}")
            for article in articles:
                db.execute(models.volume_articles.insert().values(volume_id=volume.id, article_id=article.id))

    db.commit()
    db.refresh(volume)
    return volume


@router.delete("/{volume_id}", status_code=204)
def delete_volume(
    volume_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    ensure_editor(current_user)
    volume = db.query(models.Volume).filter(models.Volume.id == volume_id).first()
    if not volume:
        raise HTTPException(status_code=404, detail="Volume not found")
    # Удаляем связи
    db.execute(models.volume_articles.delete().where(models.volume_articles.c.volume_id == volume_id))
    db.delete(volume)
    db.commit()
    return None
