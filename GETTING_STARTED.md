# Getting Started Guide

Complete setup instructions for MemoryOS development environment.

## Prerequisites

- **Node.js** 18+ ([download](https://nodejs.org/))
- **Python** 3.11+ ([download](https://www.python.org/))
- **PostgreSQL** 12+ ([download](https://www.postgresql.org/))
- **Git** ([download](https://git-scm.com/))
- Code editor: **VS Code** recommended

## Backend Setup (FastAPI)

### 1. Create Virtual Environment

```bash
cd backend

# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Create PostgreSQL database:

```bash
# Using psql
createdb memoryos

# Or using GUI (pgAdmin)
# - Create new database named "memoryos"
```

### 4. Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/memoryos
SECRET_KEY=your-secret-key-minimum-32-characters-long
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
ENVIRONMENT=development
DEBUG=True
```

### 5. Database Tables

Run this to create tables:

```bash
python -c "
from app.db.session import engine, Base
from app.models.models import User, Memory
Base.metadata.create_all(bind=engine)
print('Database tables created!')
"
```

### 6. Start Backend Server

```bash
python -m uvicorn main:app --reload
```

✅ Server running at `http://localhost:8000`
📚 API docs at `http://localhost:8000/docs`

**Test endpoint:**
```bash
curl http://localhost:8000/health
```

## Frontend Setup (Next.js)

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Environment Variables

```bash
cp .env.example .env.local
```

Edit `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_TOKEN_KEY=auth_token
NEXT_PUBLIC_APP_NAME=MemoryOS
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Start Development Server

```bash
npm run dev
```

✅ Frontend running at `http://localhost:3000`

**Visit in browser to test**

## Testing the Application

### Register New User

1. Go to `http://localhost:3000/register`
2. Fill form:
   - Email: `user@example.com`
   - Username: `testuser`
   - Password: `Password123!`
   - Full Name: `Test User`
3. Click "Register"
4. Redirected to login

### Login

1. Go to `http://localhost:3000/login`
2. Enter credentials:
   - Email: `user@example.com`
   - Password: `Password123!`
3. Click "Login"
4. Redirected to dashboard

### Test API Directly

Use Swagger UI at `http://localhost:8000/docs`

## Phase 3: Memory Library

### Features

The Memory Library allows authenticated users to:

1. **Upload Files**
   - Supported formats: PDF, Images (JPG/PNG/GIF/WebP), TXT, Markdown, Bookmarks
   - Maximum file size: 100MB
   - Drag-and-drop upload interface
   - Add metadata: title, description, tags

2. **Organize Memories**
   - View all uploaded files in grid layout
   - Each memory shows: icon, title, file type, upload date, tags, processing status
   - Edit metadata (title, description, tags)
   - Soft delete with confirmation
   - Download files

3. **Search and Filter**
   - Search by title and description (full-text)
   - Filter by file type (PDF, Image, TXT, Markdown, Bookmark)
   - Filter by tags (AND logic - file must have all selected tags)
   - Clear filters quickly

4. **Storage Analytics**
   - Total files uploaded
   - Total storage used
   - Breakdown by file type
   - List of all tags used

### Using Memory Library

1. **Access Memory Library**
   - Navigate to "Memory Library" in top navigation
   - Or go to `http://localhost:3000/memories`

2. **Upload Memory**
   - Click "Upload Memory" button
   - Drag and drop file or click to select
   - Enter title (required)
   - Add description (optional)
   - Add tags (optional, comma-separated)
   - Click "Upload"

3. **Search and Filter**
   - Use search box to find by title/description
   - Click "File Type" dropdown to filter by type
   - Click "Tags" to filter by one or more tags
   - Click "Clear Filters" to reset

4. **Manage Memory**
   - Click "Download" to download file
   - Click "Edit" to update metadata
   - Click "Delete" to remove (soft delete, can be recovered by admin)

### Memory Card Details

Each memory card displays:
- **File Icon**: Visual representation of file type
- **Title**: User-defined title
- **Filename & Size**: Original filename and file size
- **Type Badge**: File type category
- **Status Badge**: Processing status (pending, uploaded, processing, processed, failed)
- **Description**: User-added notes (if provided)
- **Tags**: User-added tags for categorization
- **Upload Date**: When file was uploaded
- **Action Buttons**: Download, Edit, Delete

### Architecture

**Backend** (`/api/v1/memories`):
- `POST /upload` - Upload file with metadata
- `GET /` - List memories with pagination
- `GET /search` - Search and filter memories
- `GET /{id}` - Get single memory details
- `PUT /{id}` - Update metadata
- `DELETE /{id}` - Soft delete
- `POST /{id}/tags` - Add tags
- `DELETE /{id}/tags/{tag}` - Remove tag
- `GET /{id}/download` - Download file
- `GET /stats/summary` - Storage analytics

**Frontend** Components:
- `MemoryUploadZone` - Drag-and-drop upload with metadata form
- `MemoryCard` - Individual memory display and actions
- `MemorySearchFilter` - Search and filter interface
- `MemoryLibrary` - Grid layout with pagination
- `MemoriesPage` - Main dashboard page

**Storage**:
- Server-side: `uploads/user_id/file_type/file_id_original_name.ext`
- User isolation: All queries filter by user_id
- Soft delete: is_deleted flag prevents permanent data loss

### Important Notes

- Authentication is required to access Memory Library
- All memories are isolated per user (cannot see other users' files)
- Files are validated before upload (type, size, format)
- Search is full-text (title and description), not AI-powered semantic search
- Tags support basic filtering with AND logic
- Processing status tracking for future pipeline integration
- No AI, embeddings, OCR, or semantic search (Phase 4+)

1. Try `POST /api/v1/auth/register`
2. Try `POST /api/v1/auth/login` → Get token
3. Click "Authorize" button in Swagger UI
4. Paste token: `Bearer <your_token_here>`
5. Try protected endpoints like `GET /api/v1/users/me`

Or use curl:

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Password123!",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Password123!"
  }'

# Use token in subsequent requests
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer <token_from_login>"
```

## Project Structure Quick Reference

```
MemoryOS/
├── frontend/                  # Next.js app
│   ├── src/app/              # Routes & pages
│   ├── src/components/       # React components
│   ├── src/services/         # API clients
│   ├── package.json          # Dependencies
│   └── README.md             # Frontend docs
│
├── backend/                   # FastAPI app
│   ├── app/api/              # API endpoints
│   ├── app/models/           # Database models
│   ├── app/schemas/          # Validation schemas
│   ├── main.py               # App entry
│   ├── requirements.txt       # Dependencies
│   └── README.md             # Backend docs
│
├── README.md                 # Overview
├── ARCHITECTURE.md           # Technical design
└── GETTING_STARTED.md        # This file
```

## Troubleshooting

### Port Already in Use

**Backend (port 8000):**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

**Frontend (port 3000):**
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :3000
kill -9 <PID>
```

### Database Connection Error

1. Verify PostgreSQL is running
   ```bash
   # Windows
   psql -U postgres
   
   # macOS
   brew services list
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Check database exists: `psql -l | grep memoryos`

3. Verify DATABASE_URL in `.env`:
   - Format: `postgresql://username:password@host:port/database`
   - Username (default): `postgres`
   - Password: what you set during PostgreSQL install
   - Host: `localhost`
   - Port: `5432`

### CORS Errors

1. Verify backend `.env` has correct `CORS_ORIGINS`
2. Ensure it includes `http://localhost:3000`
3. Restart backend

### Token Issues

1. Clear browser cookies: Dev Tools → Application → Cookies → Delete
2. Try logging in again
3. Check backend `SECRET_KEY` is set (minimum 32 chars)

## Common Commands

### Backend

```bash
# Start server
python -m uvicorn main:app --reload

# Start with specific port
python -m uvicorn main:app --reload --port 8001

# Run tests (when available)
pytest tests/

# Format code
black app/
```

### Frontend

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Start production build
npm start

# Type checking
npm run type-check

# Linting
npm run lint
```

## Phase 4: Document Intelligence Engine

### Overview

Phase 4 adds automatic document processing that extracts structured information from uploaded files. This is **NOT** AI-powered - it's rule-based text extraction and analysis designed to prepare data for future Phase 5 AI/search features.

**What Happens**:
1. User uploads file (PDF, TXT, Markdown, Image, URL)
2. File saved to storage
3. Background task automatically processes the document
4. Extracted text, metadata, topics, and structure stored
5. User can query processed data via API

**Key Feature**: Processing happens **in background** - upload returns immediately.

### Processing Capabilities

#### Supported File Types

| Format | Text Extraction | Topics | Structure | Metadata |
|--------|-----------------|--------|-----------|----------|
| PDF | ✅ PyPDF2 | ✅ Keywords | ✅ Pages | ✅ Author, dates |
| TXT | ✅ File read | ✅ Keywords | ✅ Paragraphs | ✅ Basic |
| Markdown | ✅ Parser | ✅ Keywords | ✅ Headers, code | ✅ Front matter |
| Images | ✅ OCR* | ✅ Keywords | ✅ Dimensions | ✅ Format, size |
| URLs/Bookmarks | ✅ Fetch** | ✅ Keywords | ✅ Page structure | ✅ Title, desc |

*OCR requires pytesseract (optional, graceful fallback if missing)  
**URL fetch requires network access (optional, graceful fallback if missing)

#### Extracted Information

For each document, the system extracts:

**Text & Statistics**:
- Full extracted text
- Word count & character count
- Paragraph & sentence count
- Average word length
- Estimated reading time (words ÷ 200)
- Detected language (en, es, fr, de, zh, etc.)

**Topics (Rule-Based Detection)**:
- Technologies: Python, FastAPI, PostgreSQL, Docker, JWT, etc.
- General: Backend, Security, Performance, Architecture, etc.

**Structure**:
- PDF: Pages and layout info
- Markdown: Headers and code blocks
- Images: Resolution, format, color mode

**Metadata**:
- File title and author
- Creation/modification dates
- Page count (for PDFs)
- Image properties (for images)

**Preview**: First 300 characters for quick display

### Processing Status

Each document has a processing status:

```
pending    → uploaded → processing → processed ✅
                                  ↘ failed ❌
```

- **pending**: Created, waiting for processing
- **uploaded**: File saved, ready for processing
- **processing**: Currently extracting content
- **processed**: Complete, data ready for queries
- **failed**: Error occurred (can retry via API)

### Usage Examples

#### 1. Upload File (Automatic Processing)

```bash
curl -X POST http://localhost:8000/api/v1/memories/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@report.pdf" \
  -F "title=Q4 Report" \
  -F "description=Quarterly analysis" \
  -F "tags=report,q4,analysis"

# Response (instant):
{
  "id": 1,
  "title": "Q4 Report",
  "processing_status": "uploaded",
  "word_count": 0,  # Will be filled after processing
  "upload_date": "2026-06-16T10:00:00Z"
}
```

#### 2. Get Processed Data

```bash
# Wait a few seconds, then check:

curl -X GET http://localhost:8000/api/v1/processing/memories/1 \
  -H "Authorization: Bearer <token>"

# Response:
{
  "id": 1,
  "memory_id": 1,
  "processing_status": "processed",
  "word_count": 3241,
  "char_count": 18500,
  "reading_time": 16.2,  # minutes
  "language": "en",
  "topics": {
    "technologies": ["python", "postgresql", "fastapi"],
    "general": ["backend", "performance", "security"]
  },
  "preview": "Q4 Report 2026. This report summarizes...",
  "metadata": {
    "filename": "report.pdf",
    "file_size_bytes": 2048000,
    "page_count": 12
  },
  "document_structure": {
    "total_pages": 12,
    "pages": [...]
  }
}
```

#### 3. Get Quick Preview

```bash
curl -X GET http://localhost:8000/api/v1/processing/memories/1/preview \
  -H "Authorization: Bearer <token>"

# Response:
{
  "preview": "Q4 Report 2026. This report summarizes...",
  "word_count": 3241,
  "status": "processed"
}
```

#### 4. Get Detected Topics

```bash
curl -X GET http://localhost:8000/api/v1/processing/memories/1/topics \
  -H "Authorization: Bearer <token>"

# Response:
{
  "topics": {
    "technologies": ["python", "postgresql", "fastapi", "docker"],
    "general": ["backend", "performance", "security", "architecture"]
  }
}
```

#### 5. Get User Statistics

```bash
curl -X GET http://localhost:8000/api/v1/processing/stats \
  -H "Authorization: Bearer <token>"

# Response:
{
  "total_documents": 42,
  "processed": 40,
  "failed": 1,
  "processing": 1,
  "total_words": 125000,
  "success_rate": 95.2
}
```

#### 6. Retry Failed Processing

```bash
curl -X POST http://localhost:8000/api/v1/processing/memories/1/reprocess \
  -H "Authorization: Bearer <token>"

# Document reprocessed, status updated
```

### Architecture

#### Database: ProcessedDocument Table

```
ProcessedDocument
├── id (primary key)
├── memory_id (links to Memory)
├── user_id (for isolation)
├── extracted_text (full content)
├── preview (first 300 chars)
├── word_count, char_count
├── language (detected)
├── reading_time (float)
├── topics (JSON)
├── metadata (JSON)
├── document_structure (JSON)
├── processing_status (enum)
├── processing_error (if failed)
└── timestamps (created_at, updated_at, processed_at)
```

#### Processing Pipeline

```
Upload File
    ↓
Save to Storage
    ↓
Create Memory Record
    ↓
[Return to User - instant]
    ↓
[BACKGROUND: Process Document]
    ↓
Route to Processor (PDF/TXT/MD/Image/Bookmark)
    ↓
Extract Text → Analyze → Detect Topics → Store Results
    ↓
Update Processing Status
    ↓
Data Ready for Queries
```

#### Processors (Modular)

Each file type has its own processor:

- **PDFProcessor**: Extracts text from all pages using PyPDF2
- **TextProcessor**: Reads UTF-8/Latin-1 encoded files
- **MarkdownProcessor**: Parses headers and code blocks
- **ImageProcessor**: OCR text extraction (pytesseract)
- **BookmarkProcessor**: Fetches URL metadata
- **DummyProcessor**: Fallback for unsupported types

New file types can be added by creating a new processor class.

### API Endpoints

```
GET  /api/v1/processing/memories/{id}          Get all extracted data
POST /api/v1/processing/memories/{id}/reprocess Force reprocess
GET  /api/v1/processing/memories/{id}/preview   Get preview
GET  /api/v1/processing/memories/{id}/topics    Get topics
GET  /api/v1/processing/memories/{id}/metadata  Get metadata & structure
GET  /api/v1/processing/stats                   User statistics
```

### Configuration

#### Backend Dependencies

```bash
# In requirements.txt:
PyPDF2>=3.0.0              # PDF extraction
Pillow>=10.0.0             # Image handling
pytesseract>=0.3.10        # OCR (optional)
beautifulsoup4>=4.12.0     # Web parsing (optional)
requests>=2.31.0           # URL fetching (optional)
```

#### Optional Dependencies

Some dependencies are optional and gracefully degrade if missing:

- **pytesseract**: If not installed, OCR skipped but processing continues
- **beautifulsoup4 + requests**: If not installed, URL fetch skipped but processing continues

### Performance

| File Type | Typical Time | Notes |
|-----------|-------------|-------|
| Small PDF (< 1MB) | 2-3s | Fast extraction |
| Large PDF (10MB) | 10-15s | Page-by-page processing |
| Text/Markdown | < 1s | Fastest |
| Image with OCR | 5-10s | Depends on resolution |
| URL fetch | 2-5s | Network dependent |

**All background** - users don't wait for these times.

### Error Handling

If processing fails:

1. `processing_status` set to `failed`
2. `processing_error` contains error message
3. Upload still succeeds (non-blocking)
4. User can retry via `/reprocess` endpoint

### Topic Keywords

Auto-detected topics include:

**Technologies**: Python, JavaScript, TypeScript, Java, C#, Rust, Go, PHP, Ruby, Java, Spring, FastAPI, Django, Flask, React, Vue, Angular, PostgreSQL, MongoDB, Redis, Kubernetes, Docker, etc.

**General Topics**: Backend, Frontend, Database, DevOps, Security, Performance, Testing, Architecture, CI/CD, etc.

### Important Notes

- Processing is non-blocking (user gets instant response)
- All processing happens in background
- Failed processing doesn't block uploads
- Each user only sees their own processed data
- Extracted text stored separately for Phase 5 integration
- No AI, embeddings, or semantic search (Phase 5+)

### See Also

- [PHASE_4_ARCHITECTURE.md](./PHASE_4_ARCHITECTURE.md) - Detailed technical design
- [PHASE_4_IMPLEMENTATION.md](./PHASE_4_IMPLEMENTATION.md) - Complete implementation guide

## Phase 5: Embeddings and Vector Intelligence Engine

### Overview

Phase 5 adds semantic intelligence using vector embeddings. This enables users to find documents by meaning, not just keywords. Uses local embedding models (no API keys needed).

**What Happens**:
1. Phase 4 extracts text from document
2. Phase 5 generates vector embedding (Sentence Transformers)
3. Vectors stored in ChromaDB
4. User can search by meaning
5. Find related documents by similarity

**Key Features**:
- Semantic search ("redis caching" finds docs about caching even if exact words differ)
- Related document discovery (find similar documents)
- Vector embeddings stored locally (no cloud)
- Non-blocking (happens in background)

### Installation

#### 1. Install Phase 5 Dependencies

```bash
pip install sentence-transformers chromadb
```

This adds:
- `sentence-transformers` - Embedding model (~22MB, downloads once)
- `chromadb` - Vector database

#### 2. Initialize Embeddings Database

```bash
python init_phase5_db.py
```

Creates `document_embeddings` table.

### API Endpoints

#### Find Related Documents

```bash
GET /api/v1/embeddings/memories/{id}/related
```

Response:
```json
{
  "memory_id": 5,
  "related_memories": [
    {
      "memory_id": 3,
      "filename": "PostgreSQL Optimization.pdf",
      "similarity_score": 0.8743
    }
  ],
  "total_related": 1
}
```

#### Semantic Search

```bash
POST /api/v1/embeddings/search
```

Request:
```json
{
  "query": "How do I optimize database performance?",
  "top_k": 5,
  "min_similarity": 0.3
}
```

Response:
```json
{
  "query": "How do I optimize database performance?",
  "results": [
    {
      "memory_id": 12,
      "filename": "Database Optimization.pdf",
      "similarity_score": 0.9234
    }
  ],
  "total_results": 1
}
```

#### Check Embedding Status

```bash
GET /api/v1/embeddings/memories/{id}/status
```

Response:
```json
{
  "processed_document_id": 5,
  "memory_id": 5,
  "embedding_status": "generated",
  "model_name": "all-MiniLM-L6-v2",
  "embedded_at": "2026-06-16T18:30:45Z"
}
```

#### Get Embedding Statistics

```bash
GET /api/v1/embeddings/stats
```

Response:
```json
{
  "total_embeddings": 42,
  "generated": 40,
  "failed": 1,
  "pending": 1,
  "success_rate": 95.24
}
```

### How It Works

#### Complete Pipeline

```
User Uploads File
    ↓
Phase 4: Extract Text (background)
    ├─ Select processor (PDF/TXT/MD/etc)
    ├─ Extract text
    └─ Detect topics
    ↓
Phase 5: Generate Embedding (background) [NEW]
    ├─ Generate embedding vector
    ├─ Store in ChromaDB
    └─ Create DocumentEmbedding record
    ↓
User Searches
    ├─ Query → Generate query embedding
    ├─ Search ChromaDB
    └─ Return ranked results
```

#### Semantic Search Example

```
Upload: "PostgreSQL Performance Guide"
  ↓
Extract text about database optimization
  ↓
Generate embedding (384-dimensional vector)
  ↓

User searches: "How do I make my database faster?"
  ↓
Generate embedding for query
  ↓
Compare to stored vectors (cosine similarity)
  ↓
Returns: "PostgreSQL Performance Guide" (0.92 similarity)
```

### Configuration

#### Embedding Model

Default: `all-MiniLM-L6-v2` (Sentence Transformers)

**Why this model**:
- Fast: 6-layer transformer
- Small: 22 MB
- Effective: 384-dimensional vectors
- General: Works for any text
- Open: No API keys

#### Vector Database

Default: ChromaDB (local, persistent)

**Storage**: `backend/chroma_data/`

Automatically created on first use.

### Performance

| Operation | Time | Notes |
|-----------|------|-------|
| First embedding load | ~1-2s | Model download |
| Generate embedding | ~5ms | Per document |
| Vector search | <50ms | 100K vectors |
| Batch embeddings | ~100ms | 32 documents |

All background - users don't wait.

### Important Notes

- **Optional dependencies**: If Sentence Transformers not installed, embeddings disabled but system still works
- **Local only**: No cloud, no API keys required
- **User isolation**: Each user only sees their own embeddings
- **Non-blocking**: Embedding generation doesn't block uploads
- **Reprocessing**: Can regenerate embeddings if model upgraded

### See Also

- [PHASE_5_ARCHITECTURE.md](./PHASE_5_ARCHITECTURE.md) - Technical design
- [PHASE_5_IMPLEMENTATION.md](./PHASE_5_IMPLEMENTATION.md) - Implementation details

### Next Steps




## Production Checklist

- [ ] Environment variables configured
- [ ] Database backups enabled
- [ ] HTTPS enabled
- [ ] CORS properly configured
- [ ] Rate limiting added
- [ ] Logging/monitoring set up
- [ ] Error handling tested
- [ ] Performance optimized
- [ ] Security audit completed
- [ ] Load testing done

## Getting Help

- **API Documentation**: `http://localhost:8000/docs`
- **Frontend README**: `frontend/README.md`
- **Backend README**: `backend/README.md`
- **Architecture**: `ARCHITECTURE.md`

## Summary

You now have a production-ready SaaS structure:

✅ **Frontend**: Next.js with authentication, protected routes
✅ **Backend**: FastAPI with user management, JWT auth
✅ **Database**: PostgreSQL with proper models
✅ **Security**: Password hashing, JWT tokens, CORS
✅ **Architecture**: Clean separation of concerns
✅ **Scalability**: Ready for production deployment

Start building! 🚀
