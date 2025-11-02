#!/usr/bin/env bash
# entrypoint for containers (placeholder)
set -e
python manage.py migrate --noinput
exec \"\$@\"