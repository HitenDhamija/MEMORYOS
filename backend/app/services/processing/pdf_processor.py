"""
PDF Processor

Processes PDF files using PyPDF2.
Extracts text, metadata, and structure.
"""

import os
from typing import Dict, List
from app.services.processing.base import DocumentProcessor

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PDFProcessor(DocumentProcessor):
    """Process PDF files."""
    
    def can_process(self) -> bool:
        """Check if file exists and is readable PDF."""
        if not PDF_AVAILABLE:
            return False
        try:
            return (
                os.path.exists(self.file_path) and
                os.path.isfile(self.file_path) and
                self.file_path.lower().endswith('.pdf')
            )
        except Exception:
            return False
    
    def extract_text(self) -> str:
        """
        Extract text from all pages of PDF.
        """
        try:
            text_parts = []
            with open(self.file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Extract from each page
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            
            return '\n'.join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_metadata(self) -> Dict[str, any]:
        """Extract PDF metadata."""
        try:
            metadata = {
                "filename": self.original_filename,
                "file_size_bytes": os.path.getsize(self.file_path),
            }
            
            with open(self.file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                # Page count
                metadata["page_count"] = len(pdf_reader.pages)
                
                # PDF document info
                if pdf_reader.metadata:
                    info = pdf_reader.metadata
                    if info.title:
                        metadata["title"] = info.title
                    if info.author:
                        metadata["author"] = info.author
                    if info.subject:
                        metadata["subject"] = info.subject
                    if info.creator:
                        metadata["creator"] = info.creator
                    if info.producer:
                        metadata["producer"] = info.producer
            
            return metadata
        except Exception as e:
            return {"filename": self.original_filename, "error": str(e)}
    
    def extract_structure(self) -> Dict[str, any]:
        """
        Extract PDF structure.
        Includes page breaks and basic layout info.
        """
        try:
            with open(self.file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                
                pages_info = []
                for page_num, page in enumerate(pdf_reader.pages):
                    page_info = {
                        "page_number": page_num + 1,
                        "text_length": len(page.extract_text() or ""),
                        "rotation": page.get("/Rotate", 0)
                    }
                    pages_info.append(page_info)
                
                return {
                    "total_pages": len(pdf_reader.pages),
                    "pages": pages_info,
                    "is_encrypted": pdf_reader.is_encrypted
                }
        except Exception:
            return {"total_pages": 0, "pages": []}
