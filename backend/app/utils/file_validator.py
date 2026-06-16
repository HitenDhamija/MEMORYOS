"""
File validation utilities for memory uploads.
"""

from typing import Tuple, Optional
from fastapi import UploadFile
import mimetypes
from app.core.config import settings


class FileValidator:
    """Validate uploaded files for security and compliance."""
    
    @staticmethod
    def validate_file(file: UploadFile) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate uploaded file.
        
        Args:
            file: FastAPI UploadFile object
            
        Returns:
            (is_valid: bool, error_message: str | None, file_type: str | None)
            file_type: One of "pdf", "image", "txt", "md", "bookmark", "other"
        """
        if not file or not file.filename:
            return False, "No file provided", None
        
        # Check file size
        if file.size and file.size > settings.max_file_size:
            size_mb = settings.max_file_size / (1024 * 1024)
            return False, f"File too large. Maximum {size_mb}MB allowed", None
        
        # Get file extension
        filename = file.filename.lower()
        if "." not in filename:
            return False, "File must have an extension", None
        
        ext = "." + filename.split(".")[-1]
        
        # Determine file type from extension
        file_type = FileValidator._get_file_type_from_extension(ext)
        if not file_type:
            return False, f"File type {ext} not supported", None
        
        # Validate MIME type if provided
        if file.content_type:
            valid_mime = FileValidator._validate_mime_type(ext, file.content_type)
            if not valid_mime:
                return False, f"Invalid MIME type for {ext} file", None
        
        return True, None, file_type
    
    @staticmethod
    def _get_file_type_from_extension(ext: str) -> Optional[str]:
        """Get file type category from extension."""
        for file_type, extensions in settings.allowed_extensions.items():
            if ext in extensions:
                return file_type
        return None
    
    @staticmethod
    def _validate_mime_type(ext: str, content_type: str) -> bool:
        """Validate MIME type matches extension.
        
        Note: This is basic validation. Production should use `python-magic`
        to verify file magic bytes.
        """
        content_type = content_type.lower()
        
        # Map extensions to expected MIME types
        mime_map = {
            ".pdf": ["application/pdf"],
            ".jpg": ["image/jpeg"],
            ".jpeg": ["image/jpeg"],
            ".png": ["image/png"],
            ".gif": ["image/gif"],
            ".webp": ["image/webp"],
            ".txt": ["text/plain"],
            ".md": ["text/markdown", "text/plain"],
            ".markdown": ["text/markdown", "text/plain"],
            ".url": ["text/plain"],
            ".webloc": ["text/plain"],
        }
        
        expected_types = mime_map.get(ext, [])
        return content_type in expected_types or any(ct in content_type for ct in expected_types)
    
    @staticmethod
    def is_file_type(file_type: str) -> bool:
        """Check if file type is valid."""
        return file_type in settings.allowed_extensions
