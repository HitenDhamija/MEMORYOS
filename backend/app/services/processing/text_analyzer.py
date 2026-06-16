"""
Text Analyzer

Analyzes text and extracts statistics and metrics.
"""

import re
from typing import Dict, Tuple
import string


class TextAnalyzer:
    """Analyze text and extract statistics."""
    
    # Common stop words to filter out for meaningful content analysis
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'i', 'you',
        'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
        'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that',
        'these', 'those', 'as', 'if', 'because', 'while', 'when', 'where',
        'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'some', 'any', 'no', 'nor', 'not', 'only', 'such', 'so', 'than',
        'too', 'very', 'just', 'now', 'then', 'here', 'there'
    }
    
    @classmethod
    def analyze(cls, text: str) -> Dict[str, any]:
        """
        Analyze text and return statistics.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with statistics
        """
        if not text:
            return {
                "word_count": 0,
                "char_count": 0,
                "paragraph_count": 0,
                "line_count": 0,
                "sentence_count": 0,
                "reading_time": 0,
                "language": "unknown",
                "avg_word_length": 0,
                "unique_words": 0
            }
        
        word_count = cls._count_words(text)
        char_count = len(text)
        paragraph_count = cls._count_paragraphs(text)
        line_count = len(text.split('\n'))
        sentence_count = cls._count_sentences(text)
        reading_time = cls._estimate_reading_time(word_count)
        language = cls._detect_language(text)
        unique_words = cls._count_unique_words(text)
        avg_word_length = cls._avg_word_length(text)
        
        return {
            "word_count": word_count,
            "char_count": char_count,
            "paragraph_count": paragraph_count,
            "line_count": line_count,
            "sentence_count": sentence_count,
            "reading_time": round(reading_time, 1),
            "language": language,
            "avg_word_length": round(avg_word_length, 1),
            "unique_words": unique_words
        }
    
    @classmethod
    def _count_words(cls, text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        # Split on whitespace
        words = text.split()
        return len(words)
    
    @classmethod
    def _count_paragraphs(cls, text: str) -> int:
        """Count paragraphs (separated by double newlines)."""
        if not text:
            return 0
        # Split on double newlines or more
        paragraphs = re.split(r'\n\n+', text)
        # Count non-empty paragraphs
        return len([p for p in paragraphs if p.strip()])
    
    @classmethod
    def _count_sentences(cls, text: str) -> int:
        """Count sentences (roughly)."""
        if not text:
            return 0
        # Split on . ! ? followed by space
        sentences = re.split(r'[.!?]+\s+', text)
        # Count non-empty sentences
        return len([s for s in sentences if s.strip()])
    
    @classmethod
    def _estimate_reading_time(cls, word_count: int) -> float:
        """
        Estimate reading time in minutes.
        Average reading speed: 200 words per minute
        """
        if word_count == 0:
            return 0
        return word_count / 200.0
    
    @classmethod
    def _detect_language(cls, text: str) -> str:
        """
        Detect language of text.
        Simple heuristic based on common words/scripts.
        """
        if not text:
            return "unknown"
        
        text_lower = text.lower()
        
        # Check for specific languages
        # English
        english_words = {'the', 'a', 'and', 'is', 'in', 'to', 'of', 'be'}
        english_count = sum(1 for word in english_words if word in text_lower)
        if english_count >= 3:
            return "en"
        
        # Spanish
        spanish_words = {'la', 'de', 'que', 'el', 'es', 'y', 'a', 'por'}
        spanish_count = sum(1 for word in spanish_words if word in text_lower)
        if spanish_count >= 3:
            return "es"
        
        # French
        french_words = {'la', 'de', 'le', 'et', 'est', 'un', 'une', 'par'}
        french_count = sum(1 for word in french_words if word in text_lower)
        if french_count >= 3:
            return "fr"
        
        # German
        german_words = {'der', 'die', 'und', 'in', 'das', 'ist', 'den', 'von'}
        german_count = sum(1 for word in german_words if word in text_lower)
        if german_count >= 3:
            return "de"
        
        # Italian
        italian_words = {'il', 'di', 'che', 'da', 'è', 'e', 'la', 'con'}
        italian_count = sum(1 for word in italian_words if word in text_lower)
        if italian_count >= 3:
            return "it"
        
        # Portuguese
        portuguese_words = {'o', 'a', 'que', 'e', 'de', 'da', 'em', 'um'}
        portuguese_count = sum(1 for word in portuguese_words if word in text_lower)
        if portuguese_count >= 3:
            return "pt"
        
        # Check for non-Latin scripts
        # Chinese
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "zh"
        
        # Japanese
        if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return "ja"
        
        # Korean
        if any('\uac00' <= char <= '\ud7af' for char in text):
            return "ko"
        
        # Russian/Cyrillic
        if any('\u0400' <= char <= '\u04ff' for char in text):
            return "ru"
        
        # Arabic
        if any('\u0600' <= char <= '\u06ff' for char in text):
            return "ar"
        
        # Default
        return "unknown"
    
    @classmethod
    def _count_unique_words(cls, text: str) -> int:
        """Count unique words (case-insensitive)."""
        if not text:
            return 0
        
        # Split and lowercase
        words = text.lower().split()
        
        # Remove punctuation from words
        words = [
            ''.join(c for c in word if c not in string.punctuation)
            for word in words
        ]
        
        # Remove empty strings
        words = [w for w in words if w]
        
        # Get unique
        unique = set(words)
        
        return len(unique)
    
    @classmethod
    def _avg_word_length(cls, text: str) -> float:
        """Calculate average word length."""
        if not text:
            return 0
        
        # Split and remove punctuation
        words = [
            ''.join(c for c in word if c not in string.punctuation)
            for word in text.split()
        ]
        
        # Remove empty strings
        words = [w for w in words if w]
        
        if not words:
            return 0
        
        total_length = sum(len(word) for word in words)
        return total_length / len(words)
