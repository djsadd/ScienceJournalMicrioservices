from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app import database, models, schemas


router = APIRouter(prefix="/tasks", tags=["file-processing"])


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _run_processing(task: models.FileProcessingTask) -> dict:
    if task.task_type == models.TaskType.metadata_extraction:
        return {"summary": f"Metadata extracted for file {task.file_id}"}
    if task.task_type == models.TaskType.format_check:
        return {"is_supported": True, "message": "Format check passed"}
    if task.task_type == models.TaskType.plagiarism_check:
        return {"similarity_score": 0.0, "message": "No plagiarism detected (stub)"}
    return {"message": "Unknown task type"}


@router.post("/", response_model=schemas.TaskOut)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    task = models.FileProcessingTask(
        file_id=payload.file_id,
        task_type=models.TaskType(payload.task_type),
        status=models.TaskStatus.pending,
    )
    db.add(task)
    db.flush()

    try:
        task.status = models.TaskStatus.processing
        result_data = _run_processing(task)
        task.result = json.dumps(result_data)
        task.status = models.TaskStatus.completed
    except Exception as exc:  # pragma: no cover - defensive
        task.status = models.TaskStatus.failed
        task.error_message = str(exc)

    db.commit()
    db.refresh(task)
    return task


@router.get("/", response_model=List[schemas.TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.query(models.FileProcessingTask).order_by(models.FileProcessingTask.created_at.desc()).all()
    return tasks


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.FileProcessingTask).filter(models.FileProcessingTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

