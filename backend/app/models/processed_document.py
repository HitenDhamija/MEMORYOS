"""
ProcessedDocument Model

Stores extracted and processed information from uploaded files.
Separate from Memory model to keep concerns isolated.
Links to Memory via memory_id for user isolation.
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey, Boolean, func
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

from app.db.session import Base


class ProcessedDocument(Base):
    """
    Stores extracted and processed information from uploaded memories.
    
    Separate table to keep concerns isolated:
    - Memory model: File metadata and storage
    - ProcessedDocument model: Extracted content and analysis
    
    Processing statuses:
    - pending: Created but not yet processed
    - uploaded: File stored, ready for processing
    - processing: Currently extracting content
    - processed: Successfully extracted
    - failed: Processing failed
    """
    
    __tablename__ = "processed_documents"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys for data isolation and relationship
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Extracted content
    extracted_text = Column(Text, nullable=True)  # Full text from document
    preview = Column(String(300), nullable=True)  # First 300 characters
    
    # Document statistics
    word_count = Column(Integer, default=0)
    char_count = Column(Integer, default=0)
    language = Column(String(20), default="unknown")
    reading_time = Column(Float, default=0)  # Estimated minutes
    
    # Detected information
    topics = Column(JSON, default=list)  # {"technologies": [...], "general": [...]}
    doc_metadata = Column(JSON, default=dict)  # Title, author, creation date, etc.
    document_structure = Column(JSON, default=dict)  # Headings, paragraphs, code blocks
    
    # Processing status tracking
    processing_status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True
    )
    # Possible values: pending, uploaded, processing, processed, failed
    
    processing_error = Column(Text, nullable=True)  # Error message if failed
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(pytz.UTC),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(pytz.UTC),
        onupdate=lambda: datetime.now(pytz.UTC),
        nullable=False
    )
    processed_at = Column(DateTime, nullable=True)  # When processing completed
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "extracted_text": self.extracted_text,
            "preview": self.preview,
            "word_count": self.word_count,
            "char_count": self.char_count,
            "language": self.language,
            "reading_time": round(self.reading_time, 1),
            "topics": self.topics,
            "doc_metadata": self.doc_metadata,
            "document_structure": self.document_structure,
            "processing_status": self.processing_status,
            "processing_error": self.processing_error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }
    
    def __repr__(self):
        return f"<ProcessedDocument memory_id={self.memory_id} status={self.processing_status}>"
