# Phase 4: Document Intelligence Engine - Implementation Guide

## Overview

Phase 4 implements a **modular document processing pipeline** that automatically extracts structured information from uploaded memories. This engine prepares data for future AI/search features while providing immediate utility.

**Key Point**: This is NOT AI-powered. It's rule-based text extraction and analysis designed to extract maximum value from documents without external APIs.

## What Gets Processed

After a user uploads a file, the system automatically:

1. **Extracts Text** from the document
2. **Analyzes Content** (word count, reading time, language)
3. **Detects Topics** (technologies, domains, categories)
4. **Extracts Structure** (headings, code blocks, sections)
5. **Generates Preview** (first 300 characters)
6. **Stores Metadata** (title, author, creation date, etc.)

All extraction happens **in the background** - upload returns immediately.

## Supported File Types

| Format | Extraction | Topics | Structure | Metadata |
|--------|-----------|--------|-----------|----------|
| **PDF** | ✅ PyPDF2 | ✅ Keywords | ✅ Pages | ✅ Author, creation date |
| **TXT** | ✅ File read | ✅ Keywords | ✅ Paragraphs | ✅ Basic info |
| **Markdown** | ✅ Parse | ✅ Keywords | ✅ Headers, code blocks | ✅ Front matter |
| **Images** | ✅ OCR* | ✅ Keywords | ✅ Resolution, format | ✅ Image props |
| **URLs/Bookmarks** | ✅ Fetch** | ✅ Keywords | ✅ Page structure | ✅ Title, desc |

*OCR requires pytesseract + Tesseract binary (optional, graceful fallback)
**URL fetching requires network (optional, graceful fallback)

## Architecture

### Database Model: ProcessedDocument

```python
ProcessedDocument
├── memory_id (Foreign Key)
├── user_id (Foreign Key - for isolation)
├── extracted_text (Full content)
├── preview (First 300 chars)
├── word_count, char_count
├── language (Detected)
├── reading_time (Estimated minutes)
├── topics (JSON: technologies, general)
├── metadata (JSON: title, author, etc.)
├── document_structure (JSON: headings, sections)
├── processing_status (pending/processing/processed/failed)
├── processing_error (If failed)
└── timestamps (created_at, updated_at, processed_at)
```

### Processing Pipeline

```
Upload File
    ↓
Save to Storage
    ↓
Create Memory Record
    ↓
[Return to User - instant]
    ↓
[BACKGROUND: Start Processing]
    ↓
Route to Processor (PDF/TXT/MD/Image/Bookmark)
    ↓
Extract Text → Analyze → Detect Topics → Store Results
    ↓
Update Processing Status
    ↓
[Ready for Queries]
```

**Key**: Processing is non-blocking. User gets immediate response; processing happens in background.

### Service Layer

#### 1. **Document Processors** (Modular Design)

Each file type has its own processor implementing `DocumentProcessor` interface:

- **PDFProcessor**: PyPDF2 extracts text from all pages
- **TextProcessor**: Reads UTF-8/Latin-1 encoded files
- **MarkdownProcessor**: Parses headers and code blocks
- **ImageProcessor**: pytesseract for OCR (optional)
- **BookmarkProcessor**: Extracts URL, page title, metadata
- **DummyProcessor**: Fallback for unsupported types

#### 2. **Text Analyzer**

Analyzes extracted text and calculates:

```python
{
    "word_count": int,
    "char_count": int,
    "paragraph_count": int,
    "line_count": int,
    "sentence_count": int,
    "reading_time": float,  # minutes (word_count / 200)
    "language": str,         # en, es, fr, de, it, zh, etc.
    "avg_word_length": float,
    "unique_words": int
}
```

**Language Detection**: Simple heuristic based on common words and character ranges (no external API).

#### 3. **Topic Extractor**

Rule-based keyword matching extracts topics:

```python
{
    "technologies": ["python", "fastapi", "postgresql", ...],
    "general": ["architecture", "security", "performance", ...]
}
```

**Keywords**: Pre-defined lists for backend, frontend, databases, devops, auth, testing, etc.

#### 4. **Processing Orchestrator**

Main coordinator that:
- Routes documents to appropriate processors
- Orchestrates extraction steps
- Handles errors gracefully
- Updates database with results
- Provides retry/reprocess capability

## API Endpoints

### Processing Endpoints

```
GET  /api/v1/processing/memories/{id}          Get all extracted data
POST /api/v1/processing/memories/{id}/reprocess Force reprocess
GET  /api/v1/processing/memories/{id}/preview   Get preview
GET  /api/v1/processing/memories/{id}/topics    Get detected topics
GET  /api/v1/processing/memories/{id}/metadata  Get metadata & structure
GET  /api/v1/processing/stats                   User processing stats
```

### Memory Endpoints (Updated)

```
POST /api/v1/memories/upload      [UPDATED] Triggers background processing
GET  /api/v1/memories             [Same] List memories
GET  /api/v1/memories/{id}        [Same] Memory details
PUT  /api/v1/memories/{id}        [Same] Update metadata
DELETE /api/v1/memories/{id}      [Same] Delete
```

## Usage Examples

### 1. Upload a File

```bash
curl -X POST http://localhost:8000/api/v1/memories/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@document.pdf" \
  -F "title=Project Report" \
  -F "description=Q4 project analysis" \
  -F "tags=project,analysis"

# Response (instant):
{
  "id": 1,
  "title": "Project Report",
  "processing_status": "uploaded",  # Not yet processed
  "upload_date": "2026-06-16T10:00:00Z"
}
```

### 2. Check Processing Status (Wait for completion)

```bash
# Check in 2-5 seconds for completion

curl -X GET http://localhost:8000/api/v1/processing/memories/1 \
  -H "Authorization: Bearer <token>"

# Response (when complete):
{
  "id": 1,
  "memory_id": 1,
  "processing_status": "processed",
  "word_count": 3241,
  "reading_time": 16.2,
  "language": "en",
  "topics": {
    "technologies": ["python", "postgresql", "fastapi"],
    "general": ["backend", "architecture", "performance"]
  },
  "preview": "Project Report Q4 2026...",
  "metadata": {...},
  "document_structure": {...}
}
```

### 3. Get Preview

```bash
curl -X GET http://localhost:8000/api/v1/processing/memories/1/preview \
  -H "Authorization: Bearer <token>"

# Response:
{
  "preview": "Project Report Q4 2026. This document outlines...",
  "word_count": 3241,
  "status": "processed"
}
```

### 4. Get Topics

```bash
curl -X GET http://localhost:8000/api/v1/processing/memories/1/topics \
  -H "Authorization: Bearer <token>"

# Response:
{
  "topics": {
    "technologies": ["python", "postgresql", "fastapi", "docker"],
    "general": ["backend", "architecture", "performance", "security"]
  }
}
```

### 5. Get Stats

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

### 6. Retry Failed Processing

```bash
curl -X POST http://localhost:8000/api/v1/processing/memories/1/reprocess \
  -H "Authorization: Bearer <token>"

# Starts reprocessing, returns result when done
```

## Key Features

### ✅ Automatic Processing

- Files automatically queued for processing after upload
- No manual intervention required
- Non-blocking (user gets instant response)

### ✅ Comprehensive Extraction

- Full text content extracted
- Structured data parsed (headers, code blocks)
- Metadata captured (author, dates, etc.)
- Topics auto-detected

### ✅ Error Resilience

- Failed processing marked but doesn't block upload
- Retry capability built in
- Graceful degradation (OCR optional, web fetch optional)
- Errors logged for debugging

### ✅ User Isolation

- All queries filtered by `user_id`
- Users only see their own processed data
- Storage segregated by user

### ✅ Performance

- Background processing (non-blocking)
- ThreadPoolExecutor with 2 concurrent workers
- Can scale to Celery for higher throughput
- Text/metadata stored separately from files

### ✅ Future-Proof

- Extracted text ready for embeddings (Phase 5)
- Modular processors easy to extend
- Database schema designed for semantic search
- Topic tagging enables knowledge graph (Phase 5+)

## Processing Status States

```
pending     Created, not yet processed
↓
uploaded    File saved, ready for processing
↓
processing  Actively extracting content
↓
processed   ✅ Complete (ready for queries)
└→ failed   ❌ Error occurred (check processing_error)
```

## Error Handling

### Processing Failures

Processing failures do NOT block uploads. If a document can't be processed:

1. Status set to `failed`
2. Error message stored in `processing_error`
3. User can retry via `/reprocess` endpoint
4. Error logged for admin debugging

### Graceful Degradation

- **PDF corrupted**: Mark failed, suggest re-upload
- **OCR not available**: Skip OCR, mark as processed
- **URL unreachable**: Skip URL fetch, mark as processed
- **Large file**: Process in chunks or skip OCR
- **Unknown format**: Mark as processed (no extraction)

## Configuration

### Environment Variables (in .env)

```bash
# Processing settings
PROCESSING_WORKERS=2          # ThreadPoolExecutor workers
PROCESSING_TIMEOUT=30         # Seconds per document
OCR_ENABLED=true              # Enable OCR processing
WEB_FETCH_ENABLED=true        # Enable URL fetching
```

### Python Dependencies

```bash
# Core (included)
PyPDF2>=3.0.0                # PDF text extraction
Pillow>=10.0.0               # Image handling

# Optional (graceful fallback if missing)
pytesseract>=0.3.10          # OCR support
BeautifulSoup4>=4.12.0       # Web parsing
requests>=2.31.0             # URL fetching
```

## Implementation Details

### File Structure

```
backend/
  app/
    models/
      processed_document.py        # ProcessedDocument model
    services/
      processing/
        __init__.py
        base.py                    # DocumentProcessor base class
        pdf_processor.py
        text_processor.py
        markdown_processor.py
        image_processor.py
        bookmark_processor.py
        topic_extractor.py         # Keyword matching
        text_analyzer.py           # Text statistics
        orchestrator.py            # Main coordinator
    api/
      v1/
        endpoints/
          processing.py            # Processing API endpoints
          memories.py              # [UPDATED] Upload triggers processing
    schemas/
      schemas.py                   # [UPDATED] Added ProcessedDocument schemas
```

### Background Processing

Upload triggers background task:

```python
background_tasks.add_task(
    _process_memory_background,
    memory_id,
    user_id,
    storage_path
)
```

Task:
1. Gets new database session
2. Loads memory and file
3. Calls `ProcessingOrchestrator.process_document()`
4. Updates ProcessedDocument table
5. Closes session

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Small PDF (< 1MB) | 2-3s | Fast text extraction |
| Large PDF (10MB) | 10-15s | Page-by-page processing |
| Image with OCR | 5-10s | Depends on resolution |
| Text/Markdown | < 1s | Fastest |
| URL fetch | 2-5s | Network dependent |

**All background** - user doesn't wait for these times.

## Monitoring & Debugging

### Logs

Check backend logs for processing:

```
INFO: Starting processing: Memory 1
DEBUG: Extracting text from document.pdf
DEBUG: Analyzing text from document.pdf
INFO: Successfully processed Memory 1: 3241 words
```

### Stats Endpoint

Monitor processing health:

```bash
GET /api/v1/processing/stats

{
  "total_documents": 100,
  "processed": 95,
  "failed": 2,
  "processing": 3,
  "total_words": 500000,
  "success_rate": 95.0
}
```

### Retry Failed Processing

```bash
POST /api/v1/processing/memories/{id}/reprocess
```

## Phase 5 Integration

Phase 4 output feeds Phase 5:

- **Extracted Text** → Embeddings generation
- **Topics** → Tag-based filtering
- **Language** → Multi-language support
- **Structure** → Semantic chunking for retrieval
- **Preview** → Search result display
- **Metadata** → Result ranking

## Constraints Maintained ✓

✗ **NO AI generation** - Rule-based only
✗ **NO semantic search** - Full-text only (Phase 5)
✗ **NO embeddings** - Text ready for Phase 5
✗ **NO Neo4j** - Structure ready for Phase 5+
✗ **NO paid APIs** - All local processing
✗ **NO auth changes** - Existing system preserved
✗ **NO memory model changes** - Separate table

## Future Enhancements (Phase 5+)

- **Embeddings**: Generate vector embeddings from extracted text
- **Semantic Search**: Vector similarity search using embeddings
- **Entity Extraction**: Identify people, places, organizations
- **Neo4j Integration**: Build knowledge graph from topics/entities
- **Timeline View**: Visualize documents chronologically
- **Advanced OCR**: Language-specific, layout analysis
- **Audio/Video**: Transcript extraction
- **GitHub Integration**: Process repository code
- **DOCX/Excel**: Microsoft Office support

## Testing

### Manual Testing

1. Upload a PDF
2. Check processing status (should be "processing" initially)
3. Wait 3-5 seconds
4. Check again (should be "processed")
5. Verify extracted text, topics, metadata

### API Testing

Use Swagger UI at http://localhost:8000/docs:

1. Expand `/api/v1/processing` endpoints
2. Try each endpoint with memory IDs
3. Verify response schemas

---

**Phase 4 Complete**: Documents now have extracted, queryable content ready for Phase 5 AI/search features.
