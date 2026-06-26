"""
Knowledge Assistant Service v2

Transforms the Q&A system into a real AI Knowledge Assistant that reasons
over both document content and document metadata.

Pipeline:
1. Intent Detection - Classify user question into intents
2. Hybrid Retrieval - Search metadata, collections, tags, topics, keywords, semantic, knowledge graph
3. Result Ranking - Combine and rank all results
4. Response Generation - Natural, contextual responses with actions
5. Conversation Memory - Track context for multi-turn conversations
"""

import logging
import re
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Set
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_

from app.models import Memory, ProcessedDocument, DocumentEmbedding
from app.models.collection import Collection, CollectionMembership
from app.services.embeddings.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


# ============================================================================
# INTENT DETECTION
# ============================================================================

class IntentType:
    """Supported intent types."""
    FIND_DOCUMENT = "find_document"
    COUNT_DOCUMENTS = "count_documents"
    SUMMARIZE = "summarize"
    COMPARE = "compare"
    EXPLAIN = "explain"
    SEARCH_BY_TOPIC = "search_by_topic"
    SEARCH_BY_KEYWORD = "search_by_keyword"
    SEARCH_BY_TYPE = "search_by_type"
    SEARCH_BY_COLLECTION = "search_by_collection"
    SEARCH_BY_TAG = "search_by_tag"
    SEARCH_BY_DATE = "search_by_date"
    SEARCH_BY_AUTHOR = "search_by_author"
    LIST_DOCUMENTS = "list_documents"
    RECOMMEND = "recommend"
    LOCATE = "locate"
    GENERAL = "general"


class DetectedIntent:
    """Represents a detected intent with extracted parameters."""
    
    def __init__(self, intent_type: str, confidence: float = 1.0, params: Dict = None):
        self.intent_type = intent_type
        self.confidence = confidence
        self.params = params or {}
    
    def __repr__(self):
        return f"Intent({self.intent_type}, conf={self.confidence:.2f}, params={self.params})"


class IntentDetector:
    """Detects user intent from natural language questions."""
    
    # Document type mappings
    TYPE_KEYWORDS = {
        "research_paper": ["research", "paper", "study", "academic", "journal", "publication", "arxiv"],
        "resume": ["resume", "cv", "curriculum vitae", "resume"],
        "certificate": ["certificate", "certification", "credential", "badge", "course completion"],
        "tutorial": ["tutorial", "guide", "how-to", "walkthrough", "instructions"],
        "documentation": ["documentation", "docs", "api reference", "manual", "handbook"],
        "notes": ["notes", "lecture notes", "class notes", "study notes"],
        "report": ["report", "analysis", "assessment", "evaluation"],
        "article": ["article", "blog", "post", "essay"],
        "book": ["book", "textbook", "ebook", "chapter"],
        "interview_prep": ["interview", "interview prep", "interview preparation", "behavioral", "coding interview"],
        "project": ["project", "code", "repository", "codebase"],
    }
    
    # Topic keywords
    TOPIC_KEYWORDS = {
        "computer_vision": ["computer vision", "image", "object detection", "yolo", "cnn", "opencv", "image processing"],
        "nlp": ["nlp", "natural language", "text processing", "transformer", "bert", "gpt", "language model"],
        "machine_learning": ["machine learning", "ml", "deep learning", "neural network", "training", "model"],
        "backend": ["backend", "api", "server", "database", "fastapi", "django", "flask", "node.js"],
        "frontend": ["frontend", "react", "vue", "angular", "css", "html", "javascript", "typescript"],
        "devops": ["devops", "docker", "kubernetes", "ci/cd", "deployment", "aws", "cloud"],
        "security": ["security", "authentication", "authorization", "encryption", "jwt", "oauth"],
        "data_science": ["data science", "数据分析", "statistics", "visualization", "pandas", "numpy"],
        "ai": ["ai", "artificial intelligence", "machine learning", "deep learning", "neural"],
        "programming": ["programming", "coding", "software", "development", "algorithm"],
    }
    
    # Count patterns
    COUNT_PATTERNS = [
        r"how many",
        r"count",
        r"number of",
        r"total",
        r"what.*count",
    ]
    
    # List patterns
    LIST_PATTERNS = [
        r"^list",
        r"^show me",
        r"^show all",
        r"^give me",
        r"^what are all",
        r"^what do i have",
    ]
    
    # Locate patterns
    LOCATE_PATTERNS = [
        r"where is",
        r"where.*stored",
        r"where.*save",
        r"where.*find",
        r"locate",
        r"find my",
    ]
    
    # Date patterns
    DATE_PATTERNS = [
        r"today",
        r"yesterday",
        r"this week",
        r"this month",
        r"last week",
        r"last month",
        r"recent",
        r"newest",
        r"latest",
    ]
    
    @classmethod
    def detect_intents(cls, question: str) -> List[DetectedIntent]:
        """
        Detect all intents from a user question.
        
        Returns:
            List of DetectedIntent objects sorted by confidence
        """
        q_lower = question.lower().strip()
        intents = []
        
        # 1. Check for count intent
        for pattern in cls.COUNT_PATTERNS:
            if re.search(pattern, q_lower):
                intents.append(DetectedIntent(IntentType.COUNT_DOCUMENTS, 0.9))
                break
        
        # 2. Check for list intent
        for pattern in cls.LIST_PATTERNS:
            if re.search(pattern, q_lower):
                intents.append(DetectedIntent(IntentType.LIST_DOCUMENTS, 0.85))
                break
        
        # 3. Check for locate intent
        for pattern in cls.LOCATE_PATTERNS:
            if re.search(pattern, q_lower):
                intents.append(DetectedIntent(IntentType.LOCATE, 0.9))
                break
        
        # 4. Check for summarize intent
        if any(w in q_lower for w in ["summarize", "summary", "overview", "tell me about", "describe"]):
            intents.append(DetectedIntent(IntentType.SUMMARIZE, 0.85))
        
        # 5. Check for compare intent
        if any(w in q_lower for w in ["compare", "difference", "versus", "vs", "differ", "similarities"]):
            intents.append(DetectedIntent(IntentType.COMPARE, 0.85))
        
        # 6. Check for explain intent
        if any(w in q_lower for w in ["explain", "what is", "what are", "what does", "how does"]):
            intents.append(DetectedIntent(IntentType.EXPLAIN, 0.8))
        
        # 7. Check for recommend intent
        if any(w in q_lower for w in ["recommend", "related", "similar", "suggestion"]):
            intents.append(DetectedIntent(IntentType.RECOMMEND, 0.85))
        
        # 8. Detect document type search
        for doc_type, keywords in cls.TYPE_KEYWORDS.items():
            if any(kw in q_lower for kw in keywords):
                intents.append(DetectedIntent(
                    IntentType.SEARCH_BY_TYPE,
                    0.9,
                    {"document_type": doc_type}
                ))
        
        # 9. Detect topic search
        for topic, keywords in cls.TOPIC_KEYWORDS.items():
            if any(kw in q_lower for kw in keywords):
                intents.append(DetectedIntent(
                    IntentType.SEARCH_BY_TOPIC,
                    0.85,
                    {"topic": topic}
                ))
        
        # 10. Detect collection search
        if any(w in q_lower for w in ["collection", "folder", "group", "organized"]):
            intents.append(DetectedIntent(IntentType.SEARCH_BY_COLLECTION, 0.8))
        
        # 11. Detect tag search
        if any(w in q_lower for w in ["tag", "labeled", "marked"]):
            intents.append(DetectedIntent(IntentType.SEARCH_BY_TAG, 0.8))
        
        # 12. Detect date search
        for pattern in cls.DATE_PATTERNS:
            if re.search(pattern, q_lower):
                intents.append(DetectedIntent(IntentType.SEARCH_BY_DATE, 0.8))
                break
        
        # 13. Detect author search
        if any(w in q_lower for w in ["author", "who wrote", "who created", "who made"]):
            intents.append(DetectedIntent(IntentType.SEARCH_BY_AUTHOR, 0.8))
        
        # 14. If no specific intent detected, use find_document or general
        if not intents:
            if any(w in q_lower for w in ["do i have", "any", "where", "which"]):
                intents.append(DetectedIntent(IntentType.FIND_DOCUMENT, 0.7))
            else:
                intents.append(DetectedIntent(IntentType.GENERAL, 0.5))
        
        # Sort by confidence
        intents.sort(key=lambda x: x.confidence, reverse=True)
        
        return intents
    
    @classmethod
    def extract_search_terms(cls, question: str) -> Dict[str, List[str]]:
        """
        Extract searchable terms from the question.
        
        Returns:
            Dict with keys: keywords, topics, types, collections, tags
        """
        q_lower = question.lower().strip()
        
        # Remove common question words
        stop_words = {
            "what", "where", "when", "who", "which", "how", "do", "i", "have",
            "any", "some", "the", "a", "an", "is", "are", "was", "were", "my",
            "me", "about", "related", "show", "list", "find", "search", "tell",
        }
        
        words = re.findall(r'\b[a-z]{2,}\b', q_lower)
        keywords = [w for w in words if w not in stop_words]
        
        # Extract quoted terms (exact matches)
        quoted = re.findall(r'"([^"]+)"', q_lower)
        
        # Extract topics
        topics = []
        for topic, topic_keywords in cls.TOPIC_KEYWORDS.items():
            if any(kw in q_lower for kw in topic_keywords):
                topics.append(topic)
        
        # Extract types
        types = []
        for doc_type, type_keywords in cls.TYPE_KEYWORDS.items():
            if any(kw in q_lower for kw in type_keywords):
                types.append(doc_type)
        
        return {
            "keywords": keywords + quoted,
            "topics": topics,
            "types": types,
            "collections": [],
            "tags": [],
        }


# ============================================================================
# HYBRID RETRIEVAL ENGINE
# ============================================================================

class HybridRetriever:
    """
    Searches across multiple data sources and combines results.
    
    Search order:
    1. Metadata Search (title, description)
    2. Collection Search
    3. Tag Search
    4. Topic Search
    5. Keyword Search
    6. Semantic Embedding Search
    7. Knowledge Graph Neighbors
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        self.embedding_service = get_embedding_service()
    
    def search(
        self,
        question: str,
        intents: List[DetectedIntent],
        search_terms: Dict,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Perform hybrid search across all data sources.
        
        Returns:
            List of result dicts with memory, score, match_type, match_details
        """
        results = {}  # memory_id -> result dict
        
        # 1. Metadata Search (title, description)
        metadata_results = self._search_metadata(search_terms["keywords"])
        for r in metadata_results:
            mid = r["memory_id"]
            if mid not in results:
                results[mid] = r
            else:
                results[mid]["score"] = max(results[mid]["score"], r["score"])
                results[mid]["match_types"].append("metadata")
        
        # 2. Collection Search
        for intent in intents:
            if intent.intent_type == IntentType.SEARCH_BY_COLLECTION:
                collection_results = self._search_collections(search_terms["keywords"])
                for r in collection_results:
                    mid = r["memory_id"]
                    if mid not in results:
                        results[mid] = r
                    else:
                        results[mid]["score"] = max(results[mid]["score"], r["score"])
                        results[mid]["match_types"].append("collection")
        
        # 3. Tag Search
        tag_results = self._search_tags(search_terms["keywords"])
        for r in tag_results:
            mid = r["memory_id"]
            if mid not in results:
                results[mid] = r
            else:
                results[mid]["score"] = max(results[mid]["score"], r["score"])
                results[mid]["match_types"].append("tag")
        
        # 4. Topic Search
        topic_results = self._search_topics(search_terms["topics"], search_terms["keywords"])
        for r in topic_results:
            mid = r["memory_id"]
            if mid not in results:
                results[mid] = r
            else:
                results[mid]["score"] = max(results[mid]["score"], r["score"])
                results[mid]["match_types"].append("topic")
        
        # 5. Keyword Search (in extracted text)
        keyword_results = self._search_keywords(search_terms["keywords"])
        for r in keyword_results:
            mid = r["memory_id"]
            if mid not in results:
                results[mid] = r
            else:
                results[mid]["score"] = max(results[mid]["score"], r["score"])
                results[mid]["match_types"].append("keyword")
        
        # 6. Semantic Embedding Search
        semantic_results = self._search_semantic(question, top_k * 2)
        for r in semantic_results:
            mid = r["memory_id"]
            if mid not in results:
                results[mid] = r
            else:
                results[mid]["score"] = max(results[mid]["score"], r["score"])
                results[mid]["match_types"].append("semantic")
        
        # 7. Knowledge Graph Neighbors
        if results:
            top_memory_ids = sorted(results.keys(), key=lambda x: results[x]["score"], reverse=True)[:3]
            kg_results = self._search_knowledge_graph(top_memory_ids)
            for r in kg_results:
                mid = r["memory_id"]
                if mid not in results:
                    results[mid] = r
                else:
                    results[mid]["score"] = max(results[mid]["score"], r["score"])
                    results[mid]["match_types"].append("knowledge_graph")
        
        # Sort by score and return top_k
        sorted_results = sorted(results.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:top_k]
    
    def _search_metadata(self, keywords: List[str]) -> List[Dict]:
        """Search by title and description."""
        if not keywords:
            return []
        
        results = []
        
        # Build search conditions
        conditions = []
        for kw in keywords[:5]:
            conditions.append(Memory.original_filename.ilike(f"%{kw}%"))
            if hasattr(Memory, 'description'):
                conditions.append(Memory.description.ilike(f"%{kw}%"))
        
        if not conditions:
            return []
        
        memories = self.db.query(Memory).filter(
            Memory.user_id == self.user_id,
            Memory.is_deleted == False,
            or_(*conditions)
        ).limit(20).all()
        
        for mem in memories:
            # Calculate match score based on keyword matches in title
            title_lower = (mem.original_filename or "").lower()
            matches = sum(1 for kw in keywords if kw.lower() in title_lower)
            score = min(1.0, matches / max(len(keywords), 1) * 1.5)
            
            results.append({
                "memory_id": mem.id,
                "memory": mem,
                "score": score,
                "match_types": ["metadata"],
                "match_details": {
                    "matched_keywords": [kw for kw in keywords if kw.lower() in title_lower],
                    "filename": mem.original_filename,
                },
            })
        
        return results
    
    def _search_collections(self, keywords: List[str]) -> List[Dict]:
        """Search by collection name."""
        if not keywords:
            return []
        
        results = []
        
        # Find matching collections
        conditions = [Collection.name.ilike(f"%{kw}%") for kw in keywords[:3]]
        
        collections = self.db.query(Collection).filter(
            Collection.user_id == self.user_id,
            Collection.is_deleted == False,
            or_(*conditions)
        ).all()
        
        for coll in collections:
            # Get memories in this collection
            memberships = self.db.query(CollectionMembership).filter(
                CollectionMembership.collection_id == coll.id,
                CollectionMembership.user_id == self.user_id,
            ).all()
            
            for membership in memberships:
                mem = self.db.query(Memory).filter(Memory.id == membership.memory_id).first()
                if mem and not mem.is_deleted:
                    results.append({
                        "memory_id": mem.id,
                        "memory": mem,
                        "score": 0.8,
                        "match_types": ["collection"],
                        "match_details": {
                            "collection_name": coll.name,
                            "collection_id": coll.id,
                        },
                    })
        
        return results
    
    def _search_tags(self, keywords: List[str]) -> List[Dict]:
        """Search by tags."""
        if not keywords:
            return []
        
        results = []
        
        # Search memories with matching tags
        memories = self.db.query(Memory).filter(
            Memory.user_id == self.user_id,
            Memory.is_deleted == False,
            Memory.tags.isnot(None),
        ).all()
        
        for mem in memories:
            if not mem.tags:
                continue
            
            tags = mem.tags if isinstance(mem.tags, list) else []
            if isinstance(mem.tags, str):
                try:
                    tags = json.loads(mem.tags)
                except:
                    tags = []
            
            tags_lower = [t.lower() for t in tags]
            matches = sum(1 for kw in keywords if any(kw.lower() in t for t in tags_lower))
            
            if matches > 0:
                score = min(1.0, matches / len(keywords) * 1.2)
                results.append({
                    "memory_id": mem.id,
                    "memory": mem,
                    "score": score,
                    "match_types": ["tag"],
                    "match_details": {
                        "matched_tags": [t for t in tags if any(kw.lower() in t.lower() for kw in keywords)],
                    },
                })
        
        return results
    
    def _search_topics(self, topics: List[str], keywords: List[str]) -> List[Dict]:
        """Search by topics in document intelligence metadata."""
        results = []
        
        proc_docs = self.db.query(ProcessedDocument).filter(
            ProcessedDocument.user_id == self.user_id,
            ProcessedDocument.doc_intelligence_metadata.isnot(None),
        ).all()
        
        for proc_doc in proc_docs:
            if not proc_doc.doc_intelligence_metadata:
                continue
            
            meta = proc_doc.doc_intelligence_metadata
            doc_topics = meta.get("topics_covered", [])
            doc_type = meta.get("document_metadata", {}).get("type", "")
            
            # Calculate topic match score
            topic_score = 0
            matched_topics = []
            
            for topic in topics:
                topic_keywords = IntentDetector.TOPIC_KEYWORDS.get(topic, [])
                for kw in topic_keywords:
                    if any(kw.lower() in t.lower() for t in doc_topics):
                        topic_score += 1
                        matched_topics.append(topic)
            
            # Also check direct keyword matches in topics
            for kw in keywords:
                if any(kw.lower() in t.lower() for t in doc_topics):
                    topic_score += 0.5
            
            if topic_score > 0:
                mem = self.db.query(Memory).filter(Memory.id == proc_doc.memory_id).first()
                if mem and not mem.is_deleted:
                    score = min(1.0, topic_score / max(len(topics) + len(keywords), 1))
                    results.append({
                        "memory_id": mem.id,
                        "memory": mem,
                        "score": score,
                        "match_types": ["topic"],
                        "match_details": {
                            "matched_topics": matched_topics[:5],
                            "doc_type": doc_type,
                        },
                    })
        
        return results
    
    def _search_keywords(self, keywords: List[str]) -> List[Dict]:
        """Search by keywords in extracted text."""
        if not keywords:
            return []
        
        results = []
        
        proc_docs = self.db.query(ProcessedDocument).filter(
            ProcessedDocument.user_id == self.user_id,
            ProcessedDocument.extracted_text.isnot(None),
        ).all()
        
        for proc_doc in proc_docs:
            text_lower = (proc_doc.extracted_text or "").lower()
            
            # Score based on keyword matches
            matches = sum(1 for kw in keywords if kw.lower() in text_lower)
            if matches == 0:
                continue
            
            score = min(1.0, matches / len(keywords) * 0.8)
            
            mem = self.db.query(Memory).filter(Memory.id == proc_doc.memory_id).first()
            if mem and not mem.is_deleted:
                results.append({
                    "memory_id": mem.id,
                    "memory": mem,
                    "score": score,
                    "match_types": ["keyword"],
                    "match_details": {
                        "matched_keywords": [kw for kw in keywords if kw.lower() in text_lower],
                    },
                })
        
        return results
    
    def _search_semantic(self, question: str, top_k: int) -> List[Dict]:
        """Search using semantic embeddings."""
        results = []
        
        try:
            question_embedding = self.embedding_service.embed_text(question)
            if not question_embedding:
                return []
            
            similar = self.embedding_service.find_similar(question_embedding, self.user_id, top_k)
            
            for vector_id, similarity_score in similar:
                if similarity_score < 0.2:
                    continue
                
                # Parse vector_id to get processed_document_id
                try:
                    parts = vector_id.split("_")
                    if len(parts) >= 3 and parts[0] == "proc" and parts[1] == "doc":
                        proc_doc_id = int(parts[2])
                    else:
                        continue
                except (IndexError, ValueError):
                    continue
                
                proc_doc = self.db.query(ProcessedDocument).filter(
                    ProcessedDocument.id == proc_doc_id,
                    ProcessedDocument.user_id == self.user_id,
                ).first()
                
                if not proc_doc:
                    continue
                
                mem = self.db.query(Memory).filter(Memory.id == proc_doc.memory_id).first()
                if mem and not mem.is_deleted:
                    results.append({
                        "memory_id": mem.id,
                        "memory": mem,
                        "score": similarity_score,
                        "match_types": ["semantic"],
                        "match_details": {
                            "similarity": similarity_score,
                        },
                    })
        
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
        
        return results
    
    def _search_knowledge_graph(self, memory_ids: List[int]) -> List[Dict]:
        """Find related documents via knowledge graph (collection co-occurrence)."""
        results = []
        
        # Find collections containing the given memories
        collection_ids = set()
        for mid in memory_ids:
            memberships = self.db.query(CollectionMembership).filter(
                CollectionMembership.memory_id == mid,
                CollectionMembership.user_id == self.user_id,
            ).all()
            for m in memberships:
                collection_ids.add(m.collection_id)
        
        # Find other memories in those collections
        seen_memory_ids = set(memory_ids)
        for cid in collection_ids:
            memberships = self.db.query(CollectionMembership).filter(
                CollectionMembership.collection_id == cid,
                CollectionMembership.user_id == self.user_id,
            ).all()
            
            for m in memberships:
                if m.memory_id not in seen_memory_ids:
                    seen_memory_ids.add(m.memory_id)
                    mem = self.db.query(Memory).filter(Memory.id == m.memory_id).first()
                    if mem and not mem.is_deleted:
                        results.append({
                            "memory_id": mem.id,
                            "memory": mem,
                            "score": 0.5,
                            "match_types": ["knowledge_graph"],
                            "match_details": {
                                "co_collection_id": cid,
                            },
                        })
        
        return results[:10]


# ============================================================================
# RESPONSE GENERATOR
# ============================================================================

class ResponseGenerator:
    """Generates natural, contextual responses with actions."""
    
    # Action types
    ACTIONS = {
        "open_document": {"label": "Open Document", "icon": "file", "type": "navigation"},
        "open_collection": {"label": "Open Collection", "icon": "folder", "type": "navigation"},
        "summarize": {"label": "Summarize", "icon": "sparkles", "type": "ai"},
        "compare": {"label": "Compare", "icon": "git-compare", "type": "ai"},
        "move_to_collection": {"label": "Move to Collection", "icon": "folder-plus", "type": "organization"},
        "rename": {"label": "Rename", "icon": "pencil", "type": "organization"},
        "download": {"label": "Download", "icon": "download", "type": "export"},
        "ask_followup": {"label": "Ask Follow-up", "icon": "message-circle", "type": "chat"},
    }
    
    @classmethod
    def generate_response(
        cls,
        question: str,
        intents: List[DetectedIntent],
        results: List[Dict],
        total_docs_searched: int,
    ) -> Dict:
        """
        Generate a natural response based on intents and results.
        
        Returns:
            Dict with answer, actions, follow_up_questions, confidence
        """
        if not results:
            return cls._generate_no_results_response(question, intents, total_docs_searched)
        
        # Get primary intent
        primary_intent = intents[0] if intents else DetectedIntent(IntentType.GENERAL)
        
        # Generate response based on intent type
        if primary_intent.intent_type == IntentType.COUNT_DOCUMENTS:
            return cls._generate_count_response(question, results, primary_intent, total_docs_searched)
        
        elif primary_intent.intent_type == IntentType.LIST_DOCUMENTS:
            return cls._generate_list_response(question, results, primary_intent, total_docs_searched)
        
        elif primary_intent.intent_type == IntentType.LOCATE:
            return cls._generate_locate_response(question, results, primary_intent, total_docs_searched)
        
        elif primary_intent.intent_type == IntentType.SUMMARIZE:
            return cls._generate_summarize_response(question, results, primary_intent, total_docs_searched)
        
        elif primary_intent.intent_type == IntentType.COMPARE:
            return cls._generate_compare_response(question, results, primary_intent, total_docs_searched)
        
        elif primary_intent.intent_type == IntentType.RECOMMEND:
            return cls._generate_recommend_response(question, results, primary_intent, total_docs_searched)
        
        elif primary_intent.intent_type == IntentType.SEARCH_BY_TYPE:
            return cls._generate_type_search_response(question, results, primary_intent, total_docs_searched)
        
        elif primary_intent.intent_type == IntentType.SEARCH_BY_TOPIC:
            return cls._generate_topic_search_response(question, results, primary_intent, total_docs_searched)
        
        elif primary_intent.intent_type == IntentType.FIND_DOCUMENT:
            return cls._generate_find_response(question, results, primary_intent, total_docs_searched)
        
        else:
            return cls._generate_general_response(question, results, primary_intent, total_docs_searched)
    
    @classmethod
    def _generate_count_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a count response."""
        count = len(results)
        
        # Group by type if searching by type
        doc_type = intent.params.get("document_type")
        if doc_type:
            type_label = doc_type.replace("_", " ").title()
            answer = f"Yes, you have **{count}** {type_label}{'s' if count != 1 else ''} in your knowledge base."
        else:
            answer = f"I found **{count}** document{'s' if count != 1 else ''} matching your query."
        
        # Add list
        if count > 0:
            answer += "\n\n"
            for idx, r in enumerate(results[:5], 1):
                mem = r["memory"]
                filename = mem.original_filename or f"Document {mem.id}"
                answer += f"{idx}. **{filename}**\n"
            
            if count > 5:
                answer += f"\n...and {count - 5} more."
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
        
        # Follow-up questions
        follow_ups = []
        if doc_type:
            follow_ups.append(f"What are the main topics in my {doc_type.replace('_', ' ')}s?")
            follow_ups.append(f"Summarize my {doc_type.replace('_', ' ')}s")
        else:
            follow_ups.append("Summarize these documents")
            follow_ups.append("Which of these is most recent?")
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results),
            "actions": actions,
            "follow_up_questions": follow_ups[:3],
            "confidence": 0.9,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_list_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a list response."""
        count = len(results)
        answer = f"Here are the {count} document{'s' if count != 1 else ''} I found:\n\n"
        
        for idx, r in enumerate(results[:10], 1):
            mem = r["memory"]
            filename = mem.original_filename or f"Document {mem.id}"
            match_types = ", ".join(r["match_types"])
            answer += f"{idx}. **{filename}**\n"
            answer += f"   Matched via: {match_types}\n\n"
        
        if count > 10:
            answer += f"...and {count - 10} more documents."
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
        
        # Follow-up
        follow_ups = [
            "Summarize these documents",
            "Which is most relevant?",
            "Show me more details",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.85,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_locate_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a locate response (where is my X?)."""
        if not results:
            return cls._generate_no_results_response(question, [intent], total_docs)
        
        r = results[0]
        mem = r["memory"]
        filename = mem.original_filename or f"Document {mem.id}"
        
        # Find collection
        collections = []
        memberships = r.get("_collections", [])
        if not memberships:
            # Query collections
            pass
        
        answer = f"**{filename}** is stored in your knowledge base.\n\n"
        
        # Add metadata
        if mem.upload_date:
            answer += f"**Uploaded:** {mem.upload_date.strftime('%B %d, %Y')}\n"
        
        if mem.file_type:
            answer += f"**Type:** {mem.file_type.upper()}\n"
        
        # Add topics if available
        if r["match_details"].get("matched_topics"):
            topics = r["match_details"]["matched_topics"][:3]
            answer += f"**Topics:** {', '.join(topics)}\n"
        
        # Add collection info
        if r["match_details"].get("collection_name"):
            answer += f"**Collection:** {r['match_details']['collection_name']}\n"
        
        # Actions
        actions = [
            cls._make_action("open_document", mem.id),
            cls._make_action("download", mem.id),
        ]
        
        # Follow-up
        follow_ups = [
            f"Summarize {filename}",
            f"What else is in this collection?",
            f"Show related documents",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results[:1]),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.95,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_summarize_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a summarize response."""
        if not results:
            return cls._generate_no_results_response(question, [intent], total_docs)
        
        count = len(results)
        answer = f"Here's a summary based on {count} document{'s' if count != 1 else ''}:\n\n"
        
        for idx, r in enumerate(results[:3], 1):
            mem = r["memory"]
            filename = mem.original_filename or f"Document {mem.id}"
            
            # Get preview or extract from match details
            preview = r["match_details"].get("preview", "")
            if not preview and r["match_types"]:
                preview = f"Matched via {', '.join(r['match_types'])} search"
            
            answer += f"**{filename}**\n"
            if preview:
                answer += f"{preview[:200]}\n"
            answer += "\n"
        
        if count > 3:
            answer += f"...and {count - 3} more relevant documents."
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
            actions.append(cls._make_action("ask_followup"))
        
        # Follow-up
        follow_ups = [
            "Compare the top two documents",
            "What are the key topics?",
            "Show me more details",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.85,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_compare_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a compare response."""
        if len(results) < 2:
            return cls._generate_general_response(question, results, intent, total_docs)
        
        answer = "Here's a comparison of the top documents:\n\n"
        
        for idx, r in enumerate(results[:2], 1):
            mem = r["memory"]
            filename = mem.original_filename or f"Document {mem.id}"
            
            answer += f"**{idx}. {filename}**\n"
            
            if r["match_details"].get("doc_type"):
                answer += f"   Type: {r['match_details']['doc_type']}\n"
            
            if r["match_details"].get("matched_topics"):
                topics = r["match_details"]["matched_topics"][:3]
                answer += f"   Topics: {', '.join(topics)}\n"
            
            answer += "\n"
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
            actions.append(cls._make_action("compare"))
        
        # Follow-up
        follow_ups = [
            "What are the key differences?",
            "Summarize both documents",
            "Which one is more recent?",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results[:2]),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.8,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_recommend_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a recommend response."""
        if not results:
            return cls._generate_no_results_response(question, [intent], total_docs)
        
        count = len(results)
        answer = f"Based on your query, I recommend these {count} document{'s' if count != 1 else ''}:\n\n"
        
        for idx, r in enumerate(results[:5], 1):
            mem = r["memory"]
            filename = mem.original_filename or f"Document {mem.id}"
            match_types = ", ".join(r["match_types"])
            answer += f"{idx}. **{filename}**\n"
            answer += f"   Why: Matched via {match_types}\n\n"
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
        
        # Follow-up
        follow_ups = [
            "Tell me more about the first one",
            "Summarize these documents",
            "Are there any similar documents?",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.85,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_type_search_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a response for document type search."""
        doc_type = intent.params.get("document_type", "document")
        type_label = doc_type.replace("_", " ").title()
        
        if not results:
            answer = f"I didn't find any {type_label} documents in your knowledge base.\n\n"
            answer += "However, I found some related documents that might help:"
            
            # Try to find similar documents
            return {
                "answer": answer,
                "sources": [],
                "actions": [],
                "follow_up_questions": [
                    f"Show me all documents",
                    "What document types do I have?",
                    "Search by topic instead",
                ],
                "confidence": 0.6,
                "documents_searched": total_docs,
            }
        
        count = len(results)
        answer = f"**Yes!** I found **{count}** {type_label}{'s' if count != 1 else ''} in your knowledge base:\n\n"
        
        for idx, r in enumerate(results[:5], 1):
            mem = r["memory"]
            filename = mem.original_filename or f"Document {mem.id}"
            answer += f"{idx}. **{filename}**\n"
            
            if r["match_details"].get("matched_topics"):
                topics = r["match_details"]["matched_topics"][:2]
                answer += f"   Topics: {', '.join(topics)}\n"
            
            if r["match_details"].get("collection_name"):
                answer += f"   Collection: {r['match_details']['collection_name']}\n"
            
            answer += "\n"
        
        if count > 5:
            answer += f"...and {count - 5} more {type_label.lower()}s."
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
        
        # Follow-up
        follow_ups = [
            f"Summarize my {type_label.lower()}s",
            f"What topics are in my {type_label.lower()}s?",
            "Show me related documents",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.9,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_topic_search_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a response for topic search."""
        topic = intent.params.get("topic", "this topic")
        topic_label = topic.replace("_", " ").title()
        
        if not results:
            answer = f"I didn't find documents specifically about {topic_label}.\n\n"
            answer += "Let me search for related content..."
            
            return {
                "answer": answer,
                "sources": [],
                "actions": [],
                "follow_up_questions": [
                    f"Show me all documents",
                    "Search by keyword instead",
                    "What topics do I have?",
                ],
                "confidence": 0.5,
                "documents_searched": total_docs,
            }
        
        count = len(results)
        answer = f"I found **{count}** document{'s' if count != 1 else ''} related to **{topic_label}**:\n\n"
        
        for idx, r in enumerate(results[:5], 1):
            mem = r["memory"]
            filename = mem.original_filename or f"Document {mem.id}"
            answer += f"{idx}. **{filename}**\n"
            
            if r["match_details"].get("matched_topics"):
                topics = r["match_details"]["matched_topics"][:2]
                answer += f"   Topics: {', '.join(topics)}\n"
            
            answer += "\n"
        
        if count > 5:
            answer += f"...and {count - 5} more related documents."
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
        
        # Follow-up
        follow_ups = [
            f"Tell me more about {topic_label}",
            f"Summarize these {topic_label} documents",
            "Show related topics",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.85,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_find_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a find/locate response."""
        if not results:
            return cls._generate_no_results_response(question, [intent], total_docs)
        
        count = len(results)
        answer = f"**Yes!** I found {count} document{'s' if count != 1 else ''} matching your query:\n\n"
        
        for idx, r in enumerate(results[:5], 1):
            mem = r["memory"]
            filename = mem.original_filename or f"Document {mem.id}"
            answer += f"{idx}. **{filename}**\n"
            
            if r["match_details"].get("collection_name"):
                answer += f"   Collection: {r['match_details']['collection_name']}\n"
            
            answer += "\n"
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
        
        # Follow-up
        follow_ups = [
            "Open the first one",
            "Summarize these documents",
            "Show more details",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.85,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_general_response(
        cls, question: str, results: List[Dict], intent: DetectedIntent, total_docs: int
    ) -> Dict:
        """Generate a general response."""
        if not results:
            return cls._generate_no_results_response(question, [intent], total_docs)
        
        count = len(results)
        answer = f"Based on your question, I found **{count}** relevant document{'s' if count != 1 else ''}:\n\n"
        
        for idx, r in enumerate(results[:3], 1):
            mem = r["memory"]
            filename = mem.original_filename or f"Document {mem.id}"
            match_types = ", ".join(r["match_types"])
            
            answer += f"{idx}. **{filename}**\n"
            answer += f"   Relevance: {match_types}\n\n"
        
        if count > 3:
            answer += f"...and {count - 3} more relevant documents."
        
        # Actions
        actions = []
        if results:
            actions.append(cls._make_action("open_document", results[0]["memory_id"]))
            actions.append(cls._make_action("summarize"))
        
        # Follow-up
        follow_ups = [
            "Tell me more about the first one",
            "Summarize these documents",
            "Show me related documents",
        ]
        
        return {
            "answer": answer,
            "sources": cls._format_sources(results),
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.75,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _generate_no_results_response(
        cls, question: str, intents: List[DetectedIntent], total_docs: int
    ) -> Dict:
        """Generate a no-results response with suggestions."""
        primary_intent = intents[0] if intents else DetectedIntent(IntentType.GENERAL)
        
        answer = "I couldn't find an exact match for your question.\n\n"
        answer += "However, here are some suggestions:\n\n"
        answer += "1. Try rephrasing your question\n"
        answer += "2. Use different keywords\n"
        answer += "3. Check if the document is uploaded\n\n"
        answer += "Would you like me to:\n"
        answer += "- Show all your documents?\n"
        answer += "- Search by a different topic?\n"
        answer += "- List your document collections?"
        
        # Actions
        actions = [
            cls._make_action("ask_followup"),
        ]
        
        # Follow-up
        follow_ups = [
            "Show all my documents",
            "What topics do I have?",
            "List my collections",
        ]
        
        return {
            "answer": answer,
            "sources": [],
            "actions": actions,
            "follow_up_questions": follow_ups,
            "confidence": 0.3,
            "documents_searched": total_docs,
        }
    
    @classmethod
    def _make_action(cls, action_type: str, memory_id: int = None, collection_id: int = None) -> Dict:
        """Create an action object."""
        action = cls.ACTIONS.get(action_type, {}).copy()
        if not action:
            return None
        
        action["type"] = action_type
        if memory_id:
            action["memory_id"] = memory_id
        if collection_id:
            action["collection_id"] = collection_id
        
        return action
    
    @classmethod
    def _format_sources(cls, results: List[Dict]) -> List[Dict]:
        """Format results into source objects."""
        sources = []
        for r in results[:5]:
            mem = r["memory"]
            sources.append({
                "memory_id": mem.id,
                "filename": mem.original_filename or f"Document {mem.id}",
                "similarity": r["score"],
                "preview": r["match_details"].get("preview", ""),
                "document_type": r["match_details"].get("doc_type", "Document"),
                "match_types": r["match_types"],
            })
        return sources


# ============================================================================
# CONVERSATION MEMORY
# ============================================================================

class ConversationMemory:
    """Tracks conversation context for multi-turn interactions."""
    
    def __init__(self):
        self._conversations: Dict[int, List[Dict]] = {}  # user_id -> messages
    
    def add_message(self, user_id: int, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation history."""
        if user_id not in self._conversations:
            self._conversations[user_id] = []
        
        self._conversations[user_id].append({
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now(),
        })
        
        # Keep only last 20 messages
        if len(self._conversations[user_id]) > 20:
            self._conversations[user_id] = self._conversations[user_id][-20:]
    
    def get_context(self, user_id: int) -> Dict:
        """Get conversation context for a user."""
        messages = self._conversations.get(user_id, [])
        
        if not messages:
            return {"has_context": False}
        
        # Get last user question and assistant response
        last_user = None
        last_assistant = None
        recent_doc_ids = set()
        
        for msg in reversed(messages):
            if msg["role"] == "user" and not last_user:
                last_user = msg
            elif msg["role"] == "assistant" and not last_assistant:
                last_assistant = msg
                # Track mentioned document IDs
                if msg["metadata"].get("source_ids"):
                    recent_doc_ids.update(msg["metadata"]["source_ids"])
        
        return {
            "has_context": True,
            "last_user_question": last_user["content"] if last_user else None,
            "last_assistant_answer": last_assistant["content"] if last_assistant else None,
            "recent_doc_ids": list(recent_doc_ids),
            "message_count": len(messages),
        }
    
    def resolve_reference(self, user_id: int, question: str) -> str:
        """
        Resolve references like "the second one", "that document", etc.
        
        Returns:
            Expanded question with resolved references
        """
        context = self.get_context(user_id)
        
        if not context["has_context"]:
            return question
        
        q_lower = question.lower()
        
        # Check for numbered references
        number_words = {
            "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
            "1st": 1, "2nd": 2, "3rd": 3, "4th": 4, "5th": 5,
        }
        
        for word, num in number_words.items():
            if word in q_lower:
                # Get the nth document from last response
                if context["recent_doc_ids"] and num <= len(context["recent_doc_ids"]):
                    doc_id = context["recent_doc_ids"][num - 1]
                    return f"Document {doc_id}: {question}"
        
        # Check for "that document", "the one about", etc.
        if any(phrase in q_lower for phrase in ["that document", "the one", "it", "this"]):
            if context["recent_doc_ids"]:
                doc_id = context["recent_doc_ids"][0]
                return f"Document {doc_id}: {question}"
        
        return question


# ============================================================================
# MAIN QA SERVICE
# ============================================================================

class QAService:
    """
    Knowledge Assistant that answers natural-language questions over a user's
    knowledge base using hybrid retrieval and natural response generation.
    """
    
    def __init__(self):
        self.conversation_memory = ConversationMemory()
    
    def answer_question(
        self,
        db: Session,
        question: str,
        user_id: int,
        top_k: int = 10,
        min_similarity: float = 0.2,
    ) -> Dict:
        """
        Answer a natural-language question over the user's knowledge base.
        
        Args:
            db: Database session
            question: The user's question
            user_id: User ID for data isolation
            top_k: Number of relevant documents to retrieve
            min_similarity: Minimum similarity threshold
        
        Returns:
            Dict with answer, sources, actions, follow_up_questions, confidence
        """
        try:
            # 0. Resolve conversation references
            expanded_question = self.conversation_memory.resolve_reference(
                user_id, question
            )
            
            # 1. Detect intents
            intents = IntentDetector.detect_intents(expanded_question)
            
            # 2. Extract search terms
            search_terms = IntentDetector.extract_search_terms(expanded_question)
            
            # 3. Hybrid retrieval
            retriever = HybridRetriever(db, user_id)
            results = retriever.search(
                expanded_question,
                intents,
                search_terms,
                top_k=top_k,
            )
            
            # 4. Count total documents searched
            total_docs = db.query(Memory).filter(
                Memory.user_id == user_id,
                Memory.is_deleted == False,
            ).count()
            
            # 5. Generate response
            response = ResponseGenerator.generate_response(
                question,
                intents,
                results,
                total_docs,
            )
            
            # 6. Store in conversation memory
            source_ids = [r["memory_id"] for r in results[:5]]
            self.conversation_memory.add_message(
                user_id, "user", question, {}
            )
            self.conversation_memory.add_message(
                user_id, "assistant", response["answer"],
                {"source_ids": source_ids, "confidence": response["confidence"]}
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error answering question: {e}", exc_info=True)
            return {
                "answer": f"An error occurred while processing your question: {str(e)}",
                "sources": [],
                "actions": [],
                "follow_up_questions": [],
                "confidence": 0.0,
                "documents_searched": 0,
            }


# Singleton
_qa_service: Optional[QAService] = None


def get_qa_service() -> QAService:
    """Get or create the global Q&A service instance."""
    global _qa_service
    if _qa_service is None:
        _qa_service = QAService()
    return _qa_service
