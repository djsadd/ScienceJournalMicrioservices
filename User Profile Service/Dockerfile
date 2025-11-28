FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PostgreSQL client for running raw SQL migrations
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY app ./app
COPY migrations ./migrations
COPY run_migrations.sh ./run_migrations.sh
RUN chmod +x run_migrations.sh

EXPOSE 8000
CMD ["bash", "-c", "./run_migrations.sh && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
