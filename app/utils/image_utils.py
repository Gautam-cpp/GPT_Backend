
import os
import uuid
from typing import List, Optional
from PIL import Image
import io
import base64
from fastapi import UploadFile, HTTPException

def validate_image(file: UploadFile) -> bool:
    """Validate if uploaded file is a valid image"""
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in valid_extensions:
        return False
    
    # Check file size (max 5MB)
    if file.size > 5 * 1024 * 1024:
        return False
    
    return True

def compress_image(image_bytes: bytes, max_size: tuple = (800, 600), quality: int = 85) -> bytes:
    """Compress image to reduce file size"""
    try:
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert RGBA to RGB if necessary
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # Resize image while maintaining aspect ratio
        image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Save compressed image
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)
        
        return output.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error compressing image: {str(e)}")

def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename for uploaded image"""
    file_extension = os.path.splitext(original_filename)[1].lower()
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_extension}"

async def save_image(file: UploadFile, upload_dir: str = "uploads/images") -> str:
    """Save uploaded image and return file path"""
    try:
        # Validate image
        if not validate_image(file):
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Create upload directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Read file content
        file_content = await file.read()
        
        # Compress image
        compressed_content = compress_image(file_content)
        
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(compressed_content)
        
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving image: {str(e)}")

def encode_image_to_base64(image_path: str) -> str:
    """Encode image to base64 string"""
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error encoding image: {str(e)}")
