# Azure Web App Deployment Guide for PDF Tools API

## Updated: November 2025 - With Azure Redis Integration

This guide uses:
- ✓ Azure Web App (Python 3.11)
- ✓ Azure Redis Cache (managed service)
- ✓ PyPDF2 for PDF operations (no external dependencies)
- ✓ GitHub Actions for CI/CD

---

## Quick Deployment Steps

### 1. Prerequisites
- Azure subscription with Web App and Redis Cache already created
- GitHub repository with the code
- Azure CLI (optional, for manual commands)

### 2. Azure Resources Setup (One-Time)

#### Create Resource Group
```bash
az group create --name pdf-tools-rg --location eastus
```

#### Create App Service Plan
```bash
az appservice plan create \
    --name pdf-tools-plan \
    --resource-group pdf-tools-rg \
    --sku S1 \
    --is-linux
```

#### Create Web App
```bash
az webapp create \
    --resource-group pdf-tools-rg \
    --plan pdf-tools-plan \
    --name pdfbackendpython \
    --runtime "PYTHON:3.11"
```

#### Create Azure Redis Cache
```bash
az redis create \
    --resource-group pdf-tools-rg \
    --name pythonbackendpdf \
    --location eastus \
    --sku Basic \
    --vm-size c0
```

Get the connection string from Azure Portal or CLI:
```bash
az redis list-keys \
    --resource-group pdf-tools-rg \
    --name pythonbackendpdf
```

---

### 3. Configure Environment Variables

Set these in Azure Web App → Configuration → Application settings:

```
REDIS_URL = rediss://default:YOUR_PRIMARY_KEY@pythonbackendpdf.redis.cache.windows.net:6380/0
PYTHONPATH = /home/site/wwwroot
```

**Replace `YOUR_PRIMARY_KEY`** with the primary access key from Azure Redis.

#### Using Azure CLI:
```bash
az webapp config appsettings set \
    --resource-group pdf-tools-rg \
    --name pdfbackendpython \
    --settings \
        "REDIS_URL=rediss://default:YOUR_PRIMARY_KEY@pythonbackendpdf.redis.cache.windows.net:6380/0" \
        "PYTHONPATH=/home/site/wwwroot"
```

---

### 4. Configure Startup Command

#### Option A: Using Startup File (Recommended)
```bash
az webapp config set \
    --resource-group pdf-tools-rg \
    --name pdfbackendpython \
    --startup-file "gunicorn -k uvicorn.workers.UvicornWorker main:app --workers 2 --timeout 300 --bind 0.0.0.0:8000"
```

#### Option B: In Azure Portal
1. Go to **Configuration** → **General settings**
2. Set **Startup Command** to:
```
gunicorn -k uvicorn.workers.UvicornWorker main:app --workers 2 --timeout 300 --bind 0.0.0.0:8000
```

---

### 5. Deploy Code

#### Option A: Git Push Deployment (Recommended)

**Step 1: Configure local Git deployment**
```bash
az webapp deployment source config-local-git \
    --resource-group pdf-tools-rg \
    --name pdfbackendpython
```

This returns a Git URL like: `https://yourusername@pdfbackendpython.scm.azurewebsites.net/pdfbackendpython.git`

**Step 2: Add remote and push**
```bash
git remote add azure <git-url-from-above>
git push azure main
```

#### Option B: GitHub Actions (Automated)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Azure

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'pdfbackendpython'
          publish-profile: ${{ secrets.AZURE_PUBLISH_PROFILE }}
```

**Get publish profile:**
1. In Azure Portal, go to **Web App** → **Download publish profile**
2. Add it to GitHub Secrets as `AZURE_PUBLISH_PROFILE`

#### Option C: ZIP Deployment
```bash
zip -r deploy.zip . -x "*.git*" "*venv*" "*__pycache__*" "*.pyc" "*node_modules*"

az webapp deploy \
    --resource-group pdf-tools-rg \
    --name pdfbackendpython \
    --src-path deploy.zip \
    --type zip
```

---

### 6. Verify Deployment

**Check logs:**
```bash
az webapp log tail \
    --resource-group pdf-tools-rg \
    --name pdfbackendpython
```

**Test endpoints:**
```bash
# Health check
curl https://pdfbackendpython.azurewebsites.net/health

# API info
curl https://pdfbackendpython.azurewebsites.net/

# Interactive docs
https://pdfbackendpython.azurewebsites.net/docs
```

---

### 7. Enable HTTPS Only

```bash
az webapp update \
    --resource-group pdf-tools-rg \
    --name pdfbackendpython \
    --https-only true
```

---

## Troubleshooting

### Issue: Connection Timeout to Redis
**Solution:** Check Azure Redis firewall rules
1. Azure Portal → Redis Cache → Networking → Firewall rules
2. Add your App Service IP address
3. Or enable "Allow access from Azure Services"

### Issue: 502 Bad Gateway / App Crashes
**Solution:** Check startup logs
```bash
az webapp log tail --resource-group pdf-tools-rg --name pdfbackendpython
```

Common causes:
- Missing REDIS_URL environment variable
- Redis password incorrect
- Startup command syntax error

### Issue: Celery Tasks Not Processing
**Solution:** Verify Redis connection
```bash
# Test Redis connection from app
python3 -c "from celery_app import celery_app; celery_app.broker_connection().connect()"
```

### Issue: "Gunicorn: command not found"
**Solution:** Ensure requirements.txt is installed
```bash
az webapp ssh --resource-group pdf-tools-rg --name pdfbackendpython
pip list | grep gunicorn
```

---

## Performance Optimization

### Increase Worker Processes
Edit startup command to use more workers (if using S2 or higher):
```
gunicorn -k uvicorn.workers.UvicornWorker main:app --workers 4 --timeout 300 --bind 0.0.0.0:8000
```

### Scale Up App Service
```bash
# Upgrade to S2 (2 cores, 3.5 GB RAM)
az appservice plan update \
    --name pdf-tools-plan \
    --resource-group pdf-tools-rg \
    --sku S2
```

### Enable Auto-Scaling
```bash
az monitor autoscale create \
    --resource-group pdf-tools-rg \
    --resource pdfbackendpython \
    --resource-type "Microsoft.Web/sites" \
    --min-count 1 \
    --max-count 3
```

---

## Cost Estimation

| Component | Tier | Cost/Month |
|-----------|------|-----------|
| App Service | S1 | $70 |
| Azure Redis | Basic C0 | $16 |
| **Total** | | **~$86** |

For higher traffic, upgrade to S2 ($140/month) + Standard Redis ($55/month) = $195/month

---

## Security Best Practices

### 1. Regenerate Redis Keys Regularly
```bash
az redis regenerate-keys \
    --resource-group pdf-tools-rg \
    --name pythonbackendpdf \
    --key-type primary
```

Then update `REDIS_URL` in App Settings.

### 2. Enable Azure Front Door (DDoS Protection)
```bash
az network front-door create \
    --resource-group pdf-tools-rg \
    --name pdf-tools-fd \
    --backend-address pdfbackendpython.azurewebsites.net
```

### 3. Enable Application Insights
```bash
az monitor app-insights component create \
    --app pdf-tools-insights \
    --resource-group pdf-tools-rg \
    --application-type web

# Get instrumentation key and add to App Settings
```

### 4. Restrict IP Access (Optional)
```bash
az webapp config access-restriction add \
    --resource-group pdf-tools-rg \
    --name pdfbackendpython \
    --rule-name AllowOffice \
    --action Allow \
    --ip-address 203.0.113.0/24 \
    --priority 100
```

---

## Monitoring & Alerts

### View App Service Metrics
1. Azure Portal → Web App → Metrics
2. Monitor: CPU Percentage, Memory Percentage, HTTP 5xx errors

### Set Up Alerts
```bash
az monitor metrics alert create \
    --name "High CPU Alert" \
    --resource-group pdf-tools-rg \
    --scopes /subscriptions/{sub-id}/resourceGroups/pdf-tools-rg/providers/Microsoft.Web/sites/pdfbackendpython \
    --condition "avg Percentage CPU > 80" \
    --window-size 5m \
    --evaluation-frequency 1m
```

---

## Architecture Overview

```
Client Request
    ↓
Azure Front Door / CDN (Optional)
    ↓
App Service (Web App)
    ├── FastAPI Server (Port 8000)
    ├── Gunicorn WSGI Server
    └── Python 3.11
    ↓
Azure Redis Cache (rediss://...)
    ├── Celery Broker
    └── Task Results
    ↓
Processed Response
```

---

## What's NOT Needed (Unlike Previous Docs)

- ❌ **Ghostscript** - Using PyPDF2 (pure Python)
- ❌ **Local Redis** - Using Azure Redis Cache (managed service)
- ❌ **SSH Installation** - No system dependencies needed
- ❌ **Docker** - Direct App Service deployment works fine

---

## Next Steps

1. ✅ Set `REDIS_URL` environment variable in Azure
2. ✅ Deploy code (via Git push or GitHub Actions)
3. ✅ Test `/health` endpoint
4. ✅ Monitor logs for any errors
5. ✅ Configure custom domain (optional)

For questions, check Azure documentation: https://docs.microsoft.com/en-us/azure/app-service/
