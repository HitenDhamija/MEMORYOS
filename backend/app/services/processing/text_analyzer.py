"""
Enhanced Text Analyzer

Analyzes text and extracts statistics, readability metrics,
keyword density, and content quality indicators.
"""

import re
import string
import math
from typing import Dict, List, Tuple
from collections import Counter


class TextAnalyzer:
    """Analyze text and extract comprehensive statistics."""

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
        Analyze text and return comprehensive statistics.

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
                "unique_words": 0,
                "vocabulary_richness": 0,
                "readability_score": 0,
                "top_keywords": [],
                "content_density": 0,
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
        vocabulary_richness = unique_words / max(word_count, 1)
        readability_score = cls._calculate_readability(text, word_count, sentence_count)
        top_keywords = cls._extract_top_keywords(text, top_n=10)
        content_density = cls._calculate_content_density(text)

        return {
            "word_count": word_count,
            "char_count": char_count,
            "paragraph_count": paragraph_count,
            "line_count": line_count,
            "sentence_count": sentence_count,
            "reading_time": round(reading_time, 1),
            "language": language,
            "avg_word_length": round(avg_word_length, 1),
            "unique_words": unique_words,
            "vocabulary_richness": round(vocabulary_richness, 3),
            "readability_score": round(readability_score, 1),
            "top_keywords": top_keywords,
            "content_density": round(content_density, 3),
        }

    @classmethod
    def _count_words(cls, text: str) -> int:
        """Count words in text."""
        if not text:
            return 0
        words = text.split()
        return len(words)

    @classmethod
    def _count_paragraphs(cls, text: str) -> int:
        """Count paragraphs (separated by double newlines)."""
        if not text:
            return 0
        paragraphs = re.split(r'\n\n+', text)
        return len([p for p in paragraphs if p.strip()])

    @classmethod
    def _count_sentences(cls, text: str) -> int:
        """Count sentences."""
        if not text:
            return 0
        sentences = re.split(r'[.!?]+\s+', text)
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
        """Detect language of text."""
        if not text:
            return "unknown"

        text_lower = text.lower()

        languages = {
            "en": {'the', 'a', 'and', 'is', 'in', 'to', 'of', 'be', 'that', 'have'},
            "es": {'la', 'de', 'que', 'el', 'es', 'y', 'a', 'por', 'un', 'una'},
            "fr": {'la', 'de', 'le', 'et', 'est', 'un', 'une', 'par', 'les', 'des'},
            "de": {'der', 'die', 'und', 'in', 'das', 'ist', 'den', 'von', 'ein', 'eine'},
            "it": {'il', 'di', 'che', 'da', 'e', 'la', 'con', 'per', 'un', 'una'},
            "pt": {'o', 'a', 'que', 'e', 'de', 'da', 'em', 'um', 'para', 'com'},
            "ru": set(),
            "zh": set(),
            "ja": set(),
            "ko": set(),
            "ar": set(),
        }

        # Check Latin-script languages
        for lang, words in languages.items():
            if not words:
                continue
            count = sum(1 for word in words if word in text_lower)
            if count >= 3:
                return lang

        # Check non-Latin scripts
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return "zh"
        if any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text):
            return "ja"
        if any('\uac00' <= char <= '\ud7af' for char in text):
            return "ko"
        if any('\u0400' <= char <= '\u04ff' for char in text):
            return "ru"
        if any('\u0600' <= char <= '\u06ff' for char in text):
            return "ar"

        return "unknown"

    @classmethod
    def _count_unique_words(cls, text: str) -> int:
        """Count unique words (case-insensitive)."""
        if not text:
            return 0

        words = text.lower().split()
        words = [
            ''.join(c for c in word if c not in string.punctuation)
            for word in words
        ]
        words = [w for w in words if w]
        unique = set(words)
        return len(unique)

    @classmethod
    def _avg_word_length(cls, text: str) -> float:
        """Calculate average word length."""
        if not text:
            return 0

        words = [
            ''.join(c for c in word if c not in string.punctuation)
            for word in text.split()
        ]
        words = [w for w in words if w]

        if not words:
            return 0

        total_length = sum(len(word) for word in words)
        return total_length / len(words)

    @classmethod
    def _calculate_readability(cls, text: str, word_count: int, sentence_count: int) -> float:
        """
        Calculate readability score (0-100).
        Based on Flesch Reading Ease simplified formula.
        Higher = easier to read.
        """
        if word_count == 0 or sentence_count == 0:
            return 0

        # Count syllables (simplified)
        syllable_count = cls._count_syllables(text)

        # Flesch Reading Ease formula
        score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllable_count / word_count)
        return max(0, min(100, score))

    @classmethod
    def _count_syllables(cls, text: str) -> int:
        """Estimate syllable count (simplified algorithm)."""
        text = text.lower()
        words = re.findall(r'\b[a-z]+\b', text)
        total = 0

        for word in words:
            vowels = 'aeiouy'
            count = 0
            prev_vowel = False

            for char in word:
                is_vowel = char in vowels
                if is_vowel and not prev_vowel:
                    count += 1
                prev_vowel = is_vowel

            # Adjust for silent 'e'
            if word.endswith('e') and count > 1:
                count -= 1

            total += max(1, count)

        return total

    @classmethod
    def _extract_top_keywords(cls, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """Extract top keywords by TF score."""
        words = re.findall(r'\b[a-z]{3,}\b', text.lower())

        # Filter stop words
        filtered = [w for w in words if w not in cls.STOP_WORDS]

        if not filtered:
            return []

        # Count frequencies
        word_counts = Counter(filtered)
        total = len(filtered)

        # TF normalization
        keywords = [(word, count / total) for word, count in word_counts.most_common(top_n)]
        return keywords

    @classmethod
    def _calculate_content_density(cls, text: str) -> float:
        """
        Calculate content density (0-1).
        Ratio of meaningful words to total words.
        Higher = more dense/informative content.
        """
        if not text:
            return 0

        words = text.lower().split()
        if not words:
            return 0

        meaningful = [w for w in words if len(w) > 2 and w not in cls.STOP_WORDS]
        return len(meaningful) / len(words)
