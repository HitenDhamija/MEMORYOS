"""
Memory service for business logic.
"""

from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.models import Memory
from app.models.processed_document import ProcessedDocument
from app.models.document_embedding import DocumentEmbedding
from app.schemas.schemas import MemoryCreate, MemoryUpdate, RelatedMemoryResponse
import uuid
import json
import logging

logger = logging.getLogger(__name__)


class MemoryService:
    """Handle memory management business logic."""
    
    @staticmethod
    def convert_tags_to_list(memory: Memory) -> Memory:
        """Convert tags from comma-separated string to list.
        
        Args:
            memory: Memory object with tags as string
            
        Returns:
            Memory object with tags as list
        """
        if memory and memory.tags and isinstance(memory.tags, str):
            memory.tags = [tag.strip() for tag in memory.tags.split(',') if tag.strip()]
        return memory
    
    @staticmethod
    def create_memory(
        db: Session,
        user_id: int,
        original_filename: str,
        file_type: str,
        file_size: int,
        storage_path: str,
        memory_data: MemoryCreate
    ) -> Memory:
        """Create new memory record in database.
        
        Args:
            db: Database session
            user_id: User ID
            original_filename: Original uploaded filename
            file_type: File type category
            file_size: File size in bytes
            storage_path: Relative storage path
            memory_data: Memory metadata from form
            
        Returns:
            Created Memory object
        """
        file_id = str(uuid.uuid4())
        
        memory = Memory(
            user_id=user_id,
            file_id=file_id,
            original_filename=original_filename,
            file_type=file_type,
            file_size=file_size,
            storage_path=storage_path,
            title=memory_data.title,
            description=memory_data.description,
            tags=memory_data.tags,
            processing_status="pending"
        )
        
        db.add(memory)
        db.commit()
        db.refresh(memory)
        
        return memory
    
    @staticmethod
    def get_memory(db: Session, user_id: int, memory_id: int) -> Memory:
        """Get memory by ID (with user auth check).
        
        Raises:
            HTTPException: 404 if not found or user unauthorized
        """
        memory = db.query(Memory).filter(
            and_(
                Memory.id == memory_id,
                Memory.user_id == user_id,
                Memory.is_deleted == False
            )
        ).first()
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        return memory
    
    @staticmethod
    def list_memories(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Memory], int]:
        """List user's non-deleted memories with pagination.
        
        Returns:
            (memories: List[Memory], total_count: int)
        """
        query = db.query(Memory).filter(
            and_(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            )
        ).order_by(Memory.upload_date.desc())
        
        total = query.count()
        memories = query.offset(skip).limit(limit).all()
        
        return memories, total
    
    @staticmethod
    def update_memory(
        db: Session,
        user_id: int,
        memory_id: int,
        update_data: MemoryUpdate
    ) -> Memory:
        """Update memory metadata.
        
        Raises:
            HTTPException: 404 if not found or user unauthorized
        """
        memory = MemoryService.get_memory(db, user_id, memory_id)
        
        # Update fields that are provided
        if update_data.title is not None:
            memory.title = update_data.title
        if update_data.description is not None:
            memory.description = update_data.description
        if update_data.tags is not None:
            memory.tags = update_data.tags
        
        memory.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(memory)
        
        return memory
    
    @staticmethod
    def delete_memory(
        db: Session,
        user_id: int,
        memory_id: int
    ) -> bool:
        """Soft delete memory (mark as deleted).
        
        Returns:
            True if deleted, False if not found
        """
        memory = db.query(Memory).filter(
            and_(
                Memory.id == memory_id,
                Memory.user_id == user_id
            )
        ).first()
        
        if not memory:
            return False
        
        memory.is_deleted = True
        memory.deleted_at = datetime.now(timezone.utc)
        
        db.commit()
        
        return True
    
    @staticmethod
    def search_memories(
        db: Session,
        user_id: int,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        file_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Memory], int]:
        """Search memories by metadata.
        
        Args:
            db: Database session
            user_id: User ID
            query: Search in title and description
            tags: Filter by tags (AND logic)
            file_type: Filter by file type
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            (memories: List[Memory], total_count: int)
        """
        # Base query: user's non-deleted memories
        q = db.query(Memory).filter(
            and_(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            )
        )
        
        # Apply search filters
        if query:
            search_term = f"%{query}%"
            q = q.filter(
                or_(
                    Memory.title.ilike(search_term),
                    Memory.description.ilike(search_term)
                )
            )
        
        if file_type:
            q = q.filter(Memory.file_type == file_type)
        
        # Tag filtering (AND logic - must have all tags)
        if tags:
            for tag in tags:
                tag_pattern = f"%{tag}%"
                q = q.filter(Memory.tags.ilike(tag_pattern))
        
        # Order by upload date (newest first)
        q = q.order_by(Memory.upload_date.desc())
        
        total = q.count()
        memories = q.offset(skip).limit(limit).all()
        
        return memories, total
    
    @staticmethod
    def get_tags(db: Session, user_id: int) -> List[str]:
        """Get all unique tags used by user.
        
        Returns:
            List of tags (deduplicated and sorted)
        """
        memories = db.query(Memory).filter(
            and_(
                Memory.user_id == user_id,
                Memory.is_deleted == False,
                Memory.tags.isnot(None)
            )
        ).all()
        
        # Collect all tags
        tags_set = set()
        for memory in memories:
            if memory.tags:
                # Split comma-separated tags and strip whitespace
                tags = [tag.strip() for tag in memory.tags.split(",")]
                tags_set.update(tags)
        
        return sorted(list(tags_set))
    
    @staticmethod
    def get_file_types_summary(db: Session, user_id: int) -> dict:
        """Get summary of file types for user.
        
        Returns:
            {file_type: count, ...}
        """
        memories = db.query(Memory.file_type).filter(
            and_(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            )
        ).all()
        
        summary = {}
        for (file_type,) in memories:
            summary[file_type] = summary.get(file_type, 0) + 1
        
        return summary
    
    @staticmethod
    def get_total_storage_used(db: Session, user_id: int) -> int:
        """Get total storage used by user in bytes.
        
        Returns:
            Total size in bytes
        """
        result = db.query(Memory).filter(
            and_(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            )
        ).all()
        
        return sum(memory.file_size for memory in result)
    
    @staticmethod
    def get_memory_details(
        db: Session,
        user_id: int,
        memory_id: int,
        include_related: bool = True
    ) -> Dict[str, Any]:
        """Get complete memory details with processed document and related memories.
        
        Args:
            db: Database session
            user_id: User ID
            memory_id: Memory ID
            include_related: Include related memories (via embedding similarity)
            
        Returns:
            Dictionary with memory and processed document data
            
        Raises:
            HTTPException: 404 if memory not found
        """
        # Get memory
        memory = MemoryService.get_memory(db, user_id, memory_id)
        
        # Get processed document if exists
        proc_doc = db.query(ProcessedDocument).filter(
            and_(
                ProcessedDocument.memory_id == memory_id,
                ProcessedDocument.user_id == user_id
            )
        ).first()
        
        # Get related memories using embedding orchestrator
        related_memories = []
        if include_related and proc_doc:
            try:
                from app.services.embeddings.orchestrator import EmbeddingOrchestrator
                orchestrator = EmbeddingOrchestrator()
                
                # Find related documents
                related_results = orchestrator.find_related_documents(
                    db,
                    proc_doc.id,
                    user_id,
                    top_k=5,
                    min_similarity=0.3
                )
                
                # Build related memories response
                for related_memory_id, similarity_score in related_results:
                    try:
                        related_mem = db.query(Memory).filter(
                            and_(
                                Memory.id == related_memory_id,
                                Memory.user_id == user_id,
                                Memory.is_deleted == False
                            )
                        ).first()
                        
                        if related_mem:
                            # Get preview from related processed document
                            related_proc_doc = db.query(ProcessedDocument).filter(
                                ProcessedDocument.memory_id == related_memory_id
                            ).first()
                            
                            related_memories.append({
                                "id": related_mem.id,
                                "title": related_mem.title,
                                "file_type": related_mem.file_type,
                                "similarity_score": round(similarity_score, 2),
                                "preview": related_proc_doc.preview if related_proc_doc else None,
                                "upload_date": related_mem.upload_date
                            })
                    except Exception as e:
                        logger.warning(f"Failed to build related memory response: {e}")
                        
            except Exception as e:
                logger.warning(f"Failed to find related memories: {e}")
        
        # Build response dictionary
        result = {
            # Memory fields
            "id": memory.id,
            "file_id": memory.file_id,
            "user_id": memory.user_id,
            "original_filename": memory.original_filename,
            "file_type": memory.file_type,
            "file_size": memory.file_size,
            "title": memory.title,
            "description": memory.description,
            "tags": MemoryService.convert_tags_to_list(memory).tags,
            "upload_date": memory.upload_date,
            "updated_at": memory.updated_at,
            
            # Processing status
            "is_processed": memory.is_processed,
            "processing_status": memory.processing_status,
            "processed_at": memory.processed_at,
            "processing_error": memory.processing_error,
            
            # Processed document fields (if available)
            "extracted_text": proc_doc.extracted_text if proc_doc else None,
            "preview": proc_doc.preview if proc_doc else None,
            "summary": proc_doc.summary if proc_doc else None,
            "word_count": proc_doc.word_count if proc_doc else 0,
            "char_count": proc_doc.char_count if proc_doc else 0,
            "language": proc_doc.language if proc_doc else "unknown",
            "reading_time": proc_doc.reading_time if proc_doc else 0,
            "topics": proc_doc.topics if proc_doc else None,
            "doc_metadata": proc_doc.doc_metadata if proc_doc else None,
            "document_structure": proc_doc.document_structure if proc_doc else None,
            
            # Document Intelligence fields
            "document_overview": proc_doc.document_overview if proc_doc else None,
            "topics_covered": proc_doc.topics_covered if proc_doc else None,
            "key_concepts": proc_doc.key_concepts if proc_doc else None,
            "intelligent_keywords": proc_doc.intelligent_keywords if proc_doc else None,
            "doc_intelligence_metadata": proc_doc.doc_intelligence_metadata if proc_doc else None,
            "suggested_questions": proc_doc.suggested_questions if proc_doc else None,
            "learning_objectives": proc_doc.learning_objectives if proc_doc else None,
            "knowledge_nodes": proc_doc.knowledge_nodes if proc_doc else None,
            
            # Related memories
            "related_memories": related_memories
        }
        
        return result
