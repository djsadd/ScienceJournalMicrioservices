import os
from dotenv import load_dotenv

load_dotenv()

STORAGE_PATH = os.getenv("STORAGE_PATH", "/app/storage")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fileprocessing:pass@db/fileprocessing")
