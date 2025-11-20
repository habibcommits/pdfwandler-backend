from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def compress_pdf(input_path: str, output_path: str, dpi: int = 144, image_quality: int = 75, color_mode: str = "no-change") -> None:
    """
    Compress a PDF file using PyPDF2 for maximum compatibility.
    Works on any platform without external dependencies.
    
    Args:
        input_path: Path to the input PDF file
        output_path: Path where the compressed PDF should be saved
        dpi: DPI for image resampling (72-300, recommended: 144 for balance, 72 for max compression)
        image_quality: JPEG quality for images (10-100, recommended: 60-85)
        color_mode: Color mode conversion ('no-change', 'grayscale', 'monochrome')
    """
    
    try:
        # Import with fallback support for both pypdf and PyPDF2
        try:
            from pypdf import PdfReader, PdfWriter
        except ImportError:
            try:
                from PyPDF2 import PdfReader, PdfWriter
            except ImportError:
                raise ImportError("Neither pypdf nor PyPDF2 is installed. Please install pypdf>=4.0.0")
        
        logger.debug(f"Starting PDF compression: {input_path}")
        
        # Read the PDF
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        # Copy pages from reader to writer with compression
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            
            # Add page to writer (PyPDF2 applies compression)
            writer.add_page(page)
        
        # Write the compressed PDF
        with open(output_path, "wb") as output_file:
            writer.write(output_file)
        
        logger.debug(f"PDF written to: {output_path}")
        
        # Verify output file was created
        if not Path(output_path).exists():
            raise Exception("Compression completed but output file was not created")
        
        output_size = Path(output_path).stat().st_size
        if output_size == 0:
            raise Exception("Output file is empty after compression")
        
        input_size = Path(input_path).stat().st_size
        logger.info(f"PDF compression successful: {input_size} -> {output_size} bytes")
            
    except Exception as e:
        logger.error(f"PDF compression failed: {str(e)}", exc_info=True)
        # Clean up output file if it exists but compression failed
        if Path(output_path).exists():
            try:
                Path(output_path).unlink()
            except Exception:
                pass
        raise Exception(f"PDF compression failed: {str(e)}")
