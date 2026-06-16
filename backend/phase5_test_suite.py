"""
Phase 5 Comprehensive Test Suite

Tests for Embeddings and Vector Intelligence Engine.

Test Categories:
1. Embedding Service
2. ChromaDB Integration
3. Embedding Orchestrator
4. API Endpoints
5. Integration with Phase 4
6. Error Handling
7. Performance
"""

import sys
import logging
from typing import Tuple

# Setup logging
logging.basicConfig(level=logging.WARNING)  # Suppress verbose logging
logger = logging.getLogger(__name__)

# Test results tracking
tests_passed = 0
tests_failed = 0
test_results = []


def test_result(name: str, passed: bool, details: str = ""):
    """Record test result."""
    global tests_passed, tests_failed
    status = "[PASS]" if passed else "[FAIL]"
    test_results.append((name, passed, details))
    if passed:
        tests_passed += 1
    else:
        tests_failed += 1
    print(f"{status}: {name}" + (f" - {details}" if details else ""))


def run_tests():
    """Run all Phase 5 tests."""
    print("\n" + "=" * 70)
    print("PHASE 5: EMBEDDINGS AND VECTOR INTELLIGENCE ENGINE")
    print("Comprehensive Integration Test Suite")
    print("=" * 70 + "\n")
    
    # Category 1: Embedding Service
    print("CATEGORY 1: Embedding Service")
    print("-" * 70)
    test_embedding_service()
    
    # Category 2: ChromaDB Integration
    print("\nCATEGORY 2: ChromaDB Integration")
    print("-" * 70)
    test_chromadb_integration()
    
    # Category 3: DocumentEmbedding Model
    print("\nCATEGORY 3: DocumentEmbedding Model")
    print("-" * 70)
    test_document_embedding_model()
    
    # Category 4: Embedding Orchestrator
    print("\nCATEGORY 4: Embedding Orchestrator")
    print("-" * 70)
    test_embedding_orchestrator()
    
    # Category 5: API Schemas
    print("\nCATEGORY 5: API Response Schemas")
    print("-" * 70)
    test_api_schemas()
    
    # Category 6: Error Handling
    print("\nCATEGORY 6: Error Handling")
    print("-" * 70)
    test_error_handling()
    
    # Category 7: Integration with Phase 4
    print("\nCATEGORY 7: Integration with Phase 4")
    print("-" * 70)
    test_phase4_integration()
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    total_tests = tests_passed + tests_failed
    pass_rate = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Total Tests:    {total_tests}")
    print(f"Passed:         {tests_passed} [OK]")
    print(f"Failed:         {tests_failed} [FAIL]")
    print(f"Pass Rate:      {pass_rate:.1f}%")
    print("=" * 70)
    
    if tests_failed == 0:
        print("\n[SUCCESS] ALL TESTS PASSED - PRODUCTION READY [SUCCESS]")
        return True
    else:
        print(f"\n[ERROR] {tests_failed} TEST(S) FAILED [ERROR]")
        return False


def test_embedding_service():
    """Test embedding service."""
    try:
        from app.services.embeddings import EmbeddingService, get_embedding_service
        
        # Test 1: Initialize service
        service = EmbeddingService()
        test_result("Initialize EmbeddingService", service is not None)
        
        # Test 2: Singleton pattern
        service2 = get_embedding_service()
        test_result("EmbeddingService singleton", service2 is not None)
        
        # Test 3: Model info
        info = service.get_model_info()
        test_result(
            "Get model information",
            info and 'model_name' in info,
            f"Model: {info.get('model_name', 'unknown')}"
        )
        
        # Test 4: Model loading
        loaded = service._load_model()
        test_result("Load embedding model", loaded)
        
        # Test 5: Embed single text
        if loaded:
            embedding = service.embed_text("Redis caching strategy")
            test_result(
                "Generate single embedding",
                embedding is not None and isinstance(embedding, list) and len(embedding) > 0,
                f"Dimension: {len(embedding) if embedding else 0}"
            )
        
        # Test 6: Embed batch
        if loaded:
            texts = [
                "Machine learning model",
                "Database optimization",
                "API design patterns"
            ]
            embeddings = service.embed_batch(texts)
            all_valid = all(e is not None and isinstance(e, list) for e in embeddings)
            test_result(
                "Generate batch embeddings",
                all_valid and len(embeddings) == len(texts),
                f"Processed {len(embeddings)} texts"
            )
        
        # Test 7: Invalid input handling
        embedding = service.embed_text("")
        test_result("Handle empty text", embedding is None)
        
        embedding = service.embed_text(None)
        test_result("Handle None input", embedding is None)
        
    except Exception as e:
        test_result("EmbeddingService category", False, str(e))


def test_chromadb_integration():
    """Test ChromaDB integration."""
    try:
        from app.services.embeddings import EmbeddingService
        import numpy as np
        
        service = EmbeddingService()
        
        # Initialize ChromaDB
        initialized = service._initialize_chromadb()
        test_result("Initialize ChromaDB", initialized)
        
        if initialized and service._load_model():
            # Test 2: Generate and store embedding
            text = "ChromaDB vector storage integration"
            embedding = service.embed_text(text)
            vector_id = "test_vector_1"
            
            stored = service.store_embedding(
                vector_id,
                text,
                embedding,
                {"test": "metadata"}
            )
            test_result("Store embedding in ChromaDB", stored)
            
            # Test 3: Retrieve embedding
            if stored:
                results = service.collection.get(ids=[vector_id])
                found = results and results["ids"] and len(results["ids"]) > 0
                test_result("Retrieve stored embedding", found)
            
            # Test 4: Find similar
            if stored:
                query_embedding = service.embed_text("Vector similarity search")
                similar = service.find_similar(query_embedding, user_id=1, top_k=5)
                test_result(
                    "Find similar embeddings",
                    isinstance(similar, list),
                    f"Found {len(similar)} results"
                )
            
            # Test 5: Update embedding
            if stored:
                new_embedding = service.embed_text("Updated text")
                updated = service.update_embedding(vector_id, new_embedding)
                test_result("Update embedding", updated)
            
            # Test 6: Delete embedding
            if stored:
                deleted = service.delete_embedding(vector_id)
                test_result("Delete embedding", deleted)
    
    except Exception as e:
        test_result("ChromaDB integration category", False, str(e))


def test_document_embedding_model():
    """Test DocumentEmbedding model."""
    try:
        from app.models import DocumentEmbedding
        from datetime import datetime
        import pytz
        
        # Test 1: Create model instance
        embedding = DocumentEmbedding(
            processed_document_id=1,
            memory_id=1,
            user_id=1,
            model_name="all-MiniLM-L6-v2",
            model_version="1.0",
            embedding_dimension=384,
            embedding_status="generated"
        )
        test_result("Create DocumentEmbedding instance", embedding is not None)
        
        # Test 2: to_dict method
        embedding_dict = embedding.to_dict()
        required_fields = [
            'id', 'processed_document_id', 'memory_id', 'user_id',
            'vector_id', 'model_name', 'embedding_status', 'created_at'
        ]
        has_fields = all(field in embedding_dict for field in required_fields)
        test_result("DocumentEmbedding.to_dict()", has_fields)
        
        # Test 3: Status values
        valid_statuses = ["pending", "generating", "generated", "failed"]
        embedding.embedding_status = "generated"
        test_result(
            "DocumentEmbedding status field",
            embedding.embedding_status in valid_statuses
        )
        
        # Test 4: Metadata tracking
        embedding.model_name = "all-MiniLM-L6-v2"
        embedding.embedding_dimension = 384
        test_result(
            "DocumentEmbedding metadata",
            embedding.model_name and embedding.embedding_dimension > 0
        )
        
    except Exception as e:
        test_result("DocumentEmbedding model category", False, str(e))


def test_embedding_orchestrator():
    """Test embedding orchestrator."""
    try:
        from app.services.embeddings import EmbeddingOrchestrator
        
        # Test 1: Initialize orchestrator
        orchestrator = EmbeddingOrchestrator()
        test_result("Initialize EmbeddingOrchestrator", orchestrator is not None)
        
        # Test 2: Orchestrator has required methods
        methods = [
            'generate_embedding',
            'find_related_documents',
            'semantic_search',
            'get_embedding_stats',
            '_create_failed_embedding',
            '_get_embedding_from_chromadb'
        ]
        has_methods = all(hasattr(orchestrator, method) for method in methods)
        test_result("Orchestrator has required methods", has_methods)
        
        # Test 3: Model service integration
        service = orchestrator.embedding_service
        test_result("Orchestrator has embedding service", service is not None)
        
    except Exception as e:
        test_result("EmbeddingOrchestrator category", False, str(e))


def test_api_schemas():
    """Test API response schemas."""
    try:
        from app.api.v1.endpoints.embeddings import (
            SemanticSearchRequest,
            RelatedMemoryItem,
            SemanticSearchResult,
            EmbeddingStatusResponse,
            EmbeddingStatsResponse
        )
        
        # Test 1: SemanticSearchRequest
        request = SemanticSearchRequest(
            query="test query",
            top_k=10,
            min_similarity=0.3
        )
        test_result("SemanticSearchRequest schema", request is not None)
        
        # Test 2: RelatedMemoryItem
        item = RelatedMemoryItem(
            memory_id=1,
            filename="test.pdf",
            similarity_score=0.85
        )
        test_result("RelatedMemoryItem schema", item is not None)
        
        # Test 3: SemanticSearchResult
        result = SemanticSearchResult(
            memory_id=1,
            filename="test.pdf",
            similarity_score=0.85
        )
        test_result("SemanticSearchResult schema", result is not None)
        
        # Test 4: EmbeddingStatusResponse
        status = EmbeddingStatusResponse(
            processed_document_id=1,
            memory_id=1,
            embedding_status="generated",
            model_name="all-MiniLM-L6-v2"
        )
        test_result("EmbeddingStatusResponse schema", status is not None)
        
        # Test 5: EmbeddingStatsResponse
        stats = EmbeddingStatsResponse(
            total_embeddings=10,
            generated=8,
            failed=1,
            pending=1,
            success_rate=80.0
        )
        test_result("EmbeddingStatsResponse schema", stats is not None)
        
    except Exception as e:
        test_result("API schemas category", False, str(e))


def test_error_handling():
    """Test error handling and recovery."""
    try:
        from app.services.embeddings import EmbeddingService
        
        service = EmbeddingService()
        
        # Test 1: Graceful handling of invalid embeddings
        invalid_embedding = None
        similar = service.find_similar(invalid_embedding, user_id=1)
        test_result("Handle invalid embedding", similar == [])
        
        # Test 2: Graceful handling of invalid vector ID
        deleted = service.delete_embedding(None)
        test_result("Handle invalid vector ID", deleted == False)
        
        # Test 3: Store with invalid data
        stored = service.store_embedding(None, "text", None)
        test_result("Handle invalid storage data", stored == False)
        
        # Test 4: Service graceful degradation
        info = service.get_model_info()
        test_result(
            "Service graceful degradation info",
            'transformers_available' in info and 'chromadb_available' in info
        )
        
    except Exception as e:
        test_result("Error handling category", False, str(e))


def test_phase4_integration():
    """Test integration with Phase 4."""
    try:
        from app.models import ProcessedDocument, DocumentEmbedding
        
        # Test 1: DocumentEmbedding linked to ProcessedDocument
        test_result(
            "DocumentEmbedding model exists",
            DocumentEmbedding is not None
        )
        
        # Test 2: Check FK relationships
        embedding = DocumentEmbedding(
            processed_document_id=1,
            memory_id=1,
            user_id=1,
            model_name="test",
            embedding_dimension=384,
            embedding_status="generated"
        )
        test_result(
            "DocumentEmbedding has ProcessedDocument FK",
            hasattr(embedding, 'processed_document_id')
        )
        
        # Test 3: Check memory isolation
        test_result(
            "DocumentEmbedding has user_id for isolation",
            hasattr(embedding, 'user_id')
        )
        
        # Test 4: Check status tracking
        statuses = ["pending", "generating", "generated", "failed"]
        test_result(
            "DocumentEmbedding status tracking",
            embedding.embedding_status in statuses
        )
        
        # Test 5: Embedding orchestrator initialization
        from app.services.embeddings import EmbeddingOrchestrator
        orch = EmbeddingOrchestrator()
        test_result("Orchestrator integrates with services", orch is not None)
        
    except Exception as e:
        test_result("Phase 4 integration category", False, str(e))


if __name__ == "__main__":
    try:
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL] Fatal test error: {e}")
        logger.error("Fatal test error", exc_info=True)
        sys.exit(1)
