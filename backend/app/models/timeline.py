"""
Timeline and Knowledge Evolution models for Phase 8.
"""

from datetime import datetime
import pytz
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.models import User, Memory


class TimelineEvent(Base):
    """Tracks user activity for timeline visualization."""
    
    __tablename__ = "timeline_events"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    memory_id = Column(Integer, ForeignKey("memories.id"), nullable=True, index=True)
    collection_id = Column(Integer, ForeignKey("collections.id"), nullable=True, index=True)
    
    # Event type: upload, discovery, collection_created, search, collection_updated, memory_viewed
    event_type = Column(String(50), nullable=False, index=True)
    
    # Event details
    event_data = Column(Text)  # JSON-encoded data (topics, keywords, etc)
    
    # Timestamps
    event_date = Column(DateTime, nullable=False, index=True)  # When event occurred (may differ from created_at)
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), nullable=False)
    
    # Relationships
    user = relationship("User")
    memory = relationship("Memory")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "memory_id": self.memory_id,
            "collection_id": self.collection_id,
            "event_type": self.event_type,
            "event_data": self.event_data,
            "event_date": self.event_date.isoformat() if self.event_date else None,
        }


class Milestone(Base):
    """Auto-generated learning milestones."""
    
    __tablename__ = "milestones"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Milestones (bitmask for tracking completion)
    first_upload = Column(Boolean, default=False)
    memories_50 = Column(Boolean, default=False)
    memories_100 = Column(Boolean, default=False)
    memories_500 = Column(Boolean, default=False)
    collections_5 = Column(Boolean, default=False)
    collections_10 = Column(Boolean, default=False)
    searches_50 = Column(Boolean, default=False)
    searches_100 = Column(Boolean, default=False)
    
    # Timestamps for each milestone
    first_upload_date = Column(DateTime)
    memories_50_date = Column(DateTime)
    memories_100_date = Column(DateTime)
    memories_500_date = Column(DateTime)
    collections_5_date = Column(DateTime)
    collections_10_date = Column(DateTime)
    searches_50_date = Column(DateTime)
    searches_100_date = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), onupdate=lambda: datetime.now(pytz.UTC), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        milestones = {
            "first_upload": self.first_upload,
            "memories_50": self.memories_50,
            "memories_100": self.memories_100,
            "memories_500": self.memories_500,
            "collections_5": self.collections_5,
            "collections_10": self.collections_10,
            "searches_50": self.searches_50,
            "searches_100": self.searches_100,
        }
        dates = {
            "first_upload_date": self.first_upload_date.isoformat() if self.first_upload_date else None,
            "memories_50_date": self.memories_50_date.isoformat() if self.memories_50_date else None,
            "memories_100_date": self.memories_100_date.isoformat() if self.memories_100_date else None,
            "memories_500_date": self.memories_500_date.isoformat() if self.memories_500_date else None,
            "collections_5_date": self.collections_5_date.isoformat() if self.collections_5_date else None,
            "collections_10_date": self.collections_10_date.isoformat() if self.collections_10_date else None,
            "searches_50_date": self.searches_50_date.isoformat() if self.searches_50_date else None,
            "searches_100_date": self.searches_100_date.isoformat() if self.searches_100_date else None,
        }
        return {**milestones, **dates}


class LearningStreak(Base):
    """Tracks user learning activity streaks."""
    
    __tablename__ = "learning_streaks"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    
    # Current streak
    current_streak = Column(Integer, default=0)  # Days active
    longest_streak = Column(Integer, default=0)  # Days active
    
    # Activity counts
    total_uploads = Column(Integer, default=0)
    total_searches = Column(Integer, default=0)
    total_collections_created = Column(Integer, default=0)
    
    # Dates
    last_activity_date = Column(DateTime)  # Last time user did something
    streak_start_date = Column(DateTime)  # When current streak started
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), onupdate=lambda: datetime.now(pytz.UTC), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "total_uploads": self.total_uploads,
            "total_searches": self.total_searches,
            "total_collections_created": self.total_collections_created,
            "last_activity_date": self.last_activity_date.isoformat() if self.last_activity_date else None,
            "streak_start_date": self.streak_start_date.isoformat() if self.streak_start_date else None,
        }


class KnowledgeEvolution(Base):
    """Tracks how user's knowledge/interests evolve over time."""
    
    __tablename__ = "knowledge_evolution"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Time period (YYYY-MM for monthly aggregation)
    period = Column(String(10), nullable=False, index=True)  # e.g., "2026-06"
    
    # Topics in this period (comma-separated)
    topics = Column(String(1000))
    
    # Activity stats
    memory_count = Column(Integer, default=0)
    search_count = Column(Integer, default=0)
    collection_count = Column(Integer, default=0)
    discovery_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.UTC), onupdate=lambda: datetime.now(pytz.UTC), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "period": self.period,
            "topics": self.topics.split(",") if self.topics else [],
            "memory_count": self.memory_count,
            "search_count": self.search_count,
            "collection_count": self.collection_count,
            "discovery_count": self.discovery_count,
        }
