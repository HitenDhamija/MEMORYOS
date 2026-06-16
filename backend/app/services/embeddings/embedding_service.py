"""
Embedding Service

Generates vector embeddings for document text using Sentence Transformers.
Manages ChromaDB collection for vector storage and retrieval.
"""

import logging
import os
from typing import Optional, List, Tuple
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_MODEL = "all-MiniLM-L6-v2"  # Fast, 384-dimensional embeddings
DEFAULT_EMBEDDING_BATCH_SIZE = 32
CHROMA_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data")


class EmbeddingService:
    """
    Manages document embeddings using Sentence Transformers and ChromaDB.
    
    Features:
    - Lazy loading of embedding model
    - ChromaDB collection management
    - Batch embedding generation
    - Error handling and graceful degradation
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Initialize embedding service.
        
        Args:
            model_name: Sentence Transformers model identifier
        """
        self.model_name = model_name
        self.model = None
        self.model_loaded = False
        self.collection = None
        self.client = None
        self.chroma_available = CHROMADB_AVAILABLE
        self.transformers_available = TRANSFORMERS_AVAILABLE
        
        if not self.transformers_available:
            logger.warning("Sentence Transformers not available - embedding generation disabled")
        if not self.chroma_available:
            logger.warning("ChromaDB not available - vector storage disabled")
    
    def _load_model(self) -> bool:
        """
        Lazy load the embedding model.
        
        Returns:
            True if model loaded successfully, False otherwise
        """
        if self.model_loaded:
            return True
        
        if not self.transformers_available:
            logger.error("Cannot load model: Sentence Transformers not available")
            return False
        
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.model_loaded = True
            logger.info(f"Successfully loaded model: {self.model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            return False
    
    def _initialize_chromadb(self) -> bool:
        """
        Initialize ChromaDB client and collection.
        
        Returns:
            True if initialized successfully, False otherwise
        """
        if self.collection is not None:
            return True
        
        if not self.chroma_available:
            logger.error("Cannot initialize ChromaDB: package not available")
            return False
        
        try:
            # Create chroma data directory if it doesn't exist
            os.makedirs(CHROMA_DB_PATH, exist_ok=True)
            
            logger.info(f"Initializing ChromaDB at {CHROMA_DB_PATH}")
            
            # Use new ChromaDB persistent client API
            self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name="document_embeddings",
                metadata={"hnsw:space": "cosine"}  # Cosine similarity
            )
            
            logger.info("Successfully initialized ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            return False
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding as list of floats, or None if failed
        """
        if not text or not isinstance(text, str):
            logger.warning("Invalid text for embedding")
            return None
        
        # Clean text
        text = text.strip()
        if not text:
            logger.warning("Empty text after stripping")
            return None
        
        if not self._load_model():
            return None
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    def embed_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (or None for each failed text)
        """
        if not texts:
            return []
        
        if not self._load_model():
            return [None] * len(texts)
        
        try:
            # Filter out empty texts
            valid_texts = [(i, text.strip()) for i, text in enumerate(texts) if text and text.strip()]
            
            if not valid_texts:
                logger.warning("No valid texts in batch")
                return [None] * len(texts)
            
            # Generate embeddings in batches
            results = [None] * len(texts)
            
            for i in range(0, len(valid_texts), DEFAULT_EMBEDDING_BATCH_SIZE):
                batch = [text for _, text in valid_texts[i:i + DEFAULT_EMBEDDING_BATCH_SIZE]]
                embeddings = self.model.encode(batch, convert_to_numpy=True)
                
                for j, (original_idx, _) in enumerate(valid_texts[i:i + DEFAULT_EMBEDDING_BATCH_SIZE]):
                    results[original_idx] = embeddings[j].tolist()
            
            return results
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)
    
    def store_embedding(self, vector_id: str, text: str, embedding: List[float], metadata: dict = None) -> bool:
        """
        Store embedding in ChromaDB.
        
        Args:
            vector_id: Unique identifier for the vector
            text: Original text
            embedding: The embedding vector
            metadata: Optional metadata to store with vector
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self._initialize_chromadb():
            logger.warning("ChromaDB not available - skipping storage")
            return False
        
        if not vector_id or not embedding:
            logger.error("Invalid vector_id or embedding")
            return False
        
        try:
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata["text"] = text[:1000]  # Store first 1000 chars for reference
            metadata["model"] = self.model_name
            
            # Store in ChromaDB
            self.collection.add(
                ids=[vector_id],
                embeddings=[embedding],
                documents=[text[:500]],  # Store truncated text for reference
                metadatas=[metadata]
            )
            
            logger.info(f"Stored embedding for vector_id: {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store embedding in ChromaDB: {e}")
            return False
    
    def find_similar(self, embedding: List[float], user_id: int, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find similar embeddings in ChromaDB.
        
        Args:
            embedding: Query embedding
            user_id: User ID for filtering results
            top_k: Number of results to return
            
        Returns:
            List of (vector_id, similarity_score) tuples
        """
        if not self._initialize_chromadb():
            logger.warning("ChromaDB not available - cannot search")
            return []
        
        if not embedding or not isinstance(embedding, (list, np.ndarray)):
            logger.error("Invalid embedding")
            return []
        
        try:
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                where={"user_id": user_id} if user_id else None
            )
            
            if not results or not results["ids"] or not results["ids"][0]:
                return []
            
            # Calculate similarity scores (ChromaDB returns distances, convert to similarity)
            similarities = []
            for vector_id, distance in zip(results["ids"][0], results["distances"][0]):
                # For cosine distance: similarity = 1 - distance
                similarity = 1.0 - distance
                similarities.append((vector_id, similarity))
            
            return similarities
        except Exception as e:
            logger.error(f"Failed to search embeddings: {e}")
            return []
    
    def delete_embedding(self, vector_id: str) -> bool:
        """
        Delete an embedding from ChromaDB.
        
        Args:
            vector_id: The vector ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not self._initialize_chromadb():
            logger.warning("ChromaDB not available - cannot delete")
            return False
        
        if not vector_id:
            logger.error("Invalid vector_id")
            return False
        
        try:
            self.collection.delete(ids=[vector_id])
            logger.info(f"Deleted embedding: {vector_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete embedding: {e}")
            return False
    
    def update_embedding(self, vector_id: str, embedding: List[float], metadata: dict = None) -> bool:
        """
        Update an embedding in ChromaDB.
        
        Args:
            vector_id: The vector ID to update
            embedding: New embedding vector
            metadata: Updated metadata
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self._initialize_chromadb():
            logger.warning("ChromaDB not available - cannot update")
            return False
        
        try:
            # Delete old and create new
            self.delete_embedding(vector_id)
            if metadata:
                return self.store_embedding(vector_id, metadata.get("text", ""), embedding, metadata)
            else:
                return self.store_embedding(vector_id, "", embedding)
        except Exception as e:
            logger.error(f"Failed to update embedding: {e}")
            return False
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        info = {
            "model_name": self.model_name,
            "transformers_available": self.transformers_available,
            "model_loaded": self.model_loaded,
        }
        
        if self.model_loaded and self.model:
            info["embedding_dimension"] = self.model.get_sentence_embedding_dimension()
            info["model_max_length"] = self.model.max_seq_length
        
        info["chromadb_available"] = self.chroma_available
        info["chroma_path"] = CHROMA_DB_PATH
        
        return info


# Global instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
