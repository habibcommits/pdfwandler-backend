from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import uuid
import shutil
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import logging

from tools.image_to_pdf import convert_images_to_pdf
from tools.merge_pdf import merge_pdfs
from tools.compress_pdf import compress_pdf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PDF Tools API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("uploads")
TEMP_DIR = Path("temp")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

async def cleanup_old_files():
    """Remove files older than 2 hours (increased from 1 hour for user downloads)"""
    while True:
        try:
            now = datetime.now()
            cleaned = 0
            for directory in [UPLOAD_DIR, TEMP_DIR]:
                for file_path in directory.glob("*"):
                    if file_path.is_file():
                        file_age = now - datetime.fromtimestamp(file_path.stat().st_mtime)
                        # Changed from 1 hour to 2 hours to give users more time to download
                        if file_age > timedelta(hours=2):
                            file_path.unlink()
                            cleaned += 1
            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} old files")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        # Run cleanup every 30 minutes (increased from 5 minutes)
        await asyncio.sleep(1800)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(cleanup_old_files())
    logger.info("PDF Tools API started successfully")

@app.get("/")
async def root():
    return {"message": "PDF Tools API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/image-to-pdf")
async def image_to_pdf(files: List[UploadFile] = File(...)):
    """Convert images to PDF"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}
    uploaded_files = []
    
    try:
        for file in files:
            if not file.filename:
                raise HTTPException(status_code=400, detail="Filename is required")
            
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in allowed_extensions:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid file type: {file.filename}. Allowed: JPG, PNG, GIF, BMP"
                )
            
            file_id = f"{uuid.uuid4()}{ext}"
            file_path = UPLOAD_DIR / file_id
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append(str(file_path))
        
        output_filename = f"{uuid.uuid4()}.pdf"
        output_path = TEMP_DIR / output_filename
        
        logger.info(f"Converting {len(uploaded_files)} images to PDF")
        convert_images_to_pdf(uploaded_files, str(output_path))
        
        # Clean up input files
        for file_path in uploaded_files:
            Path(file_path).unlink(missing_ok=True)
        
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="converted.pdf",
            background=None  # Don't delete file in background
        )
    
    except Exception as e:
        logger.error(f"Image to PDF error: {str(e)}")
        for file_path in uploaded_files:
            Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error converting images: {str(e)}")

@app.post("/api/merge-pdf")
async def merge_pdf_endpoint(files: List[UploadFile] = File(...)):
    """Merge multiple PDFs into one"""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) < 2:
        raise HTTPException(status_code=400, detail="At least 2 PDF files required")
    
    uploaded_files = []
    
    try:
        for file in files:
            if not file.filename:
                raise HTTPException(status_code=400, detail="Filename is required")
            
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type: {file.filename}. Only PDF files allowed"
                )
            
            file_id = f"{uuid.uuid4()}.pdf"
            file_path = UPLOAD_DIR / file_id
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            uploaded_files.append(str(file_path))
        
        output_filename = f"{uuid.uuid4()}.pdf"
        output_path = TEMP_DIR / output_filename
        
        logger.info(f"Merging {len(uploaded_files)} PDFs")
        merge_pdfs(uploaded_files, str(output_path))
        
        # Clean up input files
        for file_path in uploaded_files:
            Path(file_path).unlink(missing_ok=True)
        
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename="merged.pdf",
            background=None  # Don't delete file in background
        )
    
    except Exception as e:
        logger.error(f"Merge PDF error: {str(e)}")
        for file_path in uploaded_files:
            Path(file_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Error merging PDFs: {str(e)}")

@app.post("/api/compress-pdf")
async def compress_pdf_endpoint(
    file: UploadFile = File(...),
    dpi: int = 144,
    image_quality: int = 75,
    color_mode: str = "no-change"
):
    """Compress a PDF file with advanced options"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.filename}. Only PDF files allowed"
        )
    
    # Validate parameters
    if dpi < 72 or dpi > 300:
        raise HTTPException(status_code=400, detail="DPI must be between 72 and 300")
    
    if image_quality < 10 or image_quality > 100:
        raise HTTPException(status_code=400, detail="Image quality must be between 10 and 100")
    
    if color_mode not in ["no-change", "grayscale", "monochrome"]:
        raise HTTPException(status_code=400, detail="Color mode must be: no-change, grayscale, or monochrome")
    
    file_id = f"{uuid.uuid4()}.pdf"
    file_path = UPLOAD_DIR / file_id
    output_path = None
    
    try:
        # Save uploaded file
        logger.info(f"Compressing PDF: {file.filename} (DPI: {dpi}, Quality: {image_quality}, Color: {color_mode})")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Verify file was saved
        if not file_path.exists():
            raise Exception("Failed to save uploaded file")
        
        logger.info(f"Input file saved: {file_path} ({file_path.stat().st_size} bytes)")
        
        # Compress PDF
        output_filename = f"{uuid.uuid4()}.pdf"
        output_path = TEMP_DIR / output_filename
        
        compress_pdf(
            str(file_path), 
            str(output_path),
            dpi=dpi,
            image_quality=image_quality,
            color_mode=color_mode
        )
        
        # Verify output was created
        if not output_path.exists():
            raise Exception("Compression completed but output file was not created")
        
        logger.info(f"Output file created: {output_path} ({output_path.stat().st_size} bytes)")
        
        # Clean up input file
        file_path.unlink(missing_ok=True)
        
        # Return compressed PDF
        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename=f"compressed_{file.filename}",
            background=None  # Don't delete file in background
        )
    
    except Exception as e:
        # Clean up files on error
        logger.error(f"Compression error: {str(e)}", exc_info=True)
        if file_path.exists():
            file_path.unlink(missing_ok=True)
        if output_path and output_path.exists():
            output_path.unlink(missing_ok=True)
        
        # Return detailed error message
        error_detail = str(e)
        if "Ghostscript" in error_detail or "gs" in error_detail:
            error_detail = f"PDF compression failed: {error_detail}. Please ensure the PDF is valid and not corrupted."
        
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Railway provides the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
