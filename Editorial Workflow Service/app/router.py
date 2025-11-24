from typing import List
from fastapi import APIRouter, Depends, HTTPException, Header
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app import config, database, models, schemas

router = APIRouter(prefix="/editorial", tags=["editorial"])


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
        roles = payload.get("roles", [])
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": int(user_id), "roles": roles}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


def ensure_editor(user):
    if "editor" not in user.get("roles", []):
        raise HTTPException(status_code=403, detail="Editor role required")


@router.post("/", response_model=schemas.EditorialTaskOut)
def create_task(task: schemas.EditorialTaskCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_editor(current_user)
    new_task = models.EditorialTask(
        article_id=task.article_id,
        editor_id=current_user["user_id"],
        reviewer_ids=task.reviewer_ids or [],
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@router.get("/article/{article_id}", response_model=List[schemas.EditorialTaskOut])
def list_tasks_for_article(article_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_editor(current_user)
    tasks = db.query(models.EditorialTask).filter(models.EditorialTask.article_id == article_id).all()
    return tasks


@router.get("/{task_id}", response_model=schemas.EditorialTaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    task = db.query(models.EditorialTask).filter(models.EditorialTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.editor_id != current_user["user_id"] and "editor" not in current_user.get("roles", []):
        raise HTTPException(status_code=403, detail="Not allowed")
    return task


@router.patch("/{task_id}", response_model=schemas.EditorialTaskOut)
def update_task(task_id: int, payload: schemas.EditorialTaskUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    ensure_editor(current_user)
    task = db.query(models.EditorialTask).filter(models.EditorialTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.editor_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Only assigned editor can update task")

    task.status = payload.status
    if payload.decision is not None:
        task.decision = payload.decision
    if payload.decision_comment is not None:
        task.decision_comment = payload.decision_comment
    if payload.reviewer_ids is not None:
        task.reviewer_ids = payload.reviewer_ids

    db.commit()
    db.refresh(task)
    return task
