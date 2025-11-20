# Multi-stage Dockerfile for PDF Tools API
# Optimized for Azure Container Apps deployment with all system dependencies
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Ghostscript for PDF compression, Redis for Celery)
RUN apt-get update && apt-get install -y \
    ghostscript \
    redis-server \
    redis-tools \
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

# Create directories for temporary files and Celery logs
RUN mkdir -p uploads temp /tmp/celery

# Make startup script executable
RUN chmod +x startup.sh

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (Azure Container Apps will map this)
EXPOSE 8000

# Health check to ensure service is running
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

# Run the startup script (starts Redis, Celery, and Gunicorn)
CMD ["./startup.sh"]
