"""
User context engine for Phase 7 personalization.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
from collections import Counter
import pytz
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Memory
from app.models.processed_document import ProcessedDocument
from app.models.collection import Collection, CollectionMembership, UserContext

logger = logging.getLogger(__name__)


class ContextEngine:
    """Builds and manages user context for personalized recommendations."""
    
    @staticmethod
    def get_or_create_context(
        db: Session,
        user_id: int
    ) -> UserContext:
        """Get or create user context."""
        context = db.query(UserContext).filter(
            UserContext.user_id == user_id
        ).first()
        
        if not context:
            context = UserContext(user_id=user_id)
            db.add(context)
            db.commit()
            db.refresh(context)
        
        return context
    
    @staticmethod
    def update_context(
        db: Session,
        user_id: int
    ) -> Optional[UserContext]:
        """Recalculate and update user context."""
        try:
            context = ContextEngine.get_or_create_context(db, user_id)
            
            # Get frequently used topics
            proc_docs = db.query(ProcessedDocument).join(
                Memory,
                ProcessedDocument.memory_id == Memory.id
            ).filter(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            ).all()
            
            all_topics = []
            for doc in proc_docs:
                if doc.topics:
                    tech_topics = doc.topics.get("technologies", [])
                    for topic in tech_topics[:3]:
                        if isinstance(topic, dict):
                            all_topics.append(topic.get("name", ""))
                        else:
                            all_topics.append(str(topic))
            
            # Top 20 topics
            if all_topics:
                topic_counts = Counter(all_topics)
                top_topics = [t for t, _ in topic_counts.most_common(20)]
                context.frequently_used_topics = ",".join(top_topics)
            
            # Recent interests (last 5 topics from newest documents)
            recent_docs = proc_docs[-5:] if len(proc_docs) > 5 else proc_docs
            recent_topics = []
            for doc in reversed(recent_docs):
                if doc.topics:
                    tech_topics = doc.topics.get("technologies", [])
                    for topic in tech_topics[:2]:
                        if isinstance(topic, dict):
                            topic_name = topic.get("name", "")
                        else:
                            topic_name = str(topic)
                        if topic_name not in recent_topics:
                            recent_topics.append(topic_name)
            
            if recent_topics:
                context.recent_interests = ",".join(recent_topics[:10])
            
            # Favorite collections
            collections = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.is_deleted == False
            ).all()
            
            collection_sizes = []
            for coll in collections:
                size = db.query(func.count(CollectionMembership.id)).filter(
                    CollectionMembership.collection_id == coll.id
                ).scalar()
                collection_sizes.append((str(coll.id), size))
            
            # Top 5 collections by size
            if collection_sizes:
                favorite_ids = [c_id for c_id, _ in sorted(
                    collection_sizes,
                    key=lambda x: x[1],
                    reverse=True
                )[:5]]
                context.favorite_collections = ",".join(favorite_ids)
            
            # Stats
            context.total_memories = db.query(func.count(Memory.id)).filter(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            ).scalar()
            
            context.total_collections = len(collections)
            
            # Last upload
            last_memory = db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            ).order_by(Memory.upload_date.desc()).first()
            
            if last_memory:
                context.last_upload_date = last_memory.upload_date
            
            context.updated_at = datetime.now(pytz.UTC)
            db.commit()
            db.refresh(context)
            
            logger.info(f"Updated context for user {user_id}")
            return context
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update context: {e}")
            return None
    
    @staticmethod
    def get_user_interests(
        db: Session,
        user_id: int
    ) -> Dict[str, list]:
        """Get user's interests and preferences."""
        context = ContextEngine.get_or_create_context(db, user_id)
        
        return {
            "frequently_used_topics": context.frequently_used_topics.split(",") if context.frequently_used_topics else [],
            "recent_interests": context.recent_interests.split(",") if context.recent_interests else [],
            "favorite_collections": context.favorite_collections.split(",") if context.favorite_collections else []
        }
    
    @staticmethod
    def track_search_query(
        db: Session,
        user_id: int,
        query: str
    ) -> None:
        """Track user's search query to update recent interests."""
        try:
            context = ContextEngine.get_or_create_context(db, user_id)
            
            # Extract keywords from query (simple approach)
            keywords = query.lower().split()
            keywords = [k for k in keywords if len(k) > 2]
            
            if not keywords:
                return
            
            # Update recent interests
            current_interests = context.recent_interests.split(",") if context.recent_interests else []
            
            for keyword in keywords:
                if keyword not in current_interests:
                    current_interests.insert(0, keyword)
            
            context.recent_interests = ",".join(current_interests[:10])
            context.updated_at = datetime.now(pytz.UTC)
            db.commit()
            
            logger.debug(f"Tracked search query for user {user_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to track search query: {e}")
    
    @staticmethod
    def track_collection_access(
        db: Session,
        user_id: int,
        collection_id: int
    ) -> None:
        """Track user's collection access for personalization."""
        try:
            context = ContextEngine.get_or_create_context(db, user_id)
            
            # Update favorite collections based on access
            favorites = context.favorite_collections.split(",") if context.favorite_collections else []
            favorites = [f for f in favorites if f.strip()]
            
            collection_str = str(collection_id)
            
            # Move to front if already exists
            if collection_str in favorites:
                favorites.remove(collection_str)
            
            favorites.insert(0, collection_str)
            
            # Keep only top 5
            context.favorite_collections = ",".join(favorites[:5])
            context.updated_at = datetime.now(pytz.UTC)
            db.commit()
            
            logger.debug(f"Tracked collection access for user {user_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to track collection access: {e}")
    
    @staticmethod
    def get_context_stats(
        db: Session,
        user_id: int
    ) -> Dict:
        """Get context statistics for user."""
        try:
            context = ContextEngine.get_or_create_context(db, user_id)
            
            return {
                "total_memories": context.total_memories,
                "total_collections": context.total_collections,
                "last_upload": context.last_upload_date.isoformat() if context.last_upload_date else None,
                "interests_count": len([i for i in context.frequently_used_topics.split(",") if i.strip()]) if context.frequently_used_topics else 0,
                "favorite_collections_count": len([c for c in context.favorite_collections.split(",") if c.strip()]) if context.favorite_collections else 0
            }
        except Exception as e:
            logger.error(f"Failed to get context stats: {e}")
            return {}
