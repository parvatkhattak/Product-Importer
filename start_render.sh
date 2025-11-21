#!/bin/bash
set -e

echo "Starting Product Importer services..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start Celery worker in background
echo "Starting Celery worker..."
export C_FORCE_ROOT=1
celery -A backend.celery_app worker --loglevel=info &

# Start web server in foreground
echo "Starting web server..."
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
