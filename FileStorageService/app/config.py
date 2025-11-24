import os

STORAGE_PATH = os.getenv("STORAGE_PATH", "/app/storage")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(STORAGE_PATH, 'files.db')}")
