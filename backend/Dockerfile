# syntax=docker/dockerfile:1

ARG PYTHON_VERSION=3.11-slim
FROM python:${PYTHON_VERSION} AS base

# Install Astral uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# System dependencies (e.g. for psycopg2, networking, curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Non-privileged user with a real home directory for ChromaDB cache/onnx models
ARG UID=10001
RUN useradd -m -u ${UID} -s /bin/bash appuser

# Set user home & cache directory environment variables
ENV HOME=/home/appuser
ENV XDG_CACHE_HOME=/home/appuser/.cache

# Install python dependencies using uv
COPY requirements.txt pyproject.toml ./
RUN uv pip install --system --no-cache -r requirements.txt

# Copy application source code and prepare cache directories with proper permissions
COPY . .
RUN mkdir -p /home/appuser/.cache /app/chroma_data && \
    chown -R appuser:appuser /app /home/appuser

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
