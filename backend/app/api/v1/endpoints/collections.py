"""
Collections API endpoints for Phase 7.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User
from app.models.collection import Collection
from app.api.deps import get_current_user
from app.services.collections import CollectionService, SuggestionEngine, ContextEngine
from app.services.collections.smart_collections import SmartCollections
from app.services.collections.collection_intelligence import CollectionIntelligence

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/collections", tags=["collections"])

# ============================================================================
# SCHEMAS
# ============================================================================

class CollectionCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    color: str = "blue"
    icon: str = "folder"
    
    class Config:
        from_attributes = True


class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    is_archived: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_pinned: Optional[bool] = None
    cover_image_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class CollectionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    color: str
    icon: str
    memory_count: int
    is_archived: bool = False
    is_favorite: bool = False
    is_pinned: bool = False
    cover_image_url: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class CollectionDetailResponse(CollectionResponse):
    memories: List[dict] = []
    
    class Config:
        from_attributes = True


class SuggestionResponse(BaseModel):
    id: int
    suggested_name: str
    reasoning: Optional[str]
    topics: List[str]
    confidence_score: int
    status: str
    created_at: str
    
    class Config:
        from_attributes = True


class ContextResponse(BaseModel):
    frequently_used_topics: List[str]
    recent_interests: List[str]
    favorite_collections: List[str]
    total_memories: int
    total_collections: int
    
    class Config:
        from_attributes = True


class CollectionStatsResponse(BaseModel):
    total_collections: int
    largest_collection: Optional[dict]
    fastest_growing: Optional[dict]
    recently_updated: Optional[dict]
    average_size: float
    
    class Config:
        from_attributes = True


class BulkMoveRequest(BaseModel):
    memory_ids: List[int]
    target_collection_id: int
    
    class Config:
        from_attributes = True


class BulkDeleteRequest(BaseModel):
    memory_ids: List[int]
    
    class Config:
        from_attributes = True


class BulkOperationResponse(BaseModel):
    success_count: int
    failed_count: int
    errors: List[str] = []
    
    class Config:
        from_attributes = True


class SmartCollectionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    icon: str
    color: str
    memory_count: int
    is_smart: bool = True
    rule_id: str
    
    class Config:
        from_attributes = True


class CollectionOverviewResponse(BaseModel):
    collection: dict
    stats: dict
    topics: List[dict]
    file_types: List[dict]
    growth_trend: List[dict]
    activity_timeline: List[dict]
    
    class Config:
        from_attributes = True


class RelatedCollectionResponse(BaseModel):
    collection: dict
    similarity: float
    shared_topics: List[str]
    
    class Config:
        from_attributes = True


class KnowledgeGraphResponse(BaseModel):
    nodes: List[dict]
    edges: List[dict]
    stats: dict
    
    class Config:
        from_attributes = True


# ============================================================================
# COLLECTION ENDPOINTS
# ============================================================================

@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    request: CollectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionResponse:
    """Create a new collection."""
    collection, error = CollectionService.create_collection(
        db,
        current_user.id,
        request.name,
        request.description,
        request.color,
        request.icon
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return CollectionResponse(**collection.to_dict())


@router.get("", response_model=List[CollectionResponse])
async def list_collections(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[CollectionResponse]:
    """List user's collections."""
    collections = CollectionService.list_collections(db, current_user.id, skip, limit)
    
    return [CollectionResponse(**c.to_dict()) for c in collections]


@router.get("/search", response_model=List[CollectionResponse])
async def search_collections(
    q: str = Query(..., min_length=1, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[CollectionResponse]:
    """Search collections by name or description."""
    collections = CollectionService.search_collections(db, current_user.id, q, skip, limit)
    
    return [CollectionResponse(**c.to_dict()) for c in collections]


@router.get("/filter", response_model=List[CollectionResponse])
async def filter_collections(
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    color: Optional[str] = Query(None, description="Filter by color"),
    sort_by: Optional[str] = Query("updated_at", description="Sort field: name, created_at, updated_at, memory_count"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc or desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[CollectionResponse]:
    """Filter and sort collections."""
    collections = CollectionService.filter_collections(
        db, current_user.id,
        is_archived=is_archived,
        is_favorite=is_favorite,
        is_pinned=is_pinned,
        color=color,
        sort_by=sort_by,
        sort_order=sort_order,
        skip=skip,
        limit=limit
    )
    
    return [CollectionResponse(**c.to_dict()) for c in collections]


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionDetailResponse:
    """Get collection details."""
    collection = CollectionService.get_collection(db, collection_id, current_user.id)
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    # Track access
    ContextEngine.track_collection_access(db, current_user.id, collection_id)
    
    data = collection.to_dict()
    memories = CollectionService.get_collection_memories(db, collection_id, current_user.id)
    data["memories"] = [{
        "id": m.id,
        "filename": m.original_filename,
        "file_type": m.file_type,
        "file_size": m.file_size,
        "status": m.processing_status,
        "upload_date": m.upload_date.isoformat() if m.upload_date else None,
        "title": m.title,
        "description": m.description,
        "tags": m.tags.split(",") if m.tags and isinstance(m.tags, str) else (m.tags or []),
    } for m in memories]
    
    return CollectionDetailResponse(**data)


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: int,
    request: CollectionUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionResponse:
    """Update collection."""
    collection, error = CollectionService.update_collection(
        db,
        collection_id,
        current_user.id,
        request.name,
        request.description,
        request.color,
        request.icon,
        request.is_archived,
        request.is_favorite,
        request.is_pinned,
        request.cover_image_url
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return CollectionResponse(**collection.to_dict())


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """Delete collection."""
    success, error = CollectionService.delete_collection(db, collection_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )


# ============================================================================
# MEMORY COLLECTION ENDPOINTS
# ============================================================================

@router.post("/{collection_id}/memories/{memory_id}", status_code=status.HTTP_201_CREATED)
async def add_memory_to_collection(
    collection_id: int,
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Add memory to collection."""
    success, error = CollectionService.add_memory_to_collection(
        db,
        collection_id,
        memory_id,
        current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"success": True}


@router.delete("/{collection_id}/memories/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_memory_from_collection(
    collection_id: int,
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """Remove memory from collection."""
    success, error = CollectionService.remove_memory_from_collection(
        db,
        collection_id,
        memory_id,
        current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )


@router.get("/{memory_id}/collections", response_model=List[CollectionResponse])
async def get_memory_collections(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[CollectionResponse]:
    """Get all collections containing a memory."""
    collections = CollectionService.get_memory_collections(db, memory_id, current_user.id)
    
    return [CollectionResponse(**c.to_dict()) for c in collections]


# ============================================================================
# SUGGESTION ENDPOINTS
# ============================================================================

@router.post("/suggestions/generate", response_model=List[SuggestionResponse])
async def generate_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[SuggestionResponse]:
    """Generate collection suggestions."""
    suggestions = SuggestionEngine.generate_suggestions(db, current_user.id)
    
    return [SuggestionResponse(**s.to_dict()) for s in suggestions]


@router.get("/suggestions/pending", response_model=List[SuggestionResponse])
async def get_pending_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[SuggestionResponse]:
    """Get pending collection suggestions."""
    suggestions = SuggestionEngine.get_pending_suggestions(db, current_user.id)
    
    return [SuggestionResponse(**s.to_dict()) for s in suggestions]


@router.post("/suggestions/{suggestion_id}/accept", response_model=CollectionResponse)
async def accept_suggestion(
    suggestion_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionResponse:
    """Accept a collection suggestion."""
    collection, error = SuggestionEngine.accept_suggestion(db, suggestion_id, current_user.id)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return CollectionResponse(**collection.to_dict())


@router.post("/suggestions/{suggestion_id}/reject", status_code=status.HTTP_200_OK)
async def reject_suggestion(
    suggestion_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Reject a collection suggestion."""
    success, error = SuggestionEngine.reject_suggestion(db, suggestion_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return {"success": True}


@router.post("/suggestions/rename", response_model=List[SuggestionResponse])
async def generate_rename_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[SuggestionResponse]:
    """Generate rename suggestions for collections."""
    suggestions = SuggestionEngine.generate_rename_suggestions(db, current_user.id)
    
    return [SuggestionResponse(**s.to_dict()) for s in suggestions]


@router.post("/suggestions/merge", response_model=List[SuggestionResponse])
async def generate_merge_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[SuggestionResponse]:
    """Generate merge suggestions for similar collections."""
    suggestions = SuggestionEngine.generate_merge_suggestions(db, current_user.id)
    
    return [SuggestionResponse(**s.to_dict()) for s in suggestions]


@router.post("/suggestions/{suggestion_id}/accept-rename", response_model=CollectionResponse)
async def accept_rename_suggestion(
    suggestion_id: int,
    new_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionResponse:
    """Accept a rename suggestion with custom name."""
    collection, error = SuggestionEngine.accept_rename_suggestion(
        db, suggestion_id, current_user.id, new_name
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return CollectionResponse(**collection.to_dict())


@router.post("/suggestions/{suggestion_id}/accept-merge", response_model=CollectionResponse)
async def accept_merge_suggestion(
    suggestion_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionResponse:
    """Accept a merge suggestion."""
    collection, error = SuggestionEngine.accept_merge_suggestion(
        db, suggestion_id, current_user.id
    )
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return CollectionResponse(**collection.to_dict())


# ============================================================================
# CONTEXT ENDPOINTS
# ============================================================================

@router.get("/context/interests", response_model=ContextResponse)
async def get_user_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ContextResponse:
    """Get user's interests and context."""
    ContextEngine.update_context(db, current_user.id)
    context = ContextEngine.get_or_create_context(db, current_user.id)
    
    return ContextResponse(**context.to_dict())


# ============================================================================
# STATISTICS ENDPOINTS
# ============================================================================

@router.get("/stats/overview", response_model=CollectionStatsResponse)
async def get_collection_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionStatsResponse:
    """Get collection statistics."""
    stats = CollectionService.get_collection_stats(db, current_user.id)
    
    return CollectionStatsResponse(**stats)


# ============================================================================
# BULK OPERATION ENDPOINTS
# ============================================================================

@router.post("/bulk/move", response_model=BulkOperationResponse)
async def bulk_move_memories(
    request: BulkMoveRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BulkOperationResponse:
    """Bulk move memories to a target collection."""
    success_count = 0
    failed_count = 0
    errors = []
    
    for memory_id in request.memory_ids:
        success, error = CollectionService.add_memory_to_collection(
            db,
            request.target_collection_id,
            memory_id,
            current_user.id
        )
        if success:
            success_count += 1
        else:
            failed_count += 1
            if error:
                errors.append(f"Memory {memory_id}: {error}")
    
    return BulkOperationResponse(
        success_count=success_count,
        failed_count=failed_count,
        errors=errors[:10]  # Limit errors to first 10
    )


@router.post("/bulk/delete", response_model=BulkOperationResponse)
async def bulk_delete_memories_from_collection(
    request: BulkDeleteRequest,
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BulkOperationResponse:
    """Bulk delete memories from a collection."""
    success_count = 0
    failed_count = 0
    errors = []
    
    for memory_id in request.memory_ids:
        success, error = CollectionService.remove_memory_from_collection(
            db,
            collection_id,
            memory_id,
            current_user.id
        )
        if success:
            success_count += 1
        else:
            failed_count += 1
            if error:
                errors.append(f"Memory {memory_id}: {error}")
    
    return BulkOperationResponse(
        success_count=success_count,
        failed_count=failed_count,
        errors=errors[:10]  # Limit errors to first 10
    )


@router.post("/bulk/archive", response_model=BulkOperationResponse)
async def bulk_archive_collections(
    collection_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BulkOperationResponse:
    """Bulk archive collections."""
    success_count = 0
    failed_count = 0
    errors = []
    
    for collection_id in collection_ids:
        collection, error = CollectionService.update_collection(
            db,
            collection_id,
            current_user.id,
            is_archived=True
        )
        if collection:
            success_count += 1
        else:
            failed_count += 1
            if error:
                errors.append(f"Collection {collection_id}: {error}")
    
    return BulkOperationResponse(
        success_count=success_count,
        failed_count=failed_count,
        errors=errors[:10]
    )


@router.post("/bulk/favorite", response_model=BulkOperationResponse)
async def bulk_favorite_collections(
    collection_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> BulkOperationResponse:
    """Bulk mark collections as favorite."""
    success_count = 0
    failed_count = 0
    errors = []
    
    for collection_id in collection_ids:
        collection, error = CollectionService.update_collection(
            db,
            collection_id,
            current_user.id,
            is_favorite=True
        )
        if collection:
            success_count += 1
        else:
            failed_count += 1
            if error:
                errors.append(f"Collection {collection_id}: {error}")
    
    return BulkOperationResponse(
        success_count=success_count,
        failed_count=failed_count,
        errors=errors[:10]
    )


# ============================================================================
# SMART COLLECTION ENDPOINTS
# ============================================================================

@router.get("/smart", response_model=List[SmartCollectionResponse])
async def get_smart_collections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[SmartCollectionResponse]:
    """Get all smart collections with memory counts."""
    collections = SmartCollections.get_smart_collections(db, current_user.id)
    
    return [SmartCollectionResponse(**c) for c in collections]


@router.get("/smart/{rule_id}", response_model=List[dict])
async def get_smart_collection_memories(
    rule_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """Get memories in a smart collection."""
    memories = SmartCollections.get_smart_collection_memories(
        db, current_user.id, rule_id, skip, limit
    )
    
    return [m.to_dict() for m in memories]


@router.post("/smart/{rule_id}/convert", response_model=CollectionResponse)
async def convert_smart_to_collection(
    rule_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionResponse:
    """Convert a smart collection to a real collection."""
    collection = SmartCollections.create_collection_from_smart(
        db, current_user.id, rule_id
    )
    
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create collection from smart collection"
        )
    
    return CollectionResponse(**collection.to_dict())


# ============================================================================
# COLLECTION INTELLIGENCE ENDPOINTS
# ============================================================================

@router.get("/{collection_id}/overview", response_model=CollectionOverviewResponse)
async def get_collection_overview(
    collection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CollectionOverviewResponse:
    """Get comprehensive overview of a collection."""
    overview = CollectionIntelligence.get_collection_overview(
        db, collection_id, current_user.id
    )
    
    if not overview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Collection not found"
        )
    
    return CollectionOverviewResponse(**overview)


@router.get("/{collection_id}/related", response_model=List[RelatedCollectionResponse])
async def get_related_collections(
    collection_id: int,
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[RelatedCollectionResponse]:
    """Find collections with similar content."""
    related = CollectionIntelligence.get_related_collections(
        db, collection_id, current_user.id, limit
    )
    
    return [RelatedCollectionResponse(**r) for r in related]


@router.get("/knowledge-graph", response_model=KnowledgeGraphResponse)
async def get_knowledge_graph(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> KnowledgeGraphResponse:
    """Get knowledge graph data for all collections."""
    graph = CollectionIntelligence.get_knowledge_graph(db, current_user.id)
    
    return KnowledgeGraphResponse(**graph)
