from PIL import Image
import requests
from io import BytesIO
import os
from config import settings

def process_image(input_url, output_path):
    try:
        # Download image
        response = requests.get(input_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        
        # Compress to 50% quality
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        img.save(output_path, quality=50, optimize=True)
        
        return output_path
    except Exception as e:
        print(f"Error processing image {input_url}: {str(e)}")
        return None