from fastapi import FastAPI
from app.articles_router import router as articles_router
from app.database import Base, engine
from app import models  # register models for metadata
from alembic.config import Config
from alembic import command
import os

app = FastAPI(title="Article Management Service")


def run_migrations():
    """Run alembic migrations on startup"""
    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations applied successfully")
    except Exception as e:
        print(f"⚠️ Migration error: {e}")
        # If migrations fail, fallback to create_all
        Base.metadata.create_all(bind=engine)


# Run migrations on startup
run_migrations()

app.include_router(articles_router)
