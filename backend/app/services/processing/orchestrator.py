"""
Processing Orchestrator

Main service that coordinates document processing.
Routes documents to appropriate processors and manages the pipeline.
"""

import logging
from typing import Optional
from datetime import datetime
import pytz

from sqlalchemy.orm import Session

from app.models.models import Memory
from app.models.processed_document import ProcessedDocument
from app.services.processing.base import DocumentProcessor, DummyProcessor
from app.services.processing.pdf_processor import PDFProcessor
from app.services.processing.text_processor import TextProcessor
from app.services.processing.markdown_processor import MarkdownProcessor
from app.services.processing.image_processor import ImageProcessor
from app.services.processing.bookmark_processor import BookmarkProcessor
from app.services.processing.topic_extractor import TopicExtractor
from app.services.processing.text_analyzer import TextAnalyzer

logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """
    Orchestrates document processing pipeline.
    
    Responsibilities:
    1. Route documents to appropriate processor based on file type
    2. Extract text, metadata, and structure
    3. Analyze text and extract topics
    4. Store processed data in database
    5. Handle errors and update processing status
    """
    
    PROCESSORS_MAP = {
        'pdf': PDFProcessor,
        'txt': TextProcessor,
        'md': MarkdownProcessor,
        'image': ImageProcessor,
        'bookmark': BookmarkProcessor,
    }
    
    @classmethod
    def process_document(
        cls,
        db: Session,
        memory: Memory,
        file_path: str
    ) -> Optional[ProcessedDocument]:
        """
        Process a document and store results.
        
        This is the main entry point for document processing.
        
        Args:
            db: Database session
            memory: Memory object with file metadata
            file_path: Full path to file on disk
            
        Returns:
            ProcessedDocument with results, or None if failed
        """
        try:
            # Create or get ProcessedDocument
            processed_doc = db.query(ProcessedDocument).filter(
                ProcessedDocument.memory_id == memory.id,
                ProcessedDocument.user_id == memory.user_id
            ).first()
            
            if not processed_doc:
                processed_doc = ProcessedDocument(
                    memory_id=memory.id,
                    user_id=memory.user_id,
                    processing_status="pending"
                )
                db.add(processed_doc)
                db.commit()
            
            # Update status to processing
            processed_doc.processing_status = "processing"
            db.commit()
            
            logger.info(f"Starting processing: Memory {memory.id}")
            
            # Get appropriate processor
            processor = cls._get_processor(memory.file_type, file_path, memory.original_filename)
            
            if not processor.can_process():
                raise ValueError(f"Processor cannot handle file: {memory.original_filename}")
            
            # Extract all data
            logger.debug(f"Extracting text from {memory.original_filename}")
            extracted_text, text_error = processor.extract_text_safe()
            
            logger.debug(f"Extracting metadata from {memory.original_filename}")
            metadata, metadata_error = processor.extract_metadata_safe()
            
            logger.debug(f"Extracting structure from {memory.original_filename}")
            document_structure, structure_error = processor.extract_structure_safe()
            
            # If all extractions failed, mark as failed
            if not extracted_text:
                error_msg = "Unable to extract content from document"
                if text_error:
                    error_msg += f": {text_error}"
                raise ValueError(error_msg)
            
            # Analyze text
            logger.debug(f"Analyzing text from {memory.original_filename}")
            analysis = TextAnalyzer.analyze(extracted_text)
            
            # Extract topics
            logger.debug(f"Extracting topics from {memory.original_filename}")
            topics = TopicExtractor.extract_topics(extracted_text)
            
            # Generate preview (first 300 characters)
            preview = extracted_text[:300] if extracted_text else ""
            
            # Update ProcessedDocument with results
            processed_doc.extracted_text = extracted_text
            processed_doc.preview = preview
            
            # Statistics from analysis
            processed_doc.word_count = analysis.get("word_count", 0)
            processed_doc.char_count = analysis.get("char_count", 0)
            processed_doc.language = analysis.get("language", "unknown")
            processed_doc.reading_time = analysis.get("reading_time", 0)
            
            # Extracted information
            processed_doc.topics = topics
            processed_doc.doc_metadata = metadata
            processed_doc.document_structure = document_structure
            
            # Mark as processed
            processed_doc.processing_status = "processed"
            processed_doc.processed_at = datetime.now(pytz.UTC)
            
            db.commit()
            
            logger.info(f"Successfully processed Memory {memory.id}: {processed_doc.word_count} words")
            
            return processed_doc
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing Memory {memory.id}: {error_msg}", exc_info=True)
            
            try:
                if processed_doc:
                    processed_doc.processing_status = "failed"
                    processed_doc.processing_error = error_msg
                    processed_doc.processed_at = datetime.now(pytz.UTC)
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update processing status: {db_error}")
            
            return None
    
    @classmethod
    def _get_processor(
        cls,
        file_type: str,
        file_path: str,
        original_filename: str
    ) -> DocumentProcessor:
        """
        Get appropriate processor for file type.
        
        Args:
            file_type: Type of file (pdf, txt, md, image, bookmark, other)
            file_path: Full path to file
            original_filename: Original filename
            
        Returns:
            Processor instance
        """
        # Normalize file type
        file_type = file_type.lower()
        
        # Get processor class
        processor_class = cls.PROCESSORS_MAP.get(file_type, DummyProcessor)
        
        # Instantiate and return
        processor = processor_class(file_path, original_filename)
        
        logger.debug(f"Using {processor_class.__name__} for {file_type}")
        
        return processor
    
    @classmethod
    def reprocess_document(
        cls,
        db: Session,
        memory_id: int,
        user_id: int,
        file_path: str
    ) -> Optional[ProcessedDocument]:
        """
        Reprocess a document (useful for retrying failed processing).
        
        Args:
            db: Database session
            memory_id: ID of memory to reprocess
            user_id: ID of user (for authorization)
            file_path: Full path to file
            
        Returns:
            ProcessedDocument with new results
        """
        # Get memory
        memory = db.query(Memory).filter(
            Memory.id == memory_id,
            Memory.user_id == user_id
        ).first()
        
        if not memory:
            logger.warning(f"Memory {memory_id} not found for user {user_id}")
            return None
        
        logger.info(f"Reprocessing Memory {memory_id}")
        
        # Delete existing processed document
        db.query(ProcessedDocument).filter(
            ProcessedDocument.memory_id == memory_id,
            ProcessedDocument.user_id == user_id
        ).delete()
        db.commit()
        
        # Process again
        return cls.process_document(db, memory, file_path)
    
    @classmethod
    def get_processing_stats(cls, db: Session, user_id: int) -> dict:
        """
        Get processing statistics for a user.
        
        Args:
            db: Database session
            user_id: ID of user
            
        Returns:
            Dictionary with processing stats
        """
        from sqlalchemy import func
        
        total = db.query(func.count(ProcessedDocument.id)).filter(
            ProcessedDocument.user_id == user_id
        ).scalar() or 0
        
        processed = db.query(func.count(ProcessedDocument.id)).filter(
            ProcessedDocument.user_id == user_id,
            ProcessedDocument.processing_status == "processed"
        ).scalar() or 0
        
        failed = db.query(func.count(ProcessedDocument.id)).filter(
            ProcessedDocument.user_id == user_id,
            ProcessedDocument.processing_status == "failed"
        ).scalar() or 0
        
        processing = db.query(func.count(ProcessedDocument.id)).filter(
            ProcessedDocument.user_id == user_id,
            ProcessedDocument.processing_status == "processing"
        ).scalar() or 0
        
        total_words = db.query(func.sum(ProcessedDocument.word_count)).filter(
            ProcessedDocument.user_id == user_id,
            ProcessedDocument.processing_status == "processed"
        ).scalar() or 0
        
        return {
            "total_documents": total,
            "processed": processed,
            "failed": failed,
            "processing": processing,
            "total_words": total_words,
            "success_rate": round((processed / total * 100) if total > 0 else 0, 1)
        }


# Export module-level references for external access
PROCESSORS_MAP = ProcessingOrchestrator.PROCESSORS_MAP
__all__ = ['ProcessingOrchestrator', 'PROCESSORS_MAP']
