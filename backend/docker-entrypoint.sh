#!/bin/bash
set -e

echo "AI Context Bridge API - Starting up..."

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting FastAPI server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --workers ${WORKERS:-4} \
    --log-level ${LOG_LEVEL:-info}
