FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
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
RUN chmod +x /app/scripts/wait-for.sh

# Create processing directory
RUN mkdir -p /app/data/processing && chown -R bibliflow:bibliflow /app/data

USER bibliflow

# Health check for Celery worker
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD celery -A bibliflow inspect ping -d celery@$HOSTNAME || exit 1

CMD ["celery", "-A", "bibliflow", "worker", "--loglevel=info", "--concurrency=4"]