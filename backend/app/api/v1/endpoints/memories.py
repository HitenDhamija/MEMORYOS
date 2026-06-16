"""
Memory management API endpoints.
Secure endpoints for file upload, storage, search, and management.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Request, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from concurrent.futures import ThreadPoolExecutor
from app.db.session import get_db
from app.models.models import User, Memory
from app.api.deps import get_current_user
from app.schemas.schemas import (
    MemoryCreate,
    MemoryUpdate,
    MemoryFileResponse,
    MemoryListResponse,
    TagUpdateRequest,
)
from app.services.memory_service import MemoryService
from app.services.processing import ProcessingOrchestrator
from app.utils.file_validator import FileValidator
from app.utils.storage import StorageService
from app.middleware.request_id import get_request_id
from app.utils.logging import security_logger, SecurityEventType, LogLevel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

# Thread pool for background processing
# Limit to 2 concurrent processing tasks to avoid overwhelming the system
processing_executor = ThreadPoolExecutor(max_workers=2)

router = APIRouter(prefix="/memories", tags=["memories"])


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/upload", response_model=MemoryFileResponse, status_code=status.HTTP_201_CREATED)
async def upload_memory(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
) -> Memory:
    """Upload file with metadata.
    
    Steps:
    1. Validate file (type, size, format)
    2. Save to secure storage
    3. Create memory record
    4. Queue for background processing
    5. Return memory info
    
    Security:
    - User authentication required
    - File type whitelist enforced
    - Size limits checked
    - Path traversal prevented
    """
    request_id = get_request_id(request)
    client_ip = get_client_ip(request)
    
    # Validate file
    is_valid, error, file_type = FileValidator.validate_file(file)
    if not is_valid:
        security_logger.log_suspicious_activity(
            activity_type="invalid_file_upload",
            user_id=current_user.id,
            request_id=request_id,
            ip_address=client_ip,
            details={"filename": file.filename, "error": error}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    try:
        # Read file data
        file_data = await file.read()
        file_size = len(file_data)
        
        # Create memory metadata schema
        memory_data = MemoryCreate(
            title=title,
            description=description,
            tags=tags
        )
        
        # Save to storage
        file_id, storage_path = StorageService.save_file(
            current_user.id,
            file_type,
            file_data,
            file.filename
        )
        
        # Create database record
        memory = MemoryService.create_memory(
            db,
            current_user.id,
            file.filename,
            file_type,
            file_size,
            storage_path,
            memory_data
        )
        
        # Queue background processing task
        background_tasks.add_task(
            _process_memory_background,
            memory.id,
            current_user.id,
            storage_path
        )
        
        # Log successful upload
        security_logger.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            user_id=current_user.id,
            request_id=request_id,
            ip_address=client_ip,
            severity=LogLevel.INFO,
            details={
                "activity_type": "file_upload_success",
                "filename": file.filename,
                "file_type": file_type,
                "file_size": file_size
            }
        )
        
        return memory
    
    except HTTPException:
        raise
    except Exception as e:
        security_logger.log_suspicious_activity(
            activity_type="file_upload_error",
            user_id=current_user.id,
            request_id=request_id,
            ip_address=client_ip,
            severity=LogLevel.ERROR,
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


def _process_memory_background(memory_id: int, user_id: int, storage_path: str):
    """Background task to process uploaded memory and generate embedding."""
    try:
        from app.db.session import SessionLocal
        from pathlib import Path
        from app.models import ProcessedDocument
        from app.services.embeddings import EmbeddingOrchestrator
        
        db = SessionLocal()
        
        # Build full file path
        file_path = str(Path(StorageService.get_upload_dir()) / storage_path)
        
        # Get memory
        memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user_id).first()
        if not memory:
            logger.warning(f"Memory {memory_id} not found for processing")
            return
        
        # Phase 4: Process document (extract text)
        logger.info(f"Starting Phase 4 processing for Memory {memory_id}")
        result = ProcessingOrchestrator.process_document(db, memory, file_path)
        
        if result:
            logger.info(f"Successfully completed Phase 4 processing for Memory {memory_id}")
            
            # Phase 5: Generate embedding if document was successfully processed
            try:
                proc_doc = db.query(ProcessedDocument).filter(
                    ProcessedDocument.memory_id == memory_id,
                    ProcessedDocument.user_id == user_id
                ).first()
                
                if proc_doc and proc_doc.processing_status == "processed":
                    logger.info(f"Starting Phase 5 embedding generation for ProcessedDocument {proc_doc.id}")
                    
                    embedding_orchestrator = EmbeddingOrchestrator()
                    success, error = embedding_orchestrator.generate_embedding(
                        db,
                        proc_doc.id,
                        user_id
                    )
                    
                    if success:
                        logger.info(f"Successfully generated embedding for ProcessedDocument {proc_doc.id}")
                    else:
                        logger.warning(f"Failed to generate embedding: {error}")
                else:
                    logger.warning(f"ProcessedDocument not ready for embedding generation")
            except Exception as e:
                logger.error(f"Error during Phase 5 embedding generation: {str(e)}", exc_info=True)
        else:
            logger.error(f"Failed to process Memory {memory_id}")
    except Exception as e:
        logger.error(f"Error in background processing for Memory {memory_id}: {str(e)}", exc_info=True)
    finally:
        db.close()


@router.get("", response_model=MemoryListResponse)
async def list_memories(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """List user's memories with pagination."""
    memories, total = MemoryService.list_memories(
        db,
        current_user.id,
        skip=skip,
        limit=limit
    )
    
    return {
        "items": memories,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/search", response_model=MemoryListResponse)
async def search_memories(
    query: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    file_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Search memories by metadata."""
    tags_list = None
    if tags:
        tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
    
    memories, total = MemoryService.search_memories(
        db,
        current_user.id,
        query=query,
        tags=tags_list,
        file_type=file_type,
        skip=skip,
        limit=limit
    )
    
    return {
        "items": memories,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{memory_id}", response_model=MemoryFileResponse)
async def get_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Memory:
    """Get single memory by ID."""
    return MemoryService.get_memory(db, current_user.id, memory_id)


@router.put("/{memory_id}", response_model=MemoryFileResponse)
async def update_memory(
    memory_id: int,
    update_data: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Memory:
    """Update memory metadata."""
    return MemoryService.update_memory(
        db,
        current_user.id,
        memory_id,
        update_data
    )


@router.delete("/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    request: Request = None,
    db: Session = Depends(get_db)
) -> None:
    """Delete memory (soft delete)."""
    request_id = get_request_id(request)
    client_ip = get_client_ip(request)
    
    success = MemoryService.delete_memory(
        db,
        current_user.id,
        memory_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )
    
    security_logger.log_security_event(
        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
        user_id=current_user.id,
        request_id=request_id,
        ip_address=client_ip,
        severity=LogLevel.INFO,
        details={
            "activity_type": "memory_deleted",
            "memory_id": memory_id
        }
    )


@router.get("/{memory_id}/tags", response_model=List[str])
async def get_memory_tags(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[str]:
    """Get tags for a specific memory."""
    memory = MemoryService.get_memory(db, current_user.id, memory_id)
    
    if not memory.tags:
        return []
    
    return [tag.strip() for tag in memory.tags.split(",")]


@router.post("/{memory_id}/tags", response_model=MemoryFileResponse)
async def add_tags(
    memory_id: int,
    request_data: TagUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Memory:
    """Add tags to memory."""
    memory = MemoryService.get_memory(db, current_user.id, memory_id)
    
    existing_tags = set()
    if memory.tags:
        existing_tags = set(tag.strip() for tag in memory.tags.split(","))
    
    for tag in request_data.tags:
        existing_tags.add(tag.strip())
    
    update_data = MemoryUpdate(tags=",".join(sorted(existing_tags)))
    return MemoryService.update_memory(
        db,
        current_user.id,
        memory_id,
        update_data
    )


@router.delete("/{memory_id}/tags/{tag}")
async def remove_tag(
    memory_id: int,
    tag: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MemoryFileResponse:
    """Remove specific tag from memory."""
    memory = MemoryService.get_memory(db, current_user.id, memory_id)
    
    if not memory.tags:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Memory has no tags"
        )
    
    tags_list = set(t.strip() for t in memory.tags.split(","))
    tags_list.discard(tag.strip())
    
    if tags_list:
        update_data = MemoryUpdate(tags=",".join(sorted(tags_list)))
    else:
        update_data = MemoryUpdate(tags=None)
    
    return MemoryService.update_memory(
        db,
        current_user.id,
        memory_id,
        update_data
    )


@router.get("/{memory_id}/download")
async def download_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download memory file."""
    memory = MemoryService.get_memory(db, current_user.id, memory_id)
    
    try:
        file_path = StorageService.get_upload_dir() / memory.storage_path
        return FileResponse(
            path=file_path,
            filename=memory.original_filename,
            media_type="application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download file"
        )


@router.get("/stats/summary")
async def get_storage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get storage summary for user."""
    total_size = MemoryService.get_total_storage_used(db, current_user.id)
    file_types = MemoryService.get_file_types_summary(db, current_user.id)
    tags = MemoryService.get_tags(db, current_user.id)
    
    total_files = sum(file_types.values())
    
    return {
        "total_size": total_size,
        "total_files": total_files,
        "file_types": file_types,
        "tags": tags
    }
