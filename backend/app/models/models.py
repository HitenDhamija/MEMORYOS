"""
Database models.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime, timezone
from app.db.session import Base


class User(Base):
    """User model."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))


class Memory(Base):
    """Memory/Knowledge item model - file-based storage."""
    __tablename__ = "memories"

    # Identity
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    file_id = Column(String(255), unique=True, index=True, nullable=False)  # UUID
    
    # File Information
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False, index=True)  # pdf, image, txt, md, bookmark, other
    file_size = Column(Integer, nullable=False)  # bytes
    storage_path = Column(String(1000), nullable=False)  # relative path: uploads/user_id/file_type/file_id_name
    
    # Metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(String(1000), nullable=True)  # comma-separated, "python,data,ai"
    
    # Processing Status
    is_processed = Column(Boolean, default=False, index=True)
    processing_status = Column(String(50), default="pending")  # pending, uploaded, processing, processed, failed
    processing_error = Column(Text, nullable=True)  # error message if failed
    
    # Soft Delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime, nullable=True)
