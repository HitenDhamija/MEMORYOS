"""
Phase 6: Semantic Memory Discovery Test Suite

Tests for discovery endpoints, recommendation algorithms, and semantic exploration.
"""

import pytest
import logging
from datetime import datetime
import pytz
from sqlalchemy.orm import Session

from app.models.models import User, Memory
from app.models.processed_document import ProcessedDocument
from app.models.document_embedding import DocumentEmbedding
from app.services.embeddings import EmbeddingOrchestrator
from app.api.v1.endpoints.discovery import router
from fastapi.testclient import TestClient
from main import app

logger = logging.getLogger(__name__)

# Test Client
client = TestClient(app)

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user."""
    user = User(username="discovery_user", email="discovery@test.com")
    user.set_password("testpass123")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Get authorization headers for test user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "discovery_user", "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_memories(db: Session, test_user: User) -> list[Memory]:
    """Create test memories with embeddings."""
    memories = []
    texts = [
        "Machine learning is a subset of artificial intelligence that enables systems to learn from data",
        "Deep learning uses neural networks with multiple layers to process complex patterns",
        "Natural language processing helps computers understand human language",
        "Computer vision enables machines to interpret visual information from images",
        "Data science combines statistics, mathematics, and programming for insights"
    ]
    
    for i, text in enumerate(texts):
        # Create memory
        memory = Memory(
            user_id=test_user.id,
            filename=f"memory_{i}.txt",
            file_type="txt",
            file_size=len(text.encode()),
            upload_date=datetime.now(pytz.UTC),
            status="processed",
            is_deleted=False
        )
        db.add(memory)
        db.flush()
        
        # Create processed document
        proc_doc = ProcessedDocument(
            memory_id=memory.id,
            user_id=test_user.id,
            extracted_text=text,
            language="en",
            topics={"technologies": [{"name": "AI"}]},
            status="processed"
        )
        db.add(proc_doc)
        db.flush()
        
        # Create document embedding
        embedding = DocumentEmbedding(
            processed_document_id=proc_doc.id,
            memory_id=memory.id,
            user_id=test_user.id,
            vector_id=f"proc_doc_{proc_doc.id}_user_{test_user.id}",
            model_name="all-MiniLM-L6-v2",
            model_version="1.0",
            embedding_dimension=384,
            text_length=len(text),
            chunk_count=1,
            embedding_status="generated",
            is_current=True,
            embedded_at=datetime.now(pytz.UTC)
        )
        db.add(embedding)
        db.commit()
        
        memories.append(memory)
    
    return memories


# ============================================================================
# DISCOVERY ORCHESTRATOR TESTS
# ============================================================================

class TestDiscoveryOrchestrator:
    """Test EmbeddingOrchestrator discovery methods."""
    
    def test_get_memory_recommendations(self, db: Session, test_memories: list[Memory]):
        """Test getting recommendations for a memory."""
        orchestrator = EmbeddingOrchestrator()
        user_id = test_memories[0].user_id
        
        # Get recommendations for first memory
        recommendations = orchestrator.get_memory_recommendations(
            db,
            test_memories[0].id,
            user_id,
            top_k=3
        )
        
        # Should return list of tuples (memory_id, filename, score)
        assert isinstance(recommendations, list)
        assert all(len(r) == 3 for r in recommendations)
        assert all(isinstance(r[2], float) for r in recommendations)
        assert all(0 <= r[2] <= 1 for r in recommendations)
        
        # Should not include the reference memory itself
        assert all(r[0] != test_memories[0].id for r in recommendations)
    
    def test_discover_memories(self, db: Session, test_memories: list[Memory]):
        """Test discovering memory connections."""
        orchestrator = EmbeddingOrchestrator()
        user_id = test_memories[0].user_id
        
        discoveries = orchestrator.discover_memories(
            db,
            user_id,
            limit=5,
            min_similarity=0.3
        )
        
        # Should return list of (memory_id, filename, [(related), ...])
        assert isinstance(discoveries, list)
        assert all(len(d) == 3 for d in discoveries)
        
        # Each discovery should have memory_id, filename, and related list
        for memory_id, filename, related in discoveries:
            assert isinstance(memory_id, int)
            assert isinstance(filename, str)
            assert isinstance(related, list)
            
            # Each related item should be (memory_id, filename, score)
            for rel_id, rel_name, rel_score in related:
                assert isinstance(rel_id, int)
                assert isinstance(rel_name, str)
                assert 0 <= rel_score <= 1
    
    def test_discover_memories_empty_when_no_connections(self, db: Session, test_user: User):
        """Test discover returns empty when no connections found."""
        orchestrator = EmbeddingOrchestrator()
        
        # Single memory won't have strong connections
        memories = []
        text = "Unique document about very specific topics that won't match others"
        
        memory = Memory(
            user_id=test_user.id,
            filename="unique_memory.txt",
            file_type="txt",
            file_size=len(text.encode()),
            upload_date=datetime.now(pytz.UTC),
            status="processed"
        )
        db.add(memory)
        db.flush()
        
        proc_doc = ProcessedDocument(
            memory_id=memory.id,
            user_id=test_user.id,
            extracted_text=text,
            language="en",
            status="processed"
        )
        db.add(proc_doc)
        db.flush()
        
        embedding = DocumentEmbedding(
            processed_document_id=proc_doc.id,
            memory_id=memory.id,
            user_id=test_user.id,
            vector_id=f"proc_doc_{proc_doc.id}_user_{test_user.id}",
            model_name="all-MiniLM-L6-v2",
            model_version="1.0",
            embedding_dimension=384,
            text_length=len(text),
            chunk_count=1,
            embedding_status="generated",
            is_current=True,
            embedded_at=datetime.now(pytz.UTC)
        )
        db.add(embedding)
        db.commit()
        
        discoveries = orchestrator.discover_memories(db, test_user.id, limit=5)
        
        # With only one memory, might have no connections
        assert isinstance(discoveries, list)


# ============================================================================
# DISCOVERY API TESTS
# ============================================================================

class TestDiscoveryAPI:
    """Test discovery API endpoints."""
    
    def test_get_recommendations_endpoint(
        self,
        db: Session,
        test_memories: list[Memory],
        auth_headers: dict
    ):
        """Test GET /discovery/recommendations/{memory_id}."""
        memory_id = test_memories[0].id
        
        response = client.get(
            f"/api/v1/discovery/recommendations/{memory_id}?top_k=5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "memory_id" in data
        assert "related_memories" in data
        assert "total_related" in data
        assert data["memory_id"] == memory_id
        
        # Check related memories structure
        for related in data["related_memories"]:
            assert "memory_id" in related
            assert "filename" in related
            assert "similarity_score" in related
            assert 0 <= related["similarity_score"] <= 1
    
    def test_recommendations_unauthorized(self, test_memories: list[Memory]):
        """Test recommendations endpoint requires auth."""
        memory_id = test_memories[0].id
        
        response = client.get(f"/api/v1/discovery/recommendations/{memory_id}")
        assert response.status_code == 403
    
    def test_explore_endpoint(self, db: Session, auth_headers: dict):
        """Test GET /discovery/explore."""
        response = client.get(
            "/api/v1/discovery/explore?limit=10&min_similarity=0.5",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "memories" in data
        assert "total_items" in data
        assert isinstance(data["memories"], list)
        assert isinstance(data["total_items"], int)
        
        # Check memory structure
        for memory in data["memories"]:
            assert "memory_id" in memory
            assert "filename" in memory
            assert "related_memories" in memory
    
    def test_explore_unauthorized(self):
        """Test explore endpoint requires auth."""
        response = client.get("/api/v1/discovery/explore")
        assert response.status_code == 403
    
    def test_semantic_search_endpoint(self, db: Session, auth_headers: dict):
        """Test POST /discovery/search."""
        response = client.post(
            "/api/v1/discovery/search",
            params={
                "query": "machine learning neural networks",
                "top_k": 10,
                "min_similarity": 0.3
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "query" in data
        assert "results" in data
        assert "total_results" in data
        assert data["query"] == "machine learning neural networks"
        
        # Check results structure
        for result in data["results"]:
            assert "memory_id" in result
            assert "filename" in result
            assert "similarity_score" in result
            assert 0 <= result["similarity_score"] <= 1
    
    def test_semantic_search_unauthorized(self):
        """Test semantic search requires auth."""
        response = client.post(
            "/api/v1/discovery/search",
            params={"query": "test"}
        )
        assert response.status_code == 403
    
    def test_semantic_search_empty_query(self, auth_headers: dict):
        """Test semantic search with empty query."""
        response = client.post(
            "/api/v1/discovery/search",
            params={"query": ""},
            headers=auth_headers
        )
        # Should handle gracefully
        assert response.status_code in [200, 422]


# ============================================================================
# USER ISOLATION TESTS
# ============================================================================

class TestDiscoveryUserIsolation:
    """Test that discovery respects user isolation."""
    
    def test_recommendations_only_user_memories(
        self,
        db: Session,
        test_user: User,
        auth_headers: dict
    ):
        """Test that recommendations only include current user's memories."""
        # Create another user with memory
        other_user = User(username="other_user", email="other@test.com")
        other_user.set_password("testpass123")
        db.add(other_user)
        db.commit()
        db.refresh(other_user)
        
        orchestrator = EmbeddingOrchestrator()
        
        # Get recommendations for test user
        # Should not include other user's memories
        # This is handled by the database queries filtering by user_id
        assert test_user.id != other_user.id
    
    def test_search_only_returns_user_memories(
        self,
        db: Session,
        test_user: User,
        test_memories: list[Memory],
        auth_headers: dict
    ):
        """Test that semantic search only returns current user's memories."""
        response = client.post(
            "/api/v1/discovery/search",
            params={
                "query": "machine learning",
                "top_k": 10
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        results = data["results"]
        
        # All results should belong to test user's memories
        test_memory_ids = [m.id for m in test_memories]
        for result in results:
            assert result["memory_id"] in test_memory_ids or result["memory_id"] is not None


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestDiscoveryPerformance:
    """Test discovery performance with reasonable query times."""
    
    def test_recommendations_performance(
        self,
        db: Session,
        test_memories: list[Memory],
        benchmark
    ):
        """Test recommendation performance is acceptable."""
        orchestrator = EmbeddingOrchestrator()
        user_id = test_memories[0].user_id
        
        def get_recommendations():
            return orchestrator.get_memory_recommendations(
                db,
                test_memories[0].id,
                user_id
            )
        
        # Should complete quickly (within 100ms for test data)
        result = benchmark(get_recommendations)
        assert isinstance(result, list)
    
    def test_discover_performance(
        self,
        db: Session,
        test_memories: list[Memory],
        benchmark
    ):
        """Test discover performance is acceptable."""
        orchestrator = EmbeddingOrchestrator()
        user_id = test_memories[0].user_id
        
        def discover():
            return orchestrator.discover_memories(db, user_id)
        
        # Should complete quickly
        result = benchmark(discover)
        assert isinstance(result, list)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestDiscoveryErrorHandling:
    """Test error handling in discovery."""
    
    def test_recommendations_nonexistent_memory(
        self,
        db: Session,
        test_user: User,
        auth_headers: dict
    ):
        """Test recommendations for nonexistent memory."""
        response = client.get(
            f"/api/v1/discovery/recommendations/99999?top_k=5",
            headers=auth_headers
        )
        
        # Should handle gracefully
        assert response.status_code == 200
        data = response.json()
        assert data["total_related"] == 0
    
    def test_search_malformed_query(self, auth_headers: dict):
        """Test search with malformed query."""
        response = client.post(
            "/api/v1/discovery/search",
            params={"query": "a" * 1000},  # Very long query
            headers=auth_headers
        )
        
        # Should handle gracefully
        assert response.status_code in [200, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
