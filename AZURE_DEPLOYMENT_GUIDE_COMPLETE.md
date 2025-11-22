# Complete Azure Deployment Guide - PDF Tools API
**100% GUI-Based - No Command Line Required**

Last Updated: November 22, 2025

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Deployment Steps](#deployment-steps)
5. [Testing](#testing)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Scaling](#scaling)
9. [Cost Breakdown](#cost-breakdown)

---

## Overview

This guide will help you deploy the complete PDF Tools API to Azure using **only the Azure Portal GUI**. No command line or SSH required!

### What You'll Deploy:
- ✅ FastAPI web server
- ✅ Celery worker for background tasks
- ✅ Celery Beat for scheduled tasks
- ✅ Azure Cache for Redis
- ✅ All components running 24/7

### Deployment Options:

**Option A: Azure Container Instances (Recommended for Start)**
- Simple, managed containers
- Pay-per-second billing
- Perfect for small to medium workloads
- No server management

**Option B: Azure App Service**
- Managed web hosting
- Built-in scaling
- Good for web-only apps
- Requires separate Celery hosting

We'll cover **both options** in this guide!

---

## Prerequisites

### Before You Start:

1. **Azure Account**
   - Sign up at: https://azure.microsoft.com/free/
   - New accounts get $200 free credit

2. **Your Code Ready**
   - Have your project code in a ZIP file
   - OR have it on GitHub

3. **What You Need to Know:**
   - Your project has 4 components:
     - FastAPI Server (web API)
     - Celery Worker (processes PDFs)
     - Celery Beat (cleanup scheduler)
     - Redis (message broker)

---

## Architecture

### How It Works:

```
                   ┌─────────────────────┐
                   │  Azure Container    │
                   │  Registry (ACR)     │
                   │  Stores Docker      │
                   │  Images             │
                   └─────────────────────┘
                            │
                            │ pulls images
                            ▼
┌──────────────────────────────────────────────────┐
│  Azure Container Instances / App Service         │
├──────────────────────────────────────────────────┤
│  ┌────────────┐  ┌──────────┐  ┌─────────────┐ │
│  │  FastAPI   │  │  Celery  │  │  Celery     │ │
│  │  Server    │  │  Worker  │  │  Beat       │ │
│  │  Port 5000 │  │          │  │  Scheduler  │ │
│  └────────────┘  └──────────┘  └─────────────┘ │
│         │              │              │          │
│         └──────── talks to ────────────┘          │
│                       │                           │
│                       ▼                           │
│              ┌─────────────────┐                 │
│              │  Azure Cache    │                 │
│              │  for Redis      │                 │
│              │  (Managed)      │                 │
│              └─────────────────┘                 │
└──────────────────────────────────────────────────┘
                       │
                       │
            Users access via HTTPS
```

---

## Deployment Steps

# PART 1: Setup Azure Resources

## Step 1: Create Resource Group

A resource group is a container for all your Azure resources.

### In Azure Portal:

1. Go to https://portal.azure.com and sign in
2. Click the hamburger menu (☰) → **Resource groups**
3. Click **+ Create**
4. Fill in:
   - **Subscription:** Select your subscription
   - **Resource group:** `pdf-tools-production`
   - **Region:** `East US` (or closest to your users)
5. Click **Review + Create** → **Create**
6. Wait 5 seconds for creation

✅ **Resource Group Created!**

---

## Step 2: Create Azure Container Registry (ACR)

ACR stores your Docker images securely.

### In Azure Portal:

1. In the search bar at top, type **"Container registries"**
2. Click **Container registries**
3. Click **+ Create**
4. Fill in **Basics** tab:
   - **Resource group:** `pdf-tools-production`
   - **Registry name:** `pdftools` (must be unique, lowercase, no spaces)
   - **Location:** `East US` (same as resource group)
   - **SKU:** `Basic` ($5/month)
5. Click **Next: Networking** → Keep defaults
6. Click **Next: Encryption** → Keep defaults
7. Click **Review + Create** → **Create**
8. Wait 1-2 minutes for deployment

### Enable Admin Access:

1. After deployment, click **Go to resource**
2. In left menu, click **Access keys**
3. Toggle **Admin user** to **Enabled**
4. **IMPORTANT:** Copy and save these (you'll need them later):
   - **Login server:** `pdftools.azurecr.io`
   - **Username:** `pdftools`
   - **password:** (copy the first password)

✅ **Container Registry Created!**

---

## Step 3: Create Azure Cache for Redis

Redis is your message broker for Celery.

### In Azure Portal:

1. In the search bar, type **"Azure Cache for Redis"**
2. Click **Azure Cache for Redis**
3. Click **+ Create**
4. Fill in **Basics** tab:
   - **Subscription:** Your subscription
   - **Resource group:** `pdf-tools-production`
   - **DNS name:** `pdf-tools-redis` (must be unique)
   - **Location:** `East US` (same region)
   - **Cache type:** Click **Configure**
     - Select **Basic** tab
     - Choose **C0 (250 MB)** - $16/month
     - Click **Select**
   - **Check** the box: "I agree to the Azure Cache for Redis terms"
5. Click **Next: Networking**
   - **Connectivity method:** Public endpoint
   - **Public network access:** Enabled
6. Click **Next: Advanced**
   - **Non-TLS port (6379):** Enabled (check this box)
   - Keep other defaults
7. Click **Review + Create** → **Create**
8. Wait 5-10 minutes (Redis takes time to provision)

### Get Redis Connection String:

1. After deployment, click **Go to resource**
2. In left menu, click **Access keys**
3. **IMPORTANT:** Copy and save:
   - **Primary connection string (StackExchange.Redis):** Copy this entire string
   - It looks like: `pdftools-redis.redis.cache.windows.net:6380,password=ABC123XYZ,ssl=True,abortConnect=False`
4. **Transform it to Redis URL format:**
   - From: `pdftools-redis.redis.cache.windows.net:6380,password=ABC123XYZ,ssl=True,abortConnect=False`
   - To: `rediss://:ABC123XYZ@pdf-tools-redis.redis.cache.windows.net:6380/0`
   - Format: `rediss://:YOUR_PASSWORD@YOUR_REDIS_NAME.redis.cache.windows.net:6380/0`

✅ **Redis Created!**

---

# PART 2: Build and Push Docker Images

## Step 4: Create Docker Images Locally

You need to create Docker images for your application. If you don't have Docker installed, use **Azure Cloud Shell** instead.

### Option A: Using Azure Cloud Shell (Recommended)

1. In Azure Portal, click the **Cloud Shell** icon (>_) at the top right
2. Select **Bash**
3. Upload your project files:
   - Click the **Upload/Download** icon
   - Upload all your project files
4. Create a Dockerfile:

```bash
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads temp attached_assets/generated_pdfs

# Expose port
EXPOSE 5000

# Default command (will be overridden for different services)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
EOF
```

5. Build the image:

```bash
# Login to ACR
az acr login --name pdftools

# Build image
az acr build --registry pdftools --image pdf-tools:latest .
```

This builds and pushes the image in one command!

✅ **Docker Image Built and Pushed!**

---

## Step 5: Deploy Using Azure Container Instances

Azure Container Instances (ACI) lets you run multiple containers together.

### Create YAML Deployment File:

1. In Azure Cloud Shell, create the deployment file:

```bash
cat > deploy.yaml << 'EOF'
apiVersion: '2021-09-01'
location: eastus
name: pdf-tools-app
properties:
  containers:
  # FastAPI Web Server
  - name: fastapi-server
    properties:
      image: pdftools.azurecr.io/pdf-tools:latest
      command:
        - uvicorn
        - main:app
        - --host
        - 0.0.0.0
        - --port
        - '5000'
      resources:
        requests:
          cpu: 1.0
          memoryInGB: 2.0
      ports:
      - port: 5000
        protocol: TCP
      environmentVariables:
      - name: REDIS_URL
        secureValue: YOUR_REDIS_CONNECTION_STRING_HERE
  
  # Celery Worker
  - name: celery-worker
    properties:
      image: pdftools.azurecr.io/pdf-tools:latest
      command:
        - celery
        - -A
        - celery_app
        - worker
        - --loglevel=info
        - --concurrency=2
      resources:
        requests:
          cpu: 1.0
          memoryInGB: 2.0
      environmentVariables:
      - name: REDIS_URL
        secureValue: YOUR_REDIS_CONNECTION_STRING_HERE
  
  # Celery Beat Scheduler
  - name: celery-beat
    properties:
      image: pdftools.azurecr.io/pdf-tools:latest
      command:
        - celery
        - -A
        - celery_app
        - beat
        - --loglevel=info
      resources:
        requests:
          cpu: 0.5
          memoryInGB: 1.0
      environmentVariables:
      - name: REDIS_URL
        secureValue: YOUR_REDIS_CONNECTION_STRING_HERE

  imageRegistryCredentials:
  - server: pdftools.azurecr.io
    username: pdftools
    password: YOUR_ACR_PASSWORD_HERE
  
  ipAddress:
    type: Public
    ports:
    - protocol: TCP
      port: 5000
  
  osType: Linux
  restartPolicy: Always

type: Microsoft.ContainerInstance/containerGroups
EOF
```

2. **Edit the YAML file** to add your credentials:

```bash
# Replace YOUR_REDIS_CONNECTION_STRING_HERE with your Redis URL
# Replace YOUR_ACR_PASSWORD_HERE with your ACR password
nano deploy.yaml
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

3. **Deploy to Azure:**

```bash
az container create \
  --resource-group pdf-tools-production \
  --file deploy.yaml
```

Wait 2-3 minutes for deployment.

4. **Get your public IP:**

```bash
az container show \
  --resource-group pdf-tools-production \
  --name pdf-tools-app \
  --query ipAddress.ip \
  --output tsv
```

Copy this IP address!

✅ **Application Deployed!**

---

# ALTERNATIVE: PART 2B - Deploy Using Azure Portal GUI Only

## Step 6: Create Web App (App Service)

If you prefer using App Service instead of Container Instances:

### Create App Service:

1. In Azure Portal, search for **"App Services"**
2. Click **+ Create**
3. Fill in **Basics**:
   - **Resource Group:** `pdf-tools-production`
   - **Name:** `pdf-tools-api` (must be unique)
   - **Publish:** `Container`
   - **Operating System:** `Linux`
   - **Region:** `East US`
4. Click **Next: Container**
   - **Container type:** Single Container
   - **Image source:** Azure Container Registry
   - **Registry:** `pdftools`
   - **Image:** `pdf-tools`
   - **Tag:** `latest`
   - **Startup command:** `uvicorn main:app --host 0.0.0.0 --port 5000`
5. Click **Review + Create** → **Create**

### Configure Environment Variables:

1. Go to your **Web App** (`pdf-tools-api`)
2. Click **Configuration** in left menu
3. Click **+ New application setting**
4. Add:
   - **Name:** `REDIS_URL`
   - **Value:** (paste your Redis connection string)
5. Click **OK** → **Save**

### Configure Port:

1. Still in **Configuration**
2. Click **General settings** tab
3. **Port:** `5000`
4. Click **Save**

✅ **Web App Deployed!**

### Deploy Celery Worker Separately:

For Celery Worker and Beat, you'll need to use Container Instances (see Step 5) or deploy them as separate App Services with different startup commands.

---

# PART 3: Testing & Verification

## Step 7: Test Your Deployment

### Get Your Application URL:

**For Container Instances:**
```
http://YOUR_IP_ADDRESS:5000
```

**For App Service:**
```
https://pdf-tools-api.azurewebsites.net
```

### Test Endpoints:

1. **Health Check:**
   - Open browser: `http://YOUR_URL/health`
   - Should see: `{"status":"healthy"}`

2. **API Documentation:**
   - Open browser: `http://YOUR_URL/docs`
   - You'll see interactive Swagger UI
   - Test endpoints directly from here!

3. **Root Endpoint:**
   - Open browser: `http://YOUR_URL/`
   - Should see: `{"message":"PDF Tools API","version":"1.0.0"}`

### Test PDF Conversion:

1. Go to `http://YOUR_URL/docs`
2. Click **POST /api/image-to-pdf**
3. Click **Try it out**
4. Upload test images
5. Click **Execute**
6. Download the generated PDF

✅ **Application is Working!**

---

## Step 8: View Logs

### For Container Instances:

1. Go to **Container Instances** in Azure Portal
2. Click on `pdf-tools-app`
3. In left menu, click **Containers**
4. Click on a container name (e.g., `fastapi-server`)
5. Click **Logs** tab
6. View real-time logs

### For App Service:

1. Go to your **Web App**
2. Click **Log stream** in left menu
3. View real-time logs

---

## Monitoring

## Step 9: Set Up Monitoring

### Enable Application Insights:

1. Go to your **Web App** or **Container Instance**
2. Click **Insights** in left menu
3. Click **Turn on Application Insights**
4. Fill in:
   - **Name:** `pdf-tools-insights`
   - **Location:** Same as your app
5. Click **Apply** → **Yes**

### View Metrics:

1. Go to **Application Insights** resource
2. Click **Metrics** in left menu
3. View:
   - Request count
   - Response time
   - Failed requests
   - Server response time

### Create Alert:

1. In Application Insights, click **Alerts**
2. Click **+ Create** → **Alert rule**
3. Configure:
   - **Condition:** Failed requests > 5 in last 5 minutes
   - **Actions:** Email notification
   - **Alert rule name:** `High Error Rate`
4. Click **Create alert rule**

✅ **Monitoring Enabled!**

---

## Troubleshooting

### Common Issues:

#### 1. 502 Bad Gateway

**Symptoms:**
- Can't access the application
- 502 error in browser

**Solutions:**
1. Check if containers are running:
   - Go to Container Instance → Containers
   - Verify all containers show "Running"

2. Check logs for errors:
   - View logs for each container
   - Look for Redis connection errors

3. Verify Redis connection:
   - Ensure REDIS_URL is correct
   - Check Redis firewall allows connections

#### 2. Redis Connection Error

**Symptoms:**
- Logs show: "Connection refused" or "Redis timeout"

**Solutions:**
1. Verify Redis URL format:
   ```
   rediss://:PASSWORD@NAME.redis.cache.windows.net:6380/0
   ```

2. Enable Redis firewall:
   - Go to Redis Cache → **Networking**
   - Under **Public network access**, select **All networks**
   - Click **Save**

3. Check non-SSL port is enabled:
   - Go to Redis Cache → **Advanced settings**
   - Ensure **Non-SSL port (6379)** is **Enabled**

#### 3. Container Won't Start

**Symptoms:**
- Container shows "Terminated" or "Failed"

**Solutions:**
1. Check container logs:
   - Look for error messages
   - Common: Missing dependencies, wrong Python version

2. Verify Docker image exists:
   - Go to Container Registry → Repositories
   - Ensure `pdf-tools:latest` is present

3. Check resource limits:
   - Container might need more CPU/memory
   - Increase resources in YAML file

#### 4. PDF Processing Fails

**Symptoms:**
- Upload succeeds but PDF not generated
- Celery tasks show errors

**Solutions:**
1. Check Celery Worker logs:
   - Go to Container Instance → celery-worker → Logs
   - Look for task errors

2. Verify Celery Worker is running:
   - Should see: "celery@HOSTNAME ready"

3. Check file permissions:
   - Ensure uploads/temp directories exist
   - Verify write permissions

#### 5. Slow Performance

**Solutions:**
1. Increase container resources:
   - Edit YAML file
   - Increase CPU: 2.0, Memory: 4.0 GB
   - Redeploy

2. Scale Celery workers:
   - Increase `--concurrency=4` in worker command
   - Or add more worker containers

3. Use Premium Redis:
   - Upgrade from Basic C0 to Standard C1
   - Better performance and reliability

---

## Scaling

### Scale Container Resources:

1. Edit `deploy.yaml`:
   ```yaml
   resources:
     requests:
       cpu: 2.0  # Increase from 1.0
       memoryInGB: 4.0  # Increase from 2.0
   ```

2. Redeploy:
   ```bash
   az container create --resource-group pdf-tools-production --file deploy.yaml
   ```

### Scale Celery Workers:

1. Add more worker containers in YAML:
   ```yaml
   - name: celery-worker-2
     properties:
       image: pdftools.azurecr.io/pdf-tools:latest
       command:
         - celery
         - -A
         - celery_app
         - worker
         - --loglevel=info
         - --concurrency=2
   ```

2. Or increase concurrency:
   ```yaml
   --concurrency=4  # Process 4 tasks simultaneously
   ```

### Upgrade Redis:

1. Go to Redis Cache
2. Click **Scale** in left menu
3. Select **Standard C1** (1 GB) - $75/month
4. Click **Scale**
5. Wait 10-15 minutes for scaling

---

## Cost Breakdown

### Monthly Costs (East US region):

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| **Container Instances** | 2.5 vCPU, 5 GB RAM | ~$100 |
| **Azure Container Registry** | Basic | $5 |
| **Azure Cache for Redis** | Basic C0 (250 MB) | $16 |
| **Application Insights** | Basic (5 GB free) | $0-$10 |
| **Storage** | 10 GB | $0.50 |
| **Bandwidth** | 5 GB outbound | $0.43 |
| **TOTAL** | | **~$122/month** |

### Cost Optimization Tips:

1. **Use Spot Instances:** Can save 60-90%
2. **Auto-shutdown:** Stop containers when not in use
3. **Use Azure Reservations:** 30% discount for 1-year commit
4. **Monitor usage:** Delete unused resources

---

## Security Best Practices

### 1. Use HTTPS:

For Container Instances, use Azure Application Gateway or Azure Front Door to add HTTPS.

**Quick HTTPS with Cloudflare (Free):**
1. Sign up at cloudflare.com
2. Add your domain
3. Point A record to your Container IP
4. Enable **Flexible SSL** in Cloudflare
5. Force HTTPS redirects

### 2. Secure Redis:

1. Enable **SSL only mode:**
   - Redis Cache → **Advanced settings**
   - Disable non-SSL port
   - Use `rediss://` in connection string

2. Rotate Redis keys:
   - Redis Cache → **Access keys**
   - Click **Regenerate** every 90 days

### 3. Network Security:

1. Limit Redis access:
   - Redis Cache → **Networking**
   - Add firewall rules for specific IPs only

2. Use Virtual Network:
   - Deploy containers in VNet
   - Keep Redis private

### 4. Secrets Management:

1. Use Azure Key Vault:
   - Store Redis connection strings
   - Store ACR passwords
   - Reference secrets in container config

---

## Next Steps

### After Successful Deployment:

1. ✅ **Set up custom domain:**
   - Purchase domain from Azure or external provider
   - Add DNS A record pointing to your IP
   - Configure SSL certificate

2. ✅ **Enable CDN:**
   - Use Azure CDN for faster global delivery
   - Cache static content

3. ✅ **Set up CI/CD:**
   - Connect GitHub to Azure Container Registry
   - Auto-deploy on git push

4. ✅ **Configure backup:**
   - Backup Redis data regularly
   - Store generated PDFs in Azure Blob Storage

5. ✅ **Load testing:**
   - Test with 100+ concurrent users
   - Adjust resources based on results

6. ✅ **Rate limiting:**
   - Add rate limiting to prevent abuse
   - Use Azure API Management

---

## Support & Resources

### Azure Documentation:
- Container Instances: https://learn.microsoft.com/en-us/azure/container-instances/
- App Service: https://learn.microsoft.com/en-us/azure/app-service/
- Redis Cache: https://learn.microsoft.com/en-us/azure/azure-cache-for-redis/

### Community Support:
- Azure Forums: https://learn.microsoft.com/en-us/answers/products/azure
- Stack Overflow: https://stackoverflow.com/questions/tagged/azure

### Get Help:
- Azure Support Portal: https://portal.azure.com → **Help + support**
- Live Chat: Available in Azure Portal

---

## Complete Checklist

Use this checklist to ensure everything is configured:

### ✅ Resources Created:
- [ ] Resource Group (`pdf-tools-production`)
- [ ] Container Registry (`pdftools`)
- [ ] Redis Cache (`pdf-tools-redis`)
- [ ] Container Instance OR App Service

### ✅ Configuration:
- [ ] Docker image built and pushed
- [ ] REDIS_URL configured correctly
- [ ] All 3 containers running (FastAPI, Worker, Beat)
- [ ] Port 5000 exposed and accessible

### ✅ Testing:
- [ ] `/health` endpoint returns healthy
- [ ] `/docs` shows Swagger UI
- [ ] Image to PDF conversion works
- [ ] PDF merge works
- [ ] Logs show no errors

### ✅ Monitoring:
- [ ] Application Insights enabled
- [ ] Alerts configured
- [ ] Log monitoring set up

### ✅ Security:
- [ ] HTTPS enabled (or planned)
- [ ] Redis secured with password
- [ ] Firewall rules configured
- [ ] Secrets not exposed in logs

---

## Congratulations! 🎉

Your PDF Tools API is now running on Azure!

**Your application URL:**
- Container Instances: `http://YOUR_IP:5000`
- App Service: `https://pdf-tools-api.azurewebsites.net`

**Next:** Share your API documentation (`/docs`) with your users!

---

**Questions or Issues?**
- Check the Troubleshooting section above
- Review Azure Portal logs
- Contact Azure Support

**Happy PDF Processing! 📄✨**
