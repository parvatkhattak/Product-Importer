#!/bin/bash
set -e

echo "Starting Celery worker..."

# Force Celery to run as root (required for Docker/Railway containers)
export C_FORCE_ROOT=1

# Start the worker
celery -A backend.celery_app worker --loglevel=info
