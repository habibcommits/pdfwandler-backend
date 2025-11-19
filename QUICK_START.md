# Quick Start - Production Deployment

Fast deployment guide for PDF Tools API on Hetzner Cloud.

---

## Files Added for Production

```
NEW FILES:
✅ celery_app.py                    - Celery configuration
✅ tasks.py                         - Background task definitions
✅ .env.example                     - Environment template
✅ config/gunicorn.conf.py          - Gunicorn settings
✅ config/nginx.conf                - NGINX reverse proxy
✅ config/pdf-api.service           - Main API systemd service
✅ config/pdf-celery.service        - Celery worker service
✅ config/pdf-celery-beat.service   - Celery scheduler service

UPDATED FILES:
📝 requirements.txt                 - Added: gunicorn, celery, redis

DOCUMENTATION:
📖 DEPLOYMENT_HETZNER.md            - Complete deployment guide
📖 PRODUCTION_SETUP.md              - Configuration details
📖 README_PRODUCTION_CHANGES.md    - Change summary
📖 QUICK_START.md                   - This file
```

---

## 5-Minute Deploy on Hetzner

### Prerequisites
- Hetzner Cloud account
- Domain name
- SSH access

### Step 1: Server Setup (2 min)
```bash
# Create Ubuntu 22.04 server on Hetzner
# SSH into server
ssh root@YOUR_SERVER_IP

# Install everything
apt update && apt upgrade -y
apt install -y python3.11 python3.11-venv nginx redis-server certbot python3-certbot-nginx
apt install -y libjpeg-dev zlib1g-dev libtiff-dev libfreetype6-dev
```

### Step 2: Deploy Code (1 min)
```bash
# Create user and clone repo
adduser pdfapi
su - pdfapi
git clone YOUR_REPO_URL pdf-tools-backend
cd pdf-tools-backend

# Setup Python
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure (1 min)
```bash
# Setup environment
cp .env.example .env
nano .env  # Update ALLOWED_ORIGINS with your frontend URL

# Install systemd services
sudo cp config/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pdf-api pdf-celery redis
sudo systemctl start pdf-api pdf-celery redis
```

### Step 4: NGINX & SSL (1 min)
```bash
# Configure NGINX
sudo cp config/nginx.conf /etc/nginx/sites-available/pdf-api
sudo nano /etc/nginx/sites-available/pdf-api  # Update domain name
sudo ln -s /etc/nginx/sites-available/pdf-api /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d api.yourdomain.com
```

### Step 5: Test
```bash
# Health check
curl https://api.yourdomain.com/health

# Should return: {"status":"healthy"}
```

**Done! Your API is live! 🚀**

---

## Environment Variables (.env)

```env
# Server
PORT=8000
WORKERS=4

# CORS - UPDATE THIS!
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# File Storage
FILE_RETENTION_HOURS=1
```

---

## Service Management

```bash
# Start/Stop/Restart
sudo systemctl start pdf-api
sudo systemctl stop pdf-api
sudo systemctl restart pdf-api

# View logs
sudo journalctl -u pdf-api -f
sudo tail -f /var/log/nginx/pdf-api-error.log

# Check status
sudo systemctl status pdf-api pdf-celery redis nginx
```

---

## Frontend Integration

Update your Next.js frontend:

```env
# .env.production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

Update CORS in `main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    ...
)
```

---

## Architecture

```
Browser → NGINX (SSL/Rate Limit) → Gunicorn → FastAPI → Redis → Celery Workers
                                              ↓
                                         File System
```

---

## Performance Specs

- **Requests/sec**: 10 per IP (rate limited)
- **Max upload**: 50MB per file
- **Concurrent workers**: 4-8 (auto-scaling)
- **Task timeout**: 120 seconds
- **SSL**: TLS 1.2/1.3
- **Auto-restart**: Yes (systemd)

---

## Monitoring Commands

```bash
# Real-time logs
sudo journalctl -u pdf-api -f

# Resource usage
htop
df -h

# Celery status
celery -A celery_app status

# Redis monitor
redis-cli MONITOR
```

---

## Troubleshooting

### 502 Bad Gateway
```bash
sudo systemctl status pdf-api
sudo netstat -tulpn | grep :8000
```

### Service won't start
```bash
sudo journalctl -u pdf-api -n 50
```

### Celery not processing
```bash
redis-cli ping
sudo systemctl restart pdf-celery
```

---

## Cost

**Hetzner CX21** (4GB RAM, 2 vCPU):
- Server: €5.83/month
- Backups: €1.17/month
- **Total: ~€7/month**

---

## Security Checklist

- [x] SSL/HTTPS enabled
- [x] Rate limiting (10 req/s)
- [x] File size limits (50MB)
- [x] Security headers
- [x] Auto file cleanup
- [x] Non-root user
- [x] Redis localhost only

---

## Documentation

- **DEPLOYMENT_HETZNER.md** - Full deployment guide
- **PRODUCTION_SETUP.md** - Detailed configuration
- **README_PRODUCTION_CHANGES.md** - What changed

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/image-to-pdf` | POST | Convert images to PDF |
| `/api/merge-pdf` | POST | Merge PDFs |
| `/api/compress-pdf` | POST | Compress PDF |

---

## Support

Need help? Check the detailed guides:
1. DEPLOYMENT_HETZNER.md for step-by-step deployment
2. PRODUCTION_SETUP.md for configuration details
3. README_PRODUCTION_CHANGES.md for code changes

---

**Ready to deploy!** All code is production-ready with zero changes needed to existing API.
