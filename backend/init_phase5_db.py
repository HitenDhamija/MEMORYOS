"""
Phase 5 Database Initialization

Creates DocumentEmbedding table for storing vector embeddings.
Runs once on first deployment, idempotent.
"""

import logging
import sys
from sqlalchemy import inspect, text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_phase5_database():
    """Initialize Phase 5 database schema."""
    try:
        from app.db.session import engine, Base
        from app.models import DocumentEmbedding  # Import to ensure model is registered
        
        logger.info("=" * 60)
        logger.info("PHASE 5: Embeddings and Vector Intelligence Engine")
        logger.info("Database Initialization")
        logger.info("=" * 60)
        
        # Create tables
        logger.info("Creating Phase 5 tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✓ Tables created successfully")
        
        # Verify schema
        logger.info("\nVerifying schema...")
        inspector = inspect(engine)
        
        tables = inspector.get_table_names()
        if 'document_embeddings' in tables:
            logger.info("✓ DocumentEmbedding table exists")
            
            # List columns
            columns = inspector.get_columns('document_embeddings')
            logger.info(f"  Columns ({len(columns)}):")
            for col in columns:
                col_type = str(col['type'])
                nullable = "nullable" if col['nullable'] else "NOT NULL"
                logger.info(f"    - {col['name']:<25} {col_type:<20} {nullable}")
            
            # List indexes
            indexes = inspector.get_indexes('document_embeddings')
            if indexes:
                logger.info(f"  Indexes ({len(indexes)}):")
                for idx in indexes:
                    logger.info(f"    - {idx['name']}")
            
            # Foreign keys
            fks = inspector.get_foreign_keys('document_embeddings')
            if fks:
                logger.info(f"  Foreign Keys ({len(fks)}):")
                for fk in fks:
                    logger.info(f"    - {fk['constrained_columns']} → {fk['referred_table']}")
        else:
            logger.error("✗ DocumentEmbedding table NOT found")
            return False
        
        logger.info("\n" + "=" * 60)
        logger.info("PHASE 5 DATABASE INITIALIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info("\nNext steps:")
        logger.info("1. Install dependencies: pip install -r requirements.txt")
        logger.info("2. Start server: python -m uvicorn main:app --reload")
        logger.info("3. Access API: http://localhost:8000/docs")
        logger.info("\nPhase 5 Features:")
        logger.info("✓ Semantic embeddings (Sentence Transformers)")
        logger.info("✓ Vector storage (ChromaDB)")
        logger.info("✓ Related document discovery")
        logger.info("✓ Semantic search")
        logger.info("✓ Embedding status tracking")
        logger.info("=" * 60)
        
        return True
    
    except Exception as e:
        logger.error(f"✗ Failed to initialize Phase 5 database: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    try:
        success = init_phase5_database()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
