"""
Knowledge Assistant API Endpoint

Natural-language question answering over the user's knowledge base
with intent detection, hybrid retrieval, and natural responses.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.services.qa_service import get_qa_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/qa", tags=["knowledge-qa"])


# --- Request/Response Schemas ---

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=500, description="Natural language question")
    top_k: int = Field(default=10, ge=1, le=20, description="Number of documents to search")


class ActionItem(BaseModel):
    type: str = Field(description="Action type: open_document, open_collection, summarize, compare, move_to_collection, rename, download, ask_followup")
    label: str = Field(description="Display label for the action")
    icon: str = Field(description="Icon name")
    memory_id: Optional[int] = Field(None, description="Associated memory ID")
    collection_id: Optional[int] = Field(None, description="Associated collection ID")


class SourceItem(BaseModel):
    memory_id: int
    filename: str
    similarity: float
    preview: str
    document_type: str
    match_types: List[str] = Field(default_factory=list, description="How this result was found")


class AnswerResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    actions: List[ActionItem] = Field(default_factory=list, description="Suggested actions")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    confidence: float
    documents_searched: int


class SuggestedQuestion(BaseModel):
    question: str
    category: str


# --- Endpoints ---

@router.post("/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Ask a natural-language question about your knowledge base.

    The assistant will:
    1. Detect your intent (find, count, summarize, compare, etc.)
    2. Search across metadata, collections, tags, topics, keywords, and semantic embeddings
    3. Generate a natural response with relevant actions
    4. Remember conversation context for follow-up questions

    Examples:
    - "Do I have any research papers?"
    - "Show my certificates"
    - "Where is my resume?"
    - "Which documents mention FastAPI?"
    - "How many PDFs have I uploaded?"
    - "What AI projects do I have?"
    - "List my interview preparation material"
    - "Show documents related to Computer Vision"
    - "Where did I save my notes?"
    - "What documents discuss YOLO?"
    """
    qa_service = get_qa_service()

    result = qa_service.answer_question(
        db=db,
        question=request.question,
        user_id=current_user.id,
        top_k=request.top_k,
    )

    return AnswerResponse(
        answer=result["answer"],
        sources=[SourceItem(**s) for s in result["sources"]],
        actions=[ActionItem(**a) for a in result["actions"] if a],
        follow_up_questions=result.get("follow_up_questions", []),
        confidence=result["confidence"],
        documents_searched=result["documents_searched"],
    )


@router.get("/suggested-questions", response_model=List[SuggestedQuestion])
async def get_suggested_questions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get suggested questions based on the user's uploaded documents.
    Returns contextual questions the user might want to ask.
    """
    from app.models import Memory, ProcessedDocument
    from app.models.collection import Collection

    # Get user's document types and topics
    proc_docs = db.query(ProcessedDocument).filter(
        ProcessedDocument.user_id == current_user.id,
        ProcessedDocument.doc_intelligence_metadata.isnot(None),
    ).all()

    # Get user's collections
    collections = db.query(Collection).filter(
        Collection.user_id == current_user.id,
        Collection.is_deleted == False,
    ).all()

    # Get memory count
    memory_count = db.query(Memory).filter(
        Memory.user_id == current_user.id,
        Memory.is_deleted == False,
    ).count()

    if not proc_docs and memory_count == 0:
        return [
            SuggestedQuestion(question="What documents have I uploaded?", category="general"),
            SuggestedQuestion(question="Summarize my knowledge base", category="general"),
        ]

    suggestions = []

    # Analyze document types
    doc_types = set()
    all_topics = set()
    for doc in proc_docs:
        if doc.doc_intelligence_metadata:
            meta = doc.doc_intelligence_metadata
            doc_type = meta.get("document_metadata", {}).get("type", "")
            if doc_type:
                doc_types.add(doc_type.lower())
            
            topics = meta.get("topics_covered", [])
            all_topics.update(t[:30] for t in topics[:10])

    # Type-based suggestions
    if any("research" in dt for dt in doc_types):
        suggestions.append(SuggestedQuestion(
            question="Do I have any research papers?",
            category="research",
        ))
        suggestions.append(SuggestedQuestion(
            question="What research topics have I studied?",
            category="research",
        ))

    if any("resume" in dt for dt in doc_types):
        suggestions.append(SuggestedQuestion(
            question="Where is my resume?",
            category="resume",
        ))
        suggestions.append(SuggestedQuestion(
            question="What skills are listed in my resume?",
            category="resume",
        ))

    if any("certificate" in dt for dt in doc_types):
        suggestions.append(SuggestedQuestion(
            question="Show my certificates",
            category="certificates",
        ))

    if any("tutorial" in dt or "guide" in dt for dt in doc_types):
        suggestions.append(SuggestedQuestion(
            question="List my interview preparation material",
            category="tutorials",
        ))

    # Topic-based suggestions
    topic_list = sorted(all_topics)[:5]
    for topic in topic_list[:3]:
        suggestions.append(SuggestedQuestion(
            question=f"Which documents mention {topic}?",
            category="topics",
        ))

    # Collection-based suggestions
    if collections:
        coll_names = [c.name for c in collections[:3]]
        suggestions.append(SuggestedQuestion(
            question=f"What's in my {coll_names[0]} collection?",
            category="collections",
        ))

    # General suggestions
    suggestions.append(SuggestedQuestion(
        question="How many documents have I uploaded?",
        category="general",
    ))
    suggestions.append(SuggestedQuestion(
        question="What are the most common topics across my documents?",
        category="general",
    ))

    # Deduplicate and return
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s.question not in seen:
            seen.add(s.question)
            unique_suggestions.append(s)

    return unique_suggestions[:8]
