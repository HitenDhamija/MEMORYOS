"""
Timeline API endpoints for Phase 8.
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.models.models import User
from app.db.session import get_db
from app.services.timeline import (
    TimelineService,
    MilestoneService,
    LearningStreakService,
    KnowledgeEvolutionService,
    ForgottenMemoryService,
)

router = APIRouter(prefix="/timeline", tags=["timeline"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class TimelineEventResponse(BaseModel):
    id: int
    event_type: str
    event_date: str
    memory_id: Optional[int] = None
    collection_id: Optional[int] = None
    event_data: Optional[str] = None


class MilestoneResponse(BaseModel):
    first_upload: bool
    memories_50: bool
    memories_100: bool
    memories_500: bool
    collections_5: bool
    collections_10: bool
    searches_50: bool
    searches_100: bool
    first_upload_date: Optional[str] = None
    memories_100_date: Optional[str] = None


class AchievementResponse(BaseModel):
    id: str
    name: str
    date: Optional[str] = None


class AchievementsResponse(BaseModel):
    unlocked: List[AchievementResponse]
    progress: dict


class LearningStreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_uploads: int
    total_searches: int
    total_collections_created: int
    last_activity_date: Optional[str] = None
    streak_start_date: Optional[str] = None


class KnowledgeEvolutionResponse(BaseModel):
    period: str
    topics: List[str]
    memory_count: int
    search_count: int
    collection_count: int
    discovery_count: int


class TimelineGroupedResponse(BaseModel):
    period: str
    count: int
    event_types: dict


class ForgottenMemoriesResponse(BaseModel):
    thirty_days: int
    sixty_days: int
    ninety_days: int


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/events", response_model=List[TimelineEventResponse])
def get_timeline_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    event_types: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
):
    """Get timeline events for current user."""
    try:
        start = datetime.fromisoformat(start_date) if start_date else None
        end = datetime.fromisoformat(end_date) if end_date else None
        types = event_types.split(",") if event_types else None
        
        events = TimelineService.get_timeline(
            db,
            current_user.id,
            start_date=start,
            end_date=end,
            event_types=types,
            skip=skip,
            limit=limit
        )
        
        return [e.to_dict() for e in events]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events/grouped", response_model=dict)
def get_timeline_grouped(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    period: str = Query("month"),
):
    """Get timeline events grouped by time period."""
    try:
        grouped = TimelineService.group_events_by_period(db, current_user.id, period)
        return grouped
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/memory/{memory_id}/events", response_model=List[TimelineEventResponse])
def get_memory_timeline(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get timeline events for a specific memory."""
    try:
        events = TimelineService.get_memory_timeline(db, memory_id, current_user.id)
        return [e.to_dict() for e in events]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/milestones", response_model=MilestoneResponse)
def get_milestones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get milestone status for current user."""
    try:
        milestone, _ = MilestoneService.check_milestones(db, current_user.id)
        return milestone.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/achievements", response_model=AchievementsResponse)
def get_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get unlocked achievements and progress."""
    try:
        achievements = MilestoneService.get_achievements(db, current_user.id)
        return achievements
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/streak", response_model=LearningStreakResponse)
def get_learning_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get learning streak statistics."""
    try:
        stats = LearningStreakService.get_stats(db, current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/evolution", response_model=List[KnowledgeEvolutionResponse])
def get_knowledge_evolution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    months: int = Query(12),
):
    """Get knowledge evolution over time."""
    try:
        evolution = KnowledgeEvolutionService.get_evolution_timeline(db, current_user.id, months)
        return evolution
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/forgotten", response_model=ForgottenMemoriesResponse)
def get_forgotten_memories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get forgotten memories statistics."""
    try:
        stats = ForgottenMemoryService.get_forgotten_by_threshold(db, current_user.id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stripe-activity")
def track_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update learning streak (called after user activity)."""
    try:
        LearningStreakService.update_streak(db, current_user.id)
        KnowledgeEvolutionService.update_evolution(db, current_user.id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
