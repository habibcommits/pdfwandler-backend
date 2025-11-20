#!/bin/bash
# Azure Post-Deployment Script
# This script installs system dependencies that aren't in the base image

echo "Installing system dependencies for PDF Tools API..."

# Update package lists
apt-get update -qq

# Install Ghostscript (required for PDF compression)
echo "Installing Ghostscript..."
apt-get install -y ghostscript

# Install Redis (if not already available)
echo "Installing Redis..."
apt-get install -y redis-server redis-tools

# Verify installations
echo "Verifying installations..."
gs --version && echo "✓ Ghostscript installed successfully"
redis-server --version && echo "✓ Redis installed successfully"

echo "All system dependencies installed successfully!"
