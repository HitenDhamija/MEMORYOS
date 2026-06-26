"""
Insights and Dashboard API endpoints.

Aggregates data from memories, timeline, collections, and embeddings
to provide dashboard metrics and AI insights.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.db.session import get_db
from app.models.models import User, Memory
from app.models.processed_document import ProcessedDocument
from app.models.collection import Collection, CollectionMembership
from app.models.timeline import TimelineEvent
from app.api.deps import get_current_user
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Get comprehensive dashboard data with metrics, insights, and activity.
    """
    try:
        # Get basic metrics
        metrics = _get_metrics(db, current_user.id)
        
        # Get top topics
        top_topics = _get_top_topics(db, current_user.id)
        
        # Get recent activity (timeline events)
        recent_activity = _get_recent_activity(db, current_user.id)
        
        # Get weekly progress
        weekly_progress = _get_weekly_progress(db, current_user.id)
        
        # Generate insights
        insights = _generate_insights(db, current_user.id, metrics)
        
        return {
            'metrics': metrics,
            'topTopics': top_topics,
            'recentActivity': recent_activity,
            'weeklyProgress': weekly_progress,
            'insights': insights
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}", exc_info=True)
        return {
            'metrics': {},
            'topTopics': [],
            'recentActivity': [],
            'weeklyProgress': {},
            'insights': []
        }


def _get_metrics(db: Session, user_id: int) -> Dict:
    """Get key dashboard metrics."""
    try:
        # Total memories
        total_memories = db.query(func.count(Memory.id)).filter(
            and_(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            )
        ).scalar() or 0
        
        # Processed memories
        processed_memories = db.query(func.count(Memory.id)).filter(
            and_(
                Memory.user_id == user_id,
                Memory.is_deleted == False,
                Memory.is_processed == True
            )
        ).scalar() or 0
        
        # Total collections
        total_collections = db.query(func.count(Collection.id)).filter(
            and_(
                Collection.user_id == user_id,
                Collection.is_deleted == False
            )
        ).scalar() or 0
        
        # Total words across all processed documents
        total_words = db.query(func.sum(ProcessedDocument.word_count)).filter(
            ProcessedDocument.user_id == user_id
        ).scalar() or 0
        
        # Recent discoveries (last 7 days)
        week_ago = datetime.now(pytz.UTC) - timedelta(days=7)
        recent_discoveries = db.query(func.count(Memory.id)).filter(
            and_(
                Memory.user_id == user_id,
                Memory.upload_date >= week_ago,
                Memory.is_deleted == False
            )
        ).scalar() or 0
        
        return {
            'totalMemories': total_memories,
            'processedMemories': processed_memories,
            'totalCollections': total_collections,
            'totalWords': total_words,
            'recentDiscoveries': recent_discoveries,
            'processingRate': round((processed_memories / max(total_memories, 1)) * 100, 1)
        }
    except Exception as e:
        logger.warning(f"Failed to calculate metrics: {e}")
        return {}


def _get_top_topics(db: Session, user_id: int, limit: int = 8) -> List[Dict]:
    """Extract and count most frequent topics."""
    try:
        topic_counts = {}
        
        # Get all processed documents
        proc_docs = db.query(ProcessedDocument).filter(
            ProcessedDocument.user_id == user_id
        ).all()
        
        # Extract and count topics
        for proc_doc in proc_docs:
            if proc_doc.topics:
                topics_data = proc_doc.topics
                if isinstance(topics_data, str):
                    topics_data = json.loads(topics_data)
                
                if isinstance(topics_data, dict):
                    for key in ['technologies', 'general', 'keywords']:
                        if key in topics_data:
                            items = topics_data[key]
                            if isinstance(items, list):
                                for item in items[:5]:
                                    topic_name = None
                                    if isinstance(item, dict) and 'name' in item:
                                        topic_name = item['name']
                                    elif isinstance(item, str):
                                        topic_name = item
                                    
                                    if topic_name:
                                        topic_counts[topic_name] = topic_counts.get(topic_name, 0) + 1
        
        # Sort and return top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'topic': topic,
                'count': count,
                'trend': 'up' if count > 2 else ('stable' if count == 2 else 'down')
            }
            for topic, count in sorted_topics
        ]
    except Exception as e:
        logger.warning(f"Failed to get top topics: {e}")
        return []


def _get_recent_activity(db: Session, user_id: int, limit: int = 20) -> List[Dict]:
    """Get recent timeline events."""
    try:
        events = db.query(TimelineEvent).filter(
            TimelineEvent.user_id == user_id
        ).order_by(TimelineEvent.event_date.desc()).limit(limit).all()
        
        activity = []
        for event in events:
            activity.append({
                'id': str(event.id),
                'timestamp': event.event_date.isoformat() if event.event_date else None,
                'action': event.event_type,
                'description': _format_event_description(event)
            })
        
        return activity
    except Exception as e:
        logger.warning(f"Failed to get recent activity: {e}")
        return []


def _format_event_description(event: TimelineEvent) -> str:
    """Format timeline event for display."""
    event_data = event.event_data
    if isinstance(event_data, str):
        try:
            event_data = json.loads(event_data)
        except (json.JSONDecodeError, TypeError):
            event_data = {}

    title = ""
    if event_data and isinstance(event_data, dict):
        title = event_data.get("title", "")

    if not title and event.memory:
        try:
            title = event.memory.title if event.memory else ""
        except Exception:
            title = ""

    event_type_map = {
        'upload': f'Uploaded "{title}"' if title else 'Uploaded file',
        'document_processed': f'Processed "{title}"' if title else 'Document processed',
        'embedding_generated': f'Generated embeddings for "{title}"' if title else 'Embeddings generated',
        'collection_assigned': f'Added to {event_data.get("collection_name", "collection") if isinstance(event_data, dict) else "collection"}',
        'search': f'Searched for "{event_data.get("query", "") if isinstance(event_data, dict) else ""}"' if isinstance(event_data, dict) and event_data.get("query") else 'Performed search',
        'discovery': 'Discovered connection',
        'collection_created': f'Created collection "{event_data.get("name", "") if isinstance(event_data, dict) else ""}"' if isinstance(event_data, dict) and event_data.get("name") else 'Created collection',
        'memory_viewed': f'Viewed "{title}"' if title else 'Viewed memory',
    }

    return event_type_map.get(event.event_type, event.event_type.replace('_', ' ').title())


def _get_weekly_progress(db: Session, user_id: int) -> Dict:
    """Get activity stats for the past week."""
    try:
        week_ago = datetime.now(pytz.UTC) - timedelta(days=7)
        
        # Count uploads in past week
        uploads = db.query(func.count(Memory.id)).filter(
            and_(
                Memory.user_id == user_id,
                Memory.upload_date >= week_ago
            )
        ).scalar() or 0
        
        # Count searches in past week
        searches = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == 'search',
                TimelineEvent.event_date >= week_ago
            )
        ).scalar() or 0
        
        # Count discoveries in past week
        discoveries = db.query(func.count(TimelineEvent.id)).filter(
            and_(
                TimelineEvent.user_id == user_id,
                TimelineEvent.event_type == 'discovery',
                TimelineEvent.event_date >= week_ago
            )
        ).scalar() or 0
        
        return {
            'uploads': uploads,
            'searches': searches,
            'discoveries': discoveries
        }
    except Exception as e:
        logger.warning(f"Failed to calculate weekly progress: {e}")
        return {'uploads': 0, 'searches': 0, 'discoveries': 0}


def _generate_insights(db: Session, user_id: int, metrics: Dict) -> List[Dict]:
    """Generate AI insights based on user data."""
    insights = []
    
    try:
        # Insight 1: Processing status
        if metrics.get('processingRate', 0) < 100:
            insights.append({
                'id': 'processing_pending',
                'type': 'alert',
                'title': 'Processing in Progress',
                'description': f'{metrics.get("processedMemories", 0)} of {metrics.get("totalMemories", 0)} files processed',
                'priority': 'high',
                'icon': 'alert',
                'color': 'orange'
            })
        
        # Insight 2: Total knowledge accumulated
        if metrics.get('totalWords', 0) > 10000:
            insights.append({
                'id': 'knowledge_accumulated',
                'type': 'trending',
                'title': 'Knowledge Base Growing',
                'description': f'You\'ve accumulated {metrics.get("totalWords", 0):,} words of knowledge',
                'priority': 'medium',
                'icon': 'trending',
                'color': 'green'
            })
        
        # Insight 3: Recent activity
        if metrics.get('recentDiscoveries', 0) > 0:
            insights.append({
                'id': 'recent_activity',
                'type': 'discovery',
                'title': 'Recent Uploads',
                'description': f'You\'ve added {metrics.get("recentDiscoveries", 0)} memories this week',
                'priority': 'low',
                'icon': 'lightbulb',
                'color': 'blue'
            })
        
        # Insight 4: Collections suggestion
        if metrics.get('totalCollections', 0) == 0 and metrics.get('totalMemories', 0) > 5:
            insights.append({
                'id': 'collections_suggestion',
                'type': 'suggestion',
                'title': 'Organize with Collections',
                'description': 'Create collections to organize your growing knowledge base',
                'priority': 'medium',
                'actionUrl': '/collections',
                'actionLabel': 'Create Collection',
                'icon': 'bookmark',
                'color': 'purple'
            })
        
        # Insight 5: Graph suggestion
        if metrics.get('totalMemories', 0) > 3:
            insights.append({
                'id': 'graph_suggestion',
                'type': 'suggestion',
                'title': 'Explore Knowledge Graph',
                'description': 'Visualize connections between your memories',
                'priority': 'low',
                'actionUrl': '/knowledge-graph',
                'actionLabel': 'View Graph',
                'icon': 'star',
                'color': 'blue'
            })
    
    except Exception as e:
        logger.warning(f"Failed to generate insights: {e}")
    
    return insights
