# 🚀 Azure Container Instances - Quick Start Guide

**Deploy in 15 Minutes!** Follow these exact steps to deploy your PDF Tools API to Azure.

---

## ⚠️ CRITICAL: Docker Image Update Required

**If you built your Docker image BEFORE November 23, 2025, you MUST rebuild it!**

We fixed a critical health check issue that caused Celery containers to crash in Azure. The old Dockerfile had a health check that only worked for FastAPI containers. The new version removes the health check to support multi-container deployments.

**If you see containers restarting repeatedly in Azure, rebuild and push your image again.**

---

## ✅ Prerequisites

- [ ] Docker Hub account: https://hub.docker.com
- [ ] Azure account: https://portal.azure.com  
- [ ] Play with Docker access (or Docker installed locally): https://labs.play-with-docker.com

---

## 📦 Step 1: Build and Push Docker Image

### Option A: Using Play with Docker (No Local Installation Required)

1. **Open Play with Docker:** https://labs.play-with-docker.com
2. **Click:** "Start" button
3. **Click:** "+ ADD NEW INSTANCE" button
4. **In the terminal, run these commands:**

```bash
# Clone your repository (replace with your GitHub repo URL)
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO

# Build Docker image for AMD64 (Azure compatibility)
docker build --platform linux/amd64 -t YOUR-DOCKERHUB-USERNAME/pdf-tools:latest .

# Login to Docker Hub
docker login
# Enter your Docker Hub username and password when prompted

# Push to Docker Hub
docker push YOUR-DOCKERHUB-USERNAME/pdf-tools:latest

# Verify the push
echo "✅ Image pushed successfully!"
echo "View at: https://hub.docker.com/r/YOUR-DOCKERHUB-USERNAME/pdf-tools"
```

### Option B: Using Local Docker

```bash
# Navigate to your project directory
cd /path/to/pdf-tools-api

# Build for AMD64 architecture (required for Azure)
docker build --platform linux/amd64 -t YOUR-DOCKERHUB-USERNAME/pdf-tools:latest .

# Login to Docker Hub
docker login

# Push to Docker Hub
docker push YOUR-DOCKERHUB-USERNAME/pdf-tools:latest
```

**⏱️ Estimated time:** 3-5 minutes

---

## 🔧 Step 2: Configure Deployment YAML

1. **Open `azure-deployment.yaml` in a text editor**

2. **Replace these 4 values:**

   ```yaml
   # Line 9, 39, 61: Replace YOUR Docker Hub username
   image: YOUR-DOCKERHUB-USERNAME/pdf-tools:latest
   
   # Line 98: Choose a unique DNS name (letters, numbers, hyphens only)
   dnsNameLabel: YOUR-UNIQUE-NAME
   ```

3. **Example after changes:**
   ```yaml
   image: johnsmith/pdf-tools:latest
   dnsNameLabel: johnsmith-pdf-api
   ```

4. **Save the file**

**Your final URL will be:**
```
http://YOUR-UNIQUE-NAME.eastus.azurecontainer.io
```

**⏱️ Estimated time:** 2 minutes

---

## ☁️ Step 3: Deploy to Azure

### Method 1: Azure Portal (Easiest - No CLI Required)

1. **Login to Azure Portal:** https://portal.azure.com

2. **Search for "Container Instances"** in the top search bar

3. **Click:** "Create" button

4. **Basics Tab:**
   - **Subscription:** Select your subscription
   - **Resource Group:** Click "Create new" → Enter `pdf-tools-rg`
   - **Container group name:** Enter `pdf-tools-api`
   - **Region:** Select `East US` (or match your YAML location)

5. **⚠️ IMPORTANT - Skip to YAML:**
   - **Do NOT fill** other fields
   - **Click:** "Review + create" button at bottom
   - **Click:** "Download a template for automation" link
   
6. **Replace Template:**
   - **Delete all** the existing template content
   - **Copy and paste** your entire `azure-deployment.yaml` content
   - **Click:** "Save"

7. **Deploy:**
   - **Click:** "Review + create"
   - **Click:** "Create"
   - **Wait:** 2-5 minutes for deployment

8. **Get Your URL:**
   - After deployment completes, click "Go to resource"
   - Find **FQDN** (Fully Qualified Domain Name)
   - Example: `yourname.eastus.azurecontainer.io`

**⏱️ Estimated time:** 5 minutes

---

### Method 2: Azure CLI (For Advanced Users)

```bash
# Install Azure CLI (if not installed)
# Visit: https://learn.microsoft.com/cli/azure/install-azure-cli

# Login to Azure
az login

# Create resource group
az group create \
  --name pdf-tools-rg \
  --location eastus

# Deploy using YAML file
az container create \
  --resource-group pdf-tools-rg \
  --file azure-deployment.yaml

# Get the public URL
az container show \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --query "ipAddress.fqdn" \
  --output tsv
```

**⏱️ Estimated time:** 3 minutes

---

## ✅ Step 4: Test Your Deployment

### Quick Health Check

```bash
# Replace with your actual URL
curl http://YOUR-URL.eastus.azurecontainer.io/health

# Expected response:
# {"status":"healthy"}
```

### Test in Browser

1. **Open your browser**
2. **Visit:** `http://YOUR-URL.eastus.azurecontainer.io/docs`
3. **You should see:** Swagger UI with API documentation
4. **Try an endpoint:** Click "GET /health" → "Try it out" → "Execute"

### Test File Upload

1. **In Swagger UI:** Click "POST /api/image-to-pdf"
2. **Click:** "Try it out"
3. **Upload** an image file (JPG, PNG)
4. **Click:** "Execute"
5. **Download** the generated PDF

**⏱️ Estimated time:** 2 minutes

---

## 🔍 Troubleshooting

### Issue: Deployment Succeeds But No Response

**Check Container Logs:**

```bash
# Using Azure CLI
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name fastapi

# Or in Azure Portal:
# Go to: Container Instances → pdf-tools-api → Containers → fastapi → Logs
```

**Common Causes:**
1. ❌ Wrong Docker Hub username in YAML
2. ❌ Image not found on Docker Hub (check it's public)
3. ❌ Wrong platform (rebuild with `--platform linux/amd64`)

**Solution:**
```bash
# Make Docker Hub image public
1. Go to https://hub.docker.com
2. Click your image → Settings → Make Public

# Or rebuild with correct platform
docker build --platform linux/amd64 -t YOUR-USERNAME/pdf-tools:latest .
docker push YOUR-USERNAME/pdf-tools:latest

# Then redeploy to Azure (delete and recreate container group)
```

---

### Issue: 502 Bad Gateway

**Cause:** FastAPI container not responding on port 5000

**Check:**
```bash
# View FastAPI logs
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name fastapi
```

**Look for errors like:**
- "Error connecting to Redis"
- "ModuleNotFoundError"
- Python exceptions

**Solution:** Review `CONFIGURATION.md` for detailed troubleshooting

---

### Issue: Celery Workers Not Processing Tasks

**Check Worker Logs:**
```bash
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name celery-worker
```

**Expected in logs:**
```
[tasks]
  . tasks.process_image_to_pdf
  . tasks.process_merge_pdf
  . tasks.process_compress_pdf
  . tasks.cleanup_old_files
```

**If tasks are missing:** Check that `celery_app.py` has `include=['tasks']`

---

## 🎯 Quick Reference

### Your Deployment Info

| Item | Value | Example |
|------|-------|---------|
| **Docker Hub Image** | `YOUR-USERNAME/pdf-tools:latest` | `johnsmith/pdf-tools:latest` |
| **DNS Label** | `YOUR-UNIQUE-NAME` | `johnsmith-pdf-api` |
| **Resource Group** | `pdf-tools-rg` | `pdf-tools-rg` |
| **Container Group** | `pdf-tools-api` | `pdf-tools-api` |
| **Region** | `eastus` | `eastus` |
| **Public URL** | `http://YOUR-NAME.eastus.azurecontainer.io` | `http://johnsmith-pdf-api.eastus.azurecontainer.io` |

### API Endpoints

- **Health Check:** `GET /health`
- **API Docs:** `GET /docs`
- **Image to PDF:** `POST /api/image-to-pdf`
- **Merge PDF:** `POST /api/merge-pdf`
- **Compress PDF:** `POST /api/compress-pdf`

### Useful Commands

```bash
# View all containers in group
az container show \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --query "containers[].name"

# Restart container group
az container restart \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api

# Delete container group
az container delete \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --yes
```

---

## 💰 Cost Estimate

**Azure Container Instances Pricing (Pay-per-second):**

| Resource | vCPU | Memory | Hours/Month | Cost/Month |
|----------|------|--------|-------------|------------|
| FastAPI | 1.0 | 2.0 GB | 730 | ~$35 |
| Celery Worker | 1.0 | 1.5 GB | 730 | ~$28 |
| Celery Beat | 0.5 | 0.5 GB | 730 | ~$9 |
| Redis | 0.5 | 0.5 GB | 730 | ~$9 |
| **TOTAL** | **3.0** | **4.5 GB** | - | **~$81/month** |

**💡 Tips to reduce costs:**
- Stop container when not in use
- Use Azure Container Apps for auto-scaling
- Deploy only during business hours

---

## 🎉 Success!

**You should now have:**
- ✅ Docker image on Docker Hub
- ✅ Running Azure Container Instance
- ✅ Public URL with API documentation
- ✅ All 4 services running (FastAPI, Celery, Beat, Redis)

**Next Steps:**
- Configure custom domain (optional)
- Set up monitoring with Application Insights
- Configure auto-scaling (Azure Container Apps)
- Add authentication to API endpoints

---

## 📚 Additional Resources

- **Full Configuration Guide:** `CONFIGURATION.md`
- **Deployment Guide:** `AZURE_DEPLOYMENT_GUIDE_COMPLETE.md`
- **Inspection Report:** `INSPECTION_REPORT.md`
- **Azure Documentation:** https://learn.microsoft.com/azure/container-instances/

---

**Need help?** Review `CONFIGURATION.md` for detailed troubleshooting and environment variable configuration.
