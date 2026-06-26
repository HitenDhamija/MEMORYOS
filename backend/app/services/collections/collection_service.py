"""
Collection management service for Phase 7.
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime
import pytz
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import Memory, User
from app.models.collection import Collection, CollectionMembership, CollectionSuggestion, UserContext
from app.models.processed_document import ProcessedDocument

logger = logging.getLogger(__name__)


class CollectionService:
    """Manages user collections and memberships."""
    
    @staticmethod
    def create_collection(
        db: Session,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        color: str = "blue",
        icon: str = "folder"
    ) -> Tuple[Optional[Collection], Optional[str]]:
        """Create a new collection."""
        try:
            # Check for duplicates
            existing = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.name == name,
                Collection.is_deleted == False
            ).first()
            
            if existing:
                return None, f"Collection '{name}' already exists"
            
            collection = Collection(
                user_id=user_id,
                name=name,
                description=description,
                color=color,
                icon=icon
            )
            db.add(collection)
            db.commit()
            db.refresh(collection)
            
            logger.info(f"Created collection {collection.id} for user {user_id}")
            return collection, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create collection: {e}")
            return None, str(e)
    
    @staticmethod
    def get_collection(
        db: Session,
        collection_id: int,
        user_id: int
    ) -> Optional[Collection]:
        """Get collection by ID for user."""
        return db.query(Collection).filter(
            Collection.id == collection_id,
            Collection.user_id == user_id,
            Collection.is_deleted == False
        ).first()
    
    @staticmethod
    def list_collections(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Collection]:
        """List user's collections."""
        return db.query(Collection).filter(
            Collection.user_id == user_id,
            Collection.is_deleted == False
        ).order_by(Collection.updated_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_collection(
        db: Session,
        collection_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[str] = None,
        icon: Optional[str] = None,
        is_archived: Optional[bool] = None,
        is_favorite: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        cover_image_url: Optional[str] = None
    ) -> Tuple[Optional[Collection], Optional[str]]:
        """Update collection."""
        try:
            collection = CollectionService.get_collection(db, collection_id, user_id)
            if not collection:
                return None, "Collection not found"
            
            if name and name != collection.name:
                existing = db.query(Collection).filter(
                    Collection.user_id == user_id,
                    Collection.name == name,
                    Collection.is_deleted == False
                ).first()
                if existing:
                    return None, f"Collection '{name}' already exists"
            
            if name:
                collection.name = name
            if description is not None:
                collection.description = description
            if color:
                collection.color = color
            if icon:
                collection.icon = icon
            if is_archived is not None:
                collection.is_archived = is_archived
            if is_favorite is not None:
                collection.is_favorite = is_favorite
            if is_pinned is not None:
                collection.is_pinned = is_pinned
            if cover_image_url is not None:
                collection.cover_image_url = cover_image_url
            
            collection.updated_at = datetime.now(pytz.UTC)
            db.commit()
            db.refresh(collection)
            
            logger.info(f"Updated collection {collection_id}")
            return collection, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update collection: {e}")
            return None, str(e)
    
    @staticmethod
    def delete_collection(
        db: Session,
        collection_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Delete collection (soft delete)."""
        try:
            collection = CollectionService.get_collection(db, collection_id, user_id)
            if not collection:
                return False, "Collection not found"
            
            collection.is_deleted = True
            collection.updated_at = datetime.now(pytz.UTC)
            db.commit()
            
            logger.info(f"Deleted collection {collection_id}")
            return True, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete collection: {e}")
            return False, str(e)
    
    @staticmethod
    def add_memory_to_collection(
        db: Session,
        collection_id: int,
        memory_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Add memory to collection."""
        try:
            # Verify collection exists and belongs to user
            collection = CollectionService.get_collection(db, collection_id, user_id)
            if not collection:
                return False, "Collection not found"
            
            # Verify memory exists and belongs to user
            memory = db.query(Memory).filter(
                Memory.id == memory_id,
                Memory.user_id == user_id
            ).first()
            if not memory:
                return False, "Memory not found"
            
            # Check if already in collection
            existing = db.query(CollectionMembership).filter(
                CollectionMembership.collection_id == collection_id,
                CollectionMembership.memory_id == memory_id
            ).first()
            
            if existing:
                return True, None
            
            membership = CollectionMembership(
                collection_id=collection_id,
                memory_id=memory_id,
                user_id=user_id
            )
            db.add(membership)
            collection.updated_at = datetime.now(pytz.UTC)
            db.commit()
            
            logger.info(f"Added memory {memory_id} to collection {collection_id}")
            return True, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to add memory to collection: {e}")
            return False, str(e)
    
    @staticmethod
    def remove_memory_from_collection(
        db: Session,
        collection_id: int,
        memory_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Remove memory from collection."""
        try:
            membership = db.query(CollectionMembership).filter(
                CollectionMembership.collection_id == collection_id,
                CollectionMembership.memory_id == memory_id,
                CollectionMembership.user_id == user_id
            ).first()
            
            if not membership:
                return False, "Memory not in collection"
            
            db.delete(membership)
            
            # Update collection timestamp
            collection = CollectionService.get_collection(db, collection_id, user_id)
            if collection:
                collection.updated_at = datetime.now(pytz.UTC)
            
            db.commit()
            logger.info(f"Removed memory {memory_id} from collection {collection_id}")
            return True, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to remove memory from collection: {e}")
            return False, str(e)
    
    @staticmethod
    def get_collection_memories(
        db: Session,
        collection_id: int,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Memory]:
        """Get memories in collection."""
        return db.query(Memory).join(
            CollectionMembership,
            Memory.id == CollectionMembership.memory_id
        ).filter(
            CollectionMembership.collection_id == collection_id,
            CollectionMembership.user_id == user_id
        ).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_memory_collections(
        db: Session,
        memory_id: int,
        user_id: int
    ) -> List[Collection]:
        """Get all collections containing a memory."""
        return db.query(Collection).join(
            CollectionMembership,
            Collection.id == CollectionMembership.collection_id
        ).filter(
            CollectionMembership.memory_id == memory_id,
            CollectionMembership.user_id == user_id,
            Collection.is_deleted == False
        ).all()
    
    @staticmethod
    def get_collection_stats(
        db: Session,
        user_id: int
    ) -> dict:
        """Get collection statistics for user."""
        try:
            collections = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.is_deleted == False
            ).all()
            
            stats = {
                "total_collections": len(collections),
                "largest_collection": None,
                "fastest_growing": None,
                "recently_updated": None,
                "average_size": 0
            }
            
            if not collections:
                return stats
            
            # Calculate sizes
            sizes = {}
            for coll in collections:
                size = db.query(func.count(CollectionMembership.id)).filter(
                    CollectionMembership.collection_id == coll.id
                ).scalar()
                sizes[coll.id] = size
            
            # Largest
            if sizes:
                largest_id = max(sizes, key=sizes.get)
                largest = next(c for c in collections if c.id == largest_id)
                stats["largest_collection"] = {
                    "id": largest.id,
                    "name": largest.name,
                    "size": sizes[largest_id]
                }
                stats["average_size"] = sum(sizes.values()) / len(sizes)
            
            # Recently updated
            if collections:
                recent = max(collections, key=lambda c: c.updated_at)
                stats["recently_updated"] = {
                    "id": recent.id,
                    "name": recent.name,
                    "updated_at": recent.updated_at.isoformat()
                }
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

    @staticmethod
    def search_collections(
        db: Session,
        user_id: int,
        query: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Collection]:
        """Search collections by name or description."""
        search_term = f"%{query}%"
        return db.query(Collection).filter(
            Collection.user_id == user_id,
            Collection.is_deleted == False,
            (
                Collection.name.ilike(search_term) |
                Collection.description.ilike(search_term)
            )
        ).order_by(Collection.updated_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def filter_collections(
        db: Session,
        user_id: int,
        is_archived: Optional[bool] = None,
        is_favorite: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        color: Optional[str] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        skip: int = 0,
        limit: int = 100
    ) -> List[Collection]:
        """Filter and sort collections."""
        query = db.query(Collection).filter(
            Collection.user_id == user_id,
            Collection.is_deleted == False
        )
        
        # Apply filters
        if is_archived is not None:
            query = query.filter(Collection.is_archived == is_archived)
        if is_favorite is not None:
            query = query.filter(Collection.is_favorite == is_favorite)
        if is_pinned is not None:
            query = query.filter(Collection.is_pinned == is_pinned)
        if color:
            query = query.filter(Collection.color == color)
        
        # Apply sorting
        sort_column = getattr(Collection, sort_by, Collection.updated_at)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        return query.offset(skip).limit(limit).all()
