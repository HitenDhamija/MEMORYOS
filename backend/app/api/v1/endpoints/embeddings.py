"""
Embeddings API endpoints.

Endpoints for semantic search and related document discovery.
Uses vector embeddings stored in ChromaDB.
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import User, Memory
from app.models import ProcessedDocument, DocumentEmbedding
from app.api.deps import get_current_user
from app.services.embeddings import EmbeddingOrchestrator
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


# Request/Response schemas
class SemanticSearchRequest(BaseModel):
    """Semantic search query."""
    query: str
    top_k: Optional[int] = 10
    min_similarity: Optional[float] = 0.3


class RelatedMemoryItem(BaseModel):
    """Related memory with similarity score."""
    memory_id: int
    filename: str
    similarity_score: float
    processing_status: Optional[str] = None


class RelatedMemoriesResponse(BaseModel):
    """Response with related memories."""
    memory_id: int
    related_memories: List[RelatedMemoryItem]
    total_related: int


class SemanticSearchResult(BaseModel):
    """Single search result."""
    memory_id: int
    filename: str
    similarity_score: float
    preview: Optional[str] = None


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""
    query: str
    results: List[SemanticSearchResult]
    total_results: int


class EmbeddingStatusResponse(BaseModel):
    """Embedding status for a document."""
    processed_document_id: int
    memory_id: int
    embedding_status: str
    embedding_error: Optional[str] = None
    vector_id: Optional[str] = None
    model_name: str
    embedded_at: Optional[str] = None


class EmbeddingStatsResponse(BaseModel):
    """Embedding statistics for a user."""
    total_embeddings: int
    generated: int
    failed: int
    pending: int
    success_rate: float


# Initialize orchestrator
embedding_orchestrator = EmbeddingOrchestrator()


@router.get("/memories/{memory_id}/related", response_model=RelatedMemoriesResponse)
async def get_related_memories(
    memory_id: int,
    top_k: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.3, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get related (similar) memories for a document.
    
    Uses vector similarity to find semantically related documents.
    
    Args:
        memory_id: Reference memory ID
        top_k: Number of results (1-20)
        min_similarity: Minimum similarity score (0-1)
        
    Returns:
        Related memories with similarity scores
    """
    try:
        # Get memory and check ownership
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == current_user.id
        ).first()
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        # Get ProcessedDocument
        proc_doc = db.query(ProcessedDocument).filter(
            ProcessedDocument.memory_id == memory_id,
            ProcessedDocument.user_id == current_user.id
        ).first()
        
        if not proc_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not yet processed"
            )
        
        # Check if embedding exists
        doc_embedding = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.processed_document_id == proc_doc.id
        ).first()
        
        if not doc_embedding or doc_embedding.embedding_status != "generated":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Embedding not yet generated"
            )
        
        # Find related documents
        related = embedding_orchestrator.find_related_documents(
            db,
            proc_doc.id,
            current_user.id,
            top_k=top_k,
            min_similarity=min_similarity
        )
        
        # Get memory details for related documents
        related_memories = []
        for related_memory_id, similarity_score in related:
            related_mem = db.query(Memory).filter(
                Memory.id == related_memory_id,
                Memory.user_id == current_user.id
            ).first()
            
            if related_mem:
                related_proc_doc = db.query(ProcessedDocument).filter(
                    ProcessedDocument.memory_id == related_memory_id,
                    ProcessedDocument.user_id == current_user.id
                ).first()
                
                related_memories.append(RelatedMemoryItem(
                    memory_id=related_mem.id,
                    filename=related_mem.original_filename,
                    similarity_score=round(similarity_score, 4),
                    processing_status=related_proc_doc.processing_status if related_proc_doc else None
                ))
        
        return RelatedMemoriesResponse(
            memory_id=memory_id,
            related_memories=related_memories,
            total_related=len(related_memories)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting related memories: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get related memories"
        )


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Perform semantic search.
    
    Generates embedding for query and finds semantically similar documents.
    
    Args:
        request: Search query and parameters
        
    Returns:
        Ranked list of relevant memories
    """
    try:
        # Validate query
        if not request.query or not request.query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        # Perform search
        results = embedding_orchestrator.semantic_search(
            db,
            request.query,
            current_user.id,
            top_k=request.top_k,
            min_similarity=request.min_similarity
        )
        
        # Format results
        search_results = []
        for memory_id, filename, similarity_score in results:
            # Get preview from ProcessedDocument
            proc_doc = db.query(ProcessedDocument).filter(
                ProcessedDocument.memory_id == memory_id,
                ProcessedDocument.user_id == current_user.id
            ).first()
            
            search_results.append(SemanticSearchResult(
                memory_id=memory_id,
                filename=filename,
                similarity_score=round(similarity_score, 4),
                preview=proc_doc.preview if proc_doc else None
            ))
        
        return SemanticSearchResponse(
            query=request.query,
            results=search_results,
            total_results=len(search_results)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during semantic search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform semantic search"
        )


@router.get("/memories/{memory_id}/status", response_model=EmbeddingStatusResponse)
async def get_embedding_status(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get embedding status for a memory.
    
    Args:
        memory_id: Memory ID
        
    Returns:
        Embedding status and metadata
    """
    try:
        # Get memory
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == current_user.id
        ).first()
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        # Get ProcessedDocument
        proc_doc = db.query(ProcessedDocument).filter(
            ProcessedDocument.memory_id == memory_id,
            ProcessedDocument.user_id == current_user.id
        ).first()
        
        if not proc_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not yet processed"
            )
        
        # Get embedding status
        doc_embedding = db.query(DocumentEmbedding).filter(
            DocumentEmbedding.processed_document_id == proc_doc.id
        ).first()
        
        if not doc_embedding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embedding not yet created"
            )
        
        return EmbeddingStatusResponse(
            processed_document_id=proc_doc.id,
            memory_id=memory_id,
            embedding_status=doc_embedding.embedding_status,
            embedding_error=doc_embedding.embedding_error,
            vector_id=doc_embedding.vector_id,
            model_name=doc_embedding.model_name,
            embedded_at=doc_embedding.embedded_at.isoformat() if doc_embedding.embedded_at else None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting embedding status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get embedding status"
        )


@router.get("/stats", response_model=EmbeddingStatsResponse)
async def get_embedding_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get embedding statistics for current user.
    
    Returns:
        Count of generated, failed, and pending embeddings
    """
    try:
        stats = embedding_orchestrator.get_embedding_stats(db, current_user.id)
        return EmbeddingStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting embedding stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get embedding statistics"
        )


@router.post("/memories/{memory_id}/re-embed")
async def re_embed_document(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Force re-generation of embedding for a document.
    
    Useful if text was updated or model was upgraded.
    
    Args:
        memory_id: Memory ID
        
    Returns:
        Status of re-embedding
    """
    try:
        # Get memory
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == current_user.id
        ).first()
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        # Get ProcessedDocument
        proc_doc = db.query(ProcessedDocument).filter(
            ProcessedDocument.memory_id == memory_id,
            ProcessedDocument.user_id == current_user.id
        ).first()
        
        if not proc_doc or proc_doc.processing_status != "processed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document must be processed before embedding"
            )
        
        # Regenerate embedding
        success, error = embedding_orchestrator.generate_embedding(
            db,
            proc_doc.id,
            current_user.id
        )
        
        if success:
            return {
                "status": "success",
                "message": "Embedding regenerated",
                "processed_document_id": proc_doc.id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to regenerate embedding: {error}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error re-embedding document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to re-embed document"
        )
