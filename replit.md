# PDF Tools API

## Overview

This is a FastAPI-based web service that provides PDF manipulation tools including image-to-PDF conversion, PDF merging, and PDF compression. The application uses Celery with Redis for asynchronous task processing and implements automatic file cleanup for GDPR compliance. It's designed to be deployed on Railway with a simple, stateless architecture.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
- **FastAPI** serves as the web framework, chosen for its async capabilities, automatic API documentation, and type safety
- **Uvicorn** ASGI server handles HTTP requests with support for concurrent connections
- **Gunicorn** provides process management in production with worker configuration based on CPU cores

### Asynchronous Task Processing
- **Celery** handles background PDF processing tasks to prevent HTTP timeout issues on large files
- Tasks are queued and processed independently from the API layer
- **Redis** serves as both the message broker and result backend for Celery
- Task configuration includes timeouts (300s hard limit, 240s soft limit) to prevent runaway processes
- Worker prefetch is limited to 1 to ensure fair task distribution
- Queue routing sends all PDF tasks to a dedicated `pdf_processing` queue

### File Storage & Lifecycle Management
- **Temporary file storage** using local filesystem with two directories:
  - `uploads/` - for incoming user files
  - `temp/` - for intermediate processing files
- **Automatic cleanup** runs every 5 minutes via async background task
- Files older than 1 hour are automatically deleted for GDPR compliance
- Each file operation uses UUID-based naming to prevent collisions

### PDF Processing Tools
Three core utilities in the `tools/` package:

1. **Image to PDF Converter** (`image_to_pdf.py`)
   - Converts multiple images into a single PDF
   - Handles EXIF orientation correction
   - Scales and crops images to fit A4 dimensions (2480x3508px)
   - Converts RGBA to RGB with white background

2. **PDF Merger** (`merge_pdf.py`)
   - Combines multiple PDFs into one document
   - Uses PyPDF2 for reliable PDF manipulation

3. **PDF Compressor** (`compress_pdf.py`)
   - Reduces PDF file size through image resampling and compression
   - Configurable DPI (72-300) and JPEG quality (10-100)
   - Optional color mode conversion (grayscale/monochrome)
   - Extracts and recompresses embedded images

### CORS & Security
- Wildcard CORS configuration (`allow_origins=["*"]`) for maximum accessibility
- No authentication layer implemented - designed for public access or behind external auth gateway

### Deployment Configuration
- **Railway.json** configures Nixpacks builder with custom start command
- Environment-based configuration for Redis URLs and service ports
- Supports horizontal scaling through stateless design

## External Dependencies

### Message Queue & Cache
- **Redis** (localhost:6379/0 by default)
  - Used as Celery message broker for task queuing
  - Stores task results and state
  - Configurable via `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` environment variables

### Python Libraries
- **FastAPI** (0.109.0) - Web framework
- **Uvicorn** (0.27.0) - ASGI server with standard extras
- **Celery** (5.3.4) - Distributed task queue
- **Redis** (5.0.1) - Python client for Redis
- **PyPDF2** (3.0.1) - PDF manipulation library
- **Pillow** (10.3.0) - Image processing library
- **Gunicorn** (21.2.0) - Production WSGI server
- **python-multipart** (0.0.6) - Multipart form data parsing
- **aiofiles** (23.2.1) - Async file operations

### Deployment Platform
- **Railway** - Primary deployment target with Nixpacks build system
- Expects `PORT` environment variable for HTTP binding
- No database requirements - fully stateless operation

### System Fonts (Optional)
- DejaVu Sans Bold font (`/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`) used for test image generation
- Falls back to default font if unavailable