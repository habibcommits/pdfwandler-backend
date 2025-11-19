# Hetzner Server Deployment Guide

Complete guide to deploy the PDF Tools API backend on Hetzner Cloud with NGINX and SSL.

---

## Table of Contents

1. [Server Setup](#1-server-setup)
2. [Domain & DNS Configuration](#2-domain--dns-configuration)
3. [Initial Server Configuration](#3-initial-server-configuration)
4. [Install Dependencies](#4-install-dependencies)
5. [Deploy Backend Application](#5-deploy-backend-application)
6. [Configure NGINX](#6-configure-nginx)
7. [SSL Certificate with Let's Encrypt](#7-ssl-certificate-with-lets-encrypt)
8. [Process Management with Systemd](#8-process-management-with-systemd)
9. [Redis & Celery Setup](#9-redis--celery-setup)
10. [Security Hardening](#10-security-hardening)
11. [Monitoring & Maintenance](#11-monitoring--maintenance)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Server Setup

### Create Hetzner Cloud Server

1. **Sign up / Login** to [Hetzner Cloud Console](https://console.hetzner.cloud/)

2. **Create New Project**
   - Name: `pdf-tools-api`
   - Location: Germany (Falkenstein or Nuremberg)

3. **Create Server**
   - **Location**: Nuremberg, Germany (nbg1-dc3)
   - **Image**: Ubuntu 22.04 LTS
   - **Type**: CX11 (2GB RAM, 1 vCPU) - Minimum recommended
     - For production: CX21 or higher (4GB RAM, 2 vCPU)
   - **Networking**: 
     - Enable IPv4
     - Enable IPv6 (optional)
   - **SSH Keys**: Add your SSH public key
   - **Firewall**: Create new firewall
     - Allow SSH (Port 22)
     - Allow HTTP (Port 80)
     - Allow HTTPS (Port 443)
   - **Backups**: Enable (recommended)
   - **Name**: `pdf-api-production`

4. **Note Down**:
   - Server IP address: `YOUR_SERVER_IP`
   - Root password (if not using SSH key)

---

## 2. Domain & DNS Configuration

### Configure DNS Records

1. **Go to your domain provider** (e.g., Namecheap, GoDaddy, Cloudflare)

2. **Add A Record**:
   ```
   Type: A
   Name: api (or @ for root domain)
   Value: YOUR_SERVER_IP
   TTL: 3600
   ```

3. **Example DNS Configuration**:
   ```
   api.yourdomain.com  →  YOUR_SERVER_IP
   ```

4. **Wait for DNS Propagation** (5-30 minutes)
   ```bash
   # Check DNS propagation
   nslookup api.yourdomain.com
   ```

---

## 3. Initial Server Configuration

### Connect to Server

```bash
ssh root@YOUR_SERVER_IP
```

### Update System

```bash
# Update package lists
apt update

# Upgrade all packages
apt upgrade -y

# Install essential tools
apt install -y curl wget git vim ufw
```

### Create Non-Root User

```bash
# Create new user
adduser pdfapi

# Add to sudo group
usermod -aG sudo pdfapi

# Switch to new user
su - pdfapi
```

### Configure Firewall

```bash
# Enable UFW
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Check status
sudo ufw status
```

---

## 4. Install Dependencies

### Install Python 3.11

```bash
# Add deadsnakes PPA
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install pip
sudo apt install -y python3-pip

# Verify installation
python3.11 --version
```

### Install Image Processing Libraries

```bash
# Install system dependencies for Pillow
sudo apt install -y \
    libjpeg-dev \
    zlib1g-dev \
    libtiff-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk
```

### Install NGINX

```bash
# Install NGINX
sudo apt install -y nginx

# Start NGINX
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

### Install Redis

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis to use systemd
sudo sed -i 's/^supervised no/supervised systemd/' /etc/redis/redis.conf

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis

# Test Redis
redis-cli ping
# Should return: PONG
```

---

## 5. Deploy Backend Application

### Clone Repository

```bash
# Navigate to home directory
cd /home/pdfapi

# Clone your repository
git clone https://github.com/YOUR_USERNAME/pdf-tools-backend.git
cd pdf-tools-backend
```

### Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Install Python Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Additional production dependencies
pip install gunicorn celery redis
```

### Create Application Directories

```bash
# Create upload and temp directories
mkdir -p uploads temp

# Set proper permissions
chmod 755 uploads temp
```

### Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add the following:
```env
# Server Configuration
PORT=8000
WORKERS=4

# CORS Configuration (update with your frontend domain)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# File Storage
UPLOAD_DIR=uploads
TEMP_DIR=temp
FILE_RETENTION_HOURS=1

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Test Application

```bash
# Test run
python main.py

# In another terminal, test the API
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

# Stop the test server (Ctrl+C)
```

---

## 6. Configure NGINX

### Create NGINX Configuration

```bash
sudo nano /etc/nginx/sites-available/pdf-api
```

Add the following configuration:

```nginx
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream pdf_api {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name api.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size limit (max upload size)
    client_max_body_size 50M;

    # Timeouts
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Logging
    access_log /var/log/nginx/pdf-api-access.log;
    error_log /var/log/nginx/pdf-api-error.log;

    location / {
        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;

        # Proxy settings
        proxy_pass http://pdf_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (no rate limit)
    location /health {
        proxy_pass http://pdf_api;
        access_log off;
    }
}
```

### Enable NGINX Configuration

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/pdf-api /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test NGINX configuration
sudo nginx -t

# Reload NGINX
sudo systemctl reload nginx
```

---

## 7. SSL Certificate with Let's Encrypt

### Install Certbot

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx
```

### Obtain SSL Certificate

```bash
# Get certificate
sudo certbot --nginx -d api.yourdomain.com

# Follow the prompts:
# - Enter email address
# - Agree to terms
# - Choose whether to redirect HTTP to HTTPS (recommended: Yes)
```

### Auto-Renewal Setup

```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up a systemd timer
sudo systemctl status certbot.timer
```

### Updated NGINX Configuration (After SSL)

Certbot will automatically update your NGINX config. Verify it looks like this:

```bash
sudo nano /etc/nginx/sites-available/pdf-api
```

It should now include:
```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # ... rest of your config
}

server {
    listen 80;
    listen [::]:80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## 8. Process Management with Systemd

### Create Systemd Service for Gunicorn

```bash
sudo nano /etc/systemd/system/pdf-api.service
```

Add the following:

```ini
[Unit]
Description=PDF Tools API - Gunicorn
After=network.target

[Service]
Type=notify
User=pdfapi
Group=pdfapi
WorkingDirectory=/home/pdfapi/pdf-tools-backend
Environment="PATH=/home/pdfapi/pdf-tools-backend/venv/bin"
EnvironmentFile=/home/pdfapi/pdf-tools-backend/.env
ExecStart=/home/pdfapi/pdf-tools-backend/venv/bin/gunicorn \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 120 \
    --access-logfile /var/log/pdf-api/access.log \
    --error-logfile /var/log/pdf-api/error.log \
    --log-level info \
    main:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Create Log Directory

```bash
# Create log directory
sudo mkdir -p /var/log/pdf-api
sudo chown pdfapi:pdfapi /var/log/pdf-api
```

### Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable pdf-api

# Start service
sudo systemctl start pdf-api

# Check status
sudo systemctl status pdf-api

# View logs
sudo journalctl -u pdf-api -f
```

---

## 9. Redis & Celery Setup

### Update main.py for Celery (Optional)

If you want to add background task processing with Celery:

Create `celery_app.py`:
```python
from celery import Celery
import os

celery_app = Celery(
    'pdf_tools',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
)

celery_app.conf.task_routes = {
    'tools.tasks.*': {'queue': 'pdf_processing'}
}

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Berlin',
    enable_utc=True,
)
```

### Create Celery Systemd Service

```bash
sudo nano /etc/systemd/system/pdf-celery.service
```

Add:
```ini
[Unit]
Description=PDF Tools Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=pdfapi
Group=pdfapi
WorkingDirectory=/home/pdfapi/pdf-tools-backend
Environment="PATH=/home/pdfapi/pdf-tools-backend/venv/bin"
EnvironmentFile=/home/pdfapi/pdf-tools-backend/.env
ExecStart=/home/pdfapi/pdf-tools-backend/venv/bin/celery -A celery_app worker \
    --loglevel=info \
    --logfile=/var/log/pdf-api/celery.log \
    --pidfile=/var/run/celery/celery.pid

Restart=always

[Install]
WantedBy=multi-user.target
```

### Create PID Directory

```bash
sudo mkdir -p /var/run/celery
sudo chown pdfapi:pdfapi /var/run/celery
```

### Enable Celery Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable pdf-celery
sudo systemctl start pdf-celery
sudo systemctl status pdf-celery
```

---

## 10. Security Hardening

### Configure Fail2Ban

```bash
# Install Fail2Ban
sudo apt install -y fail2ban

# Create NGINX jail
sudo nano /etc/fail2ban/jail.local
```

Add:
```ini
[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/pdf-api-error.log

[nginx-limit-req]
enabled = true
port = http,https
logpath = /var/log/nginx/pdf-api-error.log
maxretry = 5
findtime = 600
bantime = 3600
```

```bash
# Restart Fail2Ban
sudo systemctl restart fail2ban
sudo systemctl enable fail2ban
```

### Secure Redis

```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf
```

Update:
```conf
# Bind to localhost only
bind 127.0.0.1 ::1

# Set password
requirepass YOUR_STRONG_REDIS_PASSWORD

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG ""
```

```bash
# Restart Redis
sudo systemctl restart redis
```

### File Cleanup Cron Job

```bash
# Add to crontab
crontab -e
```

Add:
```bash
# Clean up old files every hour
0 * * * * find /home/pdfapi/pdf-tools-backend/uploads -type f -mmin +60 -delete
0 * * * * find /home/pdfapi/pdf-tools-backend/temp -type f -mmin +60 -delete
```

---

## 11. Monitoring & Maintenance

### Setup Log Rotation

```bash
sudo nano /etc/logrotate.d/pdf-api
```

Add:
```
/var/log/pdf-api/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 pdfapi pdfapi
    sharedscripts
    postrotate
        systemctl reload pdf-api > /dev/null 2>&1 || true
    endscript
}
```

### Monitoring Commands

```bash
# Check service status
sudo systemctl status pdf-api
sudo systemctl status pdf-celery
sudo systemctl status nginx
sudo systemctl status redis

# View logs
sudo journalctl -u pdf-api -f
sudo tail -f /var/log/pdf-api/error.log
sudo tail -f /var/log/nginx/pdf-api-error.log

# Check server resources
htop
df -h
free -h

# Check active connections
sudo netstat -tulpn | grep :8000
```

### Health Check Script

Create `/home/pdfapi/health-check.sh`:
```bash
#!/bin/bash

HEALTH_URL="https://api.yourdomain.com/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE != "200" ]; then
    echo "Health check failed with status: $RESPONSE"
    sudo systemctl restart pdf-api
    # Send alert email (optional)
    echo "PDF API restarted at $(date)" | mail -s "API Restart Alert" admin@yourdomain.com
fi
```

```bash
chmod +x /home/pdfapi/health-check.sh

# Add to crontab (check every 5 minutes)
crontab -e
```

Add:
```bash
*/5 * * * * /home/pdfapi/health-check.sh
```

---

## 12. Troubleshooting

### Common Issues

**Issue: Service won't start**
```bash
# Check logs
sudo journalctl -u pdf-api -n 50
# Check permissions
ls -la /home/pdfapi/pdf-tools-backend
# Check Python dependencies
source /home/pdfapi/pdf-tools-backend/venv/bin/activate
pip list
```

**Issue: 502 Bad Gateway**
```bash
# Check if Gunicorn is running
sudo systemctl status pdf-api
# Check NGINX error logs
sudo tail -f /var/log/nginx/pdf-api-error.log
# Check if port 8000 is listening
sudo netstat -tulpn | grep :8000
```

**Issue: File upload fails**
```bash
# Check NGINX client_max_body_size
sudo nano /etc/nginx/sites-available/pdf-api
# Check directory permissions
ls -la /home/pdfapi/pdf-tools-backend/uploads
chmod 755 /home/pdfapi/pdf-tools-backend/uploads
```

**Issue: SSL certificate renewal fails**
```bash
# Test renewal manually
sudo certbot renew --dry-run
# Check certbot timer
sudo systemctl status certbot.timer
```

### Useful Commands

```bash
# Restart all services
sudo systemctl restart pdf-api nginx redis

# Check disk usage
du -sh /home/pdfapi/pdf-tools-backend/*

# Monitor real-time requests
sudo tail -f /var/log/nginx/pdf-api-access.log

# Test API endpoint
curl -X POST https://api.yourdomain.com/health

# Check SSL certificate expiry
sudo certbot certificates
```

---

## Deployment Checklist

- [ ] Server created on Hetzner Cloud (Germany region)
- [ ] DNS records configured (A record pointing to server IP)
- [ ] SSH access configured
- [ ] Firewall rules set (ports 22, 80, 443)
- [ ] Non-root user created
- [ ] Python 3.11 installed
- [ ] System dependencies installed (image libraries)
- [ ] NGINX installed and configured
- [ ] Redis installed and secured
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Python dependencies installed
- [ ] Environment variables configured (.env file)
- [ ] NGINX reverse proxy configured
- [ ] SSL certificate obtained (Let's Encrypt)
- [ ] Systemd service created for Gunicorn
- [ ] Celery worker configured (optional)
- [ ] File cleanup cron job configured
- [ ] Log rotation configured
- [ ] Fail2Ban configured
- [ ] Health check monitoring enabled
- [ ] Backend tested (all endpoints working)
- [ ] CORS configured for frontend domain
- [ ] Backups enabled in Hetzner Cloud

---

## Frontend Integration

After deploying the backend, update your Next.js frontend:

**Frontend .env.production:**
```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

**Update CORS in backend:**
```bash
# Edit main.py
sudo nano /home/pdfapi/pdf-tools-backend/main.py
```

Update `allow_origins`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        "https://your-frontend.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

```bash
# Restart service
sudo systemctl restart pdf-api
```

---

## Cost Estimation (Hetzner Cloud - Germany)

- **CX11** (2GB RAM): ~€4.15/month
- **CX21** (4GB RAM): ~€5.83/month
- **CX31** (8GB RAM): ~€10.59/month
- **Backups**: +20% of server cost
- **Traffic**: 20TB included (more than enough)

**Recommended**: CX21 for production = ~€7/month with backups

---

## Support & Resources

- [Hetzner Cloud Docs](https://docs.hetzner.com/cloud/)
- [NGINX Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

---

**Deployment completed!** Your PDF Tools API is now running securely on Hetzner Cloud in Germany with SSL, NGINX reverse proxy, and production-ready configuration.
