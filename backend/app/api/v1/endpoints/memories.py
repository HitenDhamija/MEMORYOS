"""
Memory management API endpoints.
Secure endpoints for file upload, storage, search, and management.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, Request, Query, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from concurrent.futures import ThreadPoolExecutor
from app.db.session import get_db, SessionLocal
from app.models.models import User, Memory
from app.models.collection import Collection
from app.api.deps import get_current_user
from app.schemas.schemas import (
    MemoryCreate,
    MemoryUpdate,
    MemoryFileResponse,
    MemoryListResponse,
    TagUpdateRequest,
    MemoryDetailsResponse,
)
from app.services.memory_service import MemoryService
from app.services.processing import ProcessingOrchestrator
from app.utils.file_validator import FileValidator
from app.utils.storage import StorageService
from app.middleware.request_id import get_request_id
from app.utils.logging import security_logger, SecurityEventType, LogLevel
from typing import Optional, List
from datetime import datetime, timezone
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
        
        # Convert tags from string to list for response schema
        memory = MemoryService.convert_tags_to_list(memory)
        
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
        from app.models.processed_document import ProcessedDocument
        from app.services.embeddings.orchestrator import EmbeddingOrchestrator
        from app.services.timeline.timeline_service import TimelineService
        
        print(f"🔄 BACKGROUND TASK STARTED for Memory {memory_id}")
        logger.info(f"🔄 BACKGROUND TASK STARTED for Memory {memory_id}")
        
        db = SessionLocal()
        
        # Build full file path
        file_path = str(Path(StorageService.get_upload_dir()) / storage_path)
        print(f"📁 Processing file: {file_path}")
        
        # Get memory
        memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user_id).first()
        if not memory:
            print(f"❌ Memory {memory_id} not found")
            logger.warning(f"Memory {memory_id} not found for processing")
            return
        
        # Create upload event
        try:
            TimelineService.create_event(
                db,
                user_id,
                event_type="upload",
                memory_id=memory_id,
                event_date=datetime.now(timezone.utc),
                event_data={
                    "title": memory.title,
                    "file_type": memory.file_type,
                    "file_size": memory.file_size
                }
            )
            print(f"📅 Timeline event created: upload")
        except Exception as e:
            logger.warning(f"Failed to create upload timeline event: {e}")
        
        # Update learning streak and evolution
        try:
            from app.services.timeline.evolution_service import LearningStreakService, KnowledgeEvolutionService
            LearningStreakService.update_streak(db, user_id)
            KnowledgeEvolutionService.update_evolution(db, user_id)
            print(f"📊 Learning streak and evolution updated")
        except Exception as e:
            logger.warning(f"Failed to update streak/evolution: {e}")
        
        # Phase 4: Process document (extract text)
        print(f"⚙️ PHASE 4: Processing document for Memory {memory_id}")
        logger.info(f"Starting Phase 4 processing for Memory {memory_id}")
        result = ProcessingOrchestrator.process_document(db, memory, file_path)
        
        if result:
            print(f"✅ PHASE 4 COMPLETED for Memory {memory_id}")
            logger.info(f"Successfully completed Phase 4 processing for Memory {memory_id}")
            
            # Update Memory status to processing
            memory.processing_status = "processing"
            db.commit()
            
            # Phase 4.5: Generate structured analysis from extracted text
            try:
                proc_doc = db.query(ProcessedDocument).filter(
                    ProcessedDocument.memory_id == memory_id,
                    ProcessedDocument.user_id == user_id
                ).first()
                
                if proc_doc and proc_doc.extracted_text:
                    from app.services.document_intelligence import DocumentIntelligence
                    
                    analysis = DocumentIntelligence.analyze(
                        proc_doc.extracted_text,
                        memory.original_filename,
                    )
                    
                    # Populate legacy summary field
                    proc_doc.summary = analysis.document_overview
                    
                    # Store all structured analysis fields
                    proc_doc.document_overview = analysis.document_overview
                    proc_doc.topics_covered = analysis.topics_covered
                    proc_doc.key_concepts = analysis.key_concepts
                    proc_doc.intelligent_keywords = analysis.keywords
                    proc_doc.doc_intelligence_metadata = analysis.document_metadata.model_dump()
                    proc_doc.suggested_questions = analysis.suggested_questions
                    proc_doc.learning_objectives = analysis.learning_objectives
                    proc_doc.type_specific_section = analysis.type_specific_section.model_dump()
                    proc_doc.knowledge_nodes = [node.model_dump() for node in analysis.knowledge_nodes]
                    
                    db.commit()
                    print(f"Document Intelligence: {len(analysis.topics_covered)} topics, {len(analysis.key_concepts)} concepts, {len(analysis.knowledge_nodes)} nodes")
            except Exception as e:
                logger.warning(f"Failed to generate document intelligence: {e}")
            
            # Create Phase 4 completion event
            try:
                proc_doc = db.query(ProcessedDocument).filter(
                    ProcessedDocument.memory_id == memory_id,
                    ProcessedDocument.user_id == user_id
                ).first()
                
                TimelineService.create_event(
                    db,
                    user_id,
                    event_type="document_processed",
                    memory_id=memory_id,
                    event_date=datetime.now(timezone.utc),
                    event_data={
                        "word_count": proc_doc.word_count if proc_doc else 0,
                        "topics": proc_doc.topics if proc_doc else []
                    }
                )
                print(f"📅 Timeline event created: document_processed")
            except Exception as e:
                logger.warning(f"Failed to create document_processed timeline event: {e}")
            
            # Phase 5: Generate embedding if document was successfully processed
            try:
                proc_doc = db.query(ProcessedDocument).filter(
                    ProcessedDocument.memory_id == memory_id,
                    ProcessedDocument.user_id == user_id
                ).first()
                
                if proc_doc and proc_doc.processing_status == "processed":
                    print(f"⚙️ PHASE 5: Generating embeddings for ProcessedDocument {proc_doc.id}")
                    logger.info(f"Starting Phase 5 embedding generation for ProcessedDocument {proc_doc.id}")
                    
                    embedding_orchestrator = EmbeddingOrchestrator()
                    success, error = embedding_orchestrator.generate_embedding(
                        db,
                        proc_doc.id,
                        user_id
                    )
                    
                    if success:
                        print(f"✅ PHASE 5 COMPLETED - Embedding generated for ProcessedDocument {proc_doc.id}")
                        logger.info(f"Successfully generated embedding for ProcessedDocument {proc_doc.id}")
                        
                        # Update Memory record to mark as processed
                        memory.is_processed = True
                        memory.processing_status = "processed"
                        memory.processed_at = datetime.now(timezone.utc)
                        db.commit()
                        print(f"📝 Updated Memory {memory_id} status to PROCESSED")
                        
                        # Create Phase 5 completion event
                        try:
                            TimelineService.create_event(
                                db,
                                user_id,
                                event_type="embedding_generated",
                                memory_id=memory_id,
                                event_date=datetime.now(timezone.utc),
                                event_data={
                                    "status": "completed"
                                }
                            )
                            print(f"📅 Timeline event created: embedding_generated")
                        except Exception as e:
                            logger.warning(f"Failed to create embedding_generated timeline event: {e}")
                        
                        # Phase 6: Auto-assign collections based on topics
                        try:
                            from app.services.collections.collection_service import CollectionService
                            
                            if proc_doc and proc_doc.topics:
                                print(f"⚙️ PHASE 6: Auto-assigning collections based on topics")
                                
                                # Extract topic names from topics dict
                                topic_names = []
                                topics_data = proc_doc.topics
                                if isinstance(topics_data, str):
                                    import json
                                    topics_data = json.loads(topics_data)
                                
                                if isinstance(topics_data, dict):
                                    # Try different topic category keys
                                    for key in ["technologies", "general", "keywords"]:
                                        if key in topics_data:
                                            items = topics_data[key]
                                            if isinstance(items, list):
                                                for item in items[:3]:  # Top 3 topics
                                                    if isinstance(item, dict) and "name" in item:
                                                        topic_names.append(item["name"])
                                                    elif isinstance(item, str):
                                                        topic_names.append(item)
                                
                                # Auto-create/assign collections
                                for topic_name in topic_names:
                                    try:
                                        # Check if collection exists
                                        existing = db.query(Collection).filter(
                                            Collection.user_id == user_id,
                                            Collection.name == topic_name,
                                            Collection.is_deleted == False
                                        ).first()
                                        
                                        if existing:
                                            collection = existing
                                        else:
                                            # Create new collection
                                            collection, error = CollectionService.create_collection(
                                                db,
                                                user_id,
                                                name=topic_name,
                                                description=f"Auto-created collection for {topic_name}"
                                            )
                                        
                                        if collection:
                                            # Add memory to collection
                                            CollectionService.add_memory_to_collection(
                                                db,
                                                user_id,
                                                collection.id,
                                                memory_id
                                            )
                                            print(f"✅ Memory assigned to collection: {topic_name}")
                                            
                                            # Create timeline event
                                            TimelineService.create_event(
                                                db,
                                                user_id,
                                                event_type="collection_assigned",
                                                memory_id=memory_id,
                                                collection_id=collection.id,
                                                event_date=datetime.now(timezone.utc),
                                                event_data={"collection_name": topic_name}
                                            )
                                    except Exception as e:
                                        logger.warning(f"Failed to auto-assign collection {topic_name}: {e}")
                                
                                print(f"✅ PHASE 6 COMPLETED - Collections auto-assigned")
                        except Exception as e:
                            logger.warning(f"Failed to auto-assign collections: {e}")

                    else:
                        print(f"❌ PHASE 5 FAILED: {error}")
                        logger.warning(f"Failed to generate embedding: {error}")
                else:
                    print(f"⚠️ ProcessedDocument not ready for embedding (status: {proc_doc.processing_status if proc_doc else 'NOT FOUND'})")
                    logger.warning(f"ProcessedDocument not ready for embedding generation")
            except Exception as e:
                print(f"❌ ERROR during PHASE 5: {str(e)}")
                logger.error(f"Error during Phase 5 embedding generation: {str(e)}", exc_info=True)
        else:
            print(f"❌ PHASE 4 FAILED for Memory {memory_id}")
            logger.error(f"Failed to process Memory {memory_id}")
            memory.processing_status = "failed"
            db.commit()
    except Exception as e:
        print(f"❌ ERROR in background processing for Memory {memory_id}: {str(e)}")
        logger.error(f"Error in background processing for Memory {memory_id}: {str(e)}", exc_info=True)
        # Mark as failed
        try:
            db = SessionLocal()
            memory = db.query(Memory).filter(Memory.id == memory_id, Memory.user_id == user_id).first()
            if memory:
                memory.processing_status = "failed"
                db.commit()
        except:
            pass
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
    
    # Convert tags from string to list for response schema
    memories = [MemoryService.convert_tags_to_list(m) for m in memories]
    
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
    
    # Convert tags from string to list for response schema
    memories = [MemoryService.convert_tags_to_list(m) for m in memories]
    
    return {
        "items": memories,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/semantic/search", response_model=MemoryListResponse)
async def semantic_search(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Semantic search across memories by meaning.
    Uses AI embeddings to find relevant memories even without exact keyword matches.
    """
    try:
        from app.services.embeddings.orchestrator import EmbeddingOrchestrator
        
        orchestrator = EmbeddingOrchestrator()
        results = orchestrator.semantic_search(
            db,
            q,
            current_user.id,
            top_k=limit,
            min_similarity=0.3
        )
        
        # Convert results to memory objects
        memories = []
        for memory_id, title, similarity_score in results:
            try:
                memory = MemoryService.get_memory(db, current_user.id, memory_id)
                memory = MemoryService.convert_tags_to_list(memory)
                memories.append(memory)
            except:
                pass
        
        return {
            "items": memories,
            "total": len(memories),
            "skip": 0,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        # Fallback to empty results
        return {
            "items": [],
            "total": 0,
            "skip": 0,
            "limit": limit
        }


@router.get("/{memory_id}", response_model=MemoryDetailsResponse)
async def get_memory(
    memory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """Get single memory details by ID with processed document and related memories."""
    details = MemoryService.get_memory_details(
        db, 
        current_user.id, 
        memory_id, 
        include_related=True
    )
    return details


@router.put("/{memory_id}", response_model=MemoryFileResponse)
async def update_memory(
    memory_id: int,
    update_data: MemoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Memory:
    """Update memory metadata."""
    memory = MemoryService.update_memory(
        db,
        current_user.id,
        memory_id,
        update_data
    )
    return MemoryService.convert_tags_to_list(memory)


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
    memory = MemoryService.update_memory(
        db,
        current_user.id,
        memory_id,
        update_data
    )
    return MemoryService.convert_tags_to_list(memory)


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
    
    memory = MemoryService.update_memory(
        db,
        current_user.id,
        memory_id,
        update_data
    )
    return MemoryService.convert_tags_to_list(memory)


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
