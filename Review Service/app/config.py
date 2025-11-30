import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://reviews:pass@db/reviews")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ARTICLE_SERVICE_URL = os.getenv("ARTICLE_SERVICE_URL", "http://articles:8000")
API_GATEWAY_URL = os.getenv("API_GATEWAY_URL", "http://localhost:8000")
SHARED_SERVICE_SECRET = os.getenv("SHARED_SERVICE_SECRET", "service-shared-secret")
