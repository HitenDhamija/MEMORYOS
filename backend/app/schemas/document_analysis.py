"""
Pydantic schemas for structured Document Intelligence output.

Every uploaded document produces a multi-section analysis
that helps users understand content within 5 seconds.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class DocumentMetadata(BaseModel):
    """Inferred metadata about the document."""

    type: str = Field(default="General", description="Document type label (e.g. Study Material, Research Paper, Resume)")
    domain: str = Field(default="General", description="Subject domain (e.g. Mathematics, Computer Science)")
    difficulty: str = Field(default="General", description="Difficulty level: Beginner, Intermediate, Advanced, General")
    estimated_reading_time: str = Field(default="0 minutes", description="Human-readable reading time")
    pages: int = Field(default=0, description="Estimated number of pages")
    contains_examples: bool = Field(default=False, description="Whether the document contains worked examples")
    contains_exercises: bool = Field(default=False, description="Whether the document contains exercises or problems")
    contains_formulas: bool = Field(default=False, description="Whether the document contains mathematical formulas")
    language: str = Field(default="English", description="Detected language name")
    engine_version: str = Field(default="5.0", description="Document Intelligence engine version")
    classification_confidence: float = Field(
        default=0.0,
        description="Confidence score for document type classification (0.0-1.0). Below 0.75 may indicate Unknown type.",
    )
    certificate_info: Optional[Dict[str, str]] = Field(
        default=None,
        description="Certificate-specific metadata (name, organization, completion_date, skills, credential_type)",
    )


class KnowledgeNode(BaseModel):
    """A semantic chunk of the document for vector embedding."""

    title: str = Field(default="", description="Short title for this chunk")
    description: str = Field(default="", description="One-sentence description of the chunk content")
    keywords: List[str] = Field(default_factory=list, description="Keywords for this chunk")
    page_numbers: List[int] = Field(default_factory=list, description="Approximate page numbers (if detectable)")


class TypeSpecificSection(BaseModel):
    """
    Type-aware section that replaces the generic 'Learning Objectives'.
    Label and content change based on document type.
    """

    label: str = Field(
        default="Learning Objectives",
        description="Section label (e.g. Candidate Highlights, Research Contributions, Key Modules)",
    )
    items: List[str] = Field(
        default_factory=list,
        description="Section content items (type-specific)",
    )


class DocumentAnalysis(BaseModel):
    """
    Complete structured analysis of an uploaded document.
    This is the primary output of the Document Intelligence pipeline.
    """

    document_overview: str = Field(
        default="",
        description="2-4 sentence high-level description of the document (max 90 words)",
    )
    topics_covered: List[str] = Field(
        default_factory=list,
        description="Major topics/sections covered in the document (semantic, not section names)",
    )
    key_concepts: List[str] = Field(
        default_factory=list,
        description="Important concepts (max 10, highest-level ideas only)",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="10-20 searchable keywords for semantic search",
    )
    document_metadata: DocumentMetadata = Field(
        default_factory=DocumentMetadata,
        description="Inferred metadata about the document",
    )
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="Deprecated: use type_specific_section instead. Kept for backward compatibility.",
    )
    type_specific_section: TypeSpecificSection = Field(
        default_factory=TypeSpecificSection,
        description="Type-aware section (Candidate Highlights, Research Contributions, etc.)",
    )
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Questions users are likely to ask about this document",
    )
    knowledge_nodes: List[KnowledgeNode] = Field(
        default_factory=list,
        description="Semantic chunks for vector embedding",
    )
    confidence_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-topic confidence scores (0.0-1.0)",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_overview": "This document is a quantitative aptitude handbook...",
                "topics_covered": ["Number System", "Time & Work", "Probability"],
                "key_concepts": ["Arithmetic Progression", "Relative Speed", "Simple Interest"],
                "keywords": ["formula", "speed", "ratio", "probability"],
                "document_metadata": {
                    "type": "Study Material",
                    "domain": "Mathematics",
                    "difficulty": "Intermediate",
                    "estimated_reading_time": "95 minutes",
                    "contains_examples": True,
                    "contains_exercises": True,
                    "contains_formulas": True,
                    "language": "English",
                    "engine_version": "4.0",
                },
                "type_specific_section": {
                    "label": "Learning Objectives",
                    "items": [
                        "Master Number System fundamentals",
                        "Solve Time and Work problems using efficiency formulas",
                    ],
                },
                "suggested_questions": ["Explain Time & Work", "Show all Probability formulas"],
                "confidence_scores": {"Number System": 0.95, "Probability": 0.88},
                "knowledge_nodes": [
                    {
                        "title": "Number System",
                        "description": "Covers types of numbers and their properties",
                        "keywords": ["number", "integer", "prime"],
                        "page_numbers": [],
                    }
                ],
            }
        }
