from PIL import Image, ImageOps
from typing import List

def convert_images_to_pdf(image_paths: List[str], output_path: str) -> None:
    """
    Convert multiple images to a single PDF file with optimization for speed.
    Uses efficient memory management and processing.
    
    Args:
        image_paths: List of paths to image files
        output_path: Path where the PDF should be saved
    """
    if not image_paths:
        raise ValueError("No images provided")
    
    # Use reasonable DPI for faster processing while maintaining quality
    DPI = 200  # Reduced from 300 for faster processing
    MAX_DIMENSION = 2000  # Max dimension to prevent huge files
    
    processed_images: List[Image.Image] = []
    
    try:
        for img_path in image_paths:
            # Open and auto-rotate based on EXIF
            with Image.open(img_path) as img_file:
                img = ImageOps.exif_transpose(img_file)
                if img is None:
                    img = img_file
                
                # Convert to RGB efficiently
                if img.mode == 'RGBA':
                    # Create RGB background and paste
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if len(img.split()) == 4:
                        rgb_img.paste(img, mask=img.split()[3])
                    else:
                        rgb_img.paste(img)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if image is too large (speeds up processing significantly)
                width, height = img.size
                if width > MAX_DIMENSION or height > MAX_DIMENSION:
                    if width > height:
                        new_width = MAX_DIMENSION
                        new_height = int(height * (MAX_DIMENSION / width))
                    else:
                        new_height = MAX_DIMENSION
                        new_width = int(width * (MAX_DIMENSION / height))
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create a copy to keep after the context manager closes
                processed_images.append(img.copy())
        
        if not processed_images:
            raise ValueError("No valid images to convert")
        
        # Save all images to PDF with optimization
        first_image = processed_images[0]
        other_images = processed_images[1:] if len(processed_images) > 1 else []
        
        first_image.save(
            output_path,
            "PDF",
            resolution=DPI,
            save_all=True,
            append_images=other_images,
            quality=85,  # Good balance between quality and file size
            optimize=True
        )
    
    finally:
        # Clean up all images from memory
        for img in processed_images:
            try:
                img.close()
            except:
                pass
