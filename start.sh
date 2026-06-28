#!/bin/bash

# Collect static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Start gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120