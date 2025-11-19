# Docker Deployment Guide - Microsoft Azure

Complete guide for deploying PDF Tools API to Microsoft Azure using Docker containers.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure Services Setup](#azure-services-setup)
3. [Build and Push Docker Image](#build-and-push-docker-image)
4. [Deploy to Azure Container Instances](#deploy-to-azure-container-instances)
5. [Deploy to Azure App Service](#deploy-to-azure-app-service)
6. [Monitoring and Logs](#monitoring-and-logs)
7. [Verification](#verification)

---

## Prerequisites

- Azure account with active subscription
- Azure CLI installed: `az --version`
- Docker installed locally: `docker --version`
- Git repository with your code

### Install Azure CLI

```bash
# macOS
brew install azure-cli

# Windows (PowerShell)
winget install -e --id Microsoft.AzureCLI

# Linux
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

---

## Azure Services Setup

### 1. Login to Azure

```bash
az login
az account list --output table
az account set --subscription "<YOUR_SUBSCRIPTION_ID>"
```

### 2. Create Resource Group

```bash
# Set variables
RESOURCE_GROUP="pdf-tools-rg"
LOCATION="westeurope"  # or your preferred location

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION
```

### 3. Create Azure Container Registry (ACR)

```bash
ACR_NAME="pdftoolsacr"  # must be globally unique, lowercase alphanumeric only

# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Get ACR credentials
az acr credential show \
  --name $ACR_NAME \
  --resource-group $RESOURCE_GROUP
```

### 4. Create Azure Cache for Redis

```bash
REDIS_NAME="pdf-tools-redis"  # must be globally unique

# Create Redis instance
az redis create \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --location $LOCATION \
  --sku Basic \
  --vm-size c0

# Get Redis connection details
az redis list-keys \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME

# Get Redis hostname
REDIS_HOST=$(az redis show \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --query hostName -o tsv)

# Get Redis primary key
REDIS_KEY=$(az redis list-keys \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --query primaryKey -o tsv)

echo "Redis URL: redis://:$REDIS_KEY@$REDIS_HOST:6380/0?ssl=True"
```

---

## Build and Push Docker Image

### 1. Build Docker Image Locally

```bash
# Build the image
docker build -t pdf-tools-api:latest .

# Test locally with docker-compose
docker-compose up -d

# Verify it works
curl http://localhost:8000/health

# Stop local test
docker-compose down
```

### 2. Push to Azure Container Registry

```bash
# Login to ACR
az acr login --name $ACR_NAME

# Tag the image
docker tag pdf-tools-api:latest $ACR_NAME.azurecr.io/pdf-tools-api:latest

# Push to ACR
docker push $ACR_NAME.azurecr.io/pdf-tools-api:latest

# Verify image in ACR
az acr repository list --name $ACR_NAME --output table
```

---

## Option 1: Deploy to Azure Container Instances (ACI)

Simple deployment for moderate traffic.

### Deploy API Container

```bash
# Set environment variables
CELERY_BROKER_URL="redis://:$REDIS_KEY@$REDIS_HOST:6380/0?ssl=True"
CELERY_RESULT_BACKEND="redis://:$REDIS_KEY@$REDIS_HOST:6380/0?ssl=True"

# Create API container
az container create \
  --resource-group $RESOURCE_GROUP \
  --name pdf-api \
  --image $ACR_NAME.azurecr.io/pdf-tools-api:latest \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv) \
  --dns-name-label pdf-tools-api \
  --ports 8000 \
  --cpu 2 \
  --memory 4 \
  --environment-variables \
    CELERY_BROKER_URL="$CELERY_BROKER_URL" \
    CELERY_RESULT_BACKEND="$CELERY_RESULT_BACKEND"

# Get API URL
az container show \
  --resource-group $RESOURCE_GROUP \
  --name pdf-api \
  --query ipAddress.fqdn -o tsv
```

### Deploy Celery Worker Container

```bash
az container create \
  --resource-group $RESOURCE_GROUP \
  --name pdf-celery-worker \
  --image $ACR_NAME.azurecr.io/pdf-tools-api:latest \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv) \
  --command-line "celery -A celery_app worker --loglevel=info --concurrency=4" \
  --cpu 2 \
  --memory 4 \
  --environment-variables \
    CELERY_BROKER_URL="$CELERY_BROKER_URL" \
    CELERY_RESULT_BACKEND="$CELERY_RESULT_BACKEND"
```

### Deploy Celery Beat Container

```bash
az container create \
  --resource-group $RESOURCE_GROUP \
  --name pdf-celery-beat \
  --image $ACR_NAME.azurecr.io/pdf-tools-api:latest \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv) \
  --command-line "celery -A celery_app beat --loglevel=info" \
  --cpu 1 \
  --memory 2 \
  --environment-variables \
    CELERY_BROKER_URL="$CELERY_BROKER_URL" \
    CELERY_RESULT_BACKEND="$CELERY_RESULT_BACKEND"
```

---

## Option 2: Deploy to Azure App Service

Better for production with auto-scaling and custom domains.

### 1. Create App Service Plan

```bash
APP_PLAN="pdf-tools-plan"

az appservice plan create \
  --resource-group $RESOURCE_GROUP \
  --name $APP_PLAN \
  --is-linux \
  --sku P1V2
```

### 2. Deploy API Web App

```bash
WEB_APP_NAME="pdf-tools-api"  # must be globally unique

az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_PLAN \
  --name $WEB_APP_NAME \
  --deployment-container-image-name $ACR_NAME.azurecr.io/pdf-tools-api:latest

# Configure ACR credentials
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --docker-custom-image-name $ACR_NAME.azurecr.io/pdf-tools-api:latest \
  --docker-registry-server-url https://$ACR_NAME.azurecr.io \
  --docker-registry-server-user $ACR_NAME \
  --docker-registry-server-password $(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Set environment variables
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
    CELERY_BROKER_URL="$CELERY_BROKER_URL" \
    CELERY_RESULT_BACKEND="$CELERY_RESULT_BACKEND" \
    WEBSITES_PORT=8000

# Get app URL
echo "https://$WEB_APP_NAME.azurewebsites.net"
```

### 3. Deploy Celery Worker as Web Job

For Celery worker in App Service, use Azure Container Instances (shown above) or Azure Kubernetes Service for better scalability.

---

## Monitoring and Logs

### View Container Logs (ACI)

```bash
# API logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name pdf-api \
  --follow

# Celery worker logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name pdf-celery-worker \
  --follow

# Celery beat logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name pdf-celery-beat \
  --follow
```

### View App Service Logs

```bash
# Enable logging
az webapp log config \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --docker-container-logging filesystem

# Stream logs
az webapp log tail \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME
```

### Check Container Status

```bash
# ACI status
az container show \
  --resource-group $RESOURCE_GROUP \
  --name pdf-api \
  --query "{Status:instanceView.state, IP:ipAddress.ip, FQDN:ipAddress.fqdn}"

# App Service status
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --query "{Status:state, URL:defaultHostName}"
```

---

## Verification

### 1. Test Health Endpoint

```bash
# Get your API URL
API_URL="https://pdf-tools-api.westeurope.azurecontainer.io:8000"  # or your App Service URL

# Test health
curl -I $API_URL/health

# Should return: HTTP/1.1 200 OK
```

### 2. Test API Documentation

```bash
# Open Swagger UI in browser
open $API_URL/docs
```

### 3. Test Image to PDF Conversion

```bash
# Run performance test
API_URL=$API_URL python performance_test.py
```

### 4. Verify Background Processing

```bash
# Check Celery worker logs for task processing
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name pdf-celery-worker

# Look for: "Task tasks.process_image_to_pdf succeeded"
```

### 5. Verify Auto-Cleanup

```bash
# Check Celery beat logs for scheduled tasks
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name pdf-celery-beat

# Look for: "Scheduler: Sending due task cleanup-temp-files-every-30-minutes"
```

---

## Production Checklist

- [ ] Redis instance created and accessible
- [ ] Docker images built and pushed to ACR
- [ ] API container running and accessible
- [ ] Celery worker container processing tasks
- [ ] Celery beat container running scheduled cleanup
- [ ] Health endpoint returns 200 OK
- [ ] API documentation accessible at `/docs`
- [ ] Performance tests pass
- [ ] Auto-cleanup scheduled and running
- [ ] Logs accessible and monitored
- [ ] Custom domain configured (if needed)
- [ ] SSL certificate installed (App Service provides free SSL)

---

## Scaling

### Scale API Container (ACI)

```bash
# Not supported in ACI - use Azure App Service or AKS for auto-scaling
```

### Scale App Service

```bash
# Manual scaling
az appservice plan update \
  --resource-group $RESOURCE_GROUP \
  --name $APP_PLAN \
  --number-of-workers 3

# Auto-scaling rules
az monitor autoscale create \
  --resource-group $RESOURCE_GROUP \
  --resource $WEB_APP_NAME \
  --resource-type Microsoft.Web/serverfarms \
  --name autoscale-rules \
  --min-count 2 \
  --max-count 10 \
  --count 2
```

---

## Cleanup

```bash
# Delete all resources
az group delete \
  --name $RESOURCE_GROUP \
  --yes \
  --no-wait
```

---

## Troubleshooting

### Container won't start

```bash
# Check container events
az container show \
  --resource-group $RESOURCE_GROUP \
  --name pdf-api \
  --query instanceView.events

# Check logs
az container logs --resource-group $RESOURCE_GROUP --name pdf-api
```

### Redis connection issues

```bash
# Test Redis connectivity
az redis show \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --query "{Host:hostName,Port:sslPort,ProvisioningState:provisioningState}"

# Ensure firewall allows your containers
az redis firewall-rules create \
  --resource-group $RESOURCE_GROUP \
  --name $REDIS_NAME \
  --rule-name AllowAzureServices \
  --start-ip 0.0.0.0 \
  --end-ip 0.0.0.0
```

### Performance issues

- Increase container CPU/memory
- Scale out Celery workers
- Check Redis performance metrics
- Review application logs for bottlenecks

---

## Support

For Azure-specific issues, consult:
- [Azure Container Instances Documentation](https://docs.microsoft.com/azure/container-instances/)
- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure Cache for Redis Documentation](https://docs.microsoft.com/azure/azure-cache-for-redis/)
