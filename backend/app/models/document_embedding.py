"""
DocumentEmbedding Model

Stores vector embeddings for processed documents.
Links ProcessedDocument to ChromaDB vectors.
Enables semantic search and similarity detection.

Separate from ProcessedDocument to keep concerns isolated:
- ProcessedDocument: Text extraction and analysis
- DocumentEmbedding: Vector representation and search
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, func
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz

from app.db.session import Base


class DocumentEmbedding(Base):
    """
    Stores vector embeddings and related metadata.
    
    Links ProcessedDocument to ChromaDB vectors.
    Enables semantic search via similarity.
    
    Embedding statuses:
    - pending: Created but not yet embedded
    - generating: Currently generating embedding
    - generated: Successfully created vector
    - failed: Embedding generation failed
    """
    
    __tablename__ = "document_embeddings"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys for data isolation and relationship
    processed_document_id = Column(
        Integer,
        ForeignKey("processed_documents.id"),
        nullable=False,
        unique=True,
        index=True
    )
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Vector reference
    vector_id = Column(String(255), nullable=True, index=True)  # ChromaDB collection id
    
    # Embedding metadata
    model_name = Column(String(100), nullable=False)  # e.g., "all-MiniLM-L6-v2"
    model_version = Column(String(50), default="1.0")  # Model version for versioning
    embedding_dimension = Column(Integer, nullable=False)  # e.g., 384 for MiniLM
    
    # Embedding statistics
    text_length = Column(Integer, default=0)  # Length of text that was embedded
    chunk_count = Column(Integer, default=0)  # Number of chunks if text was split
    
    # Processing status
    embedding_status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True
    )
    # Possible values: pending, generating, generated, failed
    
    embedding_error = Column(String(500), nullable=True)  # Error message if failed
    
    # Flags
    is_current = Column(Boolean, default=True, index=True)  # Latest version
    skip_reason = Column(String(200), nullable=True)  # Why embedding was skipped
    
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
    embedded_at = Column(DateTime, nullable=True)  # When embedding was created
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "processed_document_id": self.processed_document_id,
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "vector_id": self.vector_id,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "embedding_dimension": self.embedding_dimension,
            "text_length": self.text_length,
            "chunk_count": self.chunk_count,
            "embedding_status": self.embedding_status,
            "embedding_error": self.embedding_error,
            "is_current": self.is_current,
            "skip_reason": self.skip_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "embedded_at": self.embedded_at.isoformat() if self.embedded_at else None,
        }
    
    def __repr__(self):
        return f"<DocumentEmbedding id={self.id} status={self.embedding_status} model={self.model_name}>"
