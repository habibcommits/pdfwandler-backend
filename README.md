# PDF Tools API - Backend

Production-ready FastAPI backend for PDF processing tools with Celery, Redis, and NGINX support.

## Features

- **Image to PDF**: Convert JPG, PNG, GIF, BMP images to PDF
- **Merge PDF**: Combine multiple PDF files into one
- **Compress PDF**: Reduce PDF file size with customizable options
- **Background Processing**: Async task queue with Celery
- **Automatic Cleanup**: Files automatically deleted after 1 hour
- **Production Ready**: Gunicorn, NGINX, SSL, Systemd

## Tech Stack

### Core
- **Python 3.11**
- **FastAPI** - Modern web framework
- **Uvicorn/Gunicorn** - ASGI/WSGI servers
- **Pillow** - Image processing
- **PyPDF2** - PDF manipulation

### Production
- **Celery** - Distributed task queue
- **Redis** - Message broker
- **NGINX** - Reverse proxy
- **Systemd** - Service management
- **Let's Encrypt** - SSL certificates

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python main.py
```

API available at: `http://localhost:8000`

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Production Deployment (Hetzner Cloud)

This backend is optimized for deployment on **Hetzner Cloud** servers in Germany.

### Quick Deploy (5 minutes)

```bash
# 1. Create Hetzner Cloud server (Ubuntu 22.04, Germany region)
# 2. Install system dependencies
apt update && apt install -y python3.11 nginx redis-server certbot

# 3. Clone and setup
git clone YOUR_REPO_URL pdf-tools-backend
cd pdf-tools-backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env  # Update ALLOWED_ORIGINS

# 5. Install services
sudo cp config/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now pdf-api pdf-celery redis

# 6. Setup NGINX + SSL
sudo cp config/nginx.conf /etc/nginx/sites-available/pdf-api
sudo ln -s /etc/nginx/sites-available/pdf-api /etc/nginx/sites-enabled/
sudo certbot --nginx -d api.yourdomain.com
```

### 📚 Complete Documentation

| Guide | Description |
|-------|-------------|
| **[QUICK_START.md](QUICK_START.md)** | 5-minute deployment reference |
| **[DEPLOYMENT_HETZNER.md](DEPLOYMENT_HETZNER.md)** | Complete step-by-step deployment guide |
| **[PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)** | Detailed configuration documentation |
| **[README_PRODUCTION_CHANGES.md](README_PRODUCTION_CHANGES.md)** | Summary of production code changes |

## API Endpoints

### Health Check
```http
GET /health
```
Returns: `{"status": "healthy"}`

### Image to PDF
```http
POST /api/image-to-pdf
Content-Type: multipart/form-data
```
**Request**: Image files (JPG, PNG, GIF, BMP)  
**Response**: PDF file download

### Merge PDFs
```http
POST /api/merge-pdf
Content-Type: multipart/form-data
```
**Request**: Multiple PDF files (minimum 2)  
**Response**: Merged PDF file download

### Compress PDF
```http
POST /api/compress-pdf?dpi=144&image_quality=75&color_mode=no-change
Content-Type: multipart/form-data
```
**Request**: Single PDF file  
**Query Parameters**:
- `dpi` (optional): 72-300, default: 144
- `image_quality` (optional): 1-100, default: 75
- `color_mode` (optional): "no-change", "grayscale", "bw", default: "no-change"

**Response**: Compressed PDF file download

## Architecture

```
Internet
   ↓
NGINX (Port 443)
   ├─ SSL/TLS Termination
   ├─ Rate Limiting (10 req/s)
   └─ Security Headers
   ↓
Gunicorn (Port 8000)
   └─ 4-8 Worker Processes
   ↓
FastAPI Application
   ├─ File Upload Handler
   └─ API Endpoints
   ↓
┌────────────┬──────────────┐
│   Redis    │  File System │
│ (Port 6379)│  uploads/temp│
└─────┬──────┴──────────────┘
      ↓
Celery Workers
   └─ Background PDF Processing
```

## Configuration

### Environment Variables

Create `.env` file (see `.env.example`):

```env
# Server Configuration
PORT=8000
WORKERS=4

# CORS (Update with your frontend domain!)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# File Storage
FILE_RETENTION_HOURS=1
```

### CORS Setup

Update `main.py` with your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Project Structure

```
pdf-tools-backend/
├── main.py                      # FastAPI application
├── celery_app.py               # Celery configuration
├── tasks.py                    # Background tasks
├── requirements.txt            # Python dependencies
├── .env.example                # Environment template
│
├── config/                     # Production configurations
│   ├── gunicorn.conf.py       # Gunicorn settings
│   ├── nginx.conf             # NGINX reverse proxy
│   ├── pdf-api.service        # Main API systemd service
│   ├── pdf-celery.service     # Celery worker service
│   └── pdf-celery-beat.service # Celery scheduler service
│
├── tools/                      # PDF processing modules
│   ├── image_to_pdf.py
│   ├── merge_pdf.py
│   └── compress_pdf.py
│
├── uploads/                    # Temporary upload storage
└── temp/                       # Temporary output storage
```

## Service Management

```bash
# Start/Stop/Restart services
sudo systemctl start pdf-api
sudo systemctl stop pdf-api
sudo systemctl restart pdf-api

# View logs
sudo journalctl -u pdf-api -f
sudo journalctl -u pdf-celery -f

# Check status
sudo systemctl status pdf-api pdf-celery redis nginx
```

## Monitoring

### Health Check
```bash
curl https://api.yourdomain.com/health
```

### View Logs
```bash
# Application logs
sudo journalctl -u pdf-api -f

# NGINX logs
sudo tail -f /var/log/nginx/pdf-api-access.log
sudo tail -f /var/log/nginx/pdf-api-error.log

# Celery logs
sudo tail -f /var/log/pdf-api/celery.log
```

### Resource Monitoring
```bash
# System resources
htop
df -h
free -h

# Celery workers
celery -A celery_app status
celery -A celery_app inspect active

# Redis
redis-cli INFO
redis-cli MONITOR
```

## Performance & Limits

| Metric | Value |
|--------|-------|
| Max upload size | 50MB |
| Rate limit | 10 requests/sec per IP |
| Worker processes | 4-8 (auto-scaling) |
| Task timeout | 120 seconds |
| File retention | 1 hour |
| SSL/TLS | Enabled |
| HTTP/2 | Enabled |

## Security Features

- ✅ HTTPS/SSL encryption with Let's Encrypt
- ✅ Rate limiting per IP address
- ✅ Security headers (HSTS, X-Frame-Options, CSP)
- ✅ File size validation (50MB max)
- ✅ File type verification
- ✅ Automatic file cleanup
- ✅ Redis bound to localhost only
- ✅ Services run as non-root user

## Cost Estimation (Hetzner Cloud)

**Recommended: CX21 (Germany)**
- 2 vCPU, 4GB RAM, 40GB SSD
- 20TB traffic included
- €5.83/month + €1.17/month (backups)
- **Total: ~€7/month**

Perfect for production PDF processing API.

## Troubleshooting

### 502 Bad Gateway
```bash
sudo systemctl status pdf-api
sudo netstat -tulpn | grep :8000
sudo journalctl -u pdf-api -n 50
```

### Service Won't Start
```bash
sudo journalctl -u pdf-api -n 50
ls -la /home/pdfapi/pdf-tools-backend
```

### Celery Not Processing
```bash
redis-cli ping
celery -A celery_app status
sudo systemctl restart pdf-celery
```

## Frontend Integration

Update your Next.js frontend:

```env
# .env.production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

Example API call:
```javascript
const formData = new FormData();
formData.append('files', imageFile);

const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/image-to-pdf`, {
  method: 'POST',
  body: formData
});

const blob = await response.blob();
// Download PDF file
```

## Support

- **Deployment**: See [DEPLOYMENT_HETZNER.md](DEPLOYMENT_HETZNER.md)
- **Configuration**: See [PRODUCTION_SETUP.md](PRODUCTION_SETUP.md)
- **Quick Start**: See [QUICK_START.md](QUICK_START.md)
- **Hetzner Docs**: https://docs.hetzner.com/cloud/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

## License

Open-source project for PDF processing tools.

---

**🚀 Ready for production deployment on Hetzner Cloud!**

See [DEPLOYMENT_HETZNER.md](DEPLOYMENT_HETZNER.md) for complete deployment instructions.
