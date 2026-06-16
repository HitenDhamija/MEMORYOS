"""
Text Processor

Processes plain text files (.txt).
"""

import os
from typing import Dict
from app.services.processing.base import DocumentProcessor


class TextProcessor(DocumentProcessor):
    """Process plain text files."""
    
    def can_process(self) -> bool:
        """Check if file exists and is readable."""
        try:
            return os.path.exists(self.file_path) and os.path.isfile(self.file_path)
        except Exception:
            return False
    
    def extract_text(self) -> str:
        """
        Read and return full file content.
        Handles encoding errors gracefully.
        """
        try:
            # Try UTF-8 first (most common)
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to Latin-1 (more permissive)
            try:
                with open(self.file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                raise ValueError(f"Failed to read text file: {str(e)}")
    
    def extract_metadata(self) -> Dict[str, any]:
        """Extract file metadata."""
        try:
            file_stat = os.stat(self.file_path)
            return {
                "filename": self.original_filename,
                "file_size_bytes": file_stat.st_size,
                "created": file_stat.st_ctime,
                "modified": file_stat.st_mtime,
                "encoding": "utf-8"
            }
        except Exception as e:
            return {"filename": self.original_filename, "error": str(e)}
    
    def extract_structure(self) -> Dict[str, any]:
        """
        Analyze text structure (paragraphs, lines).
        """
        try:
            text = self.extract_text()
            
            # Split into paragraphs (separated by blank lines)
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
            
            # Count lines
            lines = text.split('\n')
            
            return {
                "paragraphs": len(paragraphs),
                "lines": len(lines),
                "first_paragraph": paragraphs[0][:100] if paragraphs else ""
            }
        except Exception:
            return {"paragraphs": 0, "lines": 0}
