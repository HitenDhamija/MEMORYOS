"""
Image Processor

Processes image files using OCR (pytesseract).
Falls back gracefully if OCR is not available.
"""

import os
from typing import Dict
from app.services.processing.base import DocumentProcessor

# Try to import PIL (required)
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Try to import OCR (optional, with multiple fallback attempts)
OCR_AVAILABLE = False
try:
    import pytesseract
    OCR_AVAILABLE = True
except (ImportError, ValueError):
    # ValueError can occur from numpy/pandas compatibility issues
    OCR_AVAILABLE = False


class ImageProcessor(DocumentProcessor):
    """Process image files with OCR."""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    
    def can_process(self) -> bool:
        """Check if file exists and is a supported image format."""
        if not PIL_AVAILABLE:
            return False
            
        try:
            ext = os.path.splitext(self.file_path)[1].lower()
            return (
                os.path.exists(self.file_path) and
                os.path.isfile(self.file_path) and
                ext in self.SUPPORTED_EXTENSIONS
            )
        except Exception:
            return False
    
    def extract_text(self) -> str:
        """
        Extract text from image using OCR.
        Falls back to empty string if OCR not available.
        """
        if not OCR_AVAILABLE:
            return ""
        
        try:
            image = Image.open(self.file_path)
            text = pytesseract.image_to_string(image)
            return text.strip()
        except Exception as e:
            # Log but don't raise - OCR is optional
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"OCR extraction failed: {str(e)}")
            return ""
    
    def extract_metadata(self) -> Dict[str, any]:
        """Extract image metadata."""
        try:
            metadata = {
                "filename": self.original_filename,
                "file_size_bytes": os.path.getsize(self.file_path),
            }
            
            try:
                image = Image.open(self.file_path)
                metadata["width"] = image.width
                metadata["height"] = image.height
                metadata["format"] = image.format
                metadata["mode"] = image.mode  # RGB, RGBA, etc.
            except Exception:
                pass
            
            # Check if OCR is available
            metadata["ocr_available"] = OCR_AVAILABLE
            
            return metadata
        except Exception as e:
            return {
                "filename": self.original_filename,
                "error": str(e),
                "ocr_available": OCR_AVAILABLE
            }
    
    def extract_structure(self) -> Dict[str, any]:
        """
        Extract image structure.
        For images, this is mainly dimension and format info.
        """
        try:
            image = Image.open(self.file_path)
            
            return {
                "width": image.width,
                "height": image.height,
                "format": image.format,
                "color_mode": image.mode,
                "has_transparency": image.mode == 'RGBA'
            }
        except Exception:
            return {"width": 0, "height": 0}
