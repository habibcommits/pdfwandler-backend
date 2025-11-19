# PDF Tools API

A production-ready FastAPI service for PDF manipulation including image-to-PDF conversion, PDF merging, and PDF compression. Built with asynchronous task processing using Celery and Redis for handling large files efficiently.

## Features

- **Image to PDF Conversion** - Convert multiple images to a single PDF with auto-rotation and proper scaling
- **PDF Merging** - Combine multiple PDFs into one document
- **PDF Compression** - Reduce PDF file sizes with configurable quality settings
- **Background Processing** - Heavy tasks processed asynchronously via Celery workers
- **Auto-cleanup** - GDPR-compliant automatic deletion of temporary files (1 hour retention)
- **Health Monitoring** - Built-in health check endpoints
- **Production Ready** - Docker containerization, proper logging, and error handling

## Quick Start with Docker

### Prerequisites

- Docker and Docker Compose
- 2GB+ RAM recommended
- Linux/macOS/Windows with WSL2

### Run with Docker Compose

```bash
# Clone the repository
git clone <your-repo-url>
cd pdf-tools-backend

# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f celery-worker
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```bash
GET /health
GET /
```

### Image to PDF
```bash
POST /api/image-to-pdf
Content-Type: multipart/form-data

# Upload multiple image files
# Supported formats: JPG, PNG, GIF, BMP
# Returns: PDF file
```

### Merge PDFs
```bash
POST /api/merge-pdf
Content-Type: multipart/form-data

# Upload 2+ PDF files
# Returns: Merged PDF file
```

### Compress PDF
```bash
POST /api/compress-pdf
Content-Type: multipart/form-data

# Parameters:
# - file: PDF file
# - dpi: 72-300 (default: 144)
# - image_quality: 10-100 (default: 75)
# - color_mode: "no-change", "grayscale", "monochrome"
```

## Interactive API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

### Services

- **API** - FastAPI application (Uvicorn/Gunicorn)
- **Redis** - Message broker and result backend
- **Celery Worker** - Background task processor (4 concurrent workers)
- **Celery Beat** - Scheduled task scheduler (auto-cleanup every 30 minutes)

### File Lifecycle

1. Files uploaded to `/uploads` directory
2. Processed files saved to `/temp` directory
3. Files automatically deleted after 1 hour (GDPR compliant)
4. Celery beat runs cleanup every 30 minutes

### Background Tasks

All PDF processing operations run asynchronously:
- `process_image_to_pdf` - Image conversion
- `process_merge_pdf` - PDF merging
- `process_compress_pdf` - PDF compression
- `cleanup_old_files` - Scheduled cleanup

## Environment Variables

See `.env.example` for all configuration options:

```bash
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
PORT=8000
WORKERS=4
ALLOWED_ORIGINS=*
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start Redis
redis-server

# Start Celery worker
celery -A celery_app worker --loglevel=info --concurrency=2

# Start Celery beat
celery -A celery_app beat --loglevel=info

# Start API server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Testing

```bash
# Run verification script
python verify_celery_redis.py

# Run performance tests
python performance_test.py

# Generate sample PDF
python test_image_to_pdf.py
```

## Production Deployment

See [docker-deployment-guide.md](docker-deployment-guide.md) for detailed Azure deployment instructions.

## Performance

Typical processing times:
- 5 images → ~2-3 seconds
- 50 images → ~15-20 seconds
- PDF merge (10 files) → ~1-2 seconds
- PDF compression → ~3-5 seconds

## Security

- CORS configured (customize `ALLOWED_ORIGINS`)
- No authentication layer (deploy behind Azure API Gateway or similar)
- Automatic file cleanup for privacy
- No permanent storage of user files

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
