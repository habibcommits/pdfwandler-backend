from PIL import Image, ImageOps
from typing import List

def convert_images_to_pdf(image_paths: List[str], output_path: str) -> None:
    """
    Convert multiple images to a single PDF file with proper scaling and rotation.
    
    Args:
        image_paths: List of paths to image files
        output_path: Path where the PDF should be saved
    """
    if not image_paths:
        raise ValueError("No images provided")
    
    A4_WIDTH_PX = 2480
    A4_HEIGHT_PX = 3508
    
    processed_images = []
    
    try:
        for img_path in image_paths:
            img = Image.open(img_path)
            
            img = ImageOps.exif_transpose(img)
            
            if img.mode == 'RGBA':
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_width, img_height = img.size
            img_aspect = img_width / img_height
            page_aspect = A4_WIDTH_PX / A4_HEIGHT_PX
            
            if img_aspect > page_aspect:
                new_height = A4_HEIGHT_PX
                new_width = int(A4_HEIGHT_PX * img_aspect)
            else:
                new_width = A4_WIDTH_PX
                new_height = int(A4_WIDTH_PX / img_aspect)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            x_offset = (new_width - A4_WIDTH_PX) // 2
            y_offset = (new_height - A4_HEIGHT_PX) // 2
            
            img_cropped = img.crop((
                x_offset,
                y_offset,
                x_offset + A4_WIDTH_PX,
                y_offset + A4_HEIGHT_PX
            ))
            
            processed_images.append(img_cropped)
            img.close()
        
        if not processed_images:
            raise ValueError("No valid images to convert")
        
        first_image = processed_images[0]
        other_images = processed_images[1:] if len(processed_images) > 1 else []
        
        first_image.save(
            output_path,
            "PDF",
            resolution=300.0,
            save_all=True,
            append_images=other_images,
            quality=95
        )
    
    finally:
        for img in processed_images:
            img.close()
