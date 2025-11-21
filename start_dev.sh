#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Stopping services..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

echo "🚀 Starting Product Importer Development Environment..."

# Check if Docker containers are running
if ! docker ps | grep -q "product-importer-postgres"; then
    echo "📦 Starting Docker containers..."
    docker-compose up -d
    echo "⏳ Waiting for database to be ready..."
    sleep 5
fi

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Start Celery Worker
echo "👷 Starting Celery Worker..."
celery -A backend.celery_app worker --loglevel=info &

# Start FastAPI Server
echo "🌐 Starting FastAPI Server..."
echo "   -> API Docs: http://localhost:8000/docs"
echo "   -> Frontend: http://localhost:8000"
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Wait for all background processes
wait
