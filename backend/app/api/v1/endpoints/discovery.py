"""
Discovery API Endpoints

Semantic memory discovery and recommendations using embeddings.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User
from app.api.deps import get_current_user
from app.services.embeddings import EmbeddingOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/discovery", tags=["discovery"])

# Schemas
class RelatedMemory(BaseModel):
    memory_id: int
    filename: str
    similarity_score: float
    
    class Config:
        from_attributes = True


class MemoryRecommendations(BaseModel):
    memory_id: int
    filename: str
    related_memories: List[RelatedMemory]
    total_related: int
    
    class Config:
        from_attributes = True


class DiscoveryItem(BaseModel):
    memory_id: int
    filename: str
    related_memories: List[RelatedMemory]
    
    class Config:
        from_attributes = True


class DiscoveryResponse(BaseModel):
    memories: List[DiscoveryItem]
    total_items: int
    
    class Config:
        from_attributes = True


@router.get("/recommendations/{memory_id}", response_model=MemoryRecommendations)
async def get_recommendations(
    memory_id: int,
    top_k: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MemoryRecommendations:
    """
    Get recommended related memories for a specific memory.
    
    Returns similar documents based on semantic similarity.
    """
    try:
        orchestrator = EmbeddingOrchestrator()
        related = orchestrator.get_memory_recommendations(
            db,
            memory_id,
            current_user.id,
            top_k
        )
        
        related_items = [
            RelatedMemory(
                memory_id=m_id,
                filename=fname,
                similarity_score=round(score, 4)
            )
            for m_id, fname, score in related
        ]
        
        return MemoryRecommendations(
            memory_id=memory_id,
            filename="",
            related_memories=related_items,
            total_related=len(related_items)
        )
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations"
        )


@router.get("/explore", response_model=DiscoveryResponse)
async def explore_memories(
    limit: int = Query(20, ge=1, le=100),
    min_similarity: float = Query(0.5, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> DiscoveryResponse:
    """
    Explore memory connections and related content.
    
    Discovers interesting semantic relationships between memories.
    """
    try:
        orchestrator = EmbeddingOrchestrator()
        discovered = orchestrator.discover_memories(
            db,
            current_user.id,
            limit,
            min_similarity
        )
        
        items = []
        for memory_id, filename, related in discovered:
            related_items = [
                RelatedMemory(
                    memory_id=m_id,
                    filename=fname,
                    similarity_score=round(score, 4)
                )
                for m_id, fname, score in related
            ]
            
            items.append(DiscoveryItem(
                memory_id=memory_id,
                filename=filename,
                related_memories=related_items
            ))
        
        return DiscoveryResponse(
            memories=items,
            total_items=len(items)
        )
    except Exception as e:
        logger.error(f"Error exploring memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to explore memories"
        )


@router.post("/search")
async def semantic_search(
    query: str = Query(..., min_length=1, max_length=500),
    top_k: int = Query(10, ge=1, le=50),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Semantic search across user's memories.
    
    Search by meaning, not just keywords.
    """
    try:
        orchestrator = EmbeddingOrchestrator()
        results = orchestrator.semantic_search(
            db,
            query,
            current_user.id,
            top_k,
            min_similarity
        )
        
        search_results = [
            {
                "memory_id": m_id,
                "filename": fname,
                "similarity_score": round(score, 4)
            }
            for m_id, fname, score in results
        ]
        
        return {
            "query": query,
            "results": search_results,
            "total_results": len(search_results)
        }
    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )
