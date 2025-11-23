#!/bin/bash
# Build and Push Docker Image to Docker Hub
# This script builds your Docker image for Azure (AMD64) and pushes to Docker Hub

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 PDF Tools API - Docker Build and Push${NC}"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Prompt for Docker Hub username
read -p "Enter your Docker Hub username: " DOCKER_USERNAME

if [ -z "$DOCKER_USERNAME" ]; then
    echo -e "${RED}❌ Error: Docker Hub username cannot be empty${NC}"
    exit 1
fi

# Set image name
IMAGE_NAME="${DOCKER_USERNAME}/pdf-tools"
IMAGE_TAG="latest"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo ""
echo -e "${YELLOW}📦 Building Docker image...${NC}"
echo "Image: $FULL_IMAGE"
echo "Platform: linux/amd64 (Azure compatible)"
echo ""

# Build the Docker image for AMD64 (Azure architecture)
docker build --platform linux/amd64 -t "$FULL_IMAGE" .

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Build failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Build successful!${NC}"
echo ""

# Check if already logged in to Docker Hub
if ! docker info | grep -q "Username: $DOCKER_USERNAME"; then
    echo -e "${YELLOW}🔐 Please login to Docker Hub...${NC}"
    docker login
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Docker login failed!${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}📤 Pushing image to Docker Hub...${NC}"
echo "This may take a few minutes..."
echo ""

# Push to Docker Hub
docker push "$FULL_IMAGE"

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Push failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ Successfully pushed to Docker Hub!${NC}"
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 All done!${NC}"
echo ""
echo "Your image: $FULL_IMAGE"
echo "View on Docker Hub: https://hub.docker.com/r/$IMAGE_NAME"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Update azure-deployment.yaml with your Docker Hub username"
echo "2. Deploy to Azure using AZURE_QUICK_START.md"
echo ""
