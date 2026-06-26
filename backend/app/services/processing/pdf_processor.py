"""
PDF Processor

Processes PDF files using PyMuPDF (primary) and PyPDF2 (fallback).
Extracts text, metadata, and structure.
"""

import os
import logging
from typing import Dict
from app.services.processing.base import DocumentProcessor

logger = logging.getLogger(__name__)

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False


class PDFProcessor(DocumentProcessor):
    """Process PDF files using PyMuPDF (primary) with PyPDF2 fallback."""

    def can_process(self) -> bool:
        """Check if file exists and is readable PDF."""
        if not PYMUPDF_AVAILABLE and not PYPDF2_AVAILABLE:
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
        """Extract text from all pages of PDF, with fallback."""
        # Try PyMuPDF first (better extraction)
        if PYMUPDF_AVAILABLE:
            try:
                return self._extract_text_pymupdf()
            except Exception as e:
                logger.warning(f"PyMuPDF extraction failed for {self.original_filename}: {e}")

        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                return self._extract_text_pypdf2()
            except Exception as e:
                logger.warning(f"PyPDF2 extraction failed for {self.original_filename}: {e}")

        raise ValueError("No PDF library available for text extraction")

    def _extract_text_pymupdf(self) -> str:
        """Extract text using PyMuPDF (fitz)."""
        text_parts = []
        doc = fitz.open(self.file_path)
        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                if text and text.strip():
                    text_parts.append(text)
        finally:
            doc.close()
        return '\n'.join(text_parts)

    def _extract_text_pypdf2(self) -> str:
        """Extract text using PyPDF2 (fallback)."""
        text_parts = []
        with open(self.file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                try:
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text and text.strip():
                        text_parts.append(text)
                except Exception as e:
                    logger.debug(f"PyPDF2 failed on page {page_num}: {e}")
                    continue
        return '\n'.join(text_parts)

    def extract_metadata(self) -> Dict[str, any]:
        """Extract PDF metadata."""
        # Try PyMuPDF first
        if PYMUPDF_AVAILABLE:
            try:
                return self._extract_metadata_pymupdf()
            except Exception as e:
                logger.warning(f"PyMuPDF metadata extraction failed: {e}")

        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                return self._extract_metadata_pypdf2()
            except Exception as e:
                logger.warning(f"PyPDF2 metadata extraction failed: {e}")

        return {"filename": self.original_filename, "file_size_bytes": os.path.getsize(self.file_path)}

    def _extract_metadata_pymupdf(self) -> Dict[str, any]:
        """Extract metadata using PyMuPDF."""
        metadata = {
            "filename": self.original_filename,
            "file_size_bytes": os.path.getsize(self.file_path),
        }
        doc = fitz.open(self.file_path)
        try:
            metadata["page_count"] = len(doc)
            meta = doc.metadata
            if meta:
                if meta.get("title"):
                    metadata["title"] = meta["title"]
                if meta.get("author"):
                    metadata["author"] = meta["author"]
                if meta.get("subject"):
                    metadata["subject"] = meta["subject"]
                if meta.get("creator"):
                    metadata["creator"] = meta["creator"]
        finally:
            doc.close()
        return metadata

    def _extract_metadata_pypdf2(self) -> Dict[str, any]:
        """Extract metadata using PyPDF2."""
        metadata = {
            "filename": self.original_filename,
            "file_size_bytes": os.path.getsize(self.file_path),
        }
        with open(self.file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            metadata["page_count"] = len(pdf_reader.pages)
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
        return metadata

    def extract_structure(self) -> Dict[str, any]:
        """Extract PDF structure."""
        # Try PyMuPDF first
        if PYMUPDF_AVAILABLE:
            try:
                return self._extract_structure_pymupdf()
            except Exception as e:
                logger.warning(f"PyMuPDF structure extraction failed: {e}")

        # Fallback to PyPDF2
        if PYPDF2_AVAILABLE:
            try:
                return self._extract_structure_pypdf2()
            except Exception as e:
                logger.warning(f"PyPDF2 structure extraction failed: {e}")

        return {"total_pages": 0, "pages": []}

    def _extract_structure_pymupdf(self) -> Dict[str, any]:
        """Extract structure using PyMuPDF."""
        doc = fitz.open(self.file_path)
        try:
            pages_info = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                pages_info.append({
                    "page_number": page_num + 1,
                    "text_length": len(text or ""),
                    "rotation": page.get("/Rotate", 0) if hasattr(page, 'get') else 0
                })
            return {
                "total_pages": len(doc),
                "pages": pages_info,
                "is_encrypted": False
            }
        finally:
            doc.close()

    def _extract_structure_pypdf2(self) -> Dict[str, any]:
        """Extract structure using PyPDF2."""
        with open(self.file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pages_info = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    text = page.extract_text() or ""
                except Exception:
                    text = ""
                page_info = {
                    "page_number": page_num + 1,
                    "text_length": len(text),
                    "rotation": page.get("/Rotate", 0)
                }
                pages_info.append(page_info)
            return {
                "total_pages": len(pdf_reader.pages),
                "pages": pages_info,
                "is_encrypted": pdf_reader.is_encrypted
            }
