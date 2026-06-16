"""
Storage service for file operations.
"""

import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import HTTPException, status
from app.core.config import settings


class StorageService:
    """Manage file storage operations."""
    
    @staticmethod
    def get_upload_dir() -> Path:
        """Get the upload directory path."""
        return Path(settings.upload_dir)
    
    @staticmethod
    def get_user_storage_path(user_id: int) -> Path:
        """Get base storage path for a user."""
        return StorageService.get_upload_dir() / str(user_id)
    
    @staticmethod
    def get_file_type_dir(user_id: int, file_type: str) -> Path:
        """Get storage path for specific file type."""
        return StorageService.get_user_storage_path(user_id) / file_type
    
    @staticmethod
    def save_file(user_id: int, file_type: str, file_data: bytes, 
                  original_filename: str) -> Tuple[str, str]:
        """Save uploaded file to storage.
        
        Args:
            user_id: User ID
            file_type: File type category (pdf, image, txt, md, bookmark, other)
            file_data: File content bytes
            original_filename: Original filename
            
        Returns:
            (file_id: str, storage_path: str)
            file_id: Unique identifier (UUID)
            storage_path: Relative path from uploads/ (e.g., "1/pdf/abc-def_report.pdf")
        """
        try:
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            
            # Create directory structure
            file_dir = StorageService.get_file_type_dir(user_id, file_type)
            file_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate internal filename (file_id + original name)
            # Keep extension from original filename
            name_part = original_filename.rsplit(".", 1)[0] if "." in original_filename else original_filename
            ext_part = "." + original_filename.split(".")[-1] if "." in original_filename else ""
            internal_filename = f"{file_id}_{name_part}{ext_part}"
            
            # Full storage path
            file_path = file_dir / internal_filename
            
            # Write file
            with open(file_path, "wb") as f:
                f.write(file_data)
            
            # Return relative storage path
            relative_path = str(file_path.relative_to(StorageService.get_upload_dir()))
            
            return file_id, relative_path
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}"
            )
    
    @staticmethod
    def get_file(user_id: int, storage_path: str) -> bytes:
        """Retrieve file from storage.
        
        Args:
            user_id: User ID (for security check)
            storage_path: Relative storage path
            
        Returns:
            File content bytes
        """
        try:
            # Prevent path traversal
            if ".." in storage_path or storage_path.startswith("/"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid path"
                )
            
            # Ensure file belongs to user
            if not storage_path.startswith(str(user_id)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            file_path = StorageService.get_upload_dir() / storage_path
            
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="File not found"
                )
            
            with open(file_path, "rb") as f:
                return f.read()
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve file: {str(e)}"
            )
    
    @staticmethod
    def delete_file(user_id: int, storage_path: str) -> bool:
        """Delete file from storage.
        
        Args:
            user_id: User ID (for security check)
            storage_path: Relative storage path
            
        Returns:
            True if deleted, False if not found
        """
        try:
            # Prevent path traversal
            if ".." in storage_path or storage_path.startswith("/"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid path"
                )
            
            # Ensure file belongs to user
            if not storage_path.startswith(str(user_id)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            file_path = StorageService.get_upload_dir() / storage_path
            
            if not file_path.exists():
                return False
            
            file_path.unlink()  # Delete file
            
            # Clean up empty directories
            StorageService._cleanup_empty_dirs(file_path.parent)
            
            return True
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete file: {str(e)}"
            )
    
    @staticmethod
    def _cleanup_empty_dirs(path: Path) -> None:
        """Recursively remove empty directories."""
        try:
            while path != StorageService.get_upload_dir() and path.exists():
                if not any(path.iterdir()):  # Empty directory
                    path.rmdir()
                    path = path.parent
                else:
                    break
        except Exception:
            pass  # Ignore cleanup errors
    
    @staticmethod
    def get_file_size(storage_path: str) -> int:
        """Get file size in bytes."""
        file_path = StorageService.get_upload_dir() / storage_path
        if file_path.exists():
            return file_path.stat().st_size
        return 0
