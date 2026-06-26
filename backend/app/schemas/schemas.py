"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """User update schema."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    """User response schema."""
    id: int
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    """Token response schema with refresh token."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    """Access token only response."""
    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class MemoryCreate(BaseModel):
    """Memory creation schema (for upload metadata)."""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    tags: Optional[str] = None  # comma-separated tags


class MemoryUpdate(BaseModel):
    """Memory metadata update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=5000)
    tags: Optional[str] = None


class MemoryFileResponse(BaseModel):
    """Memory file response schema."""
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
    """Paginated memory list response."""
    items: List[MemoryFileResponse]
    total: int
    skip: int
    limit: int


class MemorySearchRequest(BaseModel):
    """Memory search and filter request."""
    query: Optional[str] = None  # search in title, description
    tags: Optional[List[str]] = None  # filter by tags
    file_type: Optional[str] = None  # filter by file type
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class TagUpdateRequest(BaseModel):
    """Add or remove tags from memory."""
    tags: List[str] = Field(..., min_items=1)


class MemoryResponse(BaseModel):
    """Memory response schema (legacy)."""
    id: int
    user_id: int
    title: str
    tags: Optional[str]

    class Config:
        from_attributes = True


# ============== Processing/Document Intelligence Schemas ==============


class ProcessedDocumentResponse(BaseModel):
    """Processed document response schema."""
    id: int
    memory_id: int
    user_id: int
    extracted_text: Optional[str]
    preview: Optional[str]
    summary: Optional[str]
    word_count: int
    char_count: int
    language: str
    reading_time: float
    topics: dict  # {"technologies": [...], "general": [...]}
    doc_metadata: dict
    document_structure: dict
    processing_status: str  # pending, uploaded, processing, processed, failed
    processing_error: Optional[str]
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    # Document Intelligence fields
    document_overview: Optional[str] = None
    topics_covered: Optional[List[str]] = None
    key_concepts: Optional[List[str]] = None
    intelligent_keywords: Optional[List[str]] = None
    doc_intelligence_metadata: Optional[dict] = None
    suggested_questions: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    knowledge_nodes: Optional[List[dict]] = None

    class Config:
        from_attributes = True


class ProcessingStatusResponse(BaseModel):
    """Simple processing status response."""
    processing_status: str  # pending, uploaded, processing, processed, failed
    processing_error: Optional[str] = None

    class Config:
        from_attributes = True

class ProcessingStatsResponse(BaseModel):
    """Processing statistics for user."""
    total_documents: int
    processed: int
    failed: int
    processing: int
    total_words: int
    success_rate: float


class RelatedMemoryResponse(BaseModel):
    """Related memory with similarity score."""
    id: int
    title: str
    file_type: str
    similarity_score: float
    preview: Optional[str]
    upload_date: datetime


class MemoryDetailsResponse(BaseModel):
    """Complete memory details with processed document and related memories."""
    # Memory fields
    id: int
    file_id: str
    user_id: int
    original_filename: str
    file_type: str
    file_size: int
    title: str
    description: Optional[str]
    tags: Optional[List[str]]
    upload_date: datetime
    updated_at: datetime
    
    # Processing status
    is_processed: bool
    processing_status: str
    processed_at: Optional[datetime]
    processing_error: Optional[str]
    
    # Processed document fields
    extracted_text: Optional[str]
    preview: Optional[str]
    summary: Optional[str]
    word_count: int
    char_count: int
    language: str
    reading_time: float
    topics: Optional[dict]
    doc_metadata: Optional[dict]
    document_structure: Optional[dict]
    
    # Document Intelligence fields
    document_overview: Optional[str] = None
    topics_covered: Optional[List[str]] = None
    key_concepts: Optional[List[str]] = None
    intelligent_keywords: Optional[List[str]] = None
    doc_intelligence_metadata: Optional[dict] = None
    suggested_questions: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    knowledge_nodes: Optional[List[dict]] = None
    
    # Related memories
    related_memories: Optional[List[RelatedMemoryResponse]] = []
    
    class Config:
        from_attributes = True
