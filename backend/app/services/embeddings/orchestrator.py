"""
Embedding Orchestrator

Main coordinator for the embedding generation pipeline.
Manages the flow from ProcessedDocument to stored vector.

Pipeline:
1. Get ProcessedDocument
2. Extract text
3. Generate embedding
4. Store in ChromaDB
5. Update DocumentEmbedding status
6. Find similar documents
"""

import logging
from typing import Optional, List, Tuple
from datetime import datetime
import pytz
import json
from sqlalchemy.orm import Session

from app.models import ProcessedDocument, DocumentEmbedding, Memory
from app.services.embeddings.embedding_service import get_embedding_service, EmbeddingService

logger = logging.getLogger(__name__)


class EmbeddingOrchestrator:
    """
    Manages the complete embedding generation pipeline.
    
    Handles:
    - Text extraction from ProcessedDocument
    - Embedding generation
    - ChromaDB storage
    - Status tracking
    - Error handling and recovery
    """
    
    def __init__(self):
        """Initialize orchestrator."""
        self.embedding_service: EmbeddingService = get_embedding_service()
    
    def generate_embedding(
        self,
        db: Session,
        processed_document_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Generate and store embedding for a processed document.
        
        Args:
            db: Database session
            processed_document_id: ID of ProcessedDocument
            user_id: User ID for isolation
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            # Get ProcessedDocument
            proc_doc = db.query(ProcessedDocument).filter(
                ProcessedDocument.id == processed_document_id,
                ProcessedDocument.user_id == user_id
            ).first()
            
            if not proc_doc:
                error = f"ProcessedDocument {processed_document_id} not found"
                logger.error(error)
                return False, error
            
            # Check if text was extracted
            if not proc_doc.extracted_text:
                error = f"No extracted text in ProcessedDocument {processed_document_id}"
                logger.warning(error)
                
                # Create failed embedding record
                self._create_failed_embedding(
                    db,
                    processed_document_id,
                    proc_doc.memory_id,
                    user_id,
                    error,
                    skip_reason="no_extracted_text"
                )
                return False, error
            
            # Generate embedding
            logger.info(f"Generating embedding for ProcessedDocument {processed_document_id}")
            embedding = self.embedding_service.embed_text(proc_doc.extracted_text)
            
            if not embedding:
                error = "Failed to generate embedding"
                logger.error(f"{error} for ProcessedDocument {processed_document_id}")
                
                self._create_failed_embedding(
                    db,
                    processed_document_id,
                    proc_doc.memory_id,
                    user_id,
                    error
                )
                return False, error
            
            # Create vector ID
            vector_id = f"proc_doc_{processed_document_id}_user_{user_id}"
            
            # Parse topics from JSON string
            topics_str = ""
            if proc_doc.topics:
                try:
                    topics_dict = json.loads(proc_doc.topics) if isinstance(proc_doc.topics, str) else proc_doc.topics
                    technologies = topics_dict.get("technologies", [])
                    topics_str = ",".join([t["name"] if isinstance(t, dict) else t for t in technologies[:5]])
                except (json.JSONDecodeError, TypeError, KeyError):
                    topics_str = ""
            
            # Store in ChromaDB
            metadata = {
                "processed_document_id": processed_document_id,
                "memory_id": proc_doc.memory_id,
                "user_id": user_id,
                "language": proc_doc.language,
                "topics": topics_str
            }
            
            stored = self.embedding_service.store_embedding(
                vector_id,
                proc_doc.extracted_text[:5000],  # Store first 5000 chars
                embedding,
                metadata
            )
            
            if not stored:
                logger.warning("Failed to store embedding in ChromaDB, but continuing...")
            
            # Create or update DocumentEmbedding record
            doc_embedding = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.processed_document_id == processed_document_id
            ).first()
            
            if doc_embedding:
                # Update existing
                doc_embedding.vector_id = vector_id
                doc_embedding.model_name = self.embedding_service.model_name
                doc_embedding.embedding_status = "generated"
                doc_embedding.embedding_error = None
                doc_embedding.text_length = len(proc_doc.extracted_text)
                doc_embedding.chunk_count = 1
                doc_embedding.embedded_at = datetime.now(pytz.UTC)
                doc_embedding.is_current = True
                doc_embedding.updated_at = datetime.now(pytz.UTC)
            else:
                # Create new
                doc_embedding = DocumentEmbedding(
                    processed_document_id=processed_document_id,
                    memory_id=proc_doc.memory_id,
                    user_id=user_id,
                    vector_id=vector_id,
                    model_name=self.embedding_service.model_name,
                    model_version="1.0",
                    embedding_dimension=len(embedding),
                    embedding_status="generated",
                    text_length=len(proc_doc.extracted_text),
                    chunk_count=1,
                    embedded_at=datetime.now(pytz.UTC),
                    is_current=True
                )
                db.add(doc_embedding)
            
            db.commit()
            logger.info(f"Successfully generated embedding for ProcessedDocument {processed_document_id}")
            return True, None
        
        except Exception as e:
            db.rollback()
            error = f"Exception during embedding generation: {str(e)}"
            logger.error(error, exc_info=True)
            
            try:
                self._create_failed_embedding(
                    db,
                    processed_document_id,
                    -1,  # user_id will be set if we can get it
                    user_id,
                    error
                )
            except:
                pass
            
            return False, error
    
    def find_related_documents(
        self,
        db: Session,
        processed_document_id: int,
        user_id: int,
        top_k: int = 5,
        min_similarity: float = 0.3
    ) -> List[Tuple[int, float]]:
        """
        Find related (similar) documents.
        
        Args:
            db: Database session
            processed_document_id: ID of reference document
            user_id: User ID for isolation
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
            
        Returns:
            List of (memory_id, similarity_score) tuples
        """
        try:
            # Get embedding for reference document
            doc_embedding = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.processed_document_id == processed_document_id,
                DocumentEmbedding.user_id == user_id,
                DocumentEmbedding.embedding_status == "generated"
            ).first()
            
            if not doc_embedding or not doc_embedding.vector_id:
                logger.warning(f"No embedding found for ProcessedDocument {processed_document_id}")
                return []
            
            # Get embedding from ChromaDB
            embedding = self._get_embedding_from_chromadb(doc_embedding.vector_id)
            
            if not embedding:
                logger.warning(f"Could not retrieve embedding {doc_embedding.vector_id}")
                return []
            
            # Find similar embeddings
            similar = self.embedding_service.find_similar(embedding, user_id, top_k * 2)
            
            if not similar:
                logger.info(f"No similar documents found for {processed_document_id}")
                return []
            
            # Map vector IDs to memory IDs and filter by similarity
            results = []
            for vector_id, similarity_score in similar:
                # Parse vector_id to get processed_document_id
                try:
                    parts = vector_id.split("_")
                    if len(parts) >= 3 and parts[0] == "proc" and parts[1] == "doc":
                        similar_proc_doc_id = int(parts[2])
                        
                        # Skip the reference document itself
                        if similar_proc_doc_id == processed_document_id:
                            continue
                        
                        # Filter by similarity threshold
                        if similarity_score >= min_similarity:
                            # Get memory_id
                            similar_proc_doc = db.query(ProcessedDocument).filter(
                                ProcessedDocument.id == similar_proc_doc_id,
                                ProcessedDocument.user_id == user_id
                            ).first()
                            
                            if similar_proc_doc:
                                results.append((similar_proc_doc.memory_id, similarity_score))
                except (IndexError, ValueError):
                    logger.debug(f"Could not parse vector_id: {vector_id}")
                    continue
            
            logger.info(f"Found {len(results)} related documents for ProcessedDocument {processed_document_id}")
            return results[:top_k]
        
        except Exception as e:
            logger.error(f"Error finding related documents: {e}", exc_info=True)
            return []
    
    def semantic_search(
        self,
        db: Session,
        query: str,
        user_id: int,
        top_k: int = 10,
        min_similarity: float = 0.3
    ) -> List[Tuple[int, str, float]]:
        """
        Perform semantic search.
        
        Args:
            db: Database session
            query: Search query
            user_id: User ID for isolation
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
            
        Returns:
            List of (memory_id, title, similarity_score) tuples
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_text(query)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Find similar embeddings
            similar = self.embedding_service.find_similar(query_embedding, user_id, top_k)
            
            results = []
            for vector_id, similarity_score in similar:
                # Filter by similarity threshold
                if similarity_score >= min_similarity:
                    # Parse vector_id to get memory_id
                    try:
                        parts = vector_id.split("_")
                        if len(parts) >= 3 and parts[0] == "proc" and parts[1] == "doc":
                            proc_doc_id = int(parts[2])
                            
                            # Get memory info
                            proc_doc = db.query(ProcessedDocument).filter(
                                ProcessedDocument.id == proc_doc_id,
                                ProcessedDocument.user_id == user_id
                            ).first()
                            
                            if proc_doc:
                                memory = db.query(Memory).filter(
                                    Memory.id == proc_doc.memory_id,
                                    Memory.user_id == user_id
                                ).first()
                                
                                if memory:
                                    results.append((
                                        memory.id,
                                        memory.original_filename,
                                        similarity_score
                                    ))
                    except (IndexError, ValueError):
                        logger.debug(f"Could not parse vector_id: {vector_id}")
                        continue
            
            logger.info(f"Semantic search returned {len(results)} results for query: {query}")
            return results
        
        except Exception as e:
            logger.error(f"Error during semantic search: {e}", exc_info=True)
            return []
    
    def _create_failed_embedding(
        self,
        db: Session,
        processed_document_id: int,
        memory_id: int,
        user_id: int,
        error_message: str,
        skip_reason: Optional[str] = None
    ) -> None:
        """Create a failed embedding record."""
        try:
            doc_embedding = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.processed_document_id == processed_document_id
            ).first()
            
            if not doc_embedding:
                doc_embedding = DocumentEmbedding(
                    processed_document_id=processed_document_id,
                    memory_id=memory_id,
                    user_id=user_id,
                    model_name=self.embedding_service.model_name,
                    model_version="1.0",
                    embedding_dimension=0,
                    embedding_status="failed",
                    embedding_error=error_message[:500],
                    skip_reason=skip_reason,
                    is_current=False
                )
                db.add(doc_embedding)
            else:
                doc_embedding.embedding_status = "failed"
                doc_embedding.embedding_error = error_message[:500]
                doc_embedding.skip_reason = skip_reason
                doc_embedding.is_current = False
                doc_embedding.updated_at = datetime.now(pytz.UTC)
            
            db.commit()
            logger.info(f"Created failed embedding record for ProcessedDocument {processed_document_id}")
        except Exception as e:
            logger.error(f"Failed to create failed embedding record: {e}")
            db.rollback()
    
    def get_memory_recommendations(
        self,
        db: Session,
        memory_id: int,
        user_id: int,
        top_k: int = 5
    ) -> List[Tuple[int, str, float]]:
        """
        Get recommended related memories for a specific memory.
        
        Args:
            db: Database session
            memory_id: Memory ID
            user_id: User ID for isolation
            top_k: Number of recommendations
            
        Returns:
            List of (memory_id, filename, similarity_score) tuples
        """
        try:
            # Get ProcessedDocument for this memory
            proc_doc = db.query(ProcessedDocument).filter(
                ProcessedDocument.memory_id == memory_id,
                ProcessedDocument.user_id == user_id
            ).first()
            
            if not proc_doc:
                return []
            
            # Find related documents
            related = self.find_related_documents(db, proc_doc.id, user_id, top_k)
            
            # Convert to (memory_id, filename, score) format
            results = []
            for related_memory_id, score in related:
                memory = db.query(Memory).filter(
                    Memory.id == related_memory_id,
                    Memory.user_id == user_id
                ).first()
                
                if memory:
                    results.append((related_memory_id, memory.original_filename, score))
            
            return results
        except Exception as e:
            logger.error(f"Error getting memory recommendations: {e}")
            return []
    
    def discover_memories(
        self,
        db: Session,
        user_id: int,
        limit: int = 20,
        min_similarity: float = 0.5
    ) -> List[Tuple[int, str, List[Tuple[int, str, float]]]]:
        """
        Discover interesting memory connections for a user.
        
        Returns memory IDs with their related memories.
        
        Args:
            db: Database session
            user_id: User ID for isolation
            limit: Max memories to return
            min_similarity: Minimum similarity to include
            
        Returns:
            List of (memory_id, filename, [(related_id, related_name, score), ...])
        """
        try:
            # Get recent memories for this user
            recent_memories = db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            ).order_by(Memory.upload_date.desc()).limit(limit).all()
            
            results = []
            for memory in recent_memories:
                # Get related memories for each
                related = self.get_memory_recommendations(
                    db,
                    memory.id,
                    user_id,
                    top_k=3
                )
                
                if related:
                    # Filter by similarity
                    filtered_related = [(m_id, fname, score) for m_id, fname, score in related if score >= min_similarity]
                    if filtered_related:
                        results.append((memory.id, memory.original_filename, filtered_related))
            
            return results
        except Exception as e:
            logger.error(f"Error discovering memories: {e}")
            return []
    
    def _get_embedding_from_chromadb(self, vector_id: str) -> Optional[List[float]]:
        """
        Retrieve embedding from ChromaDB by ID.
        
        This is a helper to get the actual vector for similarity operations.
        """
        try:
            if not self.embedding_service.collection:
                return None
            
            results = self.embedding_service.collection.get(
                ids=[vector_id],
                include=["embeddings"]
            )
            
            if results and results["embeddings"] and len(results["embeddings"]) > 0:
                return results["embeddings"][0]
            
            return None
        except Exception as e:
            logger.error(f"Failed to get embedding from ChromaDB: {e}")
            return None
    
    def get_embedding_stats(self, db: Session, user_id: int) -> dict:
        """Get embedding statistics for a user."""
        try:
            total = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.user_id == user_id
            ).count()
            
            generated = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.user_id == user_id,
                DocumentEmbedding.embedding_status == "generated"
            ).count()
            
            failed = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.user_id == user_id,
                DocumentEmbedding.embedding_status == "failed"
            ).count()
            
            pending = db.query(DocumentEmbedding).filter(
                DocumentEmbedding.user_id == user_id,
                DocumentEmbedding.embedding_status == "pending"
            ).count()
            
            return {
                "total_embeddings": total,
                "generated": generated,
                "failed": failed,
                "pending": pending,
                "success_rate": round((generated / total * 100) if total > 0 else 0, 2)
            }
        except Exception as e:
            logger.error(f"Error getting embedding stats: {e}")
            return {
                "total_embeddings": 0,
                "generated": 0,
                "failed": 0,
                "pending": 0,
                "success_rate": 0
            }
