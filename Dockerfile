# Dockerfile for PDF Tools API (FastAPI only, production-ready)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for PDFs
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

# Copy requirements first for layer caching
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
# Redis URLs will be passed via ACI environment variables
# REDIS_URL=redis://<your-redis-host>:6379/0
# CELERY_BROKER_URL=redis://<your-redis-host>:6379/0
# CELERY_RESULT_BACKEND=redis://<your-redis-host>:6379/0

# Expose FastAPI port
EXPOSE 5000

# Start FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
