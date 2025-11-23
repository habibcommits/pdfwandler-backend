# 🔧 Azure Container Instances - Complete Configuration Guide

**Last Updated:** November 23, 2025  
**Purpose:** Step-by-step configuration guide for deploying PDF Tools API to Azure Container Instances

---

## ⚠️ IMPORTANT UPDATE (November 23, 2025)

**CRITICAL FIX:** The Dockerfile has been updated to remove a health check that caused Celery containers to crash in Azure Container Instances. If you built your Docker image before this date and are experiencing container restart issues, you **MUST rebuild and push your image**.

**What was fixed:**
- Removed FastAPI-specific health check from Dockerfile
- Health check was causing Celery Worker and Celery Beat containers to fail repeatedly
- Azure would restart these containers continuously, preventing background task processing

**Action required:** Follow Step 1 below to rebuild your Docker image with the latest Dockerfile.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Variables](#environment-variables)
3. [Docker Configuration](#docker-configuration)
4. [Azure Container Instances Setup](#azure-container-instances-setup)
5. [Troubleshooting](#troubleshooting)
6. [Monitoring & Logs](#monitoring--logs)

---

## 🎯 Prerequisites

### Required Accounts
- ✅ GitHub account (for code repository)
- ✅ Docker Hub account (for image storage)
- ✅ Azure account (for deployment)
- ✅ Play with Docker access (optional, for testing)

### Required Tools
- Azure CLI (for advanced deployment) - **Optional, GUI method available**
- Docker (for local testing) - **Optional, can use Play with Docker**

---

## 🔐 Environment Variables

### Overview
Your application requires **4 environment variables** for proper configuration:

| Variable | Purpose | Example Value | Required |
|----------|---------|---------------|----------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` | ✅ Yes |
| `CELERY_BROKER_URL` | Celery message broker | `redis://localhost:6379/0` | ✅ Yes |
| `CELERY_RESULT_BACKEND` | Celery results storage | `redis://localhost:6379/0` | ✅ Yes |
| `PYTHONUNBUFFERED` | Python logging | `1` | ⚠️ Recommended |

### Important Notes

#### For Azure Container Instances Multi-Container Deployment:
- ✅ **Use `localhost`** for all Redis URLs (containers share the same network)
- ❌ **Do NOT use** container names or external IPs
- ✅ All containers in the group communicate via `localhost`

#### Example Configuration:
```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
PYTHONUNBUFFERED=1
```

---

## 🐳 Docker Configuration

### Step 1: Build Docker Image for Azure

**CRITICAL:** Azure uses **AMD64 architecture**. If you're building on a Mac M1/M2 or ARM-based system, you MUST specify the platform:

```bash
# On any system (including Apple Silicon M1/M2)
docker build --platform linux/amd64 -t your-dockerhub-username/pdf-tools:latest .

# Verify the build
docker images | grep pdf-tools
```

### Step 2: Test Locally (Optional)

Before pushing to Azure, test the multi-container setup locally:

```bash
# Create a test network
docker network create pdf-network

# Start Redis
docker run -d --name redis --network pdf-network -p 6379:6379 redis:7-alpine

# Start your app (replace with your image name)
docker run -d --name fastapi --network pdf-network -p 5000:5000 \
  -e REDIS_URL=redis://redis:6379/0 \
  -e CELERY_BROKER_URL=redis://redis:6379/0 \
  -e CELERY_RESULT_BACKEND=redis://redis:6379/0 \
  your-dockerhub-username/pdf-tools:latest

# Check logs
docker logs fastapi
docker logs redis

# Test the API
curl http://localhost:5000/health
```

### Step 3: Push to Docker Hub

Using Play with Docker or your local Docker:

```bash
# Login to Docker Hub
docker login
# Enter your Docker Hub username and password

# Push the image
docker push your-dockerhub-username/pdf-tools:latest

# Verify it's on Docker Hub
# Visit: https://hub.docker.com/r/your-dockerhub-username/pdf-tools
```

---

## ☁️ Azure Container Instances Setup

### Deployment Method: YAML Configuration

**Why YAML?**
- Multi-container deployments in Azure Container Instances **require YAML or ARM templates**
- The Azure Portal GUI does NOT support multi-container setups
- YAML is simpler than ARM templates

### Option A: Azure Portal + YAML (Recommended)

#### Step 1: Prepare the YAML File

Use the provided `azure-deployment.yaml` file in this repository. **Update these values:**

```yaml
# Line 3: Change to your Azure region (e.g., eastus, westus2, westeurope)
location: eastus

# Line 4: Change to your desired container group name
name: pdf-tools-api

# Line 9: Update with your Docker Hub image
image: your-dockerhub-username/pdf-tools:latest

# Line 39: Update with your Docker Hub image (for Celery Worker)
image: your-dockerhub-username/pdf-tools:latest

# Line 61: Update with your Docker Hub image (for Celery Beat)
image: your-dockerhub-username/pdf-tools:latest

# Line 98: Change DNS label (this becomes your URL)
dnsNameLabel: pdf-tools-unique-name
```

**Your final URL will be:**
```
http://pdf-tools-unique-name.eastus.azurecontainer.io
```

#### Step 2: Upload YAML via Azure Portal

1. **Login to Azure Portal:** https://portal.azure.com
2. **Navigate to:** Container Instances
3. **Click:** Create
4. **Basics Tab:**
   - Subscription: Select your subscription
   - Resource Group: Create new or select existing
   - Container group name: `pdf-tools-api`
   - Region: `East US` (or your preferred region)
5. **Click:** "Review + Create" *(skip other tabs)*
6. **WAIT!** Do NOT click "Create" yet
7. **Click:** "Download a template for automation"
8. **Replace** the entire template with your `azure-deployment.yaml` content
9. **Click:** "Create"

#### Step 3: Wait for Deployment

- Deployment takes **2-5 minutes**
- Monitor progress in "Notifications" (bell icon)
- Status will show: "Deployment in progress" → "Deployment succeeded"

#### Step 4: Get Your Public URL

```bash
# Find your URL in the Azure Portal
1. Go to Container Instances → pdf-tools-api
2. Look for "FQDN" (Fully Qualified Domain Name)
3. Your URL: http://<your-dns-label>.<region>.azurecontainer.io

# Test the API
curl http://<your-url>/health
# Expected: {"status":"healthy"}
```

---

### Option B: Azure CLI (Advanced Users)

If you have Azure CLI installed:

```bash
# Login to Azure
az login

# Create resource group
az group create --name pdf-tools-rg --location eastus

# Deploy using YAML
az container create \
  --resource-group pdf-tools-rg \
  --file azure-deployment.yaml

# Check status
az container show \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --query "provisioningState"

# Get logs
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name fastapi
```

---

## 🔍 Environment Variables Configuration in YAML

Your `azure-deployment.yaml` includes environment variables for each container:

### FastAPI Container (Main API)
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

### Celery Worker Container
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

### Celery Beat Container (Scheduler)
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

### Redis Container
**No environment variables needed** - Redis runs with default configuration

---

## 🚨 Troubleshooting

### Issue 1: Container Crashes Immediately

**Symptoms:**
- Deployment succeeds but no response from API
- Container shows "Killing" in events

**Common Causes:**

#### A. Missing Environment Variables
```bash
# Check if env vars are set correctly in YAML
# They should be under each container's properties → environmentVariables
```

#### B. Wrong Platform Architecture
```bash
# Solution: Rebuild with correct platform
docker build --platform linux/amd64 -t your-image:latest .
docker push your-image:latest

# Then redeploy to Azure
```

#### C. Incorrect Restart Policy
```yaml
# In azure-deployment.yaml, line 101:
restartPolicy: Always  # ← Should be "Always" for long-running services
```

### Issue 2: Redis Connection Errors

**Symptoms:**
- Celery workers can't connect to broker
- Error: "Error 111 connecting to localhost:6379"

**Solution:**
```yaml
# Verify Redis container is in the YAML:
containers:
  - name: redis
    properties:
      image: redis:7-alpine
      ports:
      - port: 6379
```

**Check that all containers use `localhost`:**
```yaml
environmentVariables:
- name: REDIS_URL
  value: redis://localhost:6379/0  # ← Must be "localhost"
```

### Issue 3: 502 Bad Gateway

**Symptoms:**
- URL loads but shows 502 error
- FastAPI container not responding

**Solution:**
```yaml
# Verify port mapping in YAML:
ports:
- protocol: TCP
  port: 5000  # ← Must match your app's port

# And in ipAddress section:
ipAddress:
  type: Public
  ports:
  - protocol: TCP
    port: 5000  # ← Must match container port
```

### Issue 4: Cannot Find Image on Docker Hub

**Symptoms:**
- Deployment fails with "image not found"

**Solution:**
```bash
# Make sure image is public on Docker Hub
1. Go to https://hub.docker.com
2. Find your image → Settings → Make Public

# Or provide Docker Hub credentials in YAML:
imageRegistryCredentials:
- server: docker.io
  username: your-dockerhub-username
  password: your-dockerhub-password  # Use Azure Key Vault for production
```

---

## 📊 Monitoring & Logs

### View Logs in Azure Portal

1. **Go to:** Container Instances → pdf-tools-api
2. **Select:** Containers (left menu)
3. **Choose container:** fastapi, celery-worker, or redis
4. **Click:** Logs tab

### View Logs via Azure CLI

```bash
# FastAPI logs
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name fastapi

# Celery Worker logs
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name celery-worker

# Celery Beat logs
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name celery-beat

# Redis logs
az container logs \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --container-name redis
```

### Check Container Events

```bash
az container show \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --query "containers[*].instanceView.events"
```

### Enable Log Analytics (Recommended)

For persistent logs and advanced monitoring:

1. **Create Log Analytics Workspace:**
   - Azure Portal → Log Analytics Workspaces → Create
   - Name: `pdf-tools-logs`
   - Region: Same as your container

2. **Update YAML to include diagnostics:**
```yaml
diagnostics:
  logAnalytics:
    workspaceId: <your-workspace-id>
    workspaceKey: <your-workspace-key>
```

3. **Query logs with KQL:**
```kusto
ContainerInstanceLog_CL
| where TimeGenerated > ago(1h)
| where ContainerGroup_s == "pdf-tools-api"
| project TimeGenerated, ContainerName_s, Message
| order by TimeGenerated desc
```

---

## ✅ Deployment Checklist

Before deploying, verify:

- [ ] Docker image built with `--platform linux/amd64`
- [ ] Image pushed to Docker Hub
- [ ] Docker Hub image is **public** (or credentials provided)
- [ ] `azure-deployment.yaml` updated with your Docker Hub username
- [ ] DNS label is unique (no one else is using it)
- [ ] All environment variables set to `redis://localhost:6379/0`
- [ ] Resource group created in Azure
- [ ] Region matches in YAML and Azure Portal

After deployment, test:

- [ ] Health endpoint: `curl http://<your-url>/health`
- [ ] Root endpoint: `curl http://<your-url>/`
- [ ] API docs: Open `http://<your-url>/docs` in browser
- [ ] Check logs for all 4 containers (no errors)
- [ ] Upload a test PDF via Swagger UI

---

## 🎉 Success Criteria

Your deployment is successful when:

1. ✅ All 4 containers show "Running" status
2. ✅ Health endpoint returns `{"status":"healthy"}`
3. ✅ Swagger UI loads at `/docs`
4. ✅ No errors in container logs
5. ✅ You can upload and process files via API

---

## 🆘 Need Help?

### Common Commands Reference

```bash
# Restart container group
az container restart \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api

# Stop container group
az container stop \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api

# Start container group
az container start \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api

# Delete container group
az container delete \
  --resource-group pdf-tools-rg \
  --name pdf-tools-api \
  --yes
```

### Azure Support Resources

- **Documentation:** https://learn.microsoft.com/azure/container-instances/
- **Troubleshooting:** https://learn.microsoft.com/azure/container-instances/container-instances-troubleshooting
- **Pricing:** https://azure.microsoft.com/pricing/details/container-instances/

---

## 📝 Notes

- **Cost:** Azure Container Instances charges per second of CPU/memory usage
- **Scaling:** For high traffic, consider Azure Container Apps or AKS
- **Security:** Use Azure Key Vault for production secrets
- **Backups:** Container data is ephemeral; use Azure Files for persistence

---

**Configuration guide complete!** Follow this guide step-by-step for successful deployment.
