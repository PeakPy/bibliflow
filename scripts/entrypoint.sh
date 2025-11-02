#!/bin/bash
set -e

echo "Starting Bibliflow CSV Import System..."

wait_for_services() {
    echo "Checking dependencies..."

    # Database health check
    echo "Waiting for database..."
    python /app/src/manage.py wait_for_db
    echo "Database ready!"

    # Redis connection test
    echo "Checking Redis connection..."
    python /app/src/manage.py shell -c "
import redis
import os
from django.core.cache import cache
try:
    cache.set('health_check', 'ok', 1)
    print('Redis ready!')
except Exception as e:
    print(f'Redis connection failed: {e}')
    exit(1)
"
}

setup_upload_dir() {
    echo "Setting up upload directories..."
    mkdir -p /app/data/uploads/processed
    mkdir -p /app/data/uploads/failed
    chmod 755 /app/data/uploads
}

run_migrations() {
    echo "Running database migrations..."
    python /app/src/manage.py migrate --noinput
}

create_superuser() {
    if [ "$CREATE_SUPERUSER" = "true" ]; then
        echo "Creating superuser..."
        python /app/src/manage.py createsuperuser \
            --username=admin \
            --email=admin@bibliflow.com \
            --noinput || true
    fi
}

load_initial_data() {
    if [ "$LOAD_INITIAL_DATA" = "true" ]; then
        echo "Loading initial data..."
        python /app/src/manage.py loaddata initial_books || true
    fi
}

main() {
    wait_for_services
    setup_upload_dir
    run_migrations
    create_superuser
    load_initial_data

    echo "System ready - Starting server..."
    exec "$@"
}

main "$@"