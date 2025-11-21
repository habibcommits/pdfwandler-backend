# Azure Web App Deployment Guide (GUI Only - No SSH)

**Complete Azure Portal GUI Steps for PDF Tools API**  
**Last Updated:** November 21, 2025

---

## Overview

Deploy your PDF Tools API to Azure using only the Azure Portal (no command line required).

- ✅ Pure Python PDF tools (PyPDF2 - no system dependencies)
- ✅ Azure Redis Cache for task processing
- ✅ FastAPI with automatic startup
- ✅ All configuration via GUI

---

## Step 1: Create Azure Resource Group (GUI)

### In Azure Portal:

1. Go to **Home** → click **Resource groups**
2. Click **+ Create**
3. Fill in:
   - **Resource Group Name:** `pdf-tools-rg`
   - **Region:** `East US` (or your preferred region)
4. Click **Review + Create** → **Create**
5. Wait for deployment to complete

---

## Step 2: Create Azure App Service Plan (GUI)

### In Azure Portal:

1. Go to **Home** → **All services** → search **App Service plans**
2. Click **+ Create**
3. Fill in:
   - **Resource Group:** `pdf-tools-rg` (select from dropdown)
   - **Name:** `pdf-tools-plan`
   - **Operating System:** `Linux`
   - **Region:** `East US` (same as resource group)
   - **Pricing Tier:** Click **Change size**
     - Select **Dev / Test** tab
     - Choose **B1** (Basic, $13/month) for testing
     - OR **S1** (Standard, $70/month) for production
     - Click **Apply**
4. Click **Review + Create** → **Create**
5. Wait for deployment

---

## Step 3: Create Azure Web App (GUI)

### In Azure Portal:

1. Go to **Home** → **All services** → search **App Services**
2. Click **+ Create**
3. Fill in **Basics** tab:
   - **Resource Group:** `pdf-tools-rg`
   - **Name:** `pdfbackendpython` (must be unique)
   - **Publish:** `Code`
   - **Runtime Stack:** `Python 3.11`
   - **Operating System:** `Linux`
   - **Region:** `East US`
   - **App Service Plan:** `pdf-tools-plan` (or create new)
4. Click **Next: Deployment** tab:
   - **Source:** `GitHub` or `Local Git` (see deployment options below)
5. Click **Review + Create** → **Create**
6. Wait for deployment (2-5 minutes)

---

## Step 4: Create Azure Redis Cache (GUI)

### In Azure Portal:

1. Go to **Home** → **All services** → search **Azure Cache for Redis**
2. Click **+ Create**
3. Fill in:
   - **Resource Group:** `pdf-tools-rg`
   - **Resource Name:** `pythonbackendpdf`
   - **Location:** `East US` (same region)
   - **Pricing Tier:** Click **Change size**
     - Select **Basic** tier
     - Choose **250 MB (C0)** - $16/month
     - Click **Select**
4. Click **Next: Networking** → keep defaults
5. Click **Review + Create** → **Create**
6. Wait for deployment (3-5 minutes)

---

## Step 5: Get Redis Connection String (GUI)

### In Azure Portal:

1. Go to the Redis Cache you created (`pythonbackendpdf`)
2. In the left menu, click **Access keys**
3. You'll see:
   - **Primary connection string (StackExchange.Redis):** Copy this
   - **Primary key:** Also copy (for backup)
4. **Store these securely** - you'll need them next

---

## Step 6: Configure Environment Variables (GUI)

### In Azure Portal:

1. Go to your **Web App** (`pdfbackendpython`)
2. In left menu, click **Configuration**
3. Click **+ New application setting**
4. Add this setting:
   - **Name:** `REDIS_URL`
   - **Value:** Paste your Redis connection string from Step 5
     - If your string is: `rediss://default:ABC123@pythonbackendpdf.redis.cache.windows.net:6380`
     - Use: `rediss://default:ABC123@pythonbackendpdf.redis.cache.windows.net:6380/0`
5. Click **OK**
6. Add another setting:
   - **Name:** `PYTHONPATH`
   - **Value:** `/home/site/wwwroot`
7. Click **OK**
8. Click **Save** at the top
9. Click **Continue** if prompted to restart app

---

## Step 7: Configure Startup Command (GUI)

### In Azure Portal:

1. Go to your **Web App** (`pdfbackendpython`)
2. In left menu, click **Configuration**
3. Under **General settings** tab, find **Startup Command**
4. Enter this command:
   ```
   gunicorn -k uvicorn.workers.UvicornWorker main:app --workers 2 --timeout 300 --bind 0.0.0.0:8000
   ```
5. Click **Save** at the top
6. The app will restart automatically

---

## Step 8: Deploy Code to Azure Web App (GUI)

### Choose ONE deployment method:

#### **Option A: GitHub Deployment (Automated CI/CD)**

1. Go to your **Web App** (`pdfbackendpython`)
2. In left menu, click **Deployment** → **Deployment Center**
3. Select **Source:** `GitHub`
4. Click **Authorize** and sign in to GitHub
5. Select:
   - **Organization:** Your GitHub account
   - **Repository:** Your PDF Tools repo
   - **Branch:** `main`
6. Click **Save**
7. Azure will automatically deploy when you push to `main`

#### **Option B: Local Git (Manual Push)**

1. Go to your **Web App** (`pdfbackendpython`)
2. In left menu, click **Deployment** → **Deployment Center**
3. Select **Source:** `Local Git`
4. Click **Save**
5. Under **Local Git Deployment**, copy the **Git Clone URL**
   - Looks like: `https://yourusername@pdfbackendpython.scm.azurewebsites.net/pdfbackendpython.git`
6. In your local terminal:
   ```bash
   git remote add azure <paste-url-here>
   git push azure main
   ```

#### **Option C: Zip Deploy (One-Time Upload)**

1. On your computer, create a ZIP file of your project:
   - **Include:** All Python files, requirements.txt, etc.
   - **Exclude:** .git, __pycache__, .pyc files, node_modules

2. Go to your **Web App** (`pdfbackendpython`)
3. In left menu, click **Deployment** → **Deployment Center**
4. Click the **Advanced** dropdown menu
5. Select **Zip Deploy**
6. Drag your ZIP file into the box or click to browse
7. Click **Deploy**
8. Wait for deployment to complete

---

## Step 9: Allow Redis Access (GUI)

### In Azure Portal:

1. Go to your **Redis Cache** (`pythonbackendpdf`)
2. In left menu, click **Networking**
3. Under **Firewall rules**, click **+ Add a firewall rule**
4. Fill in:
   - **Rule Name:** `AllowAppService`
   - **Start IP:** `0.0.0.0`
   - **End IP:** `255.255.255.255`
5. Click **Save**

**Alternative (Recommended):**
1. In **Networking**, scroll to **Resource access**
2. Toggle **"Allow access from Azure Services"** to **ON**
3. Click **Save**

---

## Step 10: Enable HTTPS Only (GUI)

### In Azure Portal:

1. Go to your **Web App** (`pdfbackendpython`)
2. In left menu, click **Configuration**
3. Under **General settings**, find **HTTPS only**
4. Toggle to **On**
5. Click **Save**

---

## Step 11: Verify Deployment (GUI)

### In Azure Portal:

1. Go to your **Web App** (`pdfbackendpython`)
2. Click **Overview** tab
3. Find the **URL** (looks like: `https://pdfbackendpython.azurewebsites.net`)
4. Click the URL to open your app
5. You should see: `{"message":"PDF Tools API is running"}`

### Test API Health:
- Visit: `https://pdfbackendpython.azurewebsites.net/health`
- Should see: `{"status":"healthy"}`

### View API Documentation:
- Visit: `https://pdfbackendpython.azurewebsites.net/docs`
- Interactive Swagger UI (test endpoints here)

---

## Step 12: Monitor App & Logs (GUI)

### View Real-Time Logs:

1. Go to your **Web App** (`pdfbackendpython`)
2. In left menu, click **Log stream**
3. You'll see live logs as requests come in

### View Metrics:

1. Go to your **Web App** (`pdfbackendpython`)
2. Click **Metrics** in left menu
3. View:
   - **CPU Percentage**
   - **Memory Percentage**
   - **Http 5xx errors**
   - **Http 4xx errors**

### View Deployment Status:

1. Go to your **Web App** (`pdfbackendpython`)
2. Click **Deployment** → **Deployment Center**
3. See your deployment history and status

---

## Step 13: Troubleshooting (GUI)

### Problem: 502 Bad Gateway

1. Go to **Web App** → **Log stream**
2. Look for errors in the logs
3. Common fixes:
   - Verify `REDIS_URL` is set correctly (Configuration tab)
   - Check Redis firewall rules (Redis Cache → Networking)
   - Restart app (Overview → Restart button)

### Problem: Redis Connection Timeout

1. Go to **Redis Cache** (`pythonbackendpdf`)
2. Click **Networking**
3. Check if "Allow access from Azure Services" is **ON**
4. Or manually add firewall rule (see Step 9)

### Problem: App Not Starting

1. Go to **Web App** → **Configuration**
2. Verify **Startup Command** is correct
3. Check **Environment variables** (REDIS_URL, PYTHONPATH)
4. Click **Restart** button in Overview tab

### Problem: Deployment Failed

1. Go to **Deployment** → **Deployment Center**
2. Click on the failed deployment
3. View error logs
4. Click **Redeploy** to try again

---

## Step 14: Scale Up (If Needed) (GUI)

### Increase Performance:

1. Go to your **App Service Plan** (`pdf-tools-plan`)
2. In left menu, click **Scale up (App Service plan)**
3. Select a larger tier:
   - **S1** (1 core) - $70/month
   - **S2** (2 cores) - $140/month
   - **S3** (4 cores) - $280/month
4. Click **Apply**
5. App will restart during scaling

### Auto-Scale (Advanced):

1. Go to **App Service Plan** (`pdf-tools-plan`)
2. In left menu, click **Scale out (App Service plan)**
3. Click **+ Create scale rule**
4. Set rules for automatic scaling

---

## Step 15: Monitor & Alerts (GUI)

### Set Up Email Alert:

1. Go to your **Web App** (`pdfbackendpython`)
2. In left menu, click **Alerts**
3. Click **+ New alert rule**
4. Condition: `HTTP Server Errors (5xx) > 5 in last 1 hour`
5. Click **Add action groups**
   - Create new: Enter email address
6. Name: `PDF API Error Alert`
7. Click **Create alert rule**

---

## Complete Checklist

✅ **Resources Created:**
- [ ] Resource Group (`pdf-tools-rg`)
- [ ] App Service Plan (`pdf-tools-plan`)
- [ ] Web App (`pdfbackendpython`)
- [ ] Redis Cache (`pythonbackendpdf`)

✅ **Configuration:**
- [ ] `REDIS_URL` environment variable set
- [ ] `PYTHONPATH` environment variable set
- [ ] Startup command configured
- [ ] HTTPS Only enabled

✅ **Deployment:**
- [ ] Code deployed (GitHub, Local Git, or ZIP)
- [ ] Redis firewall allows App Service access
- [ ] App is running (check Overview URL)

✅ **Testing:**
- [ ] Health check endpoint works: `/health`
- [ ] API docs accessible: `/docs`
- [ ] No errors in Log stream

✅ **Security:**
- [ ] HTTPS only enabled
- [ ] REDIS_URL stored as secure setting (not visible)
- [ ] Firewall rules configured for Redis

---

## Cost Breakdown (Monthly)

| Service | Tier | Cost |
|---------|------|------|
| App Service | B1 (Testing) | $13 |
| App Service | S1 (Production) | $70 |
| Redis Cache | Basic C0 | $16 |
| **Total (S1 + Redis)** | | **$86** |

---

## Next Steps

1. **Test PDF endpoints** in the Swagger UI (`/docs`)
2. **Monitor performance** in Metrics tab
3. **Set up alerts** for errors
4. **Configure custom domain** (optional)
5. **Enable CDN** for faster delivery (optional)

---

## Support Links

- **Azure Portal:** https://portal.azure.com
- **Web App Documentation:** https://docs.microsoft.com/en-us/azure/app-service/
- **Redis Cache Help:** https://docs.microsoft.com/en-us/azure/azure-cache-for-redis/
- **FastAPI Docs:** https://fastapi.tiangolo.com/

---

**That's it! Your PDF Tools API is now deployed on Azure using only the GUI.** 🎉
