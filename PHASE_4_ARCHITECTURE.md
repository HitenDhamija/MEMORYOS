# Phase 4: Document Intelligence Engine - Architecture

## Overview

A modular, extensible document processing pipeline that extracts structured information from uploaded memories. Designed to prepare data for future AI/embedding features while remaining production-ready today.

## Core Principles

1. **Modular Design**: Each file type has its own processor
2. **Extensible**: New processors can be added without changing existing code
3. **Non-Destructive**: Original files remain unchanged
4. **Graceful Degradation**: Failed processing doesn't block uploads
5. **Production-Ready**: Comprehensive error handling and logging
6. **Future-Proof**: Extracted text stored separately for Phase 5 (embeddings/search)

## Architecture Layers

### 1. Database Layer

**New Model: `ProcessedDocument`**
```
ProcessedDocument
├── id (Primary Key)
├── memory_id (Foreign Key to Memory)
├── user_id (Foreign Key to User - for isolation)
├── extracted_text (Full text extracted from document)
├── word_count (Numeric)
├── char_count (Numeric)
├── language (Detected language)
├── reading_time (Estimated minutes)
├── preview (First 300 characters)
├── topics (JSON array of detected topics)
├── metadata (JSON - title, author, creation date, etc.)
├── document_structure (JSON - headings, paragraphs, code blocks)
├── processing_status (pending/uploaded/processing/processed/failed)
├── processing_error (Error message if failed)
└── timestamps (created_at, updated_at, processed_at)
```

### 2. Processing Service Layer

**Processor Interface** (Abstract Base Class)
```python
class DocumentProcessor(ABC):
    @abstractmethod
    def can_process(self, file_type: str) -> bool
    
    @abstractmethod
    def extract_text(self) -> str
    
    @abstractmethod
    def extract_metadata(self) -> Dict
    
    @abstractmethod
    def extract_structure(self) -> List[Dict]
```

**Concrete Processors**
- `PDFProcessor`: PyPDF2 for text extraction, structure via font analysis
- `TextProcessor`: Plain file read
- `MarkdownProcessor`: Parse markdown headers and code blocks
- `ImageProcessor`: pytesseract for OCR
- `BookmarkProcessor`: requests library for page metadata

**Processing Orchestrator**
```python
class DocumentProcessingOrchestrator:
    def process(memory: Memory) -> ProcessedDocument
        1. Route to correct processor based on file_type
        2. Extract text
        3. Extract metadata
        4. Extract structure
        5. Detect language
        6. Extract topics
        7. Generate preview
        8. Calculate statistics
        9. Store results
        10. Update Memory status
```

### 3. Text Extraction Strategy

| Format | Extraction Method | Challenges | Solution |
|--------|------------------|------------|----------|
| **PDF** | PyPDF2 library | Scanned PDFs, layouts | Fallback to OCR on failure |
| **TXT** | File read | Unicode issues | Try UTF-8, fallback to Latin-1 |
| **Markdown** | Parse headers/blocks | Complex syntax | Regex-based parsing |
| **Images** | pytesseract OCR | Accuracy, speed | Optional, graceful fail |
| **Bookmarks** | requests + beautifulsoup | Network, missing meta | Extract title from URL |

### 4. Metadata Extraction

**Automatic Extraction**:
- Title: From filename or document title
- Word Count: Split on whitespace
- Character Count: len(text)
- Language: Simple heuristic or langdetect library (free)
- Reading Time: word_count / 200 (minutes)
- File Type: From original_filename
- Upload Date: From Memory.upload_date

**Document-Specific**:
- PDF: Author, creation date, page count
- Images: Resolution, format
- Markdown: Heading levels
- Bookmarks: Page title, URL

### 5. Topic Extraction

**Technology Keywords** (Rule-Based)
```python
TECHNOLOGIES = {
    'backend': ['fastapi', 'django', 'flask', 'node', 'express', 'java', 'spring'],
    'frontend': ['react', 'vue', 'angular', 'typescript', 'javascript', 'tailwind'],
    'databases': ['postgresql', 'mongodb', 'redis', 'elasticsearch', 'neo4j'],
    'devops': ['docker', 'kubernetes', 'jenkins', 'circleci', 'github actions'],
    'auth': ['jwt', 'oauth', 'saml', 'kerberos'],
    'other': ['python', 'rust', 'go', 'aws', 'azure', 'gcp']
}

GENERAL_TOPICS = {
    'architecture': ['design', 'pattern', 'architecture', 'microservices'],
    'security': ['security', 'encryption', 'authentication', 'authorization'],
    'performance': ['optimization', 'caching', 'performance', 'benchmark'],
    'testing': ['test', 'unit', 'integration', 'e2e'],
    'documentation': ['readme', 'doc', 'guide', 'tutorial']
}
```

**Extraction Process**:
1. Convert text to lowercase
2. Search for keyword patterns (case-insensitive)
3. Count keyword occurrences
4. Return topics with occurrence count
5. Only include topics found in text

### 6. Document Structure Extraction

**PDF Structure**:
```python
{
    "headings": [
        {"level": 1, "text": "Introduction", "page": 1},
        {"level": 2, "text": "Background", "page": 1}
    ],
    "paragraphs": [
        {"text": "First paragraph...", "page": 1}
    ]
}
```

**Markdown Structure**:
```python
{
    "headers": [
        {"level": 1, "text": "Title"},
        {"level": 2, "text": "Section"}
    ],
    "code_blocks": [
        {"language": "python", "content": "..."}
    ]
}
```

### 7. Processing Pipeline (Status Flow)

```
Upload File
    ↓
Set Status: "uploaded"
    ↓
Queue for Processing (Background Job)
    ↓
Set Status: "processing"
    ↓
Extract Text, Metadata, Structure, Topics
    ↓
Store ProcessedDocument
    ↓
Set Status: "processed"
    ↓
[Available for Query/Search/Frontend Display]

Or if Error:
    ↓
Set Status: "failed"
    ↓
Store error message
    ↓
Mark for retry/manual review
```

### 8. Backend Implementation Details

**New Package**: `app/services/processing/`
```
processing/
├── __init__.py
├── base.py                 # Abstract DocumentProcessor
├── pdf_processor.py
├── text_processor.py
├── markdown_processor.py
├── image_processor.py
├── bookmark_processor.py
├── orchestrator.py         # ProcessingOrchestrator
├── topic_extractor.py      # Keyword-based topic detection
└── text_analyzer.py        # Word count, reading time, etc.
```

**Processing Workflow**:
1. Upload endpoint queues ProcessingTask
2. Background worker picks up task
3. Orchestrator routes to correct processor
4. Processor extracts all data
5. Results stored in ProcessedDocument
6. Memory.processing_status updated
7. Frontend can display results

**Async Execution Options**:
- Option A: ThreadPoolExecutor (simple, no external dependencies)
- Option B: Celery + Redis (production-grade)
- **Choice**: ThreadPoolExecutor for MVP (easy to upgrade to Celery)

### 9. Frontend Updates

**Memory Details Page** (New Route)
```
/memories/{id}/details

Display:
├── Processing Status (Badge: pending/processing/processed/failed)
├── Extracted Content Section
│   ├── Preview (First 300 chars)
│   ├── Full Text (Expandable)
│   └── Copy Button
├── Document Statistics
│   ├── Word Count
│   ├── Character Count
│   ├── Reading Time
│   ├── Language
│   └── Paragraph/Heading Count
├── Detected Topics (Tag list)
├── Document Structure (Expandable tree)
└── Metadata (Title, Upload Date, Last Updated)
```

**Memory Card Updates**:
- Show processing status badge
- Show quick stats (word count, reading time)
- Link to details page

**Processing Status Indicators**:
- `pending`: Gray (not yet processed)
- `processing`: Blue spinner
- `processed`: Green checkmark
- `failed`: Red alert with error message

### 10. API Endpoints

**New Endpoints**:
```
GET /api/v1/memories/{id}/processed
├── Returns: ProcessedDocument
└── Shows all extracted data

GET /api/v1/memories/{id}/process
├── Force reprocessing
└── Returns: ProcessedDocument (processing started)

GET /api/v1/memories/stats
├── Returns: Aggregated statistics
└── Topics frequency, language distribution, etc.
```

### 11. Error Handling Strategy

**Processor-Level**:
- Try-catch in each processor
- Log specific errors
- Return partial results if possible
- Mark status as "failed" with error message

**Pipeline-Level**:
- Don't block upload on processing errors
- User can retry from UI
- Errors visible in Memory Details page

**Specific Handlers**:
- Corrupted PDF: Log, mark failed, suggest re-upload
- Invalid image: Try next processor or mark failed
- OCR timeout: Fail gracefully, mark as processed (without OCR)
- Large file: Process in chunks or skip content extraction
- Unsupported format: Mark as processed (no extraction)

### 12. Performance Considerations

**Optimization**:
- Process in background (non-blocking)
- Cache processor instances
- Limit OCR to first N pages for large PDFs
- Compress extracted text in DB
- Index frequently queried fields

**Scalability**:
- Migrate from ThreadPoolExecutor to Celery for distributed processing
- Add worker queue management
- Monitor processing queue length
- Implement priority queue (small files first)

### 13. Testing Strategy

**Unit Tests**:
- Test each processor independently
- Mock file inputs
- Verify extraction accuracy

**Integration Tests**:
- End-to-end processing pipeline
- Verify database storage
- Test error scenarios

**Manual Tests**:
- Real PDF, TXT, MD, Image, URL files
- Large files
- Corrupted files
- Mixed content

### 14. Future Extensions (Phase 5+)

**Embeddings Integration**:
- Use extracted_text directly for embeddings generation
- Store embeddings in separate table
- Vector similarity search on top of extracted data

**Neo4j Integration**:
- Extract entities from text
- Build knowledge graph
- Query relationships

**Semantic Search**:
- Use embeddings for similarity matching
- Combine with topic tags for filtering

**OCR Improvements**:
- Language-specific OCR
- Layout analysis
- Table extraction

## Technology Stack

### Python Libraries
- **PDF**: PyPDF2 (extract text)
- **OCR**: pytesseract + Pillow (optional)
- **Markdown**: Built-in regex parsing
- **Language Detection**: langdetect (free, optional)
- **Web Scraping**: requests + beautifulsoup4 (for bookmarks)
- **Async**: ThreadPoolExecutor (stdlib)

### Database
- SQLite (existing) with new ProcessedDocument table
- Easy migration to PostgreSQL later

## Implementation Sequence

1. ✅ Create ProcessedDocument model
2. ✅ Build base processor class
3. ✅ Implement file-type processors (PDF, TXT, MD, Image, Bookmark)
4. ✅ Create topic extractor
5. ✅ Create orchestrator
6. ✅ Integrate with upload endpoint
7. ✅ Create processing status endpoint
8. ✅ Build frontend details page
9. ✅ Update memory card display
10. ✅ Add comprehensive tests
11. ✅ Error handling and logging

## Success Criteria

✓ Documents processed within 5 seconds (excluding OCR)  
✓ 95%+ success rate for supported formats  
✓ No upload blocking (async processing)  
✓ Full error logging and recovery  
✓ Production-ready error handling  
✓ Extensible to new file types  
✓ Frontend displays all extracted data  
✓ Ready for Phase 5 (embeddings/search)  

## Constraints Maintained

✗ NO AI generation  
✗ NO semantic search  
✗ NO embeddings (yet - Phase 5)  
✗ NO Neo4j (yet - Phase 5)  
✗ NO paid APIs  
✗ NO authentication changes  
✗ NO memory model changes (use separate table)  
✗ NO upload flow changes  

---

This architecture balances **immediate utility** (extract useful data today) with **future extensibility** (prepare for Phase 5 AI/search features).
