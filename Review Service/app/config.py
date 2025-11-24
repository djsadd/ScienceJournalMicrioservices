import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://reviews:pass@db/reviews")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ARTICLE_SERVICE_URL = os.getenv("ARTICLE_SERVICE_URL", "http://articles:8000")
