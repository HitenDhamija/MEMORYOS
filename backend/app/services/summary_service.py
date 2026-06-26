"""
Enhanced Summary generation service for processed documents.
Uses document-type-aware summarization with TF-IDF scoring,
redundancy penalties, and structured extraction.
"""

import logging
import re
import math
from typing import Optional, Dict, List, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class SummaryService:
    """Generate intelligent summaries of document content."""

    # Document type detection patterns
    RESUME_SIGNALS = [
        r'\bresume\b', r'\bcurriculum\s*vitae\b', r'\bcv\b',
        r'\beducation\b', r'\bexperience\b', r'\bskills\b',
        r'\blinkedin\b', r'\bgithub\.com\b', r'\bemail\b.*@',
        r'\bphone\b', r'\baddress\b', r'\bobjective\b',
        r'\bsummary\b.*(?:developer|engineer|student|professional)',
        r'\bwork\s*experience\b', r'\bprojects\b', r'\bcertifications\b',
        r'\breferences\b', r'\bdeclaration\b',
    ]

    RESEARCH_PAPER_SIGNALS = [
        r'\babstract\b', r'\bintroduction\b', r'\bmethodology\b',
        r'\bresults\b', r'\bdiscussion\b', r'\bconclusion\b',
        r'\breferences\b', r'\bcitations?\b', r'\bdoi\b',
        r'\bpaper\b', r'\bstudy\b', r'\bexperiment\b',
        r'\bhypothesis\b', r'\bfindings\b', r'\bliterature\s*review\b',
    ]

    ARTICLE_SIGNALS = [
        r'\barticle\b', r'\bblog\b', r'\bpost\b',
        r'\bauthor\b', r'\bpublished\b', r'\bdate\b',
        r'\bintroduction\b', r'\bconclusion\b',
    ]

    REPORT_SIGNALS = [
        r'\breport\b', r'\bexecutive\s*summary\b',
        r'\bfindings\b', r'\brecommendations\b',
        r'\banalysis\b', r'\bdata\b', r'\bmetrics\b',
    ]

    # Stop words for TF-IDF
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'can', 'must', 'shall', 'this',
        'that', 'these', 'those', 'it', 'its', 'not', 'no', 'nor', 'if',
        'then', 'else', 'when', 'while', 'where', 'how', 'what', 'which',
        'who', 'whom', 'why', 'all', 'each', 'every', 'both', 'few', 'more',
        'most', 'other', 'some', 'any', 'such', 'than', 'too', 'very',
        'just', 'also', 'here', 'there', 'now', 'only', 'about', 'above',
        'after', 'before', 'between', 'under', 'into', 'over', 'through',
    }

    @classmethod
    def generate_summary(
        cls,
        text: str,
        max_length: int = 600,
        memory_title: str = None,
    ) -> Optional[str]:
        """
        Generate a smart summary from document text.

        Args:
            text: Full extracted document text
            max_length: Maximum character length of summary
            memory_title: Optional title hint for the document

        Returns:
            Generated summary or None if text is too short
        """
        if not text or len(text.strip()) < 50:
            logger.debug("Text too short for summarization")
            return None

        try:
            doc_type = cls._detect_document_type(text, memory_title)
            logger.debug(f"Detected document type: {doc_type}")

            if doc_type == "resume":
                summary = cls._summarize_resume(text, max_length)
            elif doc_type == "research_paper":
                summary = cls._summarize_research_paper(text, max_length)
            elif doc_type == "report":
                summary = cls._summarize_report(text, max_length)
            elif doc_type == "article":
                summary = cls._summarize_article(text, max_length)
            else:
                summary = cls._summarize_general(text, max_length)

            if summary and len(summary) > max_length:
                summary = summary[:max_length].rsplit(' ', 1)[0] + '...'

            if summary:
                logger.debug(f"Generated {doc_type} summary ({len(summary)} chars)")
            return summary

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return cls._fallback_summary(text, max_length)

    @classmethod
    def _detect_document_type(cls, text: str, title: str = None) -> str:
        """Detect the type of document based on content signals."""
        text_lower = text.lower()
        title_lower = (title or "").lower()

        scores = {
            "resume": 0,
            "research_paper": 0,
            "report": 0,
            "article": 0,
        }

        for pattern in cls.RESUME_SIGNALS:
            if re.search(pattern, text_lower):
                scores["resume"] += 1
            if re.search(pattern, title_lower):
                scores["resume"] += 2

        for pattern in cls.RESEARCH_PAPER_SIGNALS:
            if re.search(pattern, text_lower):
                scores["research_paper"] += 1
            if re.search(pattern, title_lower):
                scores["research_paper"] += 2

        for pattern in cls.REPORT_SIGNALS:
            if re.search(pattern, text_lower):
                scores["report"] += 1
            if re.search(pattern, title_lower):
                scores["report"] += 2

        for pattern in cls.ARTICLE_SIGNALS:
            if re.search(pattern, text_lower):
                scores["article"] += 1
            if re.search(pattern, title_lower):
                scores["article"] += 2

        if re.search(r'@\w+\.\w+', text):
            scores["resume"] += 2
        if re.search(r'\b\d{10}\b', text) or re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
            scores["resume"] += 1
        if re.search(r'\bbtech\b|\bb\.tech\b|\bmaster\b|\bbachelor\b|\bphd\b|\bdegree\b', text_lower):
            scores["resume"] += 2
        if re.search(r'\bsgpa\b|\bcgpa\b|\bpercentage\b', text_lower):
            scores["resume"] += 1

        section_headers = re.findall(r'\n\s*([A-Z][A-Za-z\s]+)\s*\n', text)
        resume_sections = {'education', 'experience', 'skills', 'projects', 'certifications',
                          'achievements', 'activities', 'objective', 'summary', 'profile',
                          'work experience', 'technical skills', 'personal details'}
        found_sections = set(s.strip().lower() for s in section_headers)
        if len(found_sections & resume_sections) >= 2:
            scores["resume"] += 3

        best_type = max(scores, key=scores.get)
        if scores[best_type] < 2:
            return "general"
        return best_type

    @classmethod
    def _summarize_resume(cls, text: str, max_length: int) -> Optional[str]:
        """Generate a structured summary for a resume/CV."""
        sections = cls._extract_resume_sections(text)
        parts = []

        name = cls._extract_name(text)
        if name:
            parts.append(f"Name: {name}")

        if sections.get("summary"):
            parts.append(sections["summary"])
        elif sections.get("objective"):
            parts.append(sections["objective"])

        if sections.get("education"):
            edu_text = sections["education"][:200]
            parts.append(f"Education: {edu_text}")

        if sections.get("skills"):
            skills_text = sections["skills"][:200]
            parts.append(f"Skills: {skills_text}")

        if sections.get("experience"):
            exp_text = sections["experience"][:250]
            parts.append(f"Experience: {exp_text}")

        if sections.get("projects"):
            proj_text = sections["projects"][:200]
            parts.append(f"Projects: {proj_text}")

        if parts:
            summary = " | ".join(parts)
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
            return summary

        return cls._extract_key_sentences(text, max_length, domain="resume")

    @classmethod
    def _extract_resume_sections(cls, text: str) -> Dict[str, str]:
        """Extract sections from a resume."""
        sections = {}
        section_patterns = [
            'summary', 'objective', 'profile', 'about',
            'education', 'academic',
            'experience', 'work experience', 'employment', 'work history',
            'skills', 'technical skills', 'competencies', 'technologies',
            'projects', 'key projects', 'personal projects',
            'certifications', 'licenses',
            'achievements', 'awards', 'honors',
            'activities', 'extracurricular',
            'references', 'declaration',
        ]

        text_lines = text.split('\n')
        current_section = None
        current_content = []

        for line in text_lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            matched_section = None
            for sp in section_patterns:
                if re.match(rf'^{re.escape(sp)}\s*$', line_lower) or \
                   re.match(rf'^{re.escape(sp)}\s*[:\-]?\s*$', line_lower):
                    matched_section = sp
                    break

            if matched_section:
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = matched_section
                current_content = []
            elif current_section and line_stripped:
                current_content.append(line_stripped)

        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    @classmethod
    def _extract_name(cls, text: str) -> Optional[str]:
        """Extract the person's name from a resume."""
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            if re.search(r'@|\.com|\.org|\.net|phone|email|linkedin|github|http', line.lower()):
                continue
            if re.search(r'^[A-Z][a-z]+ [A-Z][a-z]+$', line):
                return line
            if re.search(r'^[A-Z][a-z]+ [A-Z]\.?\s*[A-Z][a-z]+$', line):
                return line
            words = line.split()
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w and w[0].isalpha()):
                return line
        return None

    @classmethod
    def _summarize_research_paper(cls, text: str, max_length: int) -> Optional[str]:
        """Generate a summary for a research paper."""
        sections = cls._extract_paper_sections(text)
        parts = []

        if sections.get("abstract"):
            parts.append(f"Abstract: {sections['abstract'][:300]}")

        if sections.get("introduction"):
            intro = sections["introduction"][:200]
            parts.append(f"Introduction: {intro}")

        if sections.get("conclusion"):
            conclusion = sections["conclusion"][:200]
            parts.append(f"Conclusion: {conclusion}")

        if sections.get("results"):
            results = sections["results"][:200]
            parts.append(f"Results: {results}")

        if parts:
            summary = " ".join(parts)
            if len(summary) > max_length:
                summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
            return summary

        return cls._extract_key_sentences(text, max_length, domain="academic")

    @classmethod
    def _extract_paper_sections(cls, text: str) -> Dict[str, str]:
        """Extract sections from a research paper."""
        sections = {}
        section_names = ['abstract', 'introduction', 'methodology', 'methods',
                        'results', 'discussion', 'conclusion', 'conclusions',
                        'related work', 'background', 'future work']

        text_lower = text.lower()
        for section in section_names:
            # Improved pattern: look for section headers followed by content
            pattern = rf'(?:^|\n)\s*{re.escape(section)}\s*[:\.]?\s*\n(.*?)(?=\n\s*(?:" + "|".join(section_names) + r")\s*[:\.]?\s*\n|\Z)'
            match = re.search(pattern, text_lower, re.DOTALL)
            if match:
                content = match.group(1).strip()
                if len(content) > 30:
                    sections[section] = content[:500]

        return sections

    @classmethod
    def _summarize_report(cls, text: str, max_length: int) -> Optional[str]:
        """Generate a summary for a report."""
        return cls._extract_key_sentences(text, max_length, domain="report")

    @classmethod
    def _summarize_article(cls, text: str, max_length: int) -> Optional[str]:
        """Generate a summary for an article."""
        return cls._extract_key_sentences(text, max_length, domain="article")

    @classmethod
    def _summarize_general(cls, text: str, max_length: int) -> Optional[str]:
        """Generate a general-purpose summary."""
        return cls._extract_key_sentences(text, max_length, domain="general")

    @classmethod
    def _extract_key_sentences(cls, text: str, max_length: int, domain: str = "general") -> Optional[str]:
        """Extract key sentences with TF-IDF scoring and redundancy penalty."""
        sentences = cls._extract_sentences(text)
        if not sentences:
            return cls._fallback_summary(text, max_length)

        if len(sentences) < 3:
            return ' '.join(sentences)[:max_length]

        scored = cls._score_sentences(sentences, text, domain)

        # Pick top sentences with redundancy penalty (avoid similar sentences)
        selected = []
        selected_words = set()
        for sentence, idx, score in scored:
            if len(selected) >= 8:
                break

            # Redundancy check: skip if >50% words overlap with already selected
            sent_words = set(re.findall(r'\b\w+\b', sentence.lower()))
            sent_words -= cls.STOP_WORDS
            if selected_words and len(sent_words & selected_words) / max(len(sent_words), 1) > 0.5:
                continue

            selected.append((sentence, idx, score))
            selected_words.update(sent_words)

        # Sort selected by original position for coherent flow
        selected.sort(key=lambda x: x[1])
        summary = ' '.join(s[0] for s in selected)

        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(' ', 1)[0] + '...'

        return summary

    @staticmethod
    def _extract_sentences(text: str) -> List[str]:
        """Extract sentences from text."""
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        sentences = [s.strip() for s in parts if s.strip() and len(s.strip()) > 15]
        return sentences

    @classmethod
    def _score_sentences(cls, sentences: List[str], text: str, domain: str = "general") -> List[Tuple[str, int, float]]:
        """Score sentences by importance with TF-IDF weighting and redundancy penalty."""
        # TF-IDF-like word frequency
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        for word in words:
            if len(word) > 3 and word not in cls.STOP_WORDS:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Normalize frequencies
        max_freq = max(word_freq.values()) if word_freq else 1
        tf_idf = {w: f / max_freq for w, f in word_freq.items()}

        # Top keywords
        keywords = sorted(tf_idf.items(), key=lambda x: x[1], reverse=True)[:30]
        keyword_set = set(w for w, _ in keywords)

        # Domain-specific important phrases
        domain_phrases = {
            "resume": ['experienced', 'skilled', 'proficient', 'developed', 'implemented',
                      'led', 'managed', 'built', 'created', 'designed', 'achieved',
                      'delivered', 'improved', 'increased', 'reduced', 'optimized',
                      'collaborated', 'mentored', 'architected', 'deployed', 'launched'],
            "academic": ['demonstrated', 'showed', 'found', 'concluded', 'significant',
                        'novel', 'first', 'improved', 'outperformed', 'proposed',
                        'introduced', 'validated', 'evaluated', 'compared', 'achieved'],
            "report": ['total', 'increase', 'decrease', 'percent', 'billion',
                      'million', 'growth', 'decline', 'revenue', 'profit',
                      'quarterly', 'annual', 'year-over-year', 'metric', 'kpi'],
            "article": ['important', 'significant', 'key', 'main', 'essential',
                       'critical', 'fundamental', 'breakthrough', 'innovative',
                       'emerging', 'trend', 'future', 'impact'],
            "general": ['important', 'significant', 'key', 'main', 'essential',
                       'approach', 'method', 'result', 'conclusion', 'based'],
        }

        scored = []
        for idx, sentence in enumerate(sentences):
            score = 0.0
            sent_lower = sentence.lower()
            word_count = len(sentence.split())

            # Position bonus (first and early sentences important)
            if idx == 0:
                score += 12
            elif idx < len(sentences) * 0.1:
                score += 8
            elif idx < len(sentences) * 0.2:
                score += 5
            elif idx < len(sentences) * 0.3:
                score += 3

            # Length bonus (prefer 12-40 word sentences)
            if 12 <= word_count <= 40:
                score += 5
            elif 8 <= word_count <= 50:
                score += 2

            # TF-IDF keyword density
            sent_words = set(re.findall(r'\b\w+\b', sent_lower))
            keyword_hits = sum(tf_idf.get(w, 0) for w in sent_words if w in keyword_set)
            score += keyword_hits * 3

            # Domain-specific phrases
            phrases = domain_phrases.get(domain, domain_phrases["general"])
            phrase_hits = sum(1 for p in phrases if p in sent_lower)
            score += phrase_hits * 4

            # Contains numbers/data (valuable in reports, academic)
            if re.search(r'\d+', sentence):
                score += 2

            # Contains percentages (strong signal for reports)
            if re.search(r'\d+%|\d+ percent', sent_lower):
                score += 3

            # Contains citations/references (strong signal for academic)
            if re.search(r'\[\d+\]|\(\w+\s+\d{4}\)', sentence):
                score += 3

            # Penalty for contact info / boilerplate
            if re.search(r'@\w+|\.com|\.org|phone|address|linkedin|http', sent_lower):
                score -= 8

            # Penalty for very short or very long
            if word_count < 5:
                score -= 5
            elif word_count > 60:
                score -= 3

            # Penalty for sentences that are mostly list items
            if re.match(r'^\s*[-•*]\s', sentence) or sentence.strip().startswith('•'):
                score -= 2

            scored.append((sentence, idx, score))

        scored.sort(key=lambda x: x[2], reverse=True)
        return scored

    @staticmethod
    def _fallback_summary(text: str, max_length: int) -> Optional[str]:
        """Fallback: return first meaningful chunk of text."""
        if not text:
            return None

        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= max_length:
            return text

        chunk = text[:max_length]
        last_period = chunk.rfind('.')
        if last_period > max_length * 0.5:
            return chunk[:last_period + 1]

        return chunk.rsplit(' ', 1)[0] + '...'
