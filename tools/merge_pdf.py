from pypdf import PdfWriter, PdfReader
from typing import List

def merge_pdfs(pdf_paths: List[str], output_path: str) -> None:
    """
    Merge multiple PDF files into a single PDF.
    
    Args:
        pdf_paths: List of paths to PDF files to merge
        output_path: Path where the merged PDF should be saved
    """
    if not pdf_paths:
        raise ValueError("No PDF files provided")
    
    if len(pdf_paths) < 2:
        raise ValueError("At least 2 PDF files are required for merging")
    
    writer = PdfWriter()
    
    for pdf_path in pdf_paths:
        reader = PdfReader(pdf_path)
        for page in reader.pages:
            writer.add_page(page)
    
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
