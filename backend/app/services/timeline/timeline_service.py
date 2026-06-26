"""
Timeline tracking service for Phase 8.
"""

from datetime import datetime, timedelta
import pytz
import json
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.timeline import TimelineEvent, Milestone, LearningStreak, KnowledgeEvolution
from app.models.models import Memory
from app.models.collection import Collection, CollectionMembership
from app.models.processed_document import ProcessedDocument


class TimelineService:
    """Track and retrieve timeline events."""
    
    @staticmethod
    def create_event(
        db: Session,
        user_id: int,
        event_type: str,
        event_date: Optional[datetime] = None,
        memory_id: Optional[int] = None,
        collection_id: Optional[int] = None,
        event_data: Optional[dict] = None
    ) -> TimelineEvent:
        """Create a timeline event."""
        if event_date is None:
            event_date = datetime.now(pytz.UTC)
        
        event = TimelineEvent(
            user_id=user_id,
            memory_id=memory_id,
            collection_id=collection_id,
            event_type=event_type,
            event_date=event_date,
            event_data=json.dumps(event_data) if event_data else None
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event
    
    @staticmethod
    def get_timeline(
        db: Session,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_types: Optional[List[str]] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[TimelineEvent]:
        """Get timeline events for a user."""
        query = db.query(TimelineEvent).filter(TimelineEvent.user_id == user_id)
        
        if start_date:
            query = query.filter(TimelineEvent.event_date >= start_date)
        if end_date:
            query = query.filter(TimelineEvent.event_date <= end_date)
        if event_types:
            query = query.filter(TimelineEvent.event_type.in_(event_types))
        
        return query.order_by(TimelineEvent.event_date.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_memory_timeline(db: Session, memory_id: int, user_id: int) -> List[TimelineEvent]:
        """Get all events related to a specific memory."""
        return db.query(TimelineEvent).filter(
            and_(
                TimelineEvent.memory_id == memory_id,
                TimelineEvent.user_id == user_id
            )
        ).order_by(TimelineEvent.event_date.desc()).all()
    
    @staticmethod
    def get_events_by_day(
        db: Session,
        user_id: int,
        date: datetime
    ) -> List[TimelineEvent]:
        """Get all events for a specific day."""
        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        return TimelineService.get_timeline(
            db,
            user_id,
            start_date=start,
            end_date=end
        )
    
    @staticmethod
    def get_events_by_month(
        db: Session,
        user_id: int,
        year: int,
        month: int
    ) -> List[TimelineEvent]:
        """Get all events for a specific month."""
        start = datetime(year, month, 1, tzinfo=pytz.UTC)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=pytz.UTC)
        else:
            end = datetime(year, month + 1, 1, tzinfo=pytz.UTC)
        
        return TimelineService.get_timeline(
            db,
            user_id,
            start_date=start,
            end_date=end
        )
    
    @staticmethod
    def group_events_by_period(
        db: Session,
        user_id: int,
        period: str = "month"  # day, week, month, year
    ) -> Dict:
        """Group timeline events by time period."""
        events = db.query(TimelineEvent).filter(
            TimelineEvent.user_id == user_id
        ).order_by(TimelineEvent.event_date.desc()).all()
        
        grouped = {}
        
        for event in events:
            if period == "day":
                key = event.event_date.strftime("%Y-%m-%d")
            elif period == "week":
                week_start = event.event_date - timedelta(days=event.event_date.weekday())
                key = week_start.strftime("%Y-W%U")
            elif period == "month":
                key = event.event_date.strftime("%Y-%m")
            elif period == "year":
                key = event.event_date.strftime("%Y")
            else:
                key = event.event_date.strftime("%Y-%m")
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(event.to_dict())
        
        return grouped
    
    @staticmethod
    def clear_old_events(db: Session, user_id: int, days: int = 730) -> int:
        """Delete timeline events older than specified days (soft archive)."""
        cutoff = datetime.now(pytz.UTC) - timedelta(days=days)
        deleted = db.query(TimelineEvent).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_date < cutoff
            )
        ).delete()
        db.commit()
        return deleted
