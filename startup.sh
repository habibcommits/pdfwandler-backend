#!/bin/bash
# Azure Web App Startup Script for PDF Tools API
# This script starts all required services for the application

set -e  # Exit on error

echo "Starting PDF Tools API services..."

# Start Redis server in background (with persistence disabled for web apps)
echo "Starting Redis server..."
redis-server --daemonize yes \
    --port 6379 \
    --loglevel notice \
    --save "" \
    --appendonly no \
    --dir /tmp

# Wait for Redis to be ready
echo "Waiting for Redis to be ready..."
sleep 3

# Verify Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: Redis failed to start"
    exit 1
fi
echo "Redis is ready"

# Create directories for logs and PIDs
mkdir -p /tmp/celery
export CELERY_LOG_DIR=/tmp/celery
export CELERY_PID_DIR=/tmp/celery

# Start Celery worker in background with proper logging
echo "Starting Celery worker..."
celery -A celery_app worker \
    --loglevel=info \
    --concurrency=2 \
    --logfile=$CELERY_LOG_DIR/worker.log \
    --pidfile=$CELERY_PID_DIR/worker.pid \
    --detach

# Start Celery beat scheduler in background with proper logging
echo "Starting Celery beat scheduler..."
celery -A celery_app beat \
    --loglevel=info \
    --logfile=$CELERY_LOG_DIR/beat.log \
    --pidfile=$CELERY_PID_DIR/beat.pid \
    --detach

# Give Celery a moment to start
sleep 2

# Verify Celery is running
if ! celery -A celery_app inspect ping > /dev/null 2>&1; then
    echo "WARNING: Celery worker may not be fully ready (this is normal on first start)"
fi

# Start Gunicorn with Uvicorn workers (production-ready ASGI server)
echo "Starting Gunicorn server with Uvicorn workers..."
echo "Application will be available on port ${PORT:-8000}"

exec gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT:-8000} \
    --timeout 120 \
    --keep-alive 5 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload
