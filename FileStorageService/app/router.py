import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app import database, models, schemas, config

router = APIRouter(prefix="/files", tags=["files"])


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_storage_dir():
    os.makedirs(config.STORAGE_PATH, exist_ok=True)


@router.post("/", response_model=schemas.FileOut)
async def upload_file(upload: UploadFile = File(...), db: Session = Depends(get_db)):
    _ensure_storage_dir()
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(upload.filename)[1]
    stored_name = f"{file_id}{extension}"
    dest_path = os.path.join(config.STORAGE_PATH, stored_name)

    size = 0
    with open(dest_path, "wb") as out_file:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            out_file.write(chunk)

    record = models.StoredFile(
        id=file_id,
        original_name=upload.filename,
        stored_name=stored_name,
        content_type=upload.content_type,
        size_bytes=size,
        path=dest_path,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return schemas.FileOut(
        id=record.id,
        original_name=record.original_name,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        url=f"/files/{record.id}/download",
        created_at=record.created_at,
    )


@router.get("/", response_model=list[schemas.FileOut])
def list_files(db: Session = Depends(get_db)):
    files = db.query(models.StoredFile).order_by(models.StoredFile.created_at.desc()).all()
    return [
        schemas.FileOut(
            id=f.id,
            original_name=f.original_name,
            content_type=f.content_type,
            size_bytes=f.size_bytes,
            url=f"/files/{f.id}/download",
            created_at=f.created_at,
        )
        for f in files
    ]


@router.get("/{file_id}", response_model=schemas.FileOut)
def get_file(file_id: str, db: Session = Depends(get_db)):
    file_obj = db.query(models.StoredFile).filter(models.StoredFile.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    return schemas.FileOut(
        id=file_obj.id,
        original_name=file_obj.original_name,
        content_type=file_obj.content_type,
        size_bytes=file_obj.size_bytes,
        url=f"/files/{file_obj.id}/download",
        created_at=file_obj.created_at,
    )


@router.get("/{file_id}/download")
def download_file(file_id: str, db: Session = Depends(get_db)):
    file_obj = db.query(models.StoredFile).filter(models.StoredFile.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    if not os.path.exists(file_obj.path):
        raise HTTPException(status_code=410, detail="File content missing")
    return FileResponse(
        path=file_obj.path,
        media_type=file_obj.content_type or "application/octet-stream",
        filename=file_obj.original_name,
    )


@router.delete("/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db)):
    file_obj = db.query(models.StoredFile).filter(models.StoredFile.id == file_id).first()
    if not file_obj:
        raise HTTPException(status_code=404, detail="File not found")
    # Remove file content if present
    try:
        if os.path.exists(file_obj.path):
            os.remove(file_obj.path)
    finally:
        db.delete(file_obj)
        db.commit()
    return {"status": "deleted", "id": file_id}
