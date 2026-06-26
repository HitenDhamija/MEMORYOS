"""
Milestone detection and tracking service for Phase 8.
"""

from datetime import datetime
import pytz
from typing import Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.timeline import Milestone
from app.models.models import Memory
from app.models.collection import Collection, CollectionMembership
from app.models.processed_document import ProcessedDocument


class MilestoneService:
    """Detect and track learning milestones."""
    
    @staticmethod
    def get_or_create_milestones(db: Session, user_id: int) -> Milestone:
        """Get or create milestone tracker for user."""
        milestone = db.query(Milestone).filter(Milestone.user_id == user_id).first()
        
        if not milestone:
            milestone = Milestone(user_id=user_id)
            db.add(milestone)
            db.commit()
            db.refresh(milestone)
        
        return milestone
    
    @staticmethod
    def check_milestones(db: Session, user_id: int) -> Tuple[Milestone, list]:
        """Check and update milestones for user. Returns updated milestone and list of new milestones."""
        milestone = MilestoneService.get_or_create_milestones(db, user_id)
        new_milestones = []
        
        # Count memories
        memory_count = db.query(func.count(Memory.id)).filter(Memory.user_id == user_id).scalar() or 0
        
        # Count collections
        collection_count = db.query(func.count(Collection.id)).filter(
            Collection.user_id == user_id,
            Collection.is_deleted == False
        ).scalar() or 0
        
        # Count searches (from timeline events)
        from app.models.timeline import TimelineEvent
        search_count = db.query(func.count(TimelineEvent.id)).filter(
            TimelineEvent.user_id == user_id,
            TimelineEvent.event_type == "search"
        ).scalar() or 0
        
        # Check first upload
        if memory_count > 0 and not milestone.first_upload:
            milestone.first_upload = True
            milestone.first_upload_date = datetime.now(pytz.UTC)
            new_milestones.append("first_upload")
        
        # Check memory milestones
        if memory_count >= 50 and not milestone.memories_50:
            milestone.memories_50 = True
            milestone.memories_50_date = datetime.now(pytz.UTC)
            new_milestones.append("memories_50")
        
        if memory_count >= 100 and not milestone.memories_100:
            milestone.memories_100 = True
            milestone.memories_100_date = datetime.now(pytz.UTC)
            new_milestones.append("memories_100")
        
        if memory_count >= 500 and not milestone.memories_500:
            milestone.memories_500 = True
            milestone.memories_500_date = datetime.now(pytz.UTC)
            new_milestones.append("memories_500")
        
        # Check collection milestones
        if collection_count >= 5 and not milestone.collections_5:
            milestone.collections_5 = True
            milestone.collections_5_date = datetime.now(pytz.UTC)
            new_milestones.append("collections_5")
        
        if collection_count >= 10 and not milestone.collections_10:
            milestone.collections_10 = True
            milestone.collections_10_date = datetime.now(pytz.UTC)
            new_milestones.append("collections_10")
        
        # Check search milestones
        if search_count >= 50 and not milestone.searches_50:
            milestone.searches_50 = True
            milestone.searches_50_date = datetime.now(pytz.UTC)
            new_milestones.append("searches_50")
        
        if search_count >= 100 and not milestone.searches_100:
            milestone.searches_100 = True
            milestone.searches_100_date = datetime.now(pytz.UTC)
            new_milestones.append("searches_100")
        
        if new_milestones:
            db.commit()
            db.refresh(milestone)
        
        return milestone, new_milestones
    
    @staticmethod
    def get_achievements(db: Session, user_id: int) -> dict:
        """Get list of unlocked achievements."""
        milestone, _ = MilestoneService.check_milestones(db, user_id)
        
        achievements = {
            "unlocked": [],
            "progress": {}
        }
        
        # Add unlocked achievements
        if milestone.first_upload:
            achievements["unlocked"].append({"id": "first_upload", "name": "First Upload", "date": milestone.first_upload_date.isoformat() if milestone.first_upload_date else ""})
        
        if milestone.memories_50:
            achievements["unlocked"].append({"id": "memories_50", "name": "50 Memories", "date": milestone.memories_50_date.isoformat() if milestone.memories_50_date else ""})
        
        if milestone.memories_100:
            achievements["unlocked"].append({"id": "memories_100", "name": "100 Memories", "date": milestone.memories_100_date.isoformat() if milestone.memories_100_date else ""})
        
        if milestone.memories_500:
            achievements["unlocked"].append({"id": "memories_500", "name": "500 Memories", "date": milestone.memories_500_date.isoformat() if milestone.memories_500_date else ""})
        
        if milestone.collections_5:
            achievements["unlocked"].append({"id": "collections_5", "name": "5 Collections", "date": milestone.collections_5_date.isoformat() if milestone.collections_5_date else ""})
        
        if milestone.collections_10:
            achievements["unlocked"].append({"id": "collections_10", "name": "10 Collections", "date": milestone.collections_10_date.isoformat() if milestone.collections_10_date else ""})
        
        if milestone.searches_50:
            achievements["unlocked"].append({"id": "searches_50", "name": "50 Searches", "date": milestone.searches_50_date.isoformat() if milestone.searches_50_date else ""})
        
        if milestone.searches_100:
            achievements["unlocked"].append({"id": "searches_100", "name": "100 Searches", "date": milestone.searches_100_date.isoformat() if milestone.searches_100_date else ""})
        
        # Get progress stats
        memory_count = db.query(func.count(Memory.id)).filter(Memory.user_id == user_id).scalar() or 0
        collection_count = db.query(func.count(Collection.id)).filter(
            Collection.user_id == user_id,
            Collection.is_deleted == False
        ).scalar() or 0
        
        from app.models.timeline import TimelineEvent
        search_count = db.query(func.count(TimelineEvent.id)).filter(
            TimelineEvent.user_id == user_id,
            TimelineEvent.event_type == "search"
        ).scalar() or 0
        
        achievements["progress"] = {
            "memories": {"current": memory_count, "targets": [50, 100, 500]},
            "collections": {"current": collection_count, "targets": [5, 10]},
            "searches": {"current": search_count, "targets": [50, 100]}
        }
        
        return achievements
