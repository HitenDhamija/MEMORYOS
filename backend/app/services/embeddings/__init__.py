"""
Embeddings Service Package

Services for vector embedding generation and semantic search.
"""

from app.services.embeddings.embedding_service import (
    EmbeddingService,
    get_embedding_service
)
from app.services.embeddings.orchestrator import EmbeddingOrchestrator

__all__ = [
    'EmbeddingService',
    'get_embedding_service',
    'EmbeddingOrchestrator'
]
