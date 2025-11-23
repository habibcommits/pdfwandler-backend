# Dockerfile for PDF Tools API
# Optimized for Azure Container Instances (multi-container) and Azure App Service
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# Note: Redis is NOT installed here - use separate Redis container for production
RUN apt-get update && apt-get install -y \
    ghostscript \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libfreetype6-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create directories for temporary files and uploads
RUN mkdir -p uploads temp /tmp/celery

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port 5000 (matches FastAPI configuration)
EXPOSE 5000

# Note: HEALTHCHECK removed for multi-container compatibility
# In Azure Container Instances, the same image is used for FastAPI, Celery worker, and Celery beat
# A FastAPI-specific health check would cause worker/beat containers to fail
# Azure monitors container state via process exit codes instead

# Default command: Start FastAPI with Uvicorn
# This can be overridden in Azure Container Instances YAML or docker-compose
# For Celery worker: celery -A celery_app worker --loglevel=info
# For Celery beat: celery -A celery_app beat --loglevel=info
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
