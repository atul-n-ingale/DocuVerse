# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for tesseract and pandas/excel
RUN apt-get update && \
    apt-get install -y tesseract-ocr libglib2.0-0 libsm6 libxext6 libxrender-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml README.md ./
RUN poetry config virtualenvs.create false && poetry lock && poetry install --only=main --no-interaction --no-ansi --no-root

COPY . .

# Default command (can be overridden in docker-compose)
CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info"] 