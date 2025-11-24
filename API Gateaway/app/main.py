from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import (
    auth,
    users,
    articles,
    reviews,
    editorial,
    layout,
    publication,
    notifications,
    analytics,
    fileprocessing,
)

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(articles.router)
app.include_router(reviews.router)
app.include_router(editorial.router)
app.include_router(layout.router)
app.include_router(publication.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(fileprocessing.router)
