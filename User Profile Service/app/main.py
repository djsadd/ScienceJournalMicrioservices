from fastapi import FastAPI
from app.users_router import router as users_router
from app.database import Base, engine

app = FastAPI(title="User Profile Service")

# создаём таблицы (можно убрать после миграций)
Base.metadata.create_all(bind=engine)

app.include_router(users_router)
