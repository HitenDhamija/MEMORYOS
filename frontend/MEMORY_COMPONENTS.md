# Phase 3.2: Memory Library Frontend - Component Guide

## Overview

The Memory Library frontend provides a complete UI for managing uploaded memory files with search, filtering, and organization capabilities.

## Architecture

```
pages/
  (dashboard)/
    memories/
      page.tsx          # Main Memory Dashboard
components/
  memories/
    MemoryUploadZone.tsx   # Drag-and-drop upload
    MemoryCard.tsx         # Individual memory display
    MemorySearchFilter.tsx # Search and filter UI
    MemoryLibrary.tsx      # Grid/list with pagination
    index.ts              # Barrel export
services/
  memoryService.ts      # API service layer
```

## Components

### 1. MemoriesPage (Main Dashboard)

**File**: `src/app/(dashboard)/memories/page.tsx`

**Features**:
- Complete Memory Library dashboard
- Upload modal management
- Search and filter orchestration
- Storage statistics display
- Error and success message handling
- Pagination management

**Key State**:
- `memories`: Currently displayed memories
- `searchQuery`, `selectedTags`, `selectedFileType`: Active filters
- `stats`: Storage analytics
- `errorMessage`, `successMessage`: UI feedback

**Usage**:
```bash
Navigate to: http://localhost:3000/memories
```

---

### 2. MemoryUploadZone

**File**: `src/components/memories/MemoryUploadZone.tsx`

**Props**:
```typescript
interface MemoryUploadZoneProps {
  onUploadSuccess: () => void;      // Called after successful upload
  onUploadError: (error: string) => void; // Called on upload error
}
```

**Features**:
- Drag-and-drop file input
- File type validation (PDF, Images, TXT, MD, Bookmarks)
- File size validation (max 100MB)
- Metadata form (title required, description/tags optional)
- Visual feedback during upload
- Multi-step UX (drop zone → form → upload)

**Supported File Types**:
- PDF: `.pdf`
- Images: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- Text: `.txt`
- Markdown: `.md`, `.markdown`
- Bookmarks: `.url`, `.webloc`

**Usage**:
```tsx
<MemoryUploadZone
  onUploadSuccess={() => console.log('Uploaded!')}
  onUploadError={(error) => alert(error)}
/>
```

---

### 3. MemoryCard

**File**: `src/components/memories/MemoryCard.tsx`

**Props**:
```typescript
interface MemoryCardProps {
  memory: Memory;              // Memory object to display
  onDelete: () => void;        // Called after deletion
  onUpdate: () => void;        // Called after update
}
```

**Features**:
- Displays memory metadata (title, description, tags)
- File icon based on type
- Processing status badge with color coding
- Upload date formatting
- Edit inline form for metadata updates
- Download file action
- Delete action with confirmation
- Responsive design (icons hidden on mobile, text hidden in buttons)

**Memory Card Displays**:
- File icon (📄📋🖼️📝🔖)
- Title (line-clamped to 2 lines)
- Filename and file size
- Type badge (pdf, image, txt, md, bookmark, other)
- Status badge (pending, uploaded, processing, processed, failed)
- Description (if provided, line-clamped to 2 lines)
- Tags (displayed as badges)
- Upload date (formatted: "Jun 16, 2026, 06:17 PM")

**Edit Mode**:
- Inline form for updating title, description, tags
- Cancel/Save buttons
- Loading state during save
- Error handling

**Actions**:
- Download: Downloads file with original filename
- Edit: Opens inline edit form
- Delete: Soft delete with confirmation

**Usage**:
```tsx
<MemoryCard
  memory={memoryObject}
  onDelete={() => refreshList()}
  onUpdate={() => refreshList()}
/>
```

---

### 4. MemorySearchFilter

**File**: `src/components/memories/MemorySearchFilter.tsx`

**Props**:
```typescript
interface MemorySearchFilterProps {
  allTags: string[];                           // All available tags
  allFileTypes: Record<string, number>;        // Count by file type
  onSearch: (query: string, tags: string[], fileType: string | null) => void;
  isLoading: boolean;                          // Show loading state
}
```

**Features**:
- Full-text search by title/description
- File type dropdown filter
- Multi-select tag filter with checkboxes
- Clear filters button (smart - only shows if filters active)
- Shows active filters summary
- Real-time search callback
- Responsive design

**Filters**:
1. **Query**: Search box for title/description full-text search
2. **File Type**: Dropdown with count of each type (pdf, image, txt, md, bookmark)
3. **Tags**: Multi-select checkboxes with AND logic (file must have all selected tags)

**UI States**:
- Filter dropdowns toggle on click
- Active filters highlighted in blue
- Clear summary showing applied filters
- Loading state disables search input

**Usage**:
```tsx
<MemorySearchFilter
  allTags={['python', 'tutorial', 'important']}
  allFileTypes={{ pdf: 5, image: 3, txt: 2 }}
  onSearch={(query, tags, fileType) => handleSearch(query, tags, fileType)}
  isLoading={false}
/>
```

---

### 5. MemoryLibrary

**File**: `src/components/memories/MemoryLibrary.tsx`

**Props**:
```typescript
interface MemoryLibraryProps {
  memories: Memory[];                  // Array of memories to display
  isLoading: boolean;                  // Loading state
  totalCount: number;                  // Total number of memories (all pages)
  currentPage: number;                 // Current page (1-indexed)
  pageSize: number;                    // Items per page
  onPageChange: (page: number) => void; // Pagination callback
  onMemoryDeleted: () => void;         // Called after memory deletion
  onMemoryUpdated: () => void;         // Called after memory update
}
```

**Features**:
- Responsive grid layout (1 col mobile, 2 col tablet, 3 col desktop)
- Smart pagination with ellipsis
- Empty state messaging
- Loading state with spinner
- Adaptive page number display
- Previous/Next buttons
- Page number buttons with current page highlight

**Grid Layout**:
```
Mobile (< 768px): 1 column
Tablet (768px): 2 columns
Desktop (>= 1024px): 3 columns
```

**Pagination**:
- Shows current page / total pages
- Always shows: 1, currentPage-1, currentPage, currentPage+1, totalPages
- Adds ellipsis (...) for gaps > 1
- Previous/Next buttons with disabled state
- Smart calculation of total pages from skip/limit/total

**Empty States**:
- Loading: Spinner + "Loading memories..."
- Empty: "No memories yet" + suggestion

**Usage**:
```tsx
<MemoryLibrary
  memories={memories}
  isLoading={isLoading}
  totalCount={100}
  currentPage={1}
  pageSize={20}
  onPageChange={(page) => handlePageChange(page)}
  onMemoryDeleted={() => refreshList()}
  onMemoryUpdated={() => refreshList()}
/>
```

---

## API Integration

### MemoryService

**File**: `src/services/memoryService.ts`

**Methods**:

```typescript
// Upload
uploadMemory(file: File, title: string, description?: string, tags?: string): Promise<Memory>

// List
listMemories(skip: number = 0, limit: number = 20): Promise<MemoryListResponse>

// Search & Filter
searchMemories(params: MemorySearchParams): Promise<MemoryListResponse>

// CRUD
getMemory(id: number): Promise<Memory>
updateMemory(id: number, updates: {...}): Promise<Memory>
deleteMemory(id: number): Promise<void>

// Tags
getMemoryTags(id: number): Promise<string[]>
addTags(id: number, tags: string[]): Promise<Memory>
removeTag(id: number, tag: string): Promise<Memory>

// File Download
downloadMemory(id: number, filename: string): Promise<void>

// Analytics
getStorageSummary(): Promise<StorageSummary>
```

**Helper Functions** (static methods on MemoryService):

```typescript
formatFileSize(bytes: number): string
// Returns: "10.5 MB", "1.2 GB", etc.

getFileIcon(fileType: string): string
// Returns: "📄" for pdf, "🖼️" for image, etc.

formatDate(dateString: string): string
// Returns: "Jun 16, 2026, 06:17 PM"

getStatusColor(status: string): string
// Returns Tailwind classes: "bg-yellow-100 text-yellow-800", etc.
```

---

## Data Interfaces

### Memory

```typescript
interface Memory {
  id: number;
  file_id: string;                    // UUID
  user_id: number;
  original_filename: string;          // e.g., "document.pdf"
  file_type: string;                  // pdf, image, txt, md, bookmark, other
  file_size: number;                  // bytes
  title: string;                      // User-defined title
  description?: string;               // Optional notes
  tags?: string[] | string;           // Array or comma-separated
  is_processed: boolean;
  processing_status: string;          // pending, uploaded, processing, processed, failed
  upload_date: string;                // ISO 8601
  updated_at: string;                 // ISO 8601
  processed_at?: string;              // ISO 8601 (optional)
}
```

### MemoryListResponse

```typescript
interface MemoryListResponse {
  items: Memory[];
  total: number;                      // Total count across all pages
  skip: number;                       // Pagination offset used
  limit: number;                      // Pagination limit used
}
```

### StorageSummary

```typescript
interface StorageSummary {
  total_size: number;                 // bytes
  total_files: number;
  file_types: Record<string, number>; // { pdf: 5, image: 3, ... }
  tags: string[];                     // All unique tags
}
```

---

## Authentication

All components are wrapped in `ProtectedRoute` which requires authentication. Users must be logged in to access the Memory Library.

**Required Hook**: `useAuth()` from `@/hooks/useAuth`

---

## Styling

**Framework**: Tailwind CSS + Lucide React Icons

**Color Scheme**:
- Primary: Blue (600, 700)
- Success: Green (50, 100, 200, 600, 700, 800)
- Error: Red (50, 100, 200, 600, 700, 800)
- Warning: Yellow (100, 800)
- Neutral: Gray (50-900)

**Responsive Breakpoints**:
- Mobile: < 640px
- Tablet: 640px - 1024px (md:)
- Desktop: >= 1024px (lg:)

**Common Patterns**:
- `px-4 sm:px-6 lg:px-8` - Responsive padding
- `grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3` - Responsive grid
- `hidden sm:inline` - Hide on mobile

---

## Error Handling

All components include error handling:

1. **Upload Errors**: Displayed in error banner at top of page
2. **Memory Operations** (edit/delete): Alert dialog to user
3. **API Errors**: Caught and displayed with error message
4. **Loading States**: Show spinners and disable interactions

---

## Future Enhancements (Phase 4+)

- AI-powered semantic search
- Document OCR with text extraction
- Automatic tagging
- Timeline view of uploads
- Sharing and collaboration
- Advanced analytics
- Neo4j knowledge graph integration

---

## Development Tips

1. **Testing Components in Isolation**:
   ```tsx
   // Use mock data for testing
   const mockMemory: Memory = {
     id: 1,
     file_id: 'uuid-123',
     user_id: 1,
     original_filename: 'test.pdf',
     // ... other required fields
   };
   ```

2. **API Testing**: Use Swagger UI at `http://localhost:8000/docs`

3. **Component Reusability**: All components are standalone and can be reused elsewhere in the app

4. **Performance**: Pagination limits results to 20 items per page to avoid rendering large lists

5. **Accessibility**: All components use semantic HTML and proper ARIA labels

---

## File Structure Summary

```
frontend/
  src/
    components/
      memories/
        MemoryUploadZone.tsx      # Drag-drop upload
        MemoryCard.tsx            # Memory display card
        MemorySearchFilter.tsx     # Search & filter UI
        MemoryLibrary.tsx         # Grid + pagination
        index.ts                  # Exports
    services/
      memoryService.ts           # API client + helpers
    app/
      (dashboard)/
        memories/
          page.tsx               # Main dashboard page
    hooks/
      useAuth.ts                 # Auth context hook
```
