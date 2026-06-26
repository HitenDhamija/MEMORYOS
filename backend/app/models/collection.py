"""
Collection model for Phase 7 Smart Collections.
"""

from datetime import datetime
import pytz
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.models import User, Memory


class Collection(Base):
    """User collection - groups related memories."""
    
    __tablename__ = "collections"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    color = Column(String(50), default="blue")  # For UI display
    icon = Column(String(50), default="folder")
    
    # Status
    is_deleted = Column(Boolean, default=False, index=True)
    is_archived = Column(Boolean, default=False, index=True)
    is_favorite = Column(Boolean, default=False, index=True)
    is_pinned = Column(Boolean, default=False, index=True)
    
    # Optional cover image
    cover_image_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), onupdate=lambda: datetime.now(pytz.UTC), nullable=False)
    
    # Relationships
    user = relationship("User", backref="collections")
    memories = relationship(
        "CollectionMembership",
        back_populates="collection",
        cascade="all, delete-orphan"
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "icon": self.icon,
            "is_archived": self.is_archived,
            "is_favorite": self.is_favorite,
            "is_pinned": self.is_pinned,
            "cover_image_url": self.cover_image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "memory_count": len(self.memories) if self.memories else 0,
        }


class CollectionMembership(Base):
    """Many-to-many relationship between collections and memories."""
    
    __tablename__ = "collection_memberships"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=False, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    added_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), nullable=False)
    
    # Relationships
    collection = relationship("Collection", back_populates="memories")
    memory = relationship("Memory")
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "collection_id": self.collection_id,
            "memory_id": self.memory_id,
            "added_at": self.added_at.isoformat() if self.added_at else None,
        }


class CollectionSuggestion(Base):
    """Auto-generated collection suggestions for users."""
    
    __tablename__ = "collection_suggestions"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Suggestion data
    suggested_name = Column(String(255), nullable=False)
    reasoning = Column(Text)
    topics = Column(String(500))  # Comma-separated topics
    confidence_score = Column(Integer, default=0)  # 0-100 confidence
    
    # Status
    status = Column(String(20), default="pending", index=True)  # pending, accepted, rejected
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), nullable=False)
    reviewed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "suggested_name": self.suggested_name,
            "reasoning": self.reasoning,
            "topics": self.topics.split(",") if self.topics else [],
            "confidence_score": self.confidence_score,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserContext(Base):
    """Tracks user behavior and interests for recommendations."""
    
    __tablename__ = "user_context"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Context data (stored as comma-separated strings for simplicity)
    frequently_used_topics = Column(String(1000))  # Top 20 topics
    recent_interests = Column(String(500))  # Recent search/view topics
    favorite_collections = Column(String(500))  # Top collection IDs
    
    # Statistics
    total_memories = Column(Integer, default=0)
    total_collections = Column(Integer, default=0)
    last_upload_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), onupdate=lambda: datetime.now(pytz.UTC), nullable=False)
    
    # Relationships
    user = relationship("User", backref="context", uselist=False)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "frequently_used_topics": self.frequently_used_topics.split(",") if self.frequently_used_topics else [],
            "recent_interests": self.recent_interests.split(",") if self.recent_interests else [],
            "favorite_collections": self.favorite_collections.split(",") if self.favorite_collections else [],
            "total_memories": self.total_memories,
            "total_collections": self.total_collections,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
