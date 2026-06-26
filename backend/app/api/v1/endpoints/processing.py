"""
Document Processing Endpoints

API endpoints for accessing and managing document processing results.
"""

import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.models import User, Memory
from app.models.processed_document import ProcessedDocument
from app.schemas.schemas import ProcessedDocumentResponse, ProcessingStatsResponse
from app.services.processing import ProcessingOrchestrator
from app.utils.storage import StorageService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/processing",
    tags=["processing"],
    dependencies=[Depends(get_current_user)]
)


@router.get("/memories/{memory_id}", response_model=ProcessedDocumentResponse)
async def get_processed_document(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get processed document details for a memory.
    
    Returns extracted text, metadata, structure, and analysis results.
    """
    # Verify memory exists and belongs to user
    memory = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.user_id == current_user.id,
        Memory.is_deleted == False
    ).first()
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Get or create processed document
    processed = db.query(ProcessedDocument).filter(
        ProcessedDocument.memory_id == memory_id,
        ProcessedDocument.user_id == current_user.id
    ).first()
    
    if not processed:
        # Create if it doesn't exist
        processed = ProcessedDocument(
            memory_id=memory_id,
            user_id=current_user.id,
            processing_status="pending"
        )
        db.add(processed)
        db.commit()
    
    return processed.to_dict()


@router.post("/memories/{memory_id}/reprocess")
async def reprocess_memory(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Force reprocessing of a memory (useful for retrying failed processing).
    """
    # Verify memory exists and belongs to user
    memory = db.query(Memory).filter(
        Memory.id == memory_id,
        Memory.user_id == current_user.id,
        Memory.is_deleted == False
    ).first()
    
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    # Get file path from storage
    storage_path = memory.storage_path
    if not storage_path:
        raise HTTPException(status_code=400, detail="Memory has no associated file")
    
    try:
        # Build full file path
        file_path = str(Path(StorageService.get_upload_dir()) / storage_path)
        
        # Reprocess
        result = ProcessingOrchestrator.reprocess_document(
            db,
            memory_id,
            current_user.id,
            file_path
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Failed to reprocess document")
        
        return result.to_dict()
    except Exception as e:
        logger.error(f"Error reprocessing memory {memory_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reprocess document")


@router.get("/stats", response_model=ProcessingStatsResponse)
async def get_processing_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get processing statistics for the current user.
    """
    stats = ProcessingOrchestrator.get_processing_stats(db, current_user.id)
    return stats


@router.get("/memories/{memory_id}/preview")
async def get_document_preview(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get text preview of processed document (first 300 characters).
    """
    processed = db.query(ProcessedDocument).filter(
        ProcessedDocument.memory_id == memory_id,
        ProcessedDocument.user_id == current_user.id
    ).first()
    
    if not processed:
        raise HTTPException(status_code=404, detail="Processed document not found")
    
    return {
        "memory_id": memory_id,
        "preview": processed.preview,
        "word_count": processed.word_count,
        "status": processed.processing_status
    }


@router.get("/memories/{memory_id}/topics")
async def get_document_topics(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detected topics from processed document.
    """
    processed = db.query(ProcessedDocument).filter(
        ProcessedDocument.memory_id == memory_id,
        ProcessedDocument.user_id == current_user.id
    ).first()
    
    if not processed:
        raise HTTPException(status_code=404, detail="Processed document not found")
    
    return {
        "memory_id": memory_id,
        "topics": processed.topics,
        "status": processed.processing_status
    }


@router.get("/memories/{memory_id}/metadata")
async def get_document_metadata(
    memory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get extracted metadata from processed document.
    """
    processed = db.query(ProcessedDocument).filter(
        ProcessedDocument.memory_id == memory_id,
        ProcessedDocument.user_id == current_user.id
    ).first()
    
    if not processed:
        raise HTTPException(status_code=404, detail="Processed document not found")
    
    return {
        "memory_id": memory_id,
        "metadata": processed.doc_metadata,
        "structure": processed.document_structure,
        "status": processed.processing_status
    }
