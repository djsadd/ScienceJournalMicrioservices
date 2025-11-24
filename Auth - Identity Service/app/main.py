from fastapi import FastAPI
from app.auth_router import router as auth_router
from app.database import Base, engine

app = FastAPI(title="Auth Service")

# создаем таблицы (можно убрать после миграций)
Base.metadata.create_all(bind=engine)

app.include_router(auth_router)
