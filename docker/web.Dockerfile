FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=on \
    PYTHONPATH=/app/src

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    file \
    libmagic1 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r bibliflow && useradd -r -g bibliflow bibliflow

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project files
COPY src/ /app/src/
COPY scripts/ /app/scripts/

# Set permissions
RUN chmod +x /app/scripts/entrypoint.sh /app/scripts/wait-for.sh

# Create upload directory
RUN mkdir -p /app/data/uploads && chown -R bibliflow:bibliflow /app/data

USER bibliflow

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/app/scripts/entrypoint.sh"]