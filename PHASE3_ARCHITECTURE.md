# Phase 3: Memory Library & Upload Engine - Architecture & Implementation Plan

**Date:** June 16, 2026  
**Phase:** 3 of N  
**Status:** Planning → Implementation  
**Dependencies:** Phase 2 (JWT Authentication) ✅ Complete

---

## 📐 Architecture Overview

### Core Principles
1. **Separation of Concerns** - Models, Services, Schemas, Routers
2. **Extensibility** - Easy to add new file types, storage backends, processing pipelines
3. **Security** - User isolation, file validation, authentication checks
4. **Scalability** - Prepared for distributed storage (S3/GCS migration path)
5. **Production-Ready** - Error handling, logging, transactions

### Storage Architecture

```
Memory Storage Structure:
uploads/
  {user_id}/
    pdf/
      {internal_id}_{original_filename}
    images/
      {internal_id}_{original_filename}
    notes/
      {internal_id}_{original_filename}
    bookmarks/
      {internal_id}_{original_filename}
    other/
      {internal_id}_{original_filename}

Database:
Memory table stores:
  - file_id (generated UUID)
  - user_id (foreign key to User)
  - original_filename
  - file_type (pdf, image, txt, md, bookmark)
  - file_size
  - storage_path (relative path from uploads/)
  - title (user-given name)
  - description (optional)
  - tags (comma-separated for MVP)
  - upload_date
  - updated_at
  - is_processed (false by default)
  - processing_status (pending, uploaded, processing, processed, failed)
  - is_deleted (soft delete)
```

### Service Layer Architecture

```
Request → Router → Service → Storage/DB
           ↓
         Auth Check
           ↓
       Validation
           ↓
      Business Logic
           ↓
    File/DB Operations
           ↓
       Response
```

**Layered Services:**
- `MemoryService` - Business logic (create, update, search)
- `StorageService` - File operations (save, delete, retrieve)
- `FileValidator` - File type and size validation
- `FileHandler` - File type-specific operations (future extensible for PDF parsing, OCR, etc.)

---

## 🔧 Backend Implementation

### 1. Models (SQLAlchemy)

**Location:** `backend/app/models/models.py` (extend existing)

```python
class Memory(Base):
    """Memory/Knowledge item model."""
    __tablename__ = "memories"
    
    # Identity
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File Info
    file_id = Column(String(255), unique=True, index=True, nullable=False)  # UUID
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False, index=True)  # pdf, image, txt, md, bookmark
    file_size = Column(Integer, nullable=False)  # bytes
    storage_path = Column(String(1000), nullable=False)  # relative to uploads/
    
    # Metadata
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(String(1000), nullable=True)  # comma-separated, "python,data,notes"
    
    # Processing
    is_processed = Column(Boolean, default=False, index=True)
    processing_status = Column(String(50), default="pending")  # pending, uploaded, processing, processed, failed
    processing_error = Column(Text, nullable=True)  # error message if processing failed
    
    # Soft Delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Timestamps
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime, nullable=True)
```

### 2. Schemas (Pydantic Validation)

**Location:** `backend/app/schemas/schemas.py` (extend existing)

```python
class MemoryCreate(BaseModel):
    """Memory creation from upload."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    tags: Optional[str] = None  # comma-separated
    # file uploaded separately via multipart

class MemoryUpdate(BaseModel):
    """Memory update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    tags: Optional[str] = None

class MemoryResponse(BaseModel):
    """Memory response schema."""
    id: int
    file_id: str
    user_id: int
    original_filename: str
    file_type: str
    file_size: int
    title: str
    description: Optional[str]
    tags: Optional[List[str]]
    is_processed: bool
    processing_status: str
    upload_date: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class MemoryListResponse(BaseModel):
    """Paginated memory list."""
    items: List[MemoryResponse]
    total: int
    skip: int
    limit: int

class MemorySearchRequest(BaseModel):
    """Search and filter request."""
    query: Optional[str] = None  # search in title, description
    tags: Optional[List[str]] = None  # filter by tags (AND logic)
    file_type: Optional[str] = None  # filter by file type
    skip: int = 0
    limit: int = 20
```

---

## 📁 File Storage Design

### Directory Structure
```
backend/
  uploads/
    user_1/
      pdf/
        a1b2c3d4_report.pdf
      images/
        e5f6g7h8_screenshot.png
      notes/
        i9j0k1l2_notes.txt
      bookmarks/
        m3n4o5p6_bookmark.md
      other/
        q7r8s9t0_file.docx

Key Points:
- user_id segregation for security
- file_type subdirectory for organization
- internal_id prefix for uniqueness (UUID)
- original_filename preserved for downloads
- No direct path traversal possible
```

### Configuration
```python
# backend/app/core/config.py (extend existing)

UPLOAD_DIR = "uploads"  # relative to backend/
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
ALLOWED_FILE_TYPES = {
    "pdf": {"extensions": [".pdf"], "mime_types": ["application/pdf"]},
    "image": {"extensions": [".jpg", ".jpeg", ".png", ".gif"], 
              "mime_types": ["image/jpeg", "image/png", "image/gif"]},
    "txt": {"extensions": [".txt"], "mime_types": ["text/plain"]},
    "md": {"extensions": [".md", ".markdown"], "mime_types": ["text/markdown"]},
    "bookmark": {"extensions": [".url", ".webloc"], "mime_types": ["text/plain"]},
}
```

---

## 🛠️ Service Layer Design

### StorageService (File Operations)

```python
class StorageService:
    """Handle file storage operations."""
    
    def save_file(self, user_id: int, file_type: str, file_data: bytes, 
                  original_filename: str) -> tuple[str, str]:
        """
        Save file and return (file_id, storage_path).
        
        file_id: UUID for unique identification
        storage_path: relative path (uploads/user_id/file_type/file_id_name)
        """
        
    def get_file(self, user_id: int, file_id: str) -> bytes:
        """Retrieve file by ID (with user auth check)."""
        
    def delete_file(self, user_id: int, file_id: str) -> bool:
        """Delete file from storage."""
        
    def get_file_path(self, storage_path: str) -> Path:
        """Convert relative storage path to absolute."""
```

### MemoryService (Business Logic)

```python
class MemoryService:
    """Handle memory management business logic."""
    
    def create_memory(self, db: Session, user_id: int, 
                     file_path: str, file_size: int, 
                     original_filename: str, file_type: str,
                     memory_data: MemoryCreate) -> Memory:
        """Create memory record in database."""
        
    def get_memory(self, db: Session, user_id: int, memory_id: int) -> Memory:
        """Get single memory (with auth check)."""
        
    def list_memories(self, db: Session, user_id: int, 
                     skip: int, limit: int) -> tuple[List[Memory], int]:
        """List user's memories with pagination."""
        
    def update_memory(self, db: Session, user_id: int, 
                     memory_id: int, update_data: MemoryUpdate) -> Memory:
        """Update memory metadata."""
        
    def delete_memory(self, db: Session, user_id: int, memory_id: int) -> bool:
        """Soft delete memory."""
        
    def search_memories(self, db: Session, user_id: int, 
                       query: str, tags: List[str], 
                       file_type: str) -> List[Memory]:
        """Search memories by metadata."""
        
    def add_tags(self, db: Session, user_id: int, 
                memory_id: int, tags: List[str]) -> Memory:
        """Add tags to memory."""
```

### FileValidator (Validation)

```python
class FileValidator:
    """Validate file type, size, content."""
    
    def validate_file(self, file: UploadFile, user_id: int) -> tuple[bool, str]:
        """Comprehensive file validation."""
        # Check extension
        # Check MIME type
        # Check file size
        # Check magic bytes (file signature)
        
    def get_file_type(self, filename: str, mime_type: str) -> Optional[str]:
        """Determine file_type category."""
```

---

## 🎯 API Endpoints Design

### Endpoints Overview

```
POST   /api/v1/memories/upload        - Upload file with metadata
GET    /api/v1/memories               - List user's memories (paginated)
GET    /api/v1/memories/{id}          - Get memory detail
PUT    /api/v1/memories/{id}          - Update memory metadata
DELETE /api/v1/memories/{id}          - Delete memory
GET    /api/v1/memories/search        - Search with filters
POST   /api/v1/memories/{id}/tags     - Add tags
DELETE /api/v1/memories/{id}/tags/{tag} - Remove tag
GET    /api/v1/memories/{id}/download - Download file
```

### Upload Endpoint Specifics

```python
@router.post("/upload")
async def upload_memory(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MemoryResponse:
    """
    Upload file with metadata.
    
    Security:
    - Authenticate user
    - Validate file type/size
    - Check file content (magic bytes)
    - Generate unique storage path
    
    Steps:
    1. Validate file (type, size, content)
    2. Save to storage
    3. Create database record
    4. Return memory info with processing status
    
    Responses:
    201 Created - File uploaded successfully
    400 Bad Request - Invalid file
    413 Payload Too Large - File too large
    415 Unsupported Media Type - File type not supported
    """
```

---

## 🎨 Frontend Implementation

### Component Hierarchy

```
(dashboard)
  /memories/
    ├── page.tsx (MemoryLibraryPage)
    │   ├── MemorySearchBar
    │   ├── MemoryTagFilter
    │   ├── MemoryList
    │   │   ├── MemoryCard (for each memory)
    │   │   │   ├── FileTypeIcon
    │   │   │   ├── Title
    │   │   │   ├── Tags
    │   │   │   ├── UploadDate
    │   │   │   └── Actions (View, Edit, Delete)
    │   └── UploadButton → MemoryUploadModal
    └── [id]/
        └── page.tsx (MemoryDetailPage)
            ├── FilePreview
            ├── Metadata
            ├── Tags
            └── Actions (Download, Edit, Delete)
```

### Services

```typescript
// memoryService.ts
- uploadMemory(file, metadata) - POST /memories/upload
- getMemories(skip, limit) - GET /memories
- getMemory(id) - GET /memories/{id}
- updateMemory(id, data) - PUT /memories/{id}
- deleteMemory(id) - DELETE /memories/{id}
- searchMemories(query, tags, fileType) - GET /memories/search
- addTags(id, tags) - POST /memories/{id}/tags
- removeTag(id, tag) - DELETE /memories/{id}/tags/{tag}
- downloadFile(id) - GET /memories/{id}/download
```

### Hooks

```typescript
// useMemories.ts
- const { memories, loading, error, pagination } = useMemories()
- const { search, filter, sort } = useMemoriesSearch()

// useMemoryUpload.ts
- const { upload, progress, error } = useMemoryUpload()
```

---

## 🔒 Security Considerations

### 1. User Isolation
- ✅ All queries filter by `user_id`
- ✅ Storage path includes `user_id`
- ✅ No cross-user access possible

### 2. File Validation
- ✅ Server-side file type validation
- ✅ MIME type checking
- ✅ Magic byte verification
- ✅ File size limits enforced
- ✅ Extension whitelist

### 3. Path Traversal Protection
- ✅ Storage paths never from user input
- ✅ UUID-based internal filenames
- ✅ No `../` allowed in paths

### 4. Authentication
- ✅ All endpoints require authentication
- ✅ Existing JWT system used
- ✅ Protected routes on frontend

### 5. CSRF Protection
- ✅ Inherits from auth system
- ✅ CSRF tokens on file upload form
- ✅ Validates on backend

---

## 📊 Database Schema Changes

### Migration Steps

```sql
-- Add memories table
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    file_id VARCHAR(255) UNIQUE NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_size INTEGER NOT NULL,
    storage_path VARCHAR(1000) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    tags VARCHAR(1000),
    is_processed BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX idx_memories_user_id ON memories(user_id);
CREATE INDEX idx_memories_file_type ON memories(file_type);
CREATE INDEX idx_memories_is_deleted ON memories(is_deleted);
CREATE INDEX idx_memories_processing_status ON memories(processing_status);
CREATE INDEX idx_memories_upload_date ON memories(upload_date DESC);
```

---

## 🎯 Implementation Phases

### Phase 3.1: Core Infrastructure (Today)
- [ ] Memory model
- [ ] Schemas and validation
- [ ] Storage service
- [ ] File validator
- [ ] Basic endpoints (CRUD)

### Phase 3.2: Frontend (Today)
- [ ] Memory service
- [ ] Upload component
- [ ] Memory library UI
- [ ] Search and filter

### Phase 3.3: Advanced Features (This Week)
- [ ] Full-text search on database
- [ ] Batch operations
- [ ] Export/import
- [ ] Advanced filtering

### Phase 3.4: Processing Pipeline (Next Week)
- [ ] Processing status updates
- [ ] Worker queue integration
- [ ] Progress tracking
- [ ] Ready for Phase 4 (AI processing)

---

## 🚀 Future Extensibility

### Adding New File Types

To add support for `.docx`, `.epub`, etc.:

1. **Update Config**
   ```python
   ALLOWED_FILE_TYPES["docx"] = {...}
   ```

2. **Add to FileValidator**
   - Add MIME type
   - Add magic bytes

3. **Create FileHandler** (Optional)
   ```python
   class DocxFileHandler(FileHandler):
       def extract_text(self) -> str: ...
       def get_metadata(self) -> dict: ...
   ```

4. **Phase 4: Content Extraction** (Later)
   - Add processor for new file type
   - Extract text/metadata
   - Generate embeddings

### Storage Backend Migration

To migrate from local storage to S3:

1. Create `S3StorageService` implementing `StorageService` interface
2. Update config to switch backends
3. No API changes needed (abstracted)

---

## 📝 Production Checklist

- [ ] All endpoints have authentication checks
- [ ] File size limits enforced
- [ ] MIME type validation working
- [ ] Path traversal impossible
- [ ] Soft delete working
- [ ] Search performant with indexes
- [ ] Error messages user-friendly
- [ ] Logging comprehensive
- [ ] Rate limiting on upload
- [ ] File cleanup on failed transactions

---

## Summary Table

| Component | Type | Purpose | Status |
|-----------|------|---------|--------|
| Memory Model | Backend | Database entity | Design ✓ |
| Storage Service | Backend | File ops | Design ✓ |
| Memory Service | Backend | Business logic | Design ✓ |
| File Validator | Backend | Validation | Design ✓ |
| API Endpoints | Backend | HTTP interface | Design ✓ |
| Memory Service | Frontend | API client | Design ✓ |
| Upload Component | Frontend | File upload UI | Design ✓ |
| Library UI | Frontend | Main dashboard | Design ✓ |
| Database | Infra | Data persistence | Design ✓ |

---

**Status:** Architecture complete. Ready for implementation.

**Next:** Implement backend (models, services, endpoints), then frontend (components, pages, hooks).
