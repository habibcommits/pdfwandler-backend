#!/usr/bin/env python3
"""
Performance test script for PDF conversion API.
Tests with 5 images and 50 images to measure processing time.
"""
import requests
import time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os


def create_test_image(width, height, color, text, filename):
    """Create a test image"""
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill='white', font=font)
    
    img.save(filename)
    return filename


def test_image_to_pdf(api_url, num_images, test_name):
    """Test image to PDF conversion with N images"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name} ({num_images} images)")
    print(f"{'='*60}")
    
    test_dir = Path("perf_test_images")
    test_dir.mkdir(exist_ok=True)
    
    print(f"Creating {num_images} test images...")
    image_files = []
    colors = ['#FF5733', '#33FF57', '#3357FF', '#FF33A1', '#FFA533', 
              '#33FFF5', '#F533FF', '#FFD700', '#8B4513', '#4B0082']
    
    for i in range(num_images):
        color = colors[i % len(colors)]
        width = 1920 if i % 2 == 0 else 1080
        height = 1080 if i % 2 == 0 else 1920
        filename = test_dir / f"test_image_{i+1}.jpg"
        create_test_image(width, height, color, f"Image {i+1}", str(filename))
        image_files.append(str(filename))
    
    print(f"✓ Created {len(image_files)} images")
    
    files = [('files', (os.path.basename(f), open(f, 'rb'), 'image/jpeg')) for f in image_files]
    
    print(f"\nSending request to {api_url}...")
    start_time = time.time()
    
    try:
        response = requests.post(f"{api_url}/api/image-to-pdf", files=files, timeout=300)
        end_time = time.time()
        
        for _, file_tuple in files:
            file_tuple[1].close()
        
        processing_time = end_time - start_time
        
        print(f"\n{'='*60}")
        print(f"RESULTS - {test_name}")
        print(f"{'='*60}")
        print(f"Status Code: {response.status_code}")
        print(f"Processing Time: {processing_time:.2f} seconds")
        print(f"Time per image: {processing_time/num_images:.2f} seconds")
        
        if response.status_code == 200:
            output_file = f"performance_test_{num_images}_images.pdf"
            with open(output_file, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(output_file)
            print(f"Output PDF: {output_file}")
            print(f"PDF Size: {file_size / 1024:.2f} KB")
            print(f"✓ SUCCESS")
        else:
            print(f"✗ FAILED: {response.text}")
        
        for img_file in image_files:
            Path(img_file).unlink(missing_ok=True)
        test_dir.rmdir()
        
        return {
            'status_code': response.status_code,
            'processing_time': processing_time,
            'time_per_image': processing_time/num_images,
            'num_images': num_images
        }
        
    except Exception as e:
        print(f"✗ ERROR: {e}")
        
        for _, file_tuple in files:
            try:
                file_tuple[1].close()
            except:
                pass
        
        for img_file in image_files:
            Path(img_file).unlink(missing_ok=True)
        
        return None


def main():
    api_url = os.getenv("API_URL", "http://localhost:8000")
    
    print(f"{'='*60}")
    print("PDF API Performance Test")
    print(f"{'='*60}")
    print(f"API URL: {api_url}")
    
    print("\nTesting /health endpoint...")
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        print(f"Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"Response: {health_response.json()}")
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return 1
    
    test_5 = test_image_to_pdf(api_url, 5, "Small Batch Test")
    
    test_50 = test_image_to_pdf(api_url, 50, "Large Batch Test")
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    if test_5:
        print(f"5 images:  {test_5['processing_time']:.2f}s total, {test_5['time_per_image']:.2f}s per image")
    
    if test_50:
        print(f"50 images: {test_50['processing_time']:.2f}s total, {test_50['time_per_image']:.2f}s per image")
    
    print(f"{'='*60}")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
