"""
Learning streak, knowledge evolution, and forgotten memory services for Phase 8.
"""

from datetime import datetime, timedelta
import pytz
from typing import List, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.timeline import TimelineEvent, LearningStreak, KnowledgeEvolution
from app.models.models import Memory
from app.models.collection import Collection


class LearningStreakService:
    """Track and update learning streaks."""
    
    @staticmethod
    def get_or_create_streak(db: Session, user_id: int) -> LearningStreak:
        """Get or create streak tracker for user."""
        streak = db.query(LearningStreak).filter(LearningStreak.user_id == user_id).first()
        
        if not streak:
            streak = LearningStreak(user_id=user_id)
            db.add(streak)
            db.commit()
            db.refresh(streak)
        
        return streak
    
    @staticmethod
    def update_streak(db: Session, user_id: int) -> LearningStreak:
        """Update streak based on activity. Called after each user action."""
        streak = LearningStreakService.get_or_create_streak(db, user_id)
        now = datetime.now(pytz.UTC)
        
        # Check if user had activity today
        if streak.last_activity_date:
            last_activity = streak.last_activity_date
            days_since = (now.date() - last_activity.date()).days
            
            if days_since == 0:
                # Activity today, streak continues
                pass
            elif days_since == 1:
                # Activity yesterday, extend streak
                streak.current_streak += 1
            else:
                # Gap in activity, reset streak
                streak.current_streak = 1
                streak.streak_start_date = now
        else:
            # First activity
            streak.current_streak = 1
            streak.streak_start_date = now
        
        # Update longest streak
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        
        # Update last activity
        streak.last_activity_date = now
        
        db.commit()
        db.refresh(streak)
        return streak
    
    @staticmethod
    def get_stats(db: Session, user_id: int) -> dict:
        """Get learning streak stats."""
        streak = LearningStreakService.get_or_create_streak(db, user_id)
        
        # Count activities
        upload_count = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == "upload"
            )
        ).scalar() or 0
        
        search_count = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == "search"
            )
        ).scalar() or 0
        
        collection_created_count = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == "collection_created"
            )
        ).scalar() or 0
        
        return {
            "current_streak": streak.current_streak,
            "longest_streak": streak.longest_streak,
            "total_uploads": upload_count,
            "total_searches": search_count,
            "total_collections_created": collection_created_count,
            "last_activity_date": streak.last_activity_date.isoformat() if streak.last_activity_date else None,
            "streak_start_date": streak.streak_start_date.isoformat() if streak.streak_start_date else None,
        }


class KnowledgeEvolutionService:
    """Track how knowledge evolves over time."""
    
    @staticmethod
    def extract_topics_for_period(db: Session, user_id: int, year: int, month: int) -> List[str]:
        """Extract topics for a specific period."""
        start = datetime(year, month, 1, tzinfo=pytz.UTC)
        if month == 12:
            end = datetime(year + 1, 1, 1, tzinfo=pytz.UTC)
        else:
            end = datetime(year, month + 1, 1, tzinfo=pytz.UTC)
        
        # Get all memories uploaded in this period
        from app.models.processed_document import ProcessedDocument
        
        memories = db.query(Memory).filter(
            and_(
                Memory.user_id == user_id,
                Memory.upload_date >= start,
                Memory.upload_date < end
            )
        ).all()
        
        topics = set()
        for memory in memories:
            # Get processed document for this memory
            proc_doc = db.query(ProcessedDocument).filter(
                ProcessedDocument.memory_id == memory.id
            ).first()
            
            if proc_doc and proc_doc.topics:
                try:
                    import json
                    data = proc_doc.topics if isinstance(proc_doc.topics, dict) else json.loads(proc_doc.topics)
                    if isinstance(data, dict):
                        for key in ["technologies", "general"]:
                            if key in data and isinstance(data[key], list):
                                for item in data[key]:
                                    if isinstance(item, str):
                                        topics.add(item)
                                    elif isinstance(item, dict) and "name" in item:
                                        topics.add(item["name"])
                except:
                    pass
        
        return sorted(list(topics))
    
    @staticmethod
    def update_evolution(db: Session, user_id: int) -> KnowledgeEvolution:
        """Update knowledge evolution for current month."""
        now = datetime.now(pytz.UTC)
        period_str = now.strftime("%Y-%m")
        
        # Get or create evolution record
        evolution = db.query(KnowledgeEvolution).filter(
            and_(
                KnowledgeEvolution.user_id == user_id,
                KnowledgeEvolution.period == period_str
            )
        ).first()
        
        if not evolution:
            evolution = KnowledgeEvolution(user_id=user_id, period=period_str)
            db.add(evolution)
        
        # Extract topics
        topics = KnowledgeEvolutionService.extract_topics_for_period(
            db,
            user_id,
            now.year,
            now.month
        )
        evolution.topics = ",".join(topics) if topics else None
        
        # Count activities this month
        start = datetime(now.year, now.month, 1, tzinfo=pytz.UTC)
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1, tzinfo=pytz.UTC)
        else:
            end = datetime(now.year, now.month + 1, 1, tzinfo=pytz.UTC)
        
        evolution.memory_count = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == "upload",
                TimelineEvent.event_date >= start,
                TimelineEvent.event_date < end
            )
        ).scalar() or 0
        
        evolution.search_count = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == "search",
                TimelineEvent.event_date >= start,
                TimelineEvent.event_date < end
            )
        ).scalar() or 0
        
        evolution.collection_count = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == "collection_created",
                TimelineEvent.event_date >= start,
                TimelineEvent.event_date < end
            )
        ).scalar() or 0
        
        evolution.discovery_count = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == "discovery",
                TimelineEvent.event_date >= start,
                TimelineEvent.event_date < end
            )
        ).scalar() or 0
        
        db.commit()
        db.refresh(evolution)
        return evolution
    
    @staticmethod
    def get_evolution_timeline(db: Session, user_id: int, months: int = 12) -> List[dict]:
        """Get knowledge evolution over past N months."""
        now = datetime.now(pytz.UTC)
        evolution_records = []
        
        for i in range(months):
            past_date = now - timedelta(days=30 * i)
            period_str = past_date.strftime("%Y-%m")
            
            evo = db.query(KnowledgeEvolution).filter(
                and_(
                    KnowledgeEvolution.user_id == user_id,
                    KnowledgeEvolution.period == period_str
                )
            ).first()
            
            if evo:
                evolution_records.append(evo.to_dict())
        
        return sorted(evolution_records, key=lambda x: x["period"])


class ForgottenMemoryService:
    """Detect memories not accessed recently."""
    
    @staticmethod
    def get_forgotten_memories(
        db: Session,
        user_id: int,
        days: int = 30
    ) -> List[Memory]:
        """Get memories not viewed in specified days."""
        cutoff = datetime.now(pytz.UTC) - timedelta(days=days)
        
        # Find memories without recent view events
        recently_viewed_ids = db.query(TimelineEvent.memory_id).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == "memory_viewed",
                TimelineEvent.event_date >= cutoff
            )
        ).distinct().all()
        
        recently_viewed_ids = [r[0] for r in recently_viewed_ids]
        
        # Get memories not in recently viewed
        forgotten = db.query(Memory).filter(
            and_(
                Memory.user_id == user_id,
                Memory.id.notin_(recently_viewed_ids) if recently_viewed_ids else True
            )
        ).order_by(Memory.upload_date.desc()).all()
        
        return forgotten
    
    @staticmethod
    def get_forgotten_by_threshold(db: Session, user_id: int) -> dict:
        """Get forgotten memories grouped by how long they've been unviewed."""
        return {
            "thirty_days": len(ForgottenMemoryService.get_forgotten_memories(db, user_id, 30)),
            "sixty_days": len(ForgottenMemoryService.get_forgotten_memories(db, user_id, 60)),
            "ninety_days": len(ForgottenMemoryService.get_forgotten_memories(db, user_id, 90)),
        }
