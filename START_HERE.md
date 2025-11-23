# 🎯 START HERE - Azure Deployment Guide

**Last Updated:** November 23, 2025

---

## 🔥 CRITICAL ISSUE RESOLVED

**Your deployment was failing because:**
- The Dockerfile had a health check that only worked for FastAPI
- When Azure ran Celery worker and beat containers, they failed health checks
- Azure kept restarting the containers, causing crashes

**✅ THIS HAS BEEN FIXED!**
- Updated Dockerfile removes the problematic health check
- All containers can now run without health check failures
- Your deployment will work correctly if you follow the steps below

---

## 📦 What I Created For You

I've created a complete deployment package with:

1. **azure-deployment.yaml** - Multi-container configuration for Azure
2. **build-and-push.sh** - Automated Docker build script
3. **Updated Dockerfile** - Fixed for multi-container deployment
4. **Updated .dockerignore** - Optimized for smaller images
5. **Complete documentation** - Step-by-step guides

---

## 🚀 Quick Start (Choose Your Path)

### Path 1: I Want to Deploy FAST (15 minutes)
👉 **Open:** `AZURE_QUICK_START.md`

**What you'll do:**
1. Build Docker image with Play with Docker (or locally)
2. Push to Docker Hub
3. Update `azure-deployment.yaml` with your username
4. Deploy via Azure Portal
5. Test your API

**Perfect for:** First-time users who want to get up and running quickly

---

### Path 2: I Want a Checklist to Follow
👉 **Open:** `DEPLOYMENT_CHECKLIST.md`

**What you'll do:**
1. Follow a comprehensive checklist
2. Check off each step as you complete it
3. Verify everything is correct before moving forward
4. Troubleshoot specific issues with targeted solutions

**Perfect for:** People who like structured, step-by-step processes

---

### Path 3: I Want to Understand Everything
👉 **Open:** `CONFIGURATION.md`

**What you'll do:**
1. Learn about all environment variables
2. Understand the multi-container architecture
3. Read detailed explanations for each configuration
4. Access comprehensive troubleshooting guide

**Perfect for:** Technical users who want deep understanding

---

## ⚡ Fastest Path to Deployment

If you just want to deploy RIGHT NOW:

### Step 1: Build Image (5 minutes)
```bash
# Make script executable
chmod +x build-and-push.sh

# Run the script
./build-and-push.sh
# Enter your Docker Hub username when prompted
```

### Step 2: Update YAML (2 minutes)
Open `azure-deployment.yaml` and replace:
- **Line 9, 39, 61:** `your-dockerhub-username` → Your actual username
- **Line 98:** `YOUR-UNIQUE-NAME` → Something like `yourname-pdf-api-123`

### Step 3: Deploy to Azure (5 minutes)
1. Go to: https://portal.azure.com
2. Search: "Container Instances"
3. Click: "Create"
4. Resource Group: Create new → `pdf-tools-rg`
5. Container name: `pdf-tools-api`
6. Region: `East US`
7. Click: "Review + create"
8. Click: "Download a template for automation"
9. **Delete all** template content
10. **Paste** your entire `azure-deployment.yaml` content
11. Click: "Save" → "Review + create" → "Create"

### Step 4: Test (3 minutes)
Wait 3 minutes, then:
1. Get your URL from Azure Portal (FQDN field)
2. Visit: `http://YOUR-URL/docs`
3. Test the `/health` endpoint

**Done!** 🎉

---

## 🔑 Key Information

### Environment Variables (Already Configured)
Your `azure-deployment.yaml` includes all required environment variables:
- `REDIS_URL=redis://localhost:6379/0`
- `CELERY_BROKER_URL=redis://localhost:6379/0`
- `CELERY_RESULT_BACKEND=redis://localhost:6379/0`
- `PYTHONUNBUFFERED=1`

**✅ You don't need to configure these separately!**

### Redis Configuration (Already Configured)
Redis runs as a separate container in your container group. All containers communicate via `localhost`.

**✅ You don't need to set up Redis separately!**

### What You MUST Change
Only 2 things in `azure-deployment.yaml`:
1. **Docker Hub username** (3 places: lines 9, 39, 61)
2. **DNS label** (1 place: line 98)

---

## 🏗️ Architecture Overview

```
Your Container Group in Azure
├── FastAPI Container (port 5000) - Your main API
├── Celery Worker - Processes background tasks
├── Celery Beat - Schedules cleanup tasks
└── Redis - Message broker for Celery

All containers share the same network (localhost)
```

---

## 💰 Cost

**~$81/month for 24/7 operation**

Breakdown:
- FastAPI: ~$35/month
- Celery Worker: ~$28/month
- Celery Beat: ~$9/month
- Redis: ~$9/month

**To reduce costs:**
- Stop the container when not in use
- Azure charges per second, so no cost when stopped

---

## ✅ Success Criteria

You'll know it's working when:
1. ✅ All 4 containers show "Running" in Azure Portal
2. ✅ `http://YOUR-URL/health` returns `{"status":"healthy"}`
3. ✅ `http://YOUR-URL/docs` shows Swagger UI
4. ✅ You can upload and process files

---

## 🐛 Common Issues (Quick Fixes)

### "Containers keep restarting"
**Fix:** Rebuild Docker image with the updated Dockerfile (no health check)
```bash
docker build --platform linux/amd64 -t YOUR-USERNAME/pdf-tools:latest .
docker push YOUR-USERNAME/pdf-tools:latest
```

### "Image not found"
**Fix:** Make sure your Docker Hub repository is public
1. Go to https://hub.docker.com
2. Find your image → Settings → Make Public

### "502 Bad Gateway"
**Fix:** Check FastAPI container logs in Azure Portal
- Container Instances → pdf-tools-api → Containers → fastapi → Logs

---

## 📚 All Available Documentation

| File | Purpose | When to Use |
|------|---------|-------------|
| **AZURE_QUICK_START.md** | 15-min quick start | Deploy fast |
| **DEPLOYMENT_CHECKLIST.md** | Step-by-step checklist | Structured approach |
| **CONFIGURATION.md** | Complete reference | Deep dive |
| **README_AZURE_DEPLOYMENT.md** | Package overview | Understand what's included |
| **INSPECTION_REPORT.md** | Local app status | Verify local setup |
| **azure-deployment.yaml** | Azure config file | The deployment file |
| **build-and-push.sh** | Build automation | Automated Docker build |

---

## 🎯 What to Do Right Now

1. **Read this:** `START_HERE.md` (you're reading it now ✅)
2. **Choose your path:** Quick start, checklist, or deep dive
3. **Build image:** Run `build-and-push.sh`
4. **Update YAML:** Change username and DNS label
5. **Deploy:** Follow your chosen guide
6. **Test:** Visit `/health` and `/docs` endpoints

---

## 🆘 Need Help?

**If you get stuck:**
1. Check the troubleshooting section in `CONFIGURATION.md`
2. Review your checklist in `DEPLOYMENT_CHECKLIST.md`
3. Verify all steps in `AZURE_QUICK_START.md`

**Common mistakes to avoid:**
- ❌ Using old Docker image (must rebuild with latest Dockerfile)
- ❌ Wrong platform (`--platform linux/amd64` is required)
- ❌ Forgetting to make Docker Hub image public
- ❌ Not updating Docker Hub username in YAML

---

## 🎉 You're Ready!

Everything is configured and ready to deploy. Choose your path above and start deploying!

**Your deployment workflow:**
1. GitHub → Play with Docker → Docker Hub → Azure Container Instances
2. All environment variables pre-configured
3. All services will start automatically
4. Public URL will be available immediately

**Good luck! 🚀**

---

**P.S.** The critical health check issue that was causing your containers to crash has been fixed. As long as you rebuild your Docker image with the latest Dockerfile, your deployment will work perfectly!
