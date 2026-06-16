#!/usr/bin/env python
"""
Initialize Phase 4 database schema.

Creates the ProcessedDocument table and indexes.
Safe to run multiple times (idempotent).
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.db.session import engine, Base
from app.models.processed_document import ProcessedDocument
from app.models.models import User, Memory

def init_database():
    """Initialize all database tables."""
    print("Initializing database schema...")
    print(f"Database: {engine.url}")
    
    try:
        # Create all tables
        print("\n[*] Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify ProcessedDocument table
        inspector_sql = f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='processed_documents'
        """
        
        with engine.connect() as conn:
            result = conn.exec_driver_sql(inspector_sql)
            tables = result.fetchall()
            
            if tables:
                print("[OK] ProcessedDocument table created successfully")
            else:
                print("[!] ProcessedDocument table not found")
                return False
        
        # Count columns
        with engine.connect() as conn:
            columns_sql = "PRAGMA table_info(processed_documents)"
            result = conn.exec_driver_sql(columns_sql)
            columns = result.fetchall()
            print(f"[OK] Table has {len(columns)} columns")
            
            print("\n[COLUMNS]")
            for col in columns:
                # PRAGMA table_info returns: (cid, name, type, notnull, dflt_value, pk)
                if len(col) >= 6:
                    cid, col_name, col_type, not_null, default, pk = col[:6]
                    nullable = "nullable" if not not_null else "NOT NULL"
                    pk_mark = " [PRIMARY KEY]" if pk else ""
                    print(f"   - {col_name}: {col_type} - {nullable}{pk_mark}")
                else:
                    print(f"   - {col}")
        
        # Check indexes
        with engine.connect() as conn:
            indexes_sql = "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='processed_documents'"
            result = conn.exec_driver_sql(indexes_sql)
            indexes = result.fetchall()
            print(f"\n[INDEXES] {len(indexes)} found")
            for idx in indexes:
                print(f"   - {idx[0]}")
        
        print("\n" + "="*60)
        print("[SUCCESS] DATABASE INITIALIZATION COMPLETE")
        print("="*60)
        print("\nProcessedDocument table is ready for Phase 4 processing!")
        print("\nNext steps:")
        print("1. Start backend: python -m uvicorn main:app --reload")
        print("2. Test upload at: http://localhost:8000/docs")
        print("3. Query results at: /api/v1/processing/memories/{id}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
