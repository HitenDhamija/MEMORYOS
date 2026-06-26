"""
Smart collection suggestion engine for Phase 7.
"""

import logging
from typing import List, Tuple, Dict, Optional
from collections import Counter
from datetime import datetime
import pytz
from sqlalchemy.orm import Session

from app.models.models import Memory
from app.models.processed_document import ProcessedDocument
from app.models.collection import Collection, CollectionSuggestion
from app.models.document_embedding import DocumentEmbedding

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """Generates smart collection suggestions based on user's memories."""
    
    @staticmethod
    def analyze_user_memories(
        db: Session,
        user_id: int,
        limit: int = 100
    ) -> Dict[str, list]:
        """Analyze user's memories to extract topics and patterns."""
        try:
            # Get user's processed documents
            proc_docs = db.query(ProcessedDocument).join(
                Memory,
                ProcessedDocument.memory_id == Memory.id
            ).filter(
                Memory.user_id == user_id,
                Memory.is_deleted == False
            ).limit(limit).all()
            
            if not proc_docs:
                return {"topics": [], "file_types": [], "languages": []}
            
            # Extract topics
            all_topics = []
            file_types = []
            languages = []
            
            for doc in proc_docs:
                # Topics
                if doc.topics:
                    tech_topics = doc.topics.get("technologies", [])
                    for topic in tech_topics[:3]:  # Top 3 per doc
                        if isinstance(topic, dict):
                            all_topics.append(topic.get("name", ""))
                        else:
                            all_topics.append(str(topic))
                
                # File types
                if doc.memory and doc.memory.file_type:
                    file_types.append(doc.memory.file_type)
                
                # Languages
                if doc.language:
                    languages.append(doc.language)
            
            # Count frequencies
            topic_counts = Counter(all_topics)
            file_type_counts = Counter(file_types)
            language_counts = Counter(languages)
            
            return {
                "topics": [t for t, _ in topic_counts.most_common(20)],
                "file_types": [ft for ft, _ in file_type_counts.most_common(10)],
                "languages": [l for l, _ in language_counts.most_common(5)]
            }
        except Exception as e:
            logger.error(f"Failed to analyze memories: {e}")
            return {"topics": [], "file_types": [], "languages": []}
    
    @staticmethod
    def generate_suggestions(
        db: Session,
        user_id: int,
        min_confidence: int = 40
    ) -> List[CollectionSuggestion]:
        """Generate collection suggestions for user."""
        try:
            # Analyze memories
            analysis = SuggestionEngine.analyze_user_memories(db, user_id)
            
            if not analysis["topics"]:
                logger.info(f"No topics found for user {user_id}")
                return []
            
            # Check for existing suggestions
            existing = db.query(CollectionSuggestion).filter(
                CollectionSuggestion.user_id == user_id,
                CollectionSuggestion.status == "pending"
            ).all()
            
            # Clear old pending suggestions
            for sugg in existing:
                db.delete(sugg)
            db.commit()
            
            suggestions = []
            
            # Generate suggestions from topics
            topic_groupings = SuggestionEngine._group_related_topics(
                analysis["topics"]
            )
            
            for group_name, topics, confidence in topic_groupings:
                # Check if collection already exists
                existing_collection = db.query(Collection).filter(
                    Collection.user_id == user_id,
                    Collection.name.ilike(group_name),
                    Collection.is_deleted == False
                ).first()
                
                if existing_collection:
                    continue
                
                if confidence >= min_confidence:
                    reasoning = f"Based on {len(topics)} related topics in your memories"
                    
                    suggestion = CollectionSuggestion(
                        user_id=user_id,
                        suggested_name=group_name,
                        reasoning=reasoning,
                        topics=",".join(topics),
                        confidence_score=confidence,
                        status="pending"
                    )
                    db.add(suggestion)
                    suggestions.append(suggestion)
            
            db.commit()
            logger.info(f"Generated {len(suggestions)} suggestions for user {user_id}")
            return suggestions
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to generate suggestions: {e}")
            return []
    
    @staticmethod
    def _group_related_topics(topics: List[str]) -> List[Tuple[str, List[str], int]]:
        """Group related topics into collection suggestions."""
        groupings = []
        
        # Define topic groupings (can be expanded)
        topic_groups = {
            "Backend Development": [
                "FastAPI", "Django", "Flask", "Node.js", "Express",
                "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes",
                "Python", "JavaScript", "Java", "Go"
            ],
            "Frontend Development": [
                "React", "Vue", "Angular", "TypeScript", "CSS",
                "HTML", "JavaScript", "Next.js", "Webpack", "Tailwind"
            ],
            "System Design": [
                "Scalability", "Database Design", "Caching", "Load Balancing",
                "Microservices", "Architecture", "Design Patterns"
            ],
            "AI & Machine Learning": [
                "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
                "NLP", "Computer Vision", "Neural Networks", "Transformers"
            ],
            "Cloud & DevOps": [
                "AWS", "GCP", "Azure", "Docker", "Kubernetes",
                "CI/CD", "Jenkins", "Terraform", "CloudFormation"
            ],
            "Security": [
                "JWT", "OAuth", "SSL/TLS", "Encryption", "Authentication",
                "Authorization", "CORS", "Security Headers", "OWASP"
            ],
            "Data & Analytics": [
                "SQL", "Pandas", "Data Analysis", "Visualization",
                "Big Data", "Spark", "Statistics", "Analytics"
            ],
            "Interview Preparation": [
                "LeetCode", "Behavioral", "System Design", "OA",
                "Amazon", "Google", "Microsoft", "Interview"
            ],
        }
        
        matched_groups = {}
        for group_name, group_topics in topic_groups.items():
            matches = [t for t in topics if any(
                topic_keyword.lower() in t.lower()
                for topic_keyword in group_topics
            )]
            
            if matches:
                confidence = min(100, len(matches) * 20 + 40)
                matched_groups[group_name] = (matches[:3], confidence)
        
        # Convert to list of tuples
        for group_name, (matched_topics, confidence) in matched_groups.items():
            groupings.append((group_name, matched_topics, confidence))
        
        return sorted(groupings, key=lambda x: x[2], reverse=True)[:10]
    
    @staticmethod
    def accept_suggestion(
        db: Session,
        suggestion_id: int,
        user_id: int
    ) -> Tuple[Optional[Collection], Optional[str]]:
        """Accept a collection suggestion."""
        try:
            suggestion = db.query(CollectionSuggestion).filter(
                CollectionSuggestion.id == suggestion_id,
                CollectionSuggestion.user_id == user_id,
                CollectionSuggestion.status == "pending"
            ).first()
            
            if not suggestion:
                return None, "Suggestion not found"
            
            # Create collection from suggestion
            from app.services.collections.collection_service import CollectionService
            
            collection, error = CollectionService.create_collection(
                db,
                user_id,
                suggestion.suggested_name,
                description=suggestion.reasoning
            )
            
            if error:
                return None, error
            
            # Update suggestion status
            suggestion.status = "accepted"
            suggestion.reviewed_at = datetime.now(pytz.UTC)
            db.commit()
            
            logger.info(f"Accepted suggestion {suggestion_id} for user {user_id}")
            return collection, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to accept suggestion: {e}")
            return None, str(e)
    
    @staticmethod
    def reject_suggestion(
        db: Session,
        suggestion_id: int,
        user_id: int
    ) -> Tuple[bool, Optional[str]]:
        """Reject a collection suggestion."""
        try:
            suggestion = db.query(CollectionSuggestion).filter(
                CollectionSuggestion.id == suggestion_id,
                CollectionSuggestion.user_id == user_id,
                CollectionSuggestion.status == "pending"
            ).first()
            
            if not suggestion:
                return False, "Suggestion not found"
            
            suggestion.status = "rejected"
            suggestion.reviewed_at = datetime.now(pytz.UTC)
            db.commit()
            
            logger.info(f"Rejected suggestion {suggestion_id}")
            return True, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to reject suggestion: {e}")
            return False, str(e)
    
    @staticmethod
    def get_pending_suggestions(
        db: Session,
        user_id: int
    ) -> List[CollectionSuggestion]:
        """Get pending suggestions for user."""
        return db.query(CollectionSuggestion).filter(
            CollectionSuggestion.user_id == user_id,
            CollectionSuggestion.status == "pending"
        ).order_by(CollectionSuggestion.confidence_score.desc()).all()

    @staticmethod
    def generate_rename_suggestions(
        db: Session,
        user_id: int
    ) -> List[CollectionSuggestion]:
        """Generate rename suggestions for collections with poor names."""
        try:
            collections = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.is_deleted == False
            ).all()
            
            suggestions = []
            
            for collection in collections:
                new_name = SuggestionEngine._suggest_better_name(collection)
                if new_name and new_name != collection.name:
                    suggestion = CollectionSuggestion(
                        user_id=user_id,
                        suggested_name=new_name,
                        reasoning=f"Rename '{collection.name}' to something more descriptive",
                        topics="",
                        confidence_score=60,
                        status="pending"
                    )
                    db.add(suggestion)
                    suggestions.append(suggestion)
            
            db.commit()
            return suggestions
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to generate rename suggestions: {e}")
            return []

    @staticmethod
    def _suggest_better_name(collection: Collection) -> Optional[str]:
        """Suggest a better name for a collection based on its contents."""
        name = collection.name.lower()
        
        # Check for generic names
        generic_names = ['untitled', 'new collection', 'misc', 'miscellaneous', 'other', 'stuff', 'things']
        if name in generic_names:
            # Try to derive name from memories
            if collection.memories:
                memory_count = len(collection.memories)
                return f"Collection ({memory_count} items)"
        
        return None

    @staticmethod
    def generate_merge_suggestions(
        db: Session,
        user_id: int
    ) -> List[CollectionSuggestion]:
        """Generate merge suggestions for similar collections."""
        try:
            collections = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.is_deleted == False
            ).all()
            
            if len(collections) < 2:
                return []
            
            suggestions = []
            checked_pairs = set()
            
            for i, coll1 in enumerate(collections):
                for coll2 in collections[i+1:]:
                    pair_key = tuple(sorted([coll1.id, coll2.id]))
                    if pair_key in checked_pairs:
                        continue
                    checked_pairs.add(pair_key)
                    
                    similarity = SuggestionEngine._calculate_collection_similarity(coll1, coll2)
                    if similarity > 0.7:  # 70% similarity threshold
                        suggestion = CollectionSuggestion(
                            user_id=user_id,
                            suggested_name=f"Merge '{coll1.name}' and '{coll2.name}'",
                            reasoning=f"Collections are {int(similarity*100)}% similar in content",
                            topics=f"{coll1.name},{coll2.name}",
                            confidence_score=int(similarity * 100),
                            status="pending"
                        )
                        db.add(suggestion)
                        suggestions.append(suggestion)
            
            db.commit()
            return suggestions[:5]  # Limit to top 5
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to generate merge suggestions: {e}")
            return []

    @staticmethod
    def _calculate_collection_similarity(coll1: Collection, coll2: Collection) -> float:
        """Calculate similarity between two collections based on names and descriptions."""
        # Simple text similarity based on common words
        words1 = set(coll1.name.lower().split())
        if coll1.description:
            words1.update(coll1.description.lower().split())
        
        words2 = set(coll2.name.lower().split())
        if coll2.description:
            words2.update(coll2.description.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0

    @staticmethod
    def accept_rename_suggestion(
        db: Session,
        suggestion_id: int,
        user_id: int,
        new_name: str
    ) -> Tuple[Optional[Collection], Optional[str]]:
        """Accept a rename suggestion with custom name."""
        try:
            suggestion = db.query(CollectionSuggestion).filter(
                CollectionSuggestion.id == suggestion_id,
                CollectionSuggestion.user_id == user_id,
                CollectionSuggestion.status == "pending"
            ).first()
            
            if not suggestion:
                return None, "Suggestion not found"
            
            # Find the collection to rename
            # Parse the original name from reasoning
            import re
            match = re.search(r"Rename '(.+?)'", suggestion.reasoning)
            if not match:
                return None, "Invalid suggestion format"
            
            original_name = match.group(1)
            collection = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.name == original_name,
                Collection.is_deleted == False
            ).first()
            
            if not collection:
                return None, "Collection not found"
            
            # Update collection name
            collection.name = new_name
            suggestion.status = "accepted"
            suggestion.reviewed_at = datetime.now(pytz.UTC)
            db.commit()
            
            return collection, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to accept rename suggestion: {e}")
            return None, str(e)

    @staticmethod
    def accept_merge_suggestion(
        db: Session,
        suggestion_id: int,
        user_id: int
    ) -> Tuple[Optional[Collection], Optional[str]]:
        """Accept a merge suggestion."""
        try:
            suggestion = db.query(CollectionSuggestion).filter(
                CollectionSuggestion.id == suggestion_id,
                CollectionSuggestion.user_id == user_id,
                CollectionSuggestion.status == "pending"
            ).first()
            
            if not suggestion:
                return None, "Suggestion not found"
            
            # Parse collection names from topics
            if not suggestion.topics:
                return None, "Invalid suggestion format"
            
            coll_names = suggestion.topics.split(",")
            if len(coll_names) != 2:
                return None, "Invalid suggestion format"
            
            # Find both collections
            coll1 = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.name == coll_names[0].strip(),
                Collection.is_deleted == False
            ).first()
            
            coll2 = db.query(Collection).filter(
                Collection.user_id == user_id,
                Collection.name == coll_names[1].strip(),
                Collection.is_deleted == False
            ).first()
            
            if not coll1 or not coll2:
                return None, "One or both collections not found"
            
            # Create merged collection
            from app.services.collections.collection_service import CollectionService
            
            merged_name = suggestion.suggested_name.replace("Merge ", "").replace(" and ", " & ")
            merged_collection, error = CollectionService.create_collection(
                db,
                user_id,
                merged_name,
                description=f"Merged from '{coll1.name}' and '{coll2.name}'"
            )
            
            if error:
                return None, error
            
            # Move all memories from both collections to merged collection
            from app.models.collection import CollectionMembership
            
            for coll in [coll1, coll2]:
                memberships = db.query(CollectionMembership).filter(
                    CollectionMembership.collection_id == coll.id
                ).all()
                
                for membership in memberships:
                    # Check if memory already in merged collection
                    existing = db.query(CollectionMembership).filter(
                        CollectionMembership.collection_id == merged_collection.id,
                        CollectionMembership.memory_id == membership.memory_id
                    ).first()
                    
                    if not existing:
                        new_membership = CollectionMembership(
                            collection_id=merged_collection.id,
                            memory_id=membership.memory_id,
                            user_id=user_id
                        )
                        db.add(new_membership)
            
            # Soft delete original collections
            coll1.is_deleted = True
            coll2.is_deleted = True
            
            suggestion.status = "accepted"
            suggestion.reviewed_at = datetime.now(pytz.UTC)
            db.commit()
            
            return merged_collection, None
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to accept merge suggestion: {e}")
            return None, str(e)
