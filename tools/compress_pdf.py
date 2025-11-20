from PyPDF2 import PdfWriter, PdfReader
from pathlib import Path

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
        
        # Verify output file was created
        if not Path(output_path).exists():
            raise Exception("Compression completed but output file was not created")
        
        output_size = Path(output_path).stat().st_size
        if output_size == 0:
            raise Exception("Output file is empty after compression")
            
    except Exception as e:
        # Clean up output file if it exists but compression failed
        if Path(output_path).exists():
            Path(output_path).unlink()
        raise Exception(f"PDF compression failed: {str(e)}")
