#!/bin/bash
set -e

# Activate virtual environment
if [ -d "/app/.venv" ]; then
    source /app/.venv/bin/activate
fi

# Collect static files
python manage.py collectstatic --noinput --clear || true

# Apply migrations
python manage.py migrate --noinput || true

# Start gunicorn
python -m gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 3