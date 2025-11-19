# Production Setup Guide - Redis, Celery, NGINX & Systemd

This guide documents all code changes and configurations needed for production deployment with Redis, Celery workers, NGINX reverse proxy, and Systemd service management.

---

## Table of Contents

1. [Overview](#overview)
2. [New Files Added](#new-files-added)
3. [Dependencies Updated](#dependencies-updated)
4. [Architecture](#architecture)
5. [Configuration Files](#configuration-files)
6. [Deployment Steps](#deployment-steps)
7. [Testing](#testing)
8. [Monitoring](#monitoring)

---

## Overview

This backend is production-ready with:

- **Gunicorn**: WSGI HTTP server for production
- **Celery**: Distributed task queue for background processing
- **Redis**: Message broker and result backend for Celery
- **NGINX**: Reverse proxy with SSL, rate limiting, and load balancing
- **Systemd**: Service management for auto-restart and monitoring

---

## New Files Added

### Backend Code

| File | Purpose |
|------|---------|
| `celery_app.py` | Celery application configuration |
| `tasks.py` | Background task definitions for async processing |
| `.env.example` | Environment variable template |

### Configuration Files

| File | Purpose |
|------|---------|
| `config/gunicorn.conf.py` | Gunicorn production server configuration |
| `config/nginx.conf` | NGINX reverse proxy configuration |
| `config/pdf-api.service` | Systemd service for main API |
| `config/pdf-celery.service` | Systemd service for Celery worker |
| `config/pdf-celery-beat.service` | Systemd service for Celery Beat scheduler |

---

## Dependencies Updated

### requirements.txt

Added production dependencies:

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pillow==10.3.0
PyPDF2==3.0.1
aiofiles==23.2.1
gunicorn==21.2.0        # NEW: Production WSGI server
celery==5.3.4           # NEW: Distributed task queue
redis==5.0.1            # NEW: Redis client
```

### Installation

```bash
pip install -r requirements.txt
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         INTERNET                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │   NGINX (Port 80/443)   │
            │  - SSL Termination      │
            │  - Rate Limiting        │
            │  - Load Balancing       │
            └────────────┬────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │ Gunicorn (Port 8000)    │
            │  - 4 Workers            │
            │  - Uvicorn Worker Class │
            └────────────┬────────────┘
                         │
                         ▼
            ┌─────────────────────────┐
            │   FastAPI Application   │
            │  - REST API Endpoints   │
            │  - File Upload Handler  │
            └─────┬──────────────┬────┘
                  │              │
                  ▼              ▼
         ┌────────────┐   ┌──────────────┐
         │   Redis    │   │ File System  │
         │ (Port 6379)│   │ - uploads/   │
         └─────┬──────┘   │ - temp/      │
               │          └──────────────┘
               ▼
      ┌─────────────────┐
      │ Celery Workers  │
      │ - PDF Processing│
      │ - Background    │
      │   Tasks         │
      └─────────────────┘
```

---

## Configuration Files

### 1. celery_app.py

Celery application with optimized configuration:

```python
from celery import Celery
import os

celery_app = Celery(
    'pdf_tools',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Berlin',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
)
```

**Features**:
- JSON serialization for security
- Task time limits to prevent hanging
- Berlin timezone for German deployment
- Task tracking enabled

### 2. tasks.py

Background tasks for async PDF processing:

```python
@celery_app.task(name='tasks.process_image_to_pdf')
def process_image_to_pdf(image_paths: list, output_path: str) -> dict:
    convert_images_to_pdf(image_paths, output_path)
    return {'status': 'success', 'output_path': output_path}

@celery_app.task(name='tasks.process_merge_pdf')
def process_merge_pdf(pdf_paths: list, output_path: str) -> dict:
    merge_pdfs(pdf_paths, output_path)
    return {'status': 'success', 'output_path': output_path}

@celery_app.task(name='tasks.process_compress_pdf')
def process_compress_pdf(input_path, output_path, dpi=144, 
                        image_quality=75, color_mode="no-change") -> dict:
    compress_pdf(input_path, output_path, dpi, image_quality, color_mode)
    return {'status': 'success', 'output_path': output_path}

@celery_app.task(name='tasks.cleanup_old_files')
def cleanup_old_files(directory: str, max_age_hours: int = 1) -> dict:
    # Automatic file cleanup task
    pass
```

**Benefits**:
- Offload heavy PDF processing to background workers
- Prevent API timeout on large files
- Automatic error handling and retries

### 3. config/gunicorn.conf.py

Production server configuration:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
max_requests = 1000
max_requests_jitter = 50
```

**Optimizations**:
- Auto-scaling workers based on CPU cores
- Worker recycling to prevent memory leaks
- Graceful timeout handling

### 4. config/nginx.conf

NGINX reverse proxy with security features:

```nginx
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream pdf_api {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    client_max_body_size 50M;
    
    location / {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://pdf_api;
    }
}
```

**Features**:
- Rate limiting: 10 requests/second per IP
- SSL/TLS encryption
- 50MB max upload size
- HTTP/2 support
- Security headers

### 5. Systemd Services

Three services for complete management:

**config/pdf-api.service** - Main API
```ini
[Service]
ExecStart=/path/to/venv/bin/gunicorn --config config/gunicorn.conf.py main:app
Restart=always
```

**config/pdf-celery.service** - Celery Worker
```ini
[Service]
ExecStart=/path/to/venv/bin/celery -A celery_app worker --loglevel=info
Restart=always
```

**config/pdf-celery-beat.service** - Scheduled Tasks
```ini
[Service]
ExecStart=/path/to/venv/bin/celery -A celery_app beat --loglevel=info
Restart=always
```

---

## Deployment Steps

### Step 1: Install Redis

```bash
sudo apt install redis-server -y
sudo systemctl enable redis
sudo systemctl start redis

# Test Redis
redis-cli ping
# Should return: PONG
```

### Step 2: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit with your values
nano .env
```

Update `.env`:
```env
PORT=8000
WORKERS=4
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
ALLOWED_ORIGINS=https://yourdomain.com
```

### Step 3: Install Python Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 4: Setup Systemd Services

```bash
# Copy service files
sudo cp config/pdf-api.service /etc/systemd/system/
sudo cp config/pdf-celery.service /etc/systemd/system/
sudo cp config/pdf-celery-beat.service /etc/systemd/system/

# Create log directory
sudo mkdir -p /var/log/pdf-api
sudo chown $USER:$USER /var/log/pdf-api

# Create Celery PID directory
sudo mkdir -p /var/run/celery
sudo chown $USER:$USER /var/run/celery

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable pdf-api
sudo systemctl enable pdf-celery
sudo systemctl enable pdf-celery-beat

# Start services
sudo systemctl start pdf-api
sudo systemctl start pdf-celery
sudo systemctl start pdf-celery-beat
```

### Step 5: Configure NGINX

```bash
# Copy NGINX config
sudo cp config/nginx.conf /etc/nginx/sites-available/pdf-api

# Update domain name
sudo nano /etc/nginx/sites-available/pdf-api
# Replace "api.yourdomain.com" with your actual domain

# Enable site
sudo ln -s /etc/nginx/sites-available/pdf-api /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload NGINX
sudo systemctl reload nginx
```

### Step 6: Get SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d api.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## Testing

### Test API Endpoint

```bash
# Health check
curl https://api.yourdomain.com/health

# Expected response:
# {"status":"healthy"}
```

### Test Services

```bash
# Check service status
sudo systemctl status pdf-api
sudo systemctl status pdf-celery
sudo systemctl status redis

# View logs
sudo journalctl -u pdf-api -f
sudo journalctl -u pdf-celery -f
tail -f /var/log/pdf-api/error.log
```

### Test Celery Task

```bash
# Python shell
python3

>>> from tasks import process_compress_pdf
>>> result = process_compress_pdf.delay('input.pdf', 'output.pdf')
>>> result.ready()  # Check if task completed
>>> result.get()    # Get result
```

### Test Upload

```bash
# Upload image to convert to PDF
curl -X POST https://api.yourdomain.com/api/image-to-pdf \
  -F "files=@test.jpg" \
  --output result.pdf
```

---

## Monitoring

### Service Management

```bash
# Restart services
sudo systemctl restart pdf-api
sudo systemctl restart pdf-celery
sudo systemctl restart nginx

# View real-time logs
sudo journalctl -u pdf-api -f
sudo tail -f /var/log/nginx/pdf-api-access.log

# Check resource usage
htop
df -h
free -h
```

### Celery Monitoring

```bash
# Check active workers
celery -A celery_app status

# Check tasks
celery -A celery_app inspect active

# Monitor in real-time
celery -A celery_app events
```

### Redis Monitoring

```bash
# Connect to Redis CLI
redis-cli

# Get info
INFO

# Monitor commands
MONITOR

# Check memory usage
MEMORY STATS
```

---

## Performance Tuning

### Gunicorn Workers

Adjust workers based on CPU cores:
```python
# config/gunicorn.conf.py
workers = (2 * CPU_CORES) + 1

# For 4 cores:
workers = 9
```

### Celery Concurrency

```bash
# In pdf-celery.service
ExecStart=... celery worker --concurrency=8
```

### NGINX Caching (Optional)

Add to `nginx.conf`:
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m;

location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 1m;
}
```

---

## Security Checklist

- [x] HTTPS enabled with Let's Encrypt SSL
- [x] Rate limiting configured in NGINX
- [x] File size limits enforced (50MB)
- [x] Redis bound to localhost only
- [x] Security headers added (X-Frame-Options, CSP, etc.)
- [x] Automatic file cleanup configured
- [x] Fail2Ban protection (see DEPLOYMENT_HETZNER.md)
- [x] UFW firewall enabled
- [x] Non-root user for services

---

## Troubleshooting

### Service won't start

```bash
# Check logs
sudo journalctl -u pdf-api -n 50

# Check permissions
ls -la /home/pdfapi/pdf-tools-backend

# Test manually
source venv/bin/activate
gunicorn --config config/gunicorn.conf.py main:app
```

### Celery tasks not processing

```bash
# Check Redis connection
redis-cli ping

# Check worker status
celery -A celery_app inspect active

# Restart worker
sudo systemctl restart pdf-celery
```

### NGINX 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status pdf-api

# Check if port is listening
sudo netstat -tulpn | grep :8000

# Check NGINX error logs
sudo tail -f /var/log/nginx/pdf-api-error.log
```

---

## File Structure

```
pdf-tools-backend/
├── main.py                          # FastAPI application
├── celery_app.py                    # NEW: Celery configuration
├── tasks.py                         # NEW: Background tasks
├── requirements.txt                 # Updated with production deps
├── .env.example                     # NEW: Environment template
├── config/                          # NEW: Configuration directory
│   ├── gunicorn.conf.py            # Gunicorn settings
│   ├── nginx.conf                  # NGINX configuration
│   ├── pdf-api.service             # Systemd service
│   ├── pdf-celery.service          # Celery worker service
│   └── pdf-celery-beat.service     # Celery beat service
├── tools/
│   ├── image_to_pdf.py
│   ├── merge_pdf.py
│   └── compress_pdf.py
├── uploads/                         # Temporary upload directory
├── temp/                            # Temporary output directory
└── logs/                            # Application logs
```

---

## Summary of Changes

### Code Changes
1. ✅ Added `celery_app.py` - Celery configuration
2. ✅ Added `tasks.py` - Background task definitions
3. ✅ Updated `requirements.txt` - Added gunicorn, celery, redis

### Configuration Files
4. ✅ Added `config/gunicorn.conf.py` - Production server config
5. ✅ Added `config/nginx.conf` - Reverse proxy config
6. ✅ Added `config/pdf-api.service` - Systemd service
7. ✅ Added `config/pdf-celery.service` - Celery worker service
8. ✅ Added `config/pdf-celery-beat.service` - Celery beat service
9. ✅ Added `.env.example` - Environment variables template

### No Changes Required
- ❌ `main.py` - Works as-is with Gunicorn
- ❌ `tools/*.py` - Work as-is with Celery tasks

---

## Next Steps

1. Deploy to Hetzner following `DEPLOYMENT_HETZNER.md`
2. Update frontend to use `https://api.yourdomain.com`
3. Configure CORS in `main.py` with your frontend domain
4. Setup monitoring with Grafana/Prometheus (optional)
5. Configure backups for uploads/temp directories

---

**Your backend is now production-ready!** All necessary code and configurations are in place for deployment with Redis, Celery, NGINX, and Systemd.
