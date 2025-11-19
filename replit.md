# PDF Tools API Backend

FastAPI backend for PDF processing tools deployed on Azure with production-ready setup for Hetzner deployment.

## Project Overview

This is a RESTful API backend that provides PDF manipulation tools:
- **Image to PDF**: Convert multiple images to a single PDF
- **Merge PDF**: Combine multiple PDFs into one
- **Compress PDF**: Reduce PDF file size with customizable options

## Tech Stack

- **Framework**: FastAPI (Python 3.11)
- **Server**: Uvicorn (development) / Gunicorn (production)
- **Task Queue**: Celery with Redis
- **Reverse Proxy**: NGINX
- **Process Manager**: Systemd
- **Image Processing**: Pillow
- **PDF Processing**: PyPDF2

## Key Features

- Automatic file cleanup (1 hour retention)
- CORS enabled for frontend integration
- Background task processing with Celery
- Production-ready with Gunicorn + NGINX
- SSL/TLS support with Let's Encrypt
- Rate limiting and security headers

## User Preferences

- Current deployment: Azure
- Target deployment: Hetzner Cloud (Germany)
