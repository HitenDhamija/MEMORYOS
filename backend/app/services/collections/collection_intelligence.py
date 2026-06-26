"""
Collection Intelligence service for analytics and insights.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pytz
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models.models import Memory, User
from app.models.collection import Collection, CollectionMembership, UserContext
from app.models.processed_document import ProcessedDocument

logger = logging.getLogger(__name__)


class CollectionIntelligence:
    """Provides analytics and insights for collections."""
    
    @staticmethod
    def get_collection_overview(
        db: Session,
        collection_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Get comprehensive overview of a collection."""
        try:
            collection = db.query(Collection).filter(
                Collection.id == collection_id,
                Collection.user_id == user_id,
                Collection.is_deleted == False
            ).first()
            
            if not collection:
                return {}
            
            # Get memories in collection
            memories = db.query(Memory).join(
                CollectionMembership,
                Memory.id == CollectionMembership.memory_id
            ).filter(
                CollectionMembership.collection_id == collection_id,
                CollectionMembership.user_id == user_id
            ).all()
            
            if not memories:
                return {
                    "collection": collection.to_dict(),
                    "stats": {"total": 0},
                    "topics": [],
                    "file_types": [],
                    "growth_trend": [],
                    "activity_timeline": [],
                }
            
            # Analyze documents
            topics = []
            file_types = []
            total_words = 0
            
            for memory in memories:
                if memory.file_type:
                    file_types.append(memory.file_type)
                
                if memory.processed_document and memory.processed_document.doc_intelligence_metadata:
                    meta = memory.processed_document.doc_intelligence_metadata
                    topics.extend(meta.get("topics_covered", []))
                    word_count = meta.get("document_metadata", {}).get("word_count", 0)
                    total_words += word_count
            
            # Count frequencies
            from collections import Counter
            topic_counts = Counter(topics).most_common(10)
            file_type_counts = Counter(file_types).most_common(5)
            
            # Calculate growth trend (last 6 months)
            growth_trend = CollectionIntelligence._calculate_growth_trend(memories)
            
            # Calculate activity timeline (last 7 days)
            activity_timeline = CollectionIntelligence._calculate_activity_timeline(memories)
            
            # Calculate average document size
            avg_size = total_words / len(memories) if memories else 0
            
            return {
                "collection": collection.to_dict(),
                "stats": {
                    "total": len(memories),
                    "total_words": total_words,
                    "average_document_size": int(avg_size),
                    "unique_topics": len(set(topics)),
                },
                "topics": [{"name": t, "count": c} for t, c in topic_counts],
                "file_types": [{"type": ft, "count": c} for ft, c in file_type_counts],
                "growth_trend": growth_trend,
                "activity_timeline": activity_timeline,
            }
        except Exception as e:
            logger.error(f"Failed to get collection overview: {e}")
            return {}
    
    @staticmethod
    def _calculate_growth_trend(memories: List[Memory]) -> List[Dict[str, Any]]:
        """Calculate collection growth over last 6 months."""
        try:
            now = datetime.now(pytz.UTC)
            trend = []
            
            for i in range(5, -1, -1):
                month_start = now - timedelta(days=30 * (i + 1))
                month_end = now - timedelta(days=30 * i)
                
                count = sum(
                    1 for m in memories
                    if m.upload_date and month_start <= m.upload_date <= month_end
                )
                
                trend.append({
                    "month": month_start.strftime("%Y-%m"),
                    "count": count,
                })
            
            return trend
        except Exception:
            return []
    
    @staticmethod
    def _calculate_activity_timeline(memories: List[Memory]) -> List[Dict[str, Any]]:
        """Calculate activity over last 7 days."""
        try:
            now = datetime.now(pytz.UTC)
            timeline = []
            
            for i in range(6, -1, -1):
                day = now - timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                
                uploads = sum(
                    1 for m in memories
                    if m.upload_date and day_start <= m.upload_date < day_end
                )
                
                timeline.append({
                    "date": day_start.strftime("%Y-%m-%d"),
                    "uploads": uploads,
                })
            
            return timeline
        except Exception:
            return []
    
    @staticmethod
    def get_related_collections(
        db: Session,
        collection_id: int,
        user_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find collections with similar content."""
        try:
            # Get current collection's topics
            current_collection = db.query(Collection).filter(
                Collection.id == collection_id,
                Collection.user_id == user_id,
                Collection.is_deleted == False
            ).first()
            
            if not current_collection:
                return []
            
            # Get topics from current collection
            current_topics = set()
            memories = db.query(Memory).join(
                CollectionMembership,
                Memory.id == CollectionMembership.memory_id
            ).filter(
                CollectionMembership.collection_id == collection_id
            ).all()
            
            for memory in memories:
                if memory.processed_document and memory.processed_document.doc_intelligence_metadata:
                    topics = memory.processed_document.doc_intelligence_metadata.get("topics_covered", [])
                    current_topics.update(topics)
            
            if not current_topics:
                return []
            
            # Find other collections with similar topics
            other_collections = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.id != collection_id,
                Collection.is_deleted == False
            ).all()
            
            related = []
            for coll in other_collections:
                coll_topics = set()
                coll_memories = db.query(Memory).join(
                    CollectionMembership,
                    Memory.id == CollectionMembership.memory_id
                ).filter(
                    CollectionMembership.collection_id == coll.id
                ).all()
                
                for memory in coll_memories:
                    if memory.processed_document and memory.processed_document.doc_intelligence_metadata:
                        topics = memory.processed_document.doc_intelligence_metadata.get("topics_covered", [])
                        coll_topics.update(topics)
                
                # Calculate similarity
                if coll_topics and current_topics:
                    intersection = current_topics.intersection(coll_topics)
                    union = current_topics.union(coll_topics)
                    similarity = len(intersection) / len(union) if union else 0
                    
                    if similarity > 0.1:  # At least 10% similarity
                        related.append({
                            "collection": coll.to_dict(),
                            "similarity": round(similarity * 100, 1),
                            "shared_topics": list(intersection)[:5],
                        })
            
            # Sort by similarity
            related.sort(key=lambda x: x["similarity"], reverse=True)
            
            return related[:limit]
        except Exception as e:
            logger.error(f"Failed to get related collections: {e}")
            return []
    
    @staticmethod
    def get_knowledge_graph(
        db: Session,
        user_id: int
    ) -> Dict[str, Any]:
        """Get knowledge graph data for all collections."""
        try:
            collections = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.is_deleted == False
            ).all()
            
            nodes = []
            edges = []
            
            # Build nodes from collections
            for coll in collections:
                topics = set()
                memories = db.query(Memory).join(
                    CollectionMembership,
                    Memory.id == CollectionMembership.memory_id
                ).filter(
                    CollectionMembership.collection_id == coll.id
                ).all()
                
                for memory in memories:
                    if memory.processed_document and memory.processed_document.doc_intelligence_metadata:
                        coll_topics = memory.processed_document.doc_intelligence_metadata.get("topics_covered", [])
                        topics.update(coll_topics)
                
                nodes.append({
                    "id": f"collection_{coll.id}",
                    "label": coll.name,
                    "type": "collection",
                    "size": len(memories),
                    "topics": list(topics)[:5],
                })
            
            # Build edges based on shared topics
            for i, coll1 in enumerate(collections):
                for coll2 in collections[i+1:]:
                    # Get topics for both
                    topics1 = set()
                    topics2 = set()
                    
                    memories1 = db.query(Memory).join(
                        CollectionMembership,
                        Memory.id == CollectionMembership.memory_id
                    ).filter(
                        CollectionMembership.collection_id == coll1.id
                    ).all()
                    
                    memories2 = db.query(Memory).join(
                        CollectionMembership,
                        Memory.id == CollectionMembership.memory_id
                    ).filter(
                        CollectionMembership.collection_id == coll2.id
                    ).all()
                    
                    for memory in memories1:
                        if memory.processed_document and memory.processed_document.doc_intelligence_metadata:
                            t = memory.processed_document.doc_intelligence_metadata.get("topics_covered", [])
                            topics1.update(t)
                    
                    for memory in memories2:
                        if memory.processed_document and memory.processed_document.doc_intelligence_metadata:
                            t = memory.processed_document.doc_intelligence_metadata.get("topics_covered", [])
                            topics2.update(t)
                    
                    if topics1 and topics2:
                        intersection = topics1.intersection(topics2)
                        if intersection:
                            edges.append({
                                "source": f"collection_{coll1.id}",
                                "target": f"collection_{coll2.id}",
                                "shared_topics": list(intersection)[:3],
                                "strength": len(intersection),
                            })
            
            return {
                "nodes": nodes,
                "edges": edges,
                "stats": {
                    "total_collections": len(nodes),
                    "total_connections": len(edges),
                }
            }
        except Exception as e:
            logger.error(f"Failed to get knowledge graph: {e}")
            return {"nodes": [], "edges": [], "stats": {}}
