# ✅ Azure Deployment Checklist

**Use this checklist to ensure successful deployment to Azure Container Instances**

---

## 🔧 Pre-Deployment (Local Setup)

### Step 1: Code Repository
- [ ] All code pushed to GitHub
- [ ] Latest version includes updated Dockerfile (without health check)
- [ ] All configuration files present:
  - `azure-deployment.yaml`
  - `CONFIGURATION.md`
  - `AZURE_QUICK_START.md`
  - `requirements.txt`

### Step 2: Docker Hub Account
- [ ] Docker Hub account created
- [ ] Account username ready (you'll need this for image naming)

---

## 🐳 Docker Image Build

### Step 3: Build Image
- [ ] Choose build method:
  - Option A: Play with Docker (online, no installation)
  - Option B: Local Docker (requires Docker installed)

### Step 4: Build Commands
```bash
# Clone repository
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO

# Build for AMD64 (Azure architecture)
docker build --platform linux/amd64 -t YOUR-DOCKERHUB-USERNAME/pdf-tools:latest .
```

- [ ] Build completed without errors
- [ ] Image size is reasonable (< 1GB)

### Step 5: Push to Docker Hub
```bash
# Login
docker login

# Push
docker push YOUR-DOCKERHUB-USERNAME/pdf-tools:latest
```

- [ ] Push completed successfully
- [ ] Image visible on Docker Hub at: `https://hub.docker.com/r/YOUR-USERNAME/pdf-tools`
- [ ] Image is set to **Public** (or you have registry credentials configured)

---

## 📝 YAML Configuration

### Step 6: Update azure-deployment.yaml

Edit `azure-deployment.yaml` and replace:

**Line 9 (FastAPI container):**
```yaml
image: YOUR-DOCKERHUB-USERNAME/pdf-tools:latest
```
- [ ] Updated with your Docker Hub username

**Line 39 (Celery Worker):**
```yaml
image: YOUR-DOCKERHUB-USERNAME/pdf-tools:latest
```
- [ ] Updated with your Docker Hub username

**Line 61 (Celery Beat):**
```yaml
image: YOUR-DOCKERHUB-USERNAME/pdf-tools:latest
```
- [ ] Updated with your Docker Hub username

**Line 98 (DNS Label):**
```yaml
dnsNameLabel: YOUR-UNIQUE-NAME
```
- [ ] Updated with a unique name (only letters, numbers, hyphens)
- [ ] Checked name is unique (try: `your-name-pdf-api-123`)

### Step 7: Verify Environment Variables

Check that all containers have these environment variables:

```yaml
environmentVariables:
- name: REDIS_URL
  value: redis://localhost:6379/0
- name: CELERY_BROKER_URL
  value: redis://localhost:6379/0
- name: CELERY_RESULT_BACKEND
  value: redis://localhost:6379/0
- name: PYTHONUNBUFFERED
  value: "1"
```

- [ ] FastAPI container has all 4 variables
- [ ] Celery Worker has all 4 variables
- [ ] Celery Beat has all 4 variables
- [ ] All values use `localhost` (not container names)

---

## ☁️ Azure Deployment

### Step 8: Azure Portal Setup

- [ ] Logged into Azure Portal: https://portal.azure.com
- [ ] Navigated to "Container Instances"
- [ ] Clicked "Create"

### Step 9: Basic Configuration

**Basics Tab:**
- [ ] Subscription selected
- [ ] Resource Group: `pdf-tools-rg` (create new)
- [ ] Container group name: `pdf-tools-api`
- [ ] Region: `East US` (or match YAML location)

### Step 10: Deploy with YAML

- [ ] Clicked "Review + create" (skip other tabs)
- [ ] Clicked "Download a template for automation"
- [ ] Deleted ALL existing template content
- [ ] Pasted entire `azure-deployment.yaml` content
- [ ] Clicked "Save"
- [ ] Clicked "Review + create"
- [ ] Clicked "Create"
- [ ] Deployment started (shows "Deployment in progress")

### Step 11: Wait for Deployment

- [ ] Waited 2-5 minutes
- [ ] Deployment status shows "Deployment succeeded"
- [ ] Clicked "Go to resource"

---

## 🧪 Post-Deployment Testing

### Step 12: Get Your URL

In the Azure Portal, on your Container Instance overview page:

- [ ] Found **FQDN** (Fully Qualified Domain Name)
- [ ] Copied URL: `http://YOUR-NAME.eastus.azurecontainer.io`

### Step 13: Test Endpoints

**Health Check:**
```bash
curl http://YOUR-URL/health
# Expected: {"status":"healthy"}
```
- [ ] Health endpoint returns 200 OK
- [ ] Response shows "healthy"

**API Documentation:**
```
http://YOUR-URL/docs
```
- [ ] Swagger UI loads in browser
- [ ] All 5 endpoints visible:
  - GET /
  - GET /health
  - POST /api/image-to-pdf
  - POST /api/merge-pdf
  - POST /api/compress-pdf

### Step 14: Check Container Status

In Azure Portal → Container Instances → pdf-tools-api → Containers:

- [ ] FastAPI: Status = "Running"
- [ ] Celery Worker: Status = "Running"
- [ ] Celery Beat: Status = "Running"
- [ ] Redis: Status = "Running"

**If any container shows "Waiting" or "Terminated":**
1. Click the container name
2. Go to "Logs" tab
3. Read error messages
4. See troubleshooting section below

### Step 15: Test File Upload

In Swagger UI (`http://YOUR-URL/docs`):

1. **Expand:** POST /api/image-to-pdf
2. **Click:** "Try it out"
3. **Upload:** A JPG or PNG image
4. **Click:** "Execute"
5. **Check:** Response shows 200 OK
6. **Download:** The generated PDF

- [ ] Image upload successful
- [ ] PDF generated correctly
- [ ] Download works

---

## 🔍 Container Log Verification

### Step 16: Check Logs for Each Container

**FastAPI Logs:**
```bash
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name fastapi
```

**Look for:**
- [ ] "Uvicorn running on http://0.0.0.0:5000"
- [ ] "Application startup complete"
- [ ] No connection errors to Redis

**Celery Worker Logs:**
```bash
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name celery-worker
```

**Look for:**
- [ ] "[tasks]" section shows 4 tasks:
  - tasks.cleanup_old_files
  - tasks.process_compress_pdf
  - tasks.process_image_to_pdf
  - tasks.process_merge_pdf
- [ ] "Connected to redis://localhost:6379/0"
- [ ] "celery@... ready"

**Celery Beat Logs:**
```bash
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name celery-beat
```

**Look for:**
- [ ] "celery beat v5.5.3 is starting"
- [ ] "beat: Starting..."
- [ ] Scheduled tasks listed

**Redis Logs:**
```bash
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name redis
```

**Look for:**
- [ ] "Ready to accept connections tcp"
- [ ] Redis version displayed
- [ ] No error messages

---

## 🚨 Troubleshooting Common Issues

### Issue 1: Containers Restarting Repeatedly

**Symptoms:**
- Container status keeps switching between "Running" and "Waiting"
- Logs show container starting then stopping

**Causes:**
1. ❌ Using old Docker image with health check
2. ❌ Wrong architecture (ARM instead of AMD64)

**Solution:**
```bash
# Rebuild image with latest Dockerfile
docker build --platform linux/amd64 -t YOUR-USERNAME/pdf-tools:latest .
docker push YOUR-USERNAME/pdf-tools:latest

# Delete and recreate container group in Azure
```

- [ ] Rebuilt image with `--platform linux/amd64`
- [ ] Verified latest Dockerfile is used (no HEALTHCHECK line)
- [ ] Pushed updated image
- [ ] Redeployed to Azure

---

### Issue 2: Image Not Found

**Symptoms:**
- Deployment fails with "image not found" error

**Causes:**
1. ❌ Image not pushed to Docker Hub
2. ❌ Image is private but no credentials provided
3. ❌ Wrong image name in YAML

**Solution:**
```bash
# Make image public on Docker Hub
# Or add credentials to YAML (see CONFIGURATION.md)
```

- [ ] Verified image exists on Docker Hub
- [ ] Image is set to Public
- [ ] Image name in YAML matches Docker Hub

---

### Issue 3: 502 Bad Gateway

**Symptoms:**
- URL loads but shows "502 Bad Gateway"

**Causes:**
1. ❌ FastAPI container crashed
2. ❌ Wrong port configuration
3. ❌ Redis connection failed

**Solution:**
- [ ] Checked FastAPI container logs
- [ ] Verified port 5000 in YAML
- [ ] Checked Redis is running
- [ ] Verified environment variables

---

### Issue 4: Celery Tasks Not Processing

**Symptoms:**
- API uploads files but background processing doesn't work

**Causes:**
1. ❌ Celery worker not running
2. ❌ Tasks not registered
3. ❌ Redis connection failed

**Solution:**
- [ ] Checked celery-worker logs
- [ ] Verified [tasks] section shows 4 tasks
- [ ] Confirmed Redis is accessible
- [ ] Checked environment variables use `localhost`

---

## ✅ Deployment Success Criteria

**Your deployment is successful when ALL of these are true:**

1. **Container Status:**
   - [ ] All 4 containers show "Running" status
   - [ ] No containers restarting

2. **API Accessibility:**
   - [ ] Health endpoint returns `{"status":"healthy"}`
   - [ ] Swagger UI loads at `/docs`
   - [ ] All endpoints visible and testable

3. **Background Processing:**
   - [ ] Celery worker shows 4 registered tasks
   - [ ] File uploads trigger background processing
   - [ ] PDFs are generated correctly

4. **Logs Clean:**
   - [ ] No connection errors in FastAPI logs
   - [ ] No "cannot connect to Redis" in Celery logs
   - [ ] Redis shows "Ready to accept connections"

---

## 📊 Monitoring (Optional)

### Enable Log Analytics

For persistent logs and advanced monitoring:

1. Create Log Analytics Workspace
2. Link to Container Instance
3. Query logs with KQL

See `CONFIGURATION.md` for detailed instructions.

---

## 💰 Cost Tracking

**Monitor your Azure spending:**

1. Go to: Cost Management + Billing
2. Set up budget alerts
3. Expected cost: ~$81/month for 24/7 operation

**To reduce costs:**
- [ ] Stop container group when not in use
- [ ] Consider Azure Container Apps for auto-scaling
- [ ] Set up automatic shutdown schedule

---

## 🎉 Congratulations!

If all checklist items are complete, your PDF Tools API is successfully deployed to Azure!

**Next Steps:**
- [ ] Configure custom domain (optional)
- [ ] Set up SSL/TLS certificate
- [ ] Add API authentication
- [ ] Configure monitoring alerts
- [ ] Set up CI/CD pipeline

---

## 📚 Additional Resources

- **Quick Start:** `AZURE_QUICK_START.md`
- **Full Configuration:** `CONFIGURATION.md`
- **Inspection Report:** `INSPECTION_REPORT.md`
- **Azure Documentation:** https://learn.microsoft.com/azure/container-instances/

---

**Last Updated:** November 23, 2025  
**Version:** 1.0 (Health check issue resolved)
