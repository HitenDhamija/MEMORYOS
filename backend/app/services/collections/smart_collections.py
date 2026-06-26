"""
Smart collections service for dynamic, rule-based collections.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.models import Memory, User
from app.models.collection import Collection, CollectionMembership
from app.models.processed_document import ProcessedDocument

logger = logging.getLogger(__name__)


class SmartCollectionRule:
    """Defines a rule for smart collection membership."""
    
    def __init__(
        self,
        name: str,
        description: str,
        icon: str = "folder",
        color: str = "blue",
        filter_func=None
    ):
        self.name = name
        self.description = description
        self.icon = icon
        self.color = color
        self.filter_func = filter_func


class SmartCollections:
    """Manages smart collections - dynamic collections based on rules."""
    
    # Predefined smart collection rules
    SMART_RULES: Dict[str, SmartCollectionRule] = {
        "recent_uploads": SmartCollectionRule(
            name="Recent Uploads",
            description="Documents uploaded in the last 7 days",
            icon="clock",
            color="blue",
            filter_func=lambda m: m.upload_date >= datetime.now(pytz.UTC) - timedelta(days=7)
        ),
        "favorites": SmartCollectionRule(
            name="Favorites",
            description="Documents marked as favorites",
            icon="star",
            color="yellow",
            filter_func=lambda m: getattr(m, 'is_favorite', False)
        ),
        "research_papers": SmartCollectionRule(
            name="Research Papers",
            description="Academic papers and research documents",
            icon="book-open",
            color="purple",
            filter_func=lambda m: m.file_type in ['pdf'] and _has_research_content(m)
        ),
        "certificates": SmartCollectionRule(
            name="Certificates",
            description="Certificates and credentials",
            icon="award",
            color="green",
            filter_func=lambda m: _is_certificate(m)
        ),
        "study_material": SmartCollectionRule(
            name="Study Material",
            description="Learning resources and study guides",
            icon="graduation-cap",
            color="indigo",
            filter_func=lambda m: _is_study_material(m)
        ),
        "needs_review": SmartCollectionRule(
            name="Needs Review",
            description="Documents that need review or have issues",
            icon="alert-circle",
            color="red",
            filter_func=lambda m: m.status in ['pending', 'failed', 'error']
        ),
        "recently_opened": SmartCollectionRule(
            name="Recently Opened",
            description="Documents accessed in the last 3 days",
            icon="eye",
            color="cyan",
            filter_func=lambda m: _was_recently_accessed(m, days=3)
        ),
        "large_documents": SmartCollectionRule(
            name="Large Documents",
            description="Documents with more than 1000 words",
            icon="file-text",
            color="orange",
            filter_func=lambda m: _is_large_document(m, min_words=1000)
        ),
    }
    
    @staticmethod
    def get_smart_collections(
        db: Session,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """Get all smart collections with their memory counts."""
        try:
            memories = db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            ).all()
            
            smart_collections = []
            
            for rule_id, rule in SmartCollections.SMART_RULES.items():
                matching_memories = [
                    m for m in memories
                    if rule.filter_func(m)
                ]
                
                if matching_memories:
                    smart_collections.append({
                        "id": f"smart_{rule_id}",
                        "name": rule.name,
                        "description": rule.description,
                        "icon": rule.icon,
                        "color": rule.color,
                        "memory_count": len(matching_memories),
                        "is_smart": True,
                        "rule_id": rule_id,
                    })
            
            # Sort by memory count descending
            smart_collections.sort(key=lambda x: x["memory_count"], reverse=True)
            
            return smart_collections
        except Exception as e:
            logger.error(f"Failed to get smart collections: {e}")
            return []
    
    @staticmethod
    def get_smart_collection_memories(
        db: Session,
        user_id: int,
        rule_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Memory]:
        """Get memories matching a smart collection rule."""
        try:
            rule = SmartCollections.SMART_RULES.get(rule_id)
            if not rule:
                return []
            
            memories = db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            ).all()
            
            matching = [m for m in memories if rule.filter_func(m)]
            
            # Apply pagination
            return matching[skip:skip + limit]
        except Exception as e:
            logger.error(f"Failed to get smart collection memories: {e}")
            return []
    
    @staticmethod
    def create_collection_from_smart(
        db: Session,
        user_id: int,
        rule_id: str
    ) -> Optional[Collection]:
        """Create a real collection from a smart collection."""
        try:
            rule = SmartCollections.SMART_RULES.get(rule_id)
            if not rule:
                return None
            
            from app.services.collections.collection_service import CollectionService
            
            collection, error = CollectionService.create_collection(
                db,
                user_id,
                rule.name,
                description=rule.description,
                color=rule.color,
                icon=rule.icon
            )
            
            if error or not collection:
                return None
            
            # Add matching memories
            memories = SmartCollections.get_smart_collection_memories(db, user_id, rule_id)
            
            for memory in memories:
                CollectionService.add_memory_to_collection(
                    db,
                    collection.id,
                    memory.id,
                    user_id
                )
            
            return collection
        except Exception as e:
            logger.error(f"Failed to create collection from smart: {e}")
            return None


def _has_research_content(memory: Memory) -> bool:
    """Check if memory contains research-like content."""
    try:
        if not memory.processed_document:
            return False
        
        doc = memory.processed_document
        if doc.doc_intelligence_metadata:
            doc_type = doc.doc_intelligence_metadata.get("document_metadata", {}).get("type", "")
            return "Research" in doc_type or "Paper" in doc_type
        
        return False
    except Exception:
        return False


def _is_certificate(memory: Memory) -> bool:
    """Check if memory is a certificate."""
    try:
        if not memory.processed_document:
            return False
        
        doc = memory.processed_document
        if doc.doc_intelligence_metadata:
            doc_type = doc.doc_intelligence_metadata.get("document_metadata", {}).get("type", "")
            return "Certificate" in doc_type
        
        # Check filename
        filename = memory.filename.lower() if memory.filename else ""
        return "certificate" in filename or "cert" in filename
    except Exception:
        return False


def _is_study_material(memory: Memory) -> bool:
    """Check if memory is study material."""
    try:
        if not memory.processed_document:
            return False
        
        doc = memory.processed_document
        if doc.doc_intelligence_metadata:
            doc_type = doc.doc_intelligence_metadata.get("document_metadata", {}).get("type", "")
            return "Study" in doc_type or "Material" in doc_type or "Tutorial" in doc_type
        
        return False
    except Exception:
        return False


def _was_recently_accessed(memory: Memory, days: int = 3) -> bool:
    """Check if memory was accessed recently."""
    try:
        if not memory.last_accessed:
            return False
        
        cutoff = datetime.now(pytz.UTC) - timedelta(days=days)
        return memory.last_accessed >= cutoff
    except Exception:
        return False


def _is_large_document(memory: Memory, min_words: int = 1000) -> bool:
    """Check if memory is a large document."""
    try:
        if not memory.processed_document:
            return False
        
        doc = memory.processed_document
        if doc.doc_intelligence_metadata:
            word_count = doc.doc_intelligence_metadata.get("document_metadata", {}).get("word_count", 0)
            return word_count >= min_words
        
        return False
    except Exception:
        return False
