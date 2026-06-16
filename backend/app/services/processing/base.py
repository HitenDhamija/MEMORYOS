"""
Base Processor

Abstract base class for all document processors.
Defines the interface that all specific processors must implement.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor(ABC):
    """
    Abstract base class for document processors.
    
    Each file type (PDF, TXT, Markdown, Image, etc.) should have
    its own processor that implements this interface.
    """
    
    def __init__(self, file_path: str, original_filename: str):
        """
        Initialize processor with file path.
        
        Args:
            file_path: Path to the file on disk
            original_filename: Original filename (for metadata)
        """
        self.file_path = file_path
        self.original_filename = original_filename
    
    @abstractmethod
    def can_process(self) -> bool:
        """
        Check if this processor can handle the file.
        Implementations should verify file exists and is readable.
        
        Returns:
            True if processor can handle this file, False otherwise
        """
        pass
    
    @abstractmethod
    def extract_text(self) -> str:
        """
        Extract plain text from the document.
        
        Returns:
            Extracted text (or empty string if extraction fails)
        """
        pass
    
    @abstractmethod
    def extract_metadata(self) -> Dict[str, any]:
        """
        Extract metadata specific to this document type.
        
        Returns:
            Dictionary with metadata (title, author, creation_date, etc.)
        """
        pass
    
    @abstractmethod
    def extract_structure(self) -> Dict[str, any]:
        """
        Extract document structure (headings, paragraphs, code blocks, etc.).
        
        Returns:
            Dictionary describing document structure
        """
        pass
    
    # Optional methods that can be overridden
    
    def extract_text_safe(self) -> Tuple[str, Optional[str]]:
        """
        Safely extract text with error handling.
        
        Returns:
            Tuple of (extracted_text, error_message)
            error_message is None if successful
        """
        try:
            text = self.extract_text()
            return text, None
        except Exception as e:
            error_msg = f"Text extraction failed: {str(e)}"
            logger.error(f"{self.__class__.__name__}: {error_msg}")
            return "", error_msg
    
    def extract_metadata_safe(self) -> Tuple[Dict, Optional[str]]:
        """
        Safely extract metadata with error handling.
        
        Returns:
            Tuple of (metadata_dict, error_message)
        """
        try:
            metadata = self.extract_metadata()
            return metadata, None
        except Exception as e:
            error_msg = f"Metadata extraction failed: {str(e)}"
            logger.error(f"{self.__class__.__name__}: {error_msg}")
            return {}, error_msg
    
    def extract_structure_safe(self) -> Tuple[Dict, Optional[str]]:
        """
        Safely extract structure with error handling.
        
        Returns:
            Tuple of (structure_dict, error_message)
        """
        try:
            structure = self.extract_structure()
            return structure, None
        except Exception as e:
            error_msg = f"Structure extraction failed: {str(e)}"
            logger.error(f"{self.__class__.__name__}: {error_msg}")
            return {}, error_msg


class DummyProcessor(DocumentProcessor):
    """
    Fallback processor for unsupported file types.
    Extracts basic info without processing content.
    """
    
    def can_process(self) -> bool:
        """Always returns True as fallback."""
        return True
    
    def extract_text(self) -> str:
        """Return empty string."""
        return ""
    
    def extract_metadata(self) -> Dict[str, any]:
        """Return basic metadata."""
        return {
            "filename": self.original_filename,
            "note": "Document type not supported for content extraction"
        }
    
    def extract_structure(self) -> Dict[str, any]:
        """Return empty structure."""
        return {"headings": [], "sections": []}
