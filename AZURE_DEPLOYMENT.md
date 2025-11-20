# Azure Web App Deployment Guide for PDF Tools API

## Quick Deployment Steps

### 1. Prerequisites
- Azure subscription
- Azure CLI installed or use Azure Portal
- Git repository

### 2. Create Azure Web App

#### Using Azure Portal:
1. Go to Azure Portal (portal.azure.com)
2. Create a new **Web App**
3. **Configuration:**
   - **Runtime Stack:** Python 3.11
   - **Operating System:** Linux
   - **Region:** Choose nearest to your users
   - **Plan:** Basic B1 or higher (recommended: Standard S1 for production)

#### Using Azure CLI:
```bash
# Login to Azure
az login

# Create resource group
az group create --name pdf-tools-rg --location eastus

# Create App Service plan (Standard S1 recommended for production)
az appservice plan create \
    --name pdf-tools-plan \
    --resource-group pdf-tools-rg \
    --sku S1 \
    --is-linux

# Create web app
az webapp create \
    --resource-group pdf-tools-rg \
    --plan pdf-tools-plan \
    --name your-pdf-tools-app \
    --runtime "PYTHON:3.11"
```

### 3. Install System Dependencies (CRITICAL)

**Azure Web Apps don't include Ghostscript or Redis by default.** You must install them.

#### Option A: Using App Service SSH (Recommended for Testing)
1. In Azure Portal, go to your Web App → Development Tools → SSH
2. Connect to the SSH console
3. Run the installation script:
```bash
cd /home/site/wwwroot
chmod +x .azure/install-dependencies.sh
./.azure/install-dependencies.sh
```

#### Option B: Using Custom Startup Command (Permanent Solution)
Create a custom Docker container or use Azure Container Apps instead. Here's a Dockerfile for reference:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ghostscript \
    redis-server \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make startup script executable
RUN chmod +x startup.sh

# Expose port
EXPOSE 8000

# Run startup script
CMD ["./startup.sh"]
```

#### Option C: Use Azure Redis Cache (Recommended for Production)

Instead of running Redis locally, use Azure Cache for Redis:

1. Create Azure Redis Cache:
```bash
az redis create \
    --resource-group pdf-tools-rg \
    --name your-redis-cache \
    --location eastus \
    --sku Basic \
    --vm-size c0
```

2. Get connection string:
```bash
az redis list-keys \
    --resource-group pdf-tools-rg \
    --name your-redis-cache
```

3. Set environment variables in Azure Web App:
```bash
az webapp config appsettings set \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app \
    --settings \
        CELERY_BROKER_URL="redis://your-redis-cache.redis.cache.windows.net:6380/0?ssl=true&password=YOUR_PASSWORD" \
        CELERY_RESULT_BACKEND="redis://your-redis-cache.redis.cache.windows.net:6380/0?ssl=true&password=YOUR_PASSWORD"
```

4. Modify startup.sh to skip Redis installation:
```bash
# Comment out Redis server start if using Azure Redis Cache
# redis-server --daemonize yes ...
```

### 4. Configure Startup Command

In Azure Portal → Configuration → General Settings → Startup Command:
```bash
bash startup.sh
```

Or using Azure CLI:
```bash
az webapp config set \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app \
    --startup-file "bash startup.sh"
```

### 5. Deploy Your Code

#### Option A: Git Deployment (Recommended)
```bash
# Configure Git deployment
az webapp deployment source config \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app \
    --repo-url https://github.com/yourusername/your-repo \
    --branch main \
    --manual-integration

# Or use local Git
az webapp deployment source config-local-git \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app

# Push your code
git remote add azure <git-url-from-above-command>
git push azure main
```

#### Option B: ZIP Deployment
```bash
# Create ZIP of your project (exclude .git, venv, etc.)
zip -r pdf-tools.zip . -x "*.git*" "*venv*" "*__pycache__*" "*.pyc"

# Deploy ZIP
az webapp deploy \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app \
    --src-path pdf-tools.zip \
    --type zip
```

### 6. Environment Variables (Optional Customization)

```bash
az webapp config appsettings set \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app \
    --settings \
        PORT="8000" \
        WORKERS="4"
```

### 7. Verify Deployment

Check if all services are running:

1. **View Logs:**
```bash
az webapp log tail \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app
```

2. **Test API:**
```bash
# Health check
curl https://your-pdf-tools-app.azurewebsites.net/health

# API info
curl https://your-pdf-tools-app.azurewebsites.net/
```

### 8. Production Recommendations

#### Use Azure Container Apps or AKS for Complex Deployments

For production with full control over dependencies:

```bash
# Create container registry
az acr create \
    --resource-group pdf-tools-rg \
    --name yourregistry \
    --sku Basic

# Build and push image
az acr build \
    --registry yourregistry \
    --image pdf-tools:latest \
    .

# Deploy to Container Apps
az containerapp create \
    --name pdf-tools-app \
    --resource-group pdf-tools-rg \
    --environment my-env \
    --image yourregistry.azurecr.io/pdf-tools:latest \
    --target-port 8000 \
    --ingress external \
    --cpu 2.0 --memory 4.0Gi
```

#### Use Azure Redis Cache (Not Local Redis)

For production, always use Azure Redis Cache:
- Automatic backups
- High availability
- Better performance
- Managed service (no maintenance)

Cost: ~$16/month for Basic tier

#### Scale Configuration

For better performance with large PDFs:

```bash
# Scale to Standard S2 (2 cores, 3.5 GB RAM)
az appservice plan update \
    --name pdf-tools-plan \
    --resource-group pdf-tools-rg \
    --sku S2

# Enable autoscaling
az monitor autoscale create \
    --resource-group pdf-tools-rg \
    --resource your-pdf-tools-app \
    --min-count 1 \
    --max-count 5 \
    --count 2
```

### 9. Troubleshooting

#### Ghostscript not found
```bash
# SSH into the app
az webapp ssh --resource-group pdf-tools-rg --name your-pdf-tools-app

# Install Ghostscript manually
apt-get update && apt-get install -y ghostscript

# Verify
gs --version
```

#### Redis connection failed
- Use Azure Redis Cache instead of local Redis
- Check firewall rules
- Verify connection string

#### Celery not starting
- Check logs: `az webapp log tail`
- Verify Redis is accessible
- Check file permissions on /tmp/celery

#### App crashes on startup
- Check startup logs
- Verify all system dependencies are installed
- Check that startup.sh is executable

## Performance Benchmarks

With Standard S1 instance + Ghostscript:
- **Image to PDF:** ~2-3 seconds for 10 images
- **Merge PDF:** ~1-2 seconds for 5 PDFs (50MB total)
- **Compress PDF:** ~3-5 seconds for 100MB PDF file

With Standard S2 instance:
- **Compress PDF:** ~2-3 seconds for 100MB PDF file (faster CPU)

## Cost Estimation (Azure)

### App Service:
- **Basic B1:** ~$13/month - Development/testing
- **Standard S1:** ~$70/month - Production (light)
- **Standard S2:** ~$140/month - Production (medium load)
- **Premium P1V2:** ~$150/month - Production (heavy load)

### Azure Redis Cache:
- **Basic C0:** ~$16/month - 250MB cache
- **Standard C1:** ~$55/month - 1GB cache with replication

### Total Recommended for Production:
- S1 App Service + Basic Redis = ~$86/month
- S2 App Service + Standard Redis = ~$195/month

## Security Best Practices

1. **Enable HTTPS only:**
```bash
az webapp update \
    --https-only true \
    --name your-pdf-tools-app \
    --resource-group pdf-tools-rg
```

2. **Enable Managed Identity** (for secure resource access):
```bash
az webapp identity assign \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app
```

3. **Configure IP restrictions** (optional):
```bash
az webapp config access-restriction add \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app \
    --rule-name AllowOffice \
    --action Allow \
    --ip-address 1.2.3.4/32 \
    --priority 100
```

4. **Enable Application Insights** (monitoring):
```bash
az monitor app-insights component create \
    --app your-pdf-tools-insights \
    --location eastus \
    --resource-group pdf-tools-rg

# Link to Web App
az webapp config appsettings set \
    --resource-group pdf-tools-rg \
    --name your-pdf-tools-app \
    --settings APPINSIGHTS_INSTRUMENTATIONKEY=<key>
```

## Alternative: Deploy to Azure Container Apps (Recommended)

Container Apps give you full control and easier dependency management:

1. **Create environment:**
```bash
az containerapp env create \
    --name pdf-tools-env \
    --resource-group pdf-tools-rg \
    --location eastus
```

2. **Build and deploy:**
```bash
# Build container
docker build -t pdf-tools:latest .

# Tag for ACR
docker tag pdf-tools:latest yourregistry.azurecr.io/pdf-tools:latest

# Push to ACR
docker push yourregistry.azurecr.io/pdf-tools:latest

# Deploy
az containerapp create \
    --name pdf-tools-app \
    --resource-group pdf-tools-rg \
    --environment pdf-tools-env \
    --image yourregistry.azurecr.io/pdf-tools:latest \
    --target-port 8000 \
    --ingress external \
    --cpu 2.0 \
    --memory 4.0Gi \
    --min-replicas 1 \
    --max-replicas 5
```

This approach is more reliable and gives you better control over system dependencies!
