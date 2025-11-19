from celery_app import celery_app
from tools.image_to_pdf import convert_images_to_pdf
from tools.merge_pdf import merge_pdfs
from tools.compress_pdf import compress_pdf
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name='tasks.process_image_to_pdf')
def process_image_to_pdf(image_paths: list, output_path: str) -> dict:
    try:
        convert_images_to_pdf(image_paths, output_path)
        return {
            'status': 'success',
            'output_path': output_path,
            'message': 'Images converted to PDF successfully'
        }
    except Exception as e:
        logger.error(f"Error converting images to PDF: {str(e)}")
        for path in image_paths:
            Path(path).unlink(missing_ok=True)
        raise

@celery_app.task(name='tasks.process_merge_pdf')
def process_merge_pdf(pdf_paths: list, output_path: str) -> dict:
    try:
        merge_pdfs(pdf_paths, output_path)
        return {
            'status': 'success',
            'output_path': output_path,
            'message': 'PDFs merged successfully'
        }
    except Exception as e:
        logger.error(f"Error merging PDFs: {str(e)}")
        for path in pdf_paths:
            Path(path).unlink(missing_ok=True)
        raise

@celery_app.task(name='tasks.process_compress_pdf')
def process_compress_pdf(input_path: str, output_path: str, dpi: int = 144, 
                        image_quality: int = 75, color_mode: str = "no-change") -> dict:
    try:
        compress_pdf(input_path, output_path, dpi, image_quality, color_mode)
        return {
            'status': 'success',
            'output_path': output_path,
            'message': 'PDF compressed successfully'
        }
    except Exception as e:
        logger.error(f"Error compressing PDF: {str(e)}")
        Path(input_path).unlink(missing_ok=True)
        raise

@celery_app.task(name='tasks.cleanup_old_files')
def cleanup_old_files(directory: str, max_age_hours: int = 1) -> dict:
    from datetime import datetime, timedelta
    
    try:
        cleaned_count = 0
        dir_path = Path(directory)
        now = datetime.now()
        
        for file_path in dir_path.glob("*"):
            if file_path.is_file():
                file_age = now - datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_age > timedelta(hours=max_age_hours):
                    file_path.unlink()
                    cleaned_count += 1
        
        return {
            'status': 'success',
            'cleaned_count': cleaned_count,
            'directory': directory
        }
    except Exception as e:
        logger.error(f"Error cleaning up files: {str(e)}")
        raise
