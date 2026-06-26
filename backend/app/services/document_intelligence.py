"""
Document Intelligence Engine v5 — Semantic Understanding Engine

Fully local (no cloud APIs). Uses sentence-transformers for semantic
embeddings, networkx for concept graphs, and sklearn for clustering.

Pipeline:
  0. OCR Cleanup
  1. Document Type Classification (enhanced with semantic signals)
  2. Named Entity Recognition (PERSON, ORG, TECH, SKILL, etc.)
  3. Concept Extraction (semantic — sentence-transformers)
  4. Topic Clustering (parent→child graph via networkx)
  5. Topic Ranking (semantic importance, graph degree, frequency)
  6. Summary Generation (type-aware, never reuses document text)
  7. Keyword Extraction
  8. Type-Specific Sections
  9. Question Generation (from concepts, not raw text)
  10. Knowledge Node Chunking
  11. Confidence Validation Loop
"""

import re
import math
import logging
from typing import List, Dict, Tuple, Optional, Set, Any
from collections import Counter
from app.schemas.document_analysis import (
    DocumentAnalysis,
    DocumentMetadata,
    KnowledgeNode,
    TypeSpecificSection,
)

logger = logging.getLogger(__name__)

# Lazy-load heavy models to avoid startup delay
_sentence_model = None
_networkx = None


def _get_sentence_model():
    """Lazy-load SentenceTransformer."""
    global _sentence_model
    if _sentence_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded SentenceTransformer model")
        except Exception as e:
            logger.warning(f"Failed to load SentenceTransformer: {e}")
            _sentence_model = False  # Mark as failed
    return _sentence_model if _sentence_model is not False else None


def _get_networkx():
    """Lazy-import networkx."""
    global _networkx
    if _networkx is None:
        try:
            import networkx as nx
            _networkx = nx
        except ImportError:
            _networkx = False
    return _networkx if _networkx is not False else None


# ── Entity Categories ──────────────────────────────────────────────────

class EntityCategory:
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    COLLEGE = "COLLEGE"
    COMPANY = "COMPANY"
    TECHNOLOGY = "TECHNOLOGY"
    FRAMEWORK = "FRAMEWORK"
    LIBRARY = "LIBRARY"
    PROGRAMMING_LANGUAGE = "PROGRAMMING_LANGUAGE"
    RESEARCH_METHOD = "RESEARCH_METHOD"
    MODEL = "MODEL"
    DATASET = "DATASET"
    ALGORITHM = "ALGORITHM"
    SKILL = "SKILL"
    PROJECT = "PROJECT"
    COURSE = "COURSE"
    CERTIFICATION = "CERTIFICATION"
    FORMULA = "FORMULA"
    TOPIC = "TOPIC"


# ── Knowledge Bases (fully local) ─────────────────────────────────────

TECHNOLOGIES: Set[str] = {
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
    'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql',
    'html', 'css', 'scss', 'sass', 'less', 'graphql', 'grpc', 'rest',
    'react', 'angular', 'vue', 'svelte', 'next', 'nuxt', 'remix',
    'node', 'express', 'fastapi', 'django', 'flask', 'spring', 'rails',
    'laravel', 'rails', 'sinatra', 'actix', 'axum', 'gin', 'echo',
    'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch', 'sqlite',
    'cassandra', 'dynamodb', 'neo4j', 'influxdb', 'cockroachdb',
    'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'terraform', 'ansible',
    'jenkins', 'github', 'gitlab', 'bitbucket', 'ci/cd', 'devops',
    'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy',
    'opencv', 'nltk', 'spacy', 'huggingface', 'transformers',
    'machine learning', 'deep learning', 'neural network', 'nlp',
    'computer vision', 'reinforcement learning', 'generative ai',
    'llm', 'gpt', 'bert', 'transformer', 'attention', 'diffusion',
    'postgresql', 'mysql', 'mongodb', 'redis', 'docker', 'kubernetes',
    'git', 'linux', 'bash', 'powershell', 'vscode', 'vim',
    'figma', 'sketch', 'adobe', 'photoshop', 'illustrator',
}

ALGORITHMS: Set[str] = {
    'binary search', 'linear search', 'bubble sort', 'merge sort',
    'quick sort', 'heap sort', 'selection sort', 'insertion sort',
    'depth first search', 'breadth first search', 'dijkstra',
    'dynamic programming', 'greedy algorithm', 'backtracking',
    'divide and conquer', 'branch and bound', 'random forest',
    'support vector machine', 'k-nearest neighbors', 'k-means',
    'dbscan', 'hierarchical clustering', 'principal component analysis',
    'neural network', 'convolutional neural network', 'recurrent neural network',
    'long short-term memory', 'gated recurrent unit', 'transformer',
    'attention mechanism', 'self-attention', 'multi-head attention',
    'bagging', 'boosting', 'gradient boosting', 'xgboost', 'lightgbm',
    'naive bayes', 'logistic regression', 'decision tree',
}

DOMAINS: Dict[str, Set[str]] = {
    'computer_science': {
        'algorithm', 'data structure', 'programming', 'software', 'database',
        'network', 'compiler', 'operating system', 'machine learning',
        'artificial intelligence', 'deep learning', 'computer vision',
        'natural language processing', 'software engineering',
        'object oriented', 'functional programming', 'concurrency',
        'parallel computing', 'distributed system', 'cloud computing',
        'cybersecurity', 'cryptography', 'blockchain',
    },
    'mathematics': {
        'algebra', 'calculus', 'geometry', 'trigonometry', 'statistics',
        'probability', 'linear algebra', 'discrete mathematics',
        'number theory', 'combinatorics', 'graph theory', 'topology',
        'differential equation', 'complex analysis', 'real analysis',
        'optimization', 'numerical analysis',
        # Aptitude / competitive exam topics
        'time and work', 'time and distance', 'pipes and cisterns',
        'profit and loss', 'simple interest', 'compound interest',
        'percentage', 'ratio and proportion', 'average',
        'number system', 'problems on trains', 'boat and stream',
        'speed distance time', 'problems on ages', 'area',
        'volume', 'surface area', 'circumference',
        'permutation', 'combination', 'binomial theorem',
        'arithmetic progression', 'geometric progression',
        'probability distribution', 'bayes theorem',
        'hcf', 'lcm', 'factorial',
    },
    'physics': {
        'mechanics', 'thermodynamics', 'electromagnetism', 'optics',
        'quantum mechanics', 'relativity', 'nuclear physics',
        'particle physics', 'astrophysics', 'cosmology', 'fluid dynamics',
        'statistical mechanics', 'electrodynamics',
    },
    'biology': {
        'cell biology', 'genetics', 'evolution', 'ecology', 'anatomy',
        'physiology', 'biochemistry', 'molecular biology', 'neuroscience',
        'immunology', 'microbiology', 'bioinformatics',
    },
    'chemistry': {
        'organic chemistry', 'inorganic chemistry', 'physical chemistry',
        'analytical chemistry', 'biochemistry', 'polymer chemistry',
        'quantum chemistry', 'nuclear chemistry',
    },
    'business': {
        'finance', 'accounting', 'marketing', 'management', 'economics',
        'strategy', 'operations', 'entrepreneurship', 'investment',
        'supply chain', 'human resources', 'project management',
    },
    'medicine': {
        'anatomy', 'physiology', 'pathology', 'pharmacology', 'diagnosis',
        'treatment', 'surgery', 'internal medicine', 'pediatrics',
        'cardiology', 'oncology', 'neurology',
    },
    'engineering': {
        'mechanical engineering', 'electrical engineering', 'civil engineering',
        'chemical engineering', 'aerospace engineering', 'biomedical engineering',
        'structural analysis', 'fluid mechanics', 'thermodynamics',
        'control systems', 'signal processing', 'power systems',
    },
}


# ── Document Intelligence V5 ──────────────────────────────────────────

class DocumentIntelligence:
    """Semantic document understanding engine. Fully local."""

    ENGINE_VERSION = "5.0"

    STOP_WORDS: Set[str] = {
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
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'her', 'our', 'their',
        'as', 'because', 'so', 'up', 'out', 'off',
        'use', 'used', 'using', 'one', 'two', 'first', 'new', 'well',
        'like', 'much', 'even', 'still', 'back', 'made', 'make',
        'many', 'way', 'may', 'part', 'go', 'see', 'come', 'know', 'take',
        'based', 'given', 'find', 'show', 'list', 'explain',
        'set', 'get', 'let', 'run', 'put', 'say', 'try', 'keep',
        'however', 'therefore', 'furthermore', 'moreover', 'nevertheless',
        'hence', 'thus', 'accordingly', 'consequently', 'additionally',
        'means', 'per', 'taken', 'called', 'known',
        'formed', 'said', 'done', 'added', 'removed', 'changed',
        'increased', 'decreased', 'greater', 'smaller', 'equal',
        'starting', 'ending', 'following', 'including', 'excluding',
        'representing', 'containing', 'consisting', 'belonging',
    }

        # Resume section headers — NEVER topics
    RESUME_SECTIONS: Set[str] = {
        'professional summary', 'work experience', 'education', 'skills',
        'projects', 'certifications', 'achievements', 'activities',
        'objective', 'summary', 'profile', 'personal details',
        'technical skills', 'work history', 'employment', 'references',
        'declaration', 'career objective', 'core competencies',
        'professional experience', 'key skills', 'areas of expertise',
        'languages', 'frameworks', 'databases', 'tools', 'platforms',
        'operating systems', 'methodologies', 'email', 'phone',
        'address', 'linkedin', 'github',
        # Certificate metadata — NOT topics
        'completion date', 'credential id', 'credential type', 'issuing organization',
        'date of issue', 'valid until', 'certificate number', 'skills earned',
        'skills gained', 'topics covered', 'competencies',
        # Book metadata — NOT topics
        'third edition', 'second edition', 'first edition', 'fourth edition',
        'preface', 'foreword', 'acknowledgments',
        # Generic structural headings
        'methodology', 'background', 'overview', 'summary', 'abstract',
        'conclusion', 'discussion', 'results', 'references',
        'related work', 'future work', 'basic formula',
    }

    # Structural headings — context-dependent, not standalone topics
    STRUCTURAL_HEADINGS: Set[str] = {
        'introduction', 'background', 'overview', 'summary', 'abstract',
        'conclusion', 'discussion', 'results', 'references', 'related work',
        'future work', 'preface', 'foreword', 'acknowledgments', 'appendix',
        'index', 'glossary', 'bibliography', 'table of contents',
        'prerequisites', 'getting started', 'installation', 'configuration',
        'changelog', 'release notes', 'migration guide',
        'attendees', 'agenda', 'action items', 'decisions',
        'next steps', 'follow up', 'minutes', 'training',
        'exercises', 'solutions', 'problems', 'review questions',
    }

    # Section heading patterns
    SECTION_PATTERNS = re.compile(
        r'^(?:chapter|section|unit|module|part|appendix|figure|table|fig|tab)'
        r'[\s\d\.\:]+',
        re.IGNORECASE,
    )

    # Person names — should not be topics
    PERSON_NAMES: Set[str] = {
        'john', 'jane', 'michael', 'david', 'sarah', 'james',
        'robert', 'william', 'richard', 'thomas', 'daniel', 'mark',
        'paul', 'steven', 'andrew', 'kevin', 'brian', 'george',
        'edward', 'ronald', 'timothy', 'jason', 'jeffrey', 'ryan',
        'jacob', 'gary', 'nicholas', 'eric', 'jonathan', 'stephen',
        'larry', 'justin', 'scott', 'brandon', 'benjamin', 'samuel',
        'raymond', 'gregory', 'frank', 'patrick', 'jack', 'dennis',
        'jerry', 'alexander', 'tyler', 'aaron', 'jose', 'nathan',
        'henry', 'peter', 'adam', 'zachary', 'douglas', 'harold',
        'carl', 'arthur', 'gerald', 'roger', 'keith', 'jeremy',
        'terry', 'lawrence', 'sean', 'christian',
        'bobby', 'ralph', 'roy', 'eugene', 'randy', 'bruce',
        'wayne', 'philip', 'howard', 'albert', 'fred',
        'prova', 'et al',
    }

    ROMAN_RE = re.compile(
        r'^(?=[IVXCLM])(X{0,3})(I{0,3}|IV|VI{0,3}|IX)'
        r'(X{0,3})(I{0,3}|IV|VI{0,3}|IX)'
        r'[.\s:)+\-]?$',
        re.IGNORECASE,
    )

    # ── Document Type Classification ────────────────────────────────────

    DOC_TYPE_CONFIGS = {
        'resume': {
            'headers': [
                'education', 'experience', 'skills', 'projects', 'certifications',
                'achievements', 'activities', 'objective', 'summary', 'profile',
                'work experience', 'technical skills', 'personal details',
                'work history', 'employment', 'references', 'declaration',
                'career objective', 'professional summary', 'core competencies',
            ],
            'patterns': [
                r'\bresume\b', r'\bcurriculum\s*vitae\b', r'\bcv\b',
                r'\blinkedin\b', r'\bgithub\.com\b', r'\bemail\b.*@',
                r'\bphone\b.*\d', r'\b\d+\s*years?\s*(of)?\s*experience\b',
                r'\bsgpa\b', r'\bcgpa\b', r'\bpercentage\b',
            ],
            'anti_patterns': [
                r'\bfunction\s*\(', r'\bconst\s+\w+\s*=', r'\bimport\s+{',
                r'\bclass\s+\w+\s*\{', r'\bdef\s+\w+\s*\(', r'\breturn\s+{',
                r'\bvar\s+\w+\s*=', r'\blet\s+\w+\s*=', r'\b=>\s*{',
                r'\bapi\s*\(', r'\bfetch\s*\(', r'\b\.then\s*\(',
                r'\bcomponent\b', r'\bhook\b', r'\brender\b',
            ],
            'min_headers': 3,
            'weight': 2.0,
        },
        'research_paper': {
            'headers': [
                'abstract', 'introduction', 'methodology', 'methods', 'results',
                'discussion', 'conclusion', 'conclusions', 'literature review',
                'related work', 'future work', 'background', 'findings',
            ],
            'patterns': [
                r'\babstract\b', r'\bdoi\b', r'\bstudy\b', r'\bexperiment\b',
                r'\bhypothesis\b', r'\bfindings\b', r'\bcitations?\b',
                r'\barxiv\b', r'\bproceedings\b',
                r'\bpeer[\s-]?review', r'\bjournal\b',
            ],
            'min_headers': 2,
            'weight': 2.0,
        },
        'book': {
            'headers': [
                'chapter', 'appendix', 'bibliography', 'glossary', 'index',
                'preface', 'foreword', 'acknowledgments', 'table of contents',
            ],
            'patterns': [
                r'\bchapter\s+\d+\b', r'\bappendix\b', r'\bbibliography\b',
                r'\bpreface\b', r'\bforeword\b', r'\bglossary\b',
                r'\bedition\b', r'\bpublisher\b', r'\bisbn\b',
            ],
            'min_headers': 3,
            'weight': 1.8,
        },
        'documentation': {
            'headers': [
                'getting started', 'installation', 'configuration', 'api reference',
                'usage', 'examples', 'parameters', 'return value',
                'prerequisites', 'requirements', 'troubleshooting', 'faq',
                'changelog', 'release notes', 'migration guide',
            ],
            'patterns': [
                r'\bapi\s+reference\b', r'\bdocumentation\b',
                r'\bgetting\s+started\b', r'\binstallation\b',
                r'\bparameters?\b', r'\breturn\s+value\b',
                r'\bversion\b.*\d+\.\d+', r'\brelease\s+notes?\b',
            ],
            'min_headers': 2,
            'weight': 1.8,
        },
        'study_material': {
            'headers': [
                'exercises', 'problems', 'solutions', 'formulas',
                'theorems', 'definitions', 'worked examples', 'practice',
                'review questions', 'objective questions', 'numericals',
            ],
            'patterns': [
                r'\bexercise\b', r'\bproblem\b.*\bsolution\b',
                r'\bformula\b', r'\btheorem\b', r'\bdefinition\b',
                r'\bcompetitive\s+exam\b', r'\baptitude\b',
                r'\bshortcut\b', r'\bplacement\b', r'\binterview\s+prep\b',
            ],
            'min_headers': 1,
            'weight': 1.5,
        },
        'certificate': {
            'headers': [
                'certificate', 'certification', 'completion', 'awarded',
                'credential', 'professional development', 'training',
                'this certifies', 'has successfully completed',
            ],
            'patterns': [
                r'\bcertificate\b', r'\bcertification\b', r'\bcredential\b',
                r'\bhas\s+successfully\s+completed\b', r'\bthis\s+certifies\b',
                r'\bawarded\s+to\b', r'\bcompletion\s+date\b',
                r'\bvalid\s+until\b', r'\bcredential\s+id\b',
            ],
            'min_headers': 1,
            'weight': 2.5,
        },
        'tutorial': {
            'headers': [
                'tutorial', 'guide', 'step by step', 'quickstart',
                'prerequisites', 'setup', 'hello world', 'first app',
            ],
            'patterns': [
                r'\btutorial\b', r'\bhow\s+to\b', r'\bstep\s+by\s+step\b',
                r'\blet\'s\s+build\b', r'\bbeginners?\b',
            ],
            'min_headers': 1,
            'weight': 1.5,
        },
        'lecture_notes': {
            'headers': [
                'lecture', 'class notes', 'key points', 'takeaways',
                'topics covered', 'syllabus',
            ],
            'patterns': [
                r'\blecture\s+notes?\b', r'\bclass\s+notes?\b',
                r'\bkey\s+points?\b', r'\bprofessor\b',
                r'\bsemester\b', r'\bquiz\b', r'\bassignment\b',
            ],
            'min_headers': 1,
            'weight': 1.3,
        },
        'cheat_sheet': {
            'headers': [
                'cheat sheet', 'cheatsheet', 'quick reference', 'reference card',
                'syntax', 'commands', 'shortcuts', 'quick guide',
            ],
            'patterns': [
                r'\bcheat\s*sheet\b', r'\bquick\s+reference\b',
                r'\bsyntax\b.*\bexample\b', r'\bcommands?\b.*\blist\b',
            ],
            'min_headers': 1,
            'weight': 2.8,
        },
    }

    # ── Stage 0: OCR Cleanup ────────────────────────────────────────────

    @classmethod
    def _cleanup_ocr(cls, text: str) -> str:
        if not text:
            return ""

        lines = text.split('\n')
        cleaned: List[str] = []
        seen_lines: Set[str] = set()

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if cleaned and cleaned[-1] != '':
                    cleaned.append('')
                continue

            if re.match(r'^[\d\s\.\,\-\/]+$', stripped):
                continue
            if len(stripped) <= 2 and not stripped.isalpha():
                continue
            if re.match(r'^[\s\-\=\*\#\_\~\`\@\$\%\^\&\(\)\[\]\{\}\<\>\/\\\|]+$', stripped):
                continue
            if stripped.lower() in {s.lower() for s in seen_lines}:
                continue
            if re.match(r'^(?:confidential|copyright|all rights|terms|privacy|disclaimer)', stripped.lower()):
                continue
            if re.match(r'^https?://', stripped.lower()):
                continue
            if re.match(r'^[\w\.\-]+@[\w\.\-]+\.\w+$', stripped):
                continue

            stripped = re.sub(r'\s{2,}', ' ', stripped)
            cleaned.append(stripped)
            if len(seen_lines) < 2000:
                seen_lines.add(stripped)

        result = []
        prev_blank = False
        for line in cleaned:
            if line == '':
                if not prev_blank:
                    result.append(line)
                prev_blank = True
            else:
                result.append(line)
                prev_blank = False

        return '\n'.join(result).strip()

    # ── Stage 1: Document Type Classification ───────────────────────────

    @classmethod
    def _classify_document_type(cls, text_lower: str, filename: str) -> Tuple[str, float]:
        title_lower = filename.lower().replace('_', ' ').replace('-', ' ')

        scores: Dict[str, float] = {}
        for dtype, config in cls.DOC_TYPE_CONFIGS.items():
            score = 0.0
            headers_found = 0

            for header in config['headers']:
                if re.search(r'\b' + re.escape(header) + r'\b', text_lower):
                    headers_found += 1
                    score += 2
                if re.search(r'\b' + re.escape(header) + r'\b', title_lower):
                    score += 4

            if config.get('min_headers', 0) > 0 and headers_found < config['min_headers']:
                score *= 0.2

            for pattern in config['patterns']:
                if re.search(pattern, text_lower):
                    score += 1.5
                if re.search(pattern, title_lower):
                    score += 3

            anti_patterns = config.get('anti_patterns', [])
            if anti_patterns:
                anti_hits = sum(1 for ap in anti_patterns if re.search(ap, text_lower))
                if anti_hits >= 3:
                    score *= 0.1
                elif anti_hits >= 2:
                    score *= 0.3
                elif anti_hits >= 1:
                    score *= 0.6

            scores[dtype] = score * config['weight']

        if not scores:
            return ('general', 0.0)

        best = max(scores, key=scores.get)
        if scores[best] < 2:
            return ('general', 0.0)

        confidence = cls._calculate_classification_confidence(scores, best, text_lower)
        return (best, confidence)

    @classmethod
    def _calculate_classification_confidence(cls, scores, best_type, text_lower):
        if not scores or best_type not in scores:
            return 0.0
        best_score = scores[best_type]
        sorted_scores = sorted(scores.values(), reverse=True)
        second_best = sorted_scores[1] if len(sorted_scores) > 1 else 0

        margin_ratio = (best_score - second_best) / max(best_score, 0.01)
        margin_score = min(0.4, margin_ratio * 0.4)
        magnitude_score = min(0.3, (best_score / 15) * 0.3)

        word_count = len(text_lower.split())
        if word_count > 1000:
            length_score = 0.2
        elif word_count > 500:
            length_score = 0.15
        elif word_count > 200:
            length_score = 0.1
        elif word_count > 50:
            length_score = 0.05
        else:
            length_score = 0.0

        config = cls.DOC_TYPE_CONFIGS.get(best_type, {})
        patterns_matched = sum(1 for p in config.get('patterns', []) if re.search(p, text_lower))
        diversity_score = min(0.1, (patterns_matched / 5) * 0.1)

        total = margin_score + magnitude_score + length_score + diversity_score
        return max(0.0, min(1.0, round(total, 2)))

    # ── Stage 2: Named Entity Recognition ───────────────────────────────

    @classmethod
    def _extract_entities(cls, text: str, text_lower: str, doc_type: str) -> Dict[str, List[str]]:
        """
        Classify every extracted phrase into entity categories.
        Returns dict of category → list of entity names.
        """
        entities: Dict[str, List[str]] = {cat: [] for cat in [
            EntityCategory.TECHNOLOGY, EntityCategory.FRAMEWORK,
            EntityCategory.LIBRARY, EntityCategory.PROGRAMMING_LANGUAGE,
            EntityCategory.ALGORITHM, EntityCategory.MODEL,
            EntityCategory.ORGANIZATION, EntityCategory.COMPANY,
            EntityCategory.COLLEGE, EntityCategory.CERTIFICATION,
            EntityCategory.SKILL, EntityCategory.PROJECT,
        ]}

        # Extract technologies present in text
        for tech in TECHNOLOGIES:
            if tech in text_lower:
                if tech in {'python', 'java', 'javascript', 'typescript', 'c++', 'c#',
                           'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala',
                           'r', 'matlab', 'sql', 'html', 'css'}:
                    if tech.title() not in entities[EntityCategory.PROGRAMMING_LANGUAGE]:
                        entities[EntityCategory.PROGRAMMING_LANGUAGE].append(tech.title())
                elif tech in {'react', 'angular', 'vue', 'svelte', 'next', 'nuxt',
                             'node', 'express', 'fastapi', 'django', 'flask', 'spring',
                             'rails', 'laravel'}:
                    if tech.title() not in entities[EntityCategory.FRAMEWORK]:
                        entities[EntityCategory.FRAMEWORK].append(tech.title())
                elif tech in {'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'pandas',
                             'numpy', 'opencv', 'nltk', 'spacy', 'huggingface', 'transformers'}:
                    if tech.title() not in entities[EntityCategory.LIBRARY]:
                        entities[EntityCategory.LIBRARY].append(tech.title())
                else:
                    if tech.title() not in entities[EntityCategory.TECHNOLOGY]:
                        entities[EntityCategory.TECHNOLOGY].append(tech.title())

        # Extract algorithms
        for algo in ALGORITHMS:
            if algo in text_lower:
                name = algo.title()
                if name not in entities[EntityCategory.ALGORITHM]:
                    entities[EntityCategory.ALGORITHM].append(name)

        # Extract organizations / companies
        org_patterns = [
            r'\b(?:at|from|by|@\s*)([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b',
            r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+(?:Inc|Corp|LLC|Ltd|University|Institute|Academy|Foundation|Laboratories)\b',
        ]
        for pattern in org_patterns:
            for match in re.finditer(pattern, text):
                org = match.group(1).strip()
                if 2 <= len(org.split()) <= 4 and len(org) > 3:
                    if org.lower() not in cls.PERSON_NAMES and org.lower() not in cls.STOP_WORDS:
                        if org not in entities[EntityCategory.ORGANIZATION]:
                            entities[EntityCategory.ORGANIZATION].append(org)

        # Extract college/university
        college_patterns = [
            r'([A-Z][a-zA-Z\s]+(?:University|College|Institute|School|Academy))',
        ]
        for pattern in college_patterns:
            for match in re.finditer(pattern, text):
                college = match.group(1).strip()
                if 3 < len(college) < 80:
                    if college not in entities[EntityCategory.COLLEGE]:
                        entities[EntityCategory.COLLEGE].append(college)

        # Extract certifications
        cert_patterns = [
            r'(?:AWS|Google Cloud|Azure|Cisco|Oracle|Red Hat|IBM|Salesforce)\s+(?:Certified?\s+)?(\w[\w\s]{5,40})',
            r'(\w[\w\s]{5,40})\s+(?:Certification|Certificate|Certified)',
        ]
        for pattern in cert_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                cert = match.group(0).strip()
                if 5 < len(cert) < 60:
                    if cert not in entities[EntityCategory.CERTIFICATION]:
                        entities[EntityCategory.CERTIFICATION].append(cert)

        return entities

    # ── Stage 3: Concept Extraction (Semantic) ──────────────────────────

    @classmethod
    def _extract_concepts_semantic(cls, text: str, text_lower: str, doc_type: str) -> List[str]:
        """
        Extract concepts using semantic embeddings + domain knowledge.
        Returns highest-level ideas only (not individual question titles).
        """
        # Phase 1: Extract candidate phrases
        candidates: Set[str] = set()

        # Source: bold/emphasized terms
        for match in re.finditer(r'\*\*(.+?)\*\*|__(.+?)__', text):
            term = (match.group(1) or match.group(2)).strip()
            if 2 < len(term) < 60:
                candidates.add(term)

        # Source: definition patterns ("Term: ...", "Term is a/an ...")
        for line in text.split('\n'):
            stripped = line.strip()
            if not stripped or len(stripped) > 120:
                continue
            m = re.match(r'^([A-Z][A-Za-z\s\-]{2,50}):\s+\w', stripped)
            if m:
                term = m.group(1).strip()
                if 2 <= len(term.split()) <= 5:
                    candidates.add(term)
            m = re.match(r'^([A-Z][A-Za-z\s\-]{2,50})\s+(?:is|are|refers)\s+(?:a|an|the)\b', stripped)
            if m:
                term = m.group(1).strip()
                if 2 <= len(term.split()) <= 5:
                    candidates.add(term)

        # Source: section headings (filtered)
        headings = cls._extract_section_headings(text)
        for h in headings:
            h_lower = h.lower()
            if h_lower not in cls.STRUCTURAL_HEADINGS and h_lower not in cls.RESUME_SECTIONS:
                candidates.add(h)

        # Source: domain concepts from knowledge base
        for domain_name, domain_concepts in DOMAINS.items():
            for concept in domain_concepts:
                if concept in text_lower:
                    candidates.add(concept.title())

        # Source: algorithm names
        for algo in ALGORITHMS:
            if algo in text_lower:
                candidates.add(algo.title())

        # Source: technology names
        for tech in TECHNOLOGIES:
            if tech in text_lower:
                candidates.add(tech.title())

        # Phase 2: Filter candidates
        filtered: List[str] = []
        for candidate in candidates:
            if cls._is_valid_concept_v5(candidate, text_lower, doc_type):
                filtered.append(candidate)

        if not filtered:
            return []

        # Phase 3: Semantic deduplication using embeddings
        model = _get_sentence_model()
        if model and len(filtered) > 1:
            try:
                embeddings = model.encode(filtered, show_progress_bar=False)
                # Cluster similar concepts
                from sklearn.cluster import AgglomerativeClustering
                import numpy as np

                # Compute similarity matrix
                from sklearn.metrics.pairwise import cosine_similarity
                sim_matrix = cosine_similarity(embeddings)
                distance_matrix = 1 - sim_matrix
                np.fill_diagonal(distance_matrix, 0)

                # Cluster with distance threshold
                n_clusters = max(1, len(filtered) // 3)
                if n_clusters > 1 and len(filtered) > 3:
                    clustering = AgglomerativeClustering(
                        n_clusters=n_clusters,
                        metric='precomputed',
                        linkage='average',
                    )
                    labels = clustering.fit_predict(distance_matrix)

                    # Keep the highest-scored concept from each cluster
                    cluster_map: Dict[int, List[int]] = {}
                    for i, label in enumerate(labels):
                        if label not in cluster_map:
                            cluster_map[label] = []
                        cluster_map[label].append(i)

                    deduplicated: List[str] = []
                    for label, indices in cluster_map.items():
                        # Pick the concept with highest TF as representative
                        best_idx = max(indices, key=lambda i: text_lower.count(filtered[i].lower()))
                        deduplicated.append(filtered[best_idx])
                    filtered = deduplicated
            except Exception as e:
                logger.warning(f"Semantic dedup failed: {e}")
                # Fallback: simple dedup
                seen: Set[str] = set()
                deduplicated = []
                for c in filtered:
                    key = c.lower().strip()
                    if key not in seen:
                        seen.add(key)
                        deduplicated.append(c)
                filtered = deduplicated

        # Phase 4: Rank by semantic importance
        ranked = cls._rank_concepts(filtered, text_lower, doc_type)

        return ranked[:12]

    @classmethod
    def _is_valid_concept_v5(cls, term: str, text_lower: str, doc_type: str) -> bool:
        """Validate concept quality for V5 engine."""
        t = term.lower().strip()

        # Length
        if len(t) < 3 or len(t) > 60:
            return False

        # Pure noise
        if t in cls.STRUCTURAL_HEADINGS:
            return False

        # Resume section headers and metadata
        if t in cls.RESUME_SECTIONS:
            return False

        # Section patterns
        if cls.SECTION_PATTERNS.match(t):
            return False

        # Question numbers / exercise numbers
        if re.match(r'^(?:q\.?\s*\d|model\s*:?\s*\d|sol\.?\s|ans\.?\s|hint|exercise\s*\d)', t):
            return False

        # Roman numerals
        if cls.ROMAN_RE.match(t.rstrip('.:+-) ')):
            return False

        # Pure numbers
        if re.match(r'^[\d\s\.\-\/qQ]+$', t):
            return False

        # Formulas
        if re.search(r'[=+\-*/^√∫∑∏\\]|\\frac|\\sqrt', t):
            return False

        # URL / email
        if re.search(r'(?:http|www|\.com|\.org|@)', t):
            return False

        # ALL CAPS (section heading)
        if re.match(r'^[A-Z\s]+$', term.strip()):
            return False

        # Person name pattern (except known technical terms)
        if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', term.strip()):
            if t.split()[0] in cls.PERSON_NAMES:
                return False

        # Resume labels with colon ("Languages: ...")
        if ':' in t:
            label = t.split(':')[0].strip()
            if label in cls.RESUME_SECTIONS:
                return False

        # Starts with articles
        if t.startswith('the ') or t.startswith('a ') or t.startswith('an '):
            return False

        # Sentence fragments — contains common verbs in middle positions
        FRAGMENT_VERBS = {'is', 'are', 'was', 'were', 'have', 'has', 'had',
                         'means', 'refers', 'into', 'from', 'with', 'using'}
        words = t.split()
        if len(words) >= 3:
            if any(w in FRAGMENT_VERBS for w in words[1:-1]):
                return False

        # Ends with preposition
        if words and words[-1] in {'by', 'in', 'at', 'with', 'of', 'to', 'for', 'on', 'from', 'than', 'is', 'are', 'was'}:
            return False

        # Starts with common verbs (bullet points / instruction fragments)
        BULLET_VERBS = {
            'designed', 'built', 'reduced', 'created', 'developed', 'implemented',
            'managed', 'led', 'contributed', 'established', 'optimized', 'improved',
            'increased', 'decreased', 'launched', 'delivered', 'maintained',
            'combine', 'divide', 'conquer', 'solve', 'implement', 'build',
            'create', 'design', 'write', 'develop', 'use', 'apply',
            'find', 'show', 'list', 'explain', 'describe', 'compare',
            'given', 'suppose', 'consider', 'assume', 'let',
        }
        if words and words[0].lower() in BULLET_VERBS:
            return False

        # Changelog entries
        if re.match(r'^(?:added|removed|updated|fixed|changed|improved|deprecated)\s+\w+', t):
            return False

        # "N words" patterns that are just phrases from text, not concepts
        if len(words) >= 4:
            # Check if most words are common/stop words
            common_count = sum(1 for w in words if w in cls.STOP_WORDS or len(w) <= 3)
            if common_count / len(words) > 0.5:
                return False
            # Check if it looks like a sentence (has articles, prepositions in middle)
            if any(w in {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'} for w in words[1:-1]):
                return False

        # Trailing colon (definition fragment)
        if t.endswith(':'):
            return False

        # Generic single words
        if ' ' not in t and len(t) < 10:
            GENERIC = {
                'model', 'network', 'data', 'system', 'code', 'input',
                'output', 'class', 'method', 'function', 'string', 'array',
                'item', 'name', 'number', 'value', 'list', 'tree',
                'graph', 'hash', 'stack', 'queue', 'heap', 'node', 'key',
                'design', 'language', 'based', 'stored', 'types', 'child',
                'find', 'natural', 'prime', 'thrown', 'limits', 'mode',
                'scale', 'index', 'bias', 'scope', 'range', 'field',
                'form', 'set', 'work', 'days', 'takes', 'together',
                'efficiency', 'same', 'done', 'fraction', 'software',
                'optimization', 'problem', 'solution', 'approach',
            }
            if t in GENERIC:
                return False

        return True

    @classmethod
    def _rank_concepts(cls, concepts: List[str], text_lower: str, doc_type: str) -> List[str]:
        """Rank concepts by multi-signal scoring."""
        total_words = len(text_lower.split())
        sections = text_lower.split('\n\n')

        scored: List[Tuple[str, float]] = []
        for concept in concepts:
            t_lower = concept.lower()
            words = t_lower.split()

            score = 0.0

            # 1. Multi-word phrases are better
            if len(words) >= 3:
                score += 0.3
            elif len(words) >= 2:
                score += 0.2

            # 2. Frequency (TF-IDF approximation)
            tf = text_lower.count(t_lower) / max(total_words, 1)
            doc_freq = sum(1 for s in sections if t_lower in s)
            idf = math.log(max(len(sections), 1) / max(doc_freq, 1))
            score += min(0.3, tf * idf * 10)

            # 3. Title presence
            title_line = cls._get_title_line(text_lower)
            if title_line and t_lower in title_line:
                score += 0.2

            # 4. Is a known technical term
            if any(w in TECHNOLOGIES for w in words):
                score += 0.15
            if any(w in ALGORITHMS for w in words):
                score += 0.15
            if t_lower in {c.lower() for c in DOMAINS.get('computer_science', set())}:
                score += 0.1

            # 5. Heading presence
            headings = cls._extract_section_headings(text_lower)
            headings_lower = {h.lower() for h in headings}
            if t_lower in headings_lower:
                score += 0.1

            scored.append((concept, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in scored]

    # ── Stage 4: Topic Clustering (Concept Graph) ──────────────────────

    @classmethod
    def _build_concept_graph(cls, concepts: List[str], text_lower: str) -> Dict[str, List[str]]:
        """
        Build a parent→child concept graph.
        Only parent concepts become Topics.
        Child nodes become Key Concepts.
        This prevents question titles becoming topics.
        """
        nx = _get_networkx()
        if not nx or len(concepts) < 2:
            # Fallback: return flat structure
            return {c: [] for c in concepts}

        G = nx.Graph()

        # Add all concepts as nodes
        for concept in concepts:
            G.add_node(concept)

        # Connect concepts that share significant word overlap
        for i, c1 in enumerate(concepts):
            words1 = set(c1.lower().split())
            for c2 in concepts[i+1:]:
                words2 = set(c2.lower().split())
                # Jaccard-like overlap
                intersection = len(words1 & words2)
                union = len(words1 | words2)
                if union > 0 and intersection / union >= 0.3:
                    G.add_edge(c1, c2, weight=intersection / union)

        # Also connect parent-child by substring containment
        for c1 in concepts:
            for c2 in concepts:
                if c1 != c2:
                    c1_lower = c1.lower()
                    c2_lower = c2.lower()
                    # c1 is a substring of c2 → c2 is parent
                    if c1_lower in c2_lower and len(c1_lower) < len(c2_lower):
                        G.add_edge(c1, c2, weight=0.8)
                    elif c2_lower in c1_lower and len(c2_lower) < len(c1_lower):
                        G.add_edge(c1, c2, weight=0.8)

        # Identify parent concepts (high degree = parent)
        result: Dict[str, List[str]] = {}
        for node in G.nodes():
            neighbors = list(G.neighbors(node))
            if len(neighbors) == 0:
                result[node] = []
            else:
                # This node is a parent — its neighbors are children
                children = []
                for n in neighbors:
                    # Only include children that are substrings or have lower degree
                    if G.degree(n) <= G.degree(node):
                        children.append(n)
                result[node] = children

        # Remove nodes that are children of other nodes (to avoid duplicates)
        all_children: Set[str] = set()
        for children in result.values():
            all_children.update(children)

        final = {}
        for parent, children in result.items():
            if parent not in all_children:
                final[parent] = [c for c in children if c in result]

        return final if final else {c: [] for c in concepts}

    # ── Stage 5: Topic Ranking ─────────────────────────────────────────

    @classmethod
    def _rank_topics(
        cls,
        concept_graph: Dict[str, List[str]],
        text_lower: str,
        doc_type: str,
        entities: Dict[str, List[str]],
    ) -> Tuple[List[str], List[str], Dict[str, float]]:
        """
        Rank topics and concepts by semantic importance.
        Returns (topics, key_concepts, confidence_scores).

        Max topics by doc type:
          resume → 8
          research_paper → 10
          study_material → 12
          documentation → 10
          book → 10
          general → 8
        """
        TYPE_MAX_TOPICS = {
            'resume': 8,
            'research_paper': 10,
            'study_material': 12,
            'documentation': 10,
            'book': 10,
            'certificate': 6,
            'cheat_sheet': 8,
            'tutorial': 8,
            'lecture_notes': 8,
            'general': 8,
        }
        max_topics = TYPE_MAX_TOPICS.get(doc_type, 8)

        total_words = len(text_lower.split())
        sections = text_lower.split('\n\n')
        headings = cls._extract_section_headings(text_lower)
        headings_lower = {h.lower() for h in headings}
        title_line = cls._get_title_line(text_lower)

        scored_items: List[Tuple[str, float, bool]] = []  # (name, score, is_parent)

        for parent, children in concept_graph.items():
            p_lower = parent.lower()

            # Multi-signal scoring
            score = 0.0

            # 1. Semantic Importance (0.3)
            # Parent concepts are inherently more important
            if children:
                score += 0.3
            else:
                score += 0.15

            # 2. Concept Centrality — how many children/connections
            centrality = len(children) * 0.05
            score += min(0.15, centrality)

            # 3. Frequency (TF-IDF approximation) (0.2)
            tf = text_lower.count(p_lower) / max(total_words, 1)
            doc_freq = sum(1 for s in sections if p_lower in s)
            idf = math.log(max(len(sections), 1) / max(doc_freq, 1))
            score += min(0.2, tf * idf * 10)

            # 4. Heading Weight (0.15)
            if p_lower in headings_lower:
                score += 0.15
            for h in headings_lower:
                if p_lower in h or h in p_lower:
                    score += 0.1
                    break

            # 5. Domain Weight (0.1)
            for domain_name, domain_concepts in DOMAINS.items():
                if p_lower in domain_concepts:
                    score += 0.1
                    break

            # 6. Graph Degree (0.1)
            degree = len(children)
            score += min(0.1, degree * 0.03)

            # 7. Type-specific entity boost
            if doc_type == 'resume':
                # Boost technologies and skills for resumes
                all_tech = set()
                for cat in [EntityCategory.TECHNOLOGY, EntityCategory.FRAMEWORK,
                           EntityCategory.LIBRARY, EntityCategory.PROGRAMMING_LANGUAGE]:
                    all_tech.update(e.lower() for e in entities.get(cat, []))
                if p_lower in all_tech:
                    score += 0.2

            elif doc_type == 'research_paper':
                # Boost algorithms and methods for research papers
                all_research = set()
                for cat in [EntityCategory.ALGORITHM, EntityCategory.MODEL,
                           EntityCategory.DATASET]:
                    all_research.update(e.lower() for e in entities.get(cat, []))
                if p_lower in all_research:
                    score += 0.2

            scored_items.append((parent, score, bool(children)))

        # Sort by score
        scored_items.sort(key=lambda x: x[1], reverse=True)

        # Extract topics (parents) and concepts (all)
        topics: List[str] = []
        all_concepts: List[str] = []
        confidence_scores: Dict[str, float] = {}

        if scored_items:
            max_score = scored_items[0][1] if scored_items[0][1] > 0 else 1.0
        else:
            max_score = 1.0

        for name, score, is_parent in scored_items:
            confidence = min(1.0, score / max(max_score, 0.01))
            confidence_scores[name] = round(confidence, 2)
            all_concepts.append(name)

            if is_parent and len(topics) < max_topics:
                topics.append(name)

        # If we have too few topics, add non-parent concepts
        if len(topics) < 3:
            for name, score, is_parent in scored_items:
                if name not in topics and len(topics) < max_topics:
                    topics.append(name)

        return topics, all_concepts, confidence_scores

    # ── Stage 6: Summary Generation (Document-Aware) ────────────────────

    @classmethod
    def _generate_overview(cls, text: str, text_lower: str, doc_type: str,
                           topics: List[str], concepts: List[str], filename: str) -> str:
        """
        Generate type-aware summary. Max 80 words. Never reuses document text.
        Answers: "What is this document about?"
        """
        if doc_type == 'resume':
            return cls._overview_resume(text, text_lower, topics, concepts)
        elif doc_type == 'research_paper':
            return cls._overview_paper(text, text_lower, topics, concepts)
        elif doc_type == 'study_material':
            return cls._overview_study(text, text_lower, topics, concepts)
        elif doc_type == 'documentation':
            return cls._overview_docs(text, text_lower, topics, concepts)
        elif doc_type == 'book':
            return cls._overview_book(text, text_lower, topics, concepts)
        elif doc_type == 'certificate':
            return cls._overview_certificate(text, text_lower, topics, concepts)
        else:
            return cls._overview_generic(text, text_lower, doc_type, topics, concepts)

    @classmethod
    def _overview_resume(cls, text, text_lower, topics, concepts):
        """Who is this person? What skills? What projects?"""
        # Extract name
        name = ""
        for line in text.strip().split('\n')[:5]:
            stripped = line.strip()
            if 2 < len(stripped) < 40:
                words = stripped.split()
                if words and all(w[0].isupper() for w in words if w and w[0].isalpha()):
                    if not any(c in stripped for c in '@.comhttp'):
                        name = stripped
                        break

        # Extract skills from concepts (exclude section labels)
        skills = [c for c in concepts if c.lower() not in cls.RESUME_SECTIONS]
        skill_str = f" with expertise in {', '.join(skills[:5])}" if skills else ""

        has_projects = bool(re.search(r'\bproject\b|\bbuilt\b|\bdesigned\b', text_lower))
        has_experience = bool(re.search(r'\d+\s*years?\s*(of)?\s*experience', text_lower))

        name_str = f" for {name}" if name else ""
        proj_str = " and notable project contributions" if has_projects else ""
        exp_str = " with industry experience" if has_experience else ""

        sentences = [
            f"This is a professional resume{name_str}{skill_str}{exp_str}{proj_str}.",
            f"The candidate demonstrates technical proficiency{' and practical project experience' if has_projects else ''}.",
        ]
        return ' '.join(sentences)[:400]

    @classmethod
    def _overview_paper(cls, text, text_lower, topics, concepts):
        """What problem? What method? Main contribution? Results?"""
        topic_str = ', '.join(topics[:3]) if topics else 'its research area'

        has_method = bool(re.search(r'\bmethodology\b|\bmethod\b|\bapproach\b|\bproposed\b', text_lower))
        has_results = bool(re.search(r'\bresult\b|\bfinding\b|\bperformance\b|\baccuracy\b', text_lower))
        has_dataset = bool(re.search(r'\bdataset\b|\bcorpus\b|\bbenchmark\b', text_lower))

        sentences = [
            f"This research paper investigates {topic_str}.",
        ]
        if has_method:
            sentences.append("It proposes a novel methodology with empirical evaluation.")
        if has_results:
            sentences.append("Results demonstrate measurable improvements over existing approaches.")
        if has_dataset:
            sentences.append("Evaluation is conducted on standard benchmarks.")
        if len(sentences) < 3:
            sentences.append("The work contributes to the existing body of knowledge in the field.")

        return ' '.join(sentences)[:400]

    @classmethod
    def _overview_study(cls, text, text_lower, topics, concepts):
        """Subject? Difficulty? Concepts? Audience?"""
        topic_str = ', '.join(topics[:4]) if topics else 'core concepts'

        has_formulas = bool(re.search(r'formula|equation|theorem', text_lower))
        has_exercises = bool(re.search(r'\bexercise\b|\bproblem\b|\bpractice\b', text_lower))
        has_examples = bool(re.search(r'\bexample\b|\bsolved\b|\bworked\b', text_lower))

        features = []
        if has_formulas:
            features.append('mathematical formulas')
        if has_examples:
            features.append('worked examples')
        if has_exercises:
            features.append('practice exercises')
        feature_str = f" It includes {', '.join(features)}." if features else ""

        word_count = len(text_lower.split())
        depth = 'comprehensive' if word_count > 5000 else 'thorough' if word_count > 2000 else 'focused'

        sentences = [
            f"This is a {depth} study guide covering {topic_str}.{feature_str}",
            f"Designed for students preparing for competitive examinations and technical placements.",
        ]
        return ' '.join(sentences)[:400]

    @classmethod
    def _overview_docs(cls, text, text_lower, topics, concepts):
        """Purpose? Architecture? Technologies?"""
        topic_str = ', '.join(topics[:3]) if topics else 'this software'

        has_api = bool(re.search(r'\bapi\b|\bendpoint\b|\brequest\b', text_lower))
        has_install = bool(re.search(r'\binstall\b|\bsetup\b', text_lower))

        sentences = [
            f"This is technical documentation for {topic_str}.",
        ]
        if has_api:
            sentences.append("It includes API references and usage examples.")
        if has_install:
            sentences.append("Installation and configuration guides are provided.")
        if len(sentences) < 3:
            sentences.append("The documentation covers setup, usage, and troubleshooting.")

        return ' '.join(sentences)[:400]

    @classmethod
    def _overview_book(cls, text, text_lower, topics, concepts):
        """Genre? Themes? Learning outcome?"""
        topic_str = ', '.join(topics[:3]) if topics else 'its subject area'
        word_count = len(text_lower.split())

        has_exercises = bool(re.search(r'\bexercise\b|\bproblem\b', text_lower))
        exercise_str = " Includes exercises for reinforcement." if has_exercises else ""

        sentences = [
            f"This book covers {topic_str}.{exercise_str}",
            f"Spanning approximately {word_count:,} words, it provides {'in-depth' if word_count > 20000 else 'detailed'} coverage.",
        ]
        return ' '.join(sentences)[:400]

    @classmethod
    def _overview_certificate(cls, text, text_lower, topics, concepts):
        """Certificate provider? Skills earned? Completion?"""
        org_match = re.search(
            r'(?:issued\s+by|presented\s+by|organization)[:\s]*(.{5,60}?)(?:\.|,|\n|$)',
            text_lower
        )
        org = org_match.group(1).strip().title() if org_match else ""

        skill_str = f" covering {', '.join(topics[:3])}" if topics else ""

        sentences = [
            f"This is a professional certificate{skill_str}.",
        ]
        if org:
            sentences.append(f"Issued by {org}.")
        sentences.append("It validates completion and acquired competencies.")

        return ' '.join(sentences)[:400]

    @classmethod
    def _overview_generic(cls, text, text_lower, doc_type, topics, concepts):
        type_label = doc_type.replace('_', ' ')
        topic_str = ', '.join(topics[:4]) if topics else 'its subject matter'

        sentences = [
            f"This is a {type_label} covering {topic_str}.",
            f"The material is designed for readers seeking information on this subject.",
        ]
        return ' '.join(sentences)[:400]

    # ── Stage 7: Keyword Extraction ─────────────────────────────────────

    @classmethod
    def _extract_keywords(cls, text_lower: str, doc_type: str) -> List[str]:
        """Extract 10-15 meaningful, searchable keywords."""
        # Combine domain keywords + extracted terms
        domain = cls._detect_domain(text_lower)

        domain_kws: List[str] = []
        for domain_name, concepts in DOMAINS.items():
            for concept in concepts:
                if concept in text_lower:
                    domain_kws.append(concept.title())

        # TF-based keywords
        text_clean = re.sub(r'\d+', ' ', text_lower)
        text_clean = re.sub(r'[^\w\s]', ' ', text_clean)
        words = text_clean.split()
        meaningful = [
            w for w in words
            if len(w) > 2
            and w not in cls.STOP_WORDS
            and not w.isdigit()
        ]

        if not meaningful:
            return domain_kws[:15]

        freq = Counter(meaningful)

        # Bigrams and trigrams
        all_candidates: Dict[str, float] = {}
        for window in [2, 3]:
            for i in range(len(words) - window + 1):
                gram = words[i:i + window]
                if all(len(w) > 2 and w not in cls.STOP_WORDS for w in gram):
                    phrase = ' '.join(gram)
                    score = sum(freq.get(w, 0) for w in gram)
                    unique = len(set(w for w in gram if w not in cls.STOP_WORDS))
                    if unique >= 2:
                        score *= 1.5
                    all_candidates[phrase] = max(all_candidates.get(phrase, 0), score)

        sorted_kw = sorted(all_candidates.items(), key=lambda x: x[1], reverse=True)

        keywords: List[str] = list(domain_kws)
        seen_words: Set[str] = set(w.lower() for w in domain_kws)
        for dk in domain_kws:
            for w in dk.lower().split():
                seen_words.add(w)

        for kw, score in sorted_kw:
            if len(keywords) >= 15:
                break
            kw_lower = kw.lower().strip()
            if kw_lower in seen_words:
                continue
            if any(kw_lower in existing.lower() or existing.lower() in kw_lower for existing in keywords):
                continue
            display_kw = kw.title()
            keywords.append(display_kw)
            seen_words.add(kw_lower)
            for w in kw.split():
                seen_words.add(w)

        return keywords[:15]

    # ── Stage 8: Type-Specific Sections ─────────────────────────────────

    @classmethod
    def _generate_type_specific_section(cls, text, text_lower, doc_type, topics, concepts):
        if doc_type == 'resume':
            return cls._section_resume(text, text_lower, concepts)
        elif doc_type == 'research_paper':
            return cls._section_paper(text, text_lower, topics, concepts)
        elif doc_type == 'study_material':
            return cls._section_study(text, text_lower, topics)
        elif doc_type == 'documentation':
            return cls._section_docs(text, text_lower, topics)
        elif doc_type == 'book':
            return cls._section_book(text, text_lower, topics)
        elif doc_type == 'certificate':
            return cls._section_certificate(text, text_lower, concepts)
        elif doc_type == 'cheat_sheet':
            return cls._section_cheatsheet(text, text_lower, topics, concepts)
        else:
            return cls._section_generic(text, text_lower, topics)

    @classmethod
    def _section_resume(cls, text, text_lower, concepts):
        items = []
        exp_match = re.search(r'(\d+)\+?\s*years?\s*(of)?\s*experience', text_lower)
        if exp_match:
            items.append(f"{exp_match.group(1)}+ years of professional experience")

        skills = [c for c in concepts if c.lower() not in cls.RESUME_SECTIONS]
        if skills:
            items.append(f"Core skills: {', '.join(skills[:5])}")

        companies = re.findall(r'(?:at|@\s*)([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)', text)
        if companies:
            unique_companies = list(dict.fromkeys(companies))[:3]
            items.append(f"Experience at {', '.join(unique_companies)}")

        edu_matches = re.findall(r'(Bachelor|Master|PhD|B\.?S\.?|M\.?S\.?|B\.?Tech|M\.?Tech)[^.\n]{0,80}', text, re.IGNORECASE)
        if edu_matches:
            items.append(f"Education: {edu_matches[0].strip()[:60]}")

        project_matches = re.findall(r'(?:Project|Built|Designed|Developed)[:\s]*(.{10,60}?)(?:\n|$)', text, re.IGNORECASE)
        if project_matches:
            items.append(f"Notable project: {project_matches[0].strip()[:50]}")

        if not items:
            items.append("Professional background with technical expertise")

        return TypeSpecificSection(label="Candidate Highlights", items=items[:6])

    @classmethod
    def _section_paper(cls, text, text_lower, topics, concepts):
        items = []

        problem_match = re.search(r'(?:problem|challenge|issue|gap)[\s:]*(.{10,80}?)(?:\.|$)', text_lower)
        if problem_match:
            items.append(f"Addresses: {problem_match.group(0).strip()[:60]}")

        method_match = re.search(r'(?:propose|present|introduce|develop)[\s:]*(.{10,80}?)(?:\.|$)', text_lower)
        if method_match:
            items.append(f"Proposed approach: {method_match.group(0).strip()[:60]}")

        result_match = re.search(r'(?:achieve|demonstrate|show|improve)[\s:]*(.{10,80}?)(?:\.|$)', text_lower)
        if result_match:
            items.append(f"Key finding: {result_match.group(0).strip()[:60]}")

        for topic in topics[:3]:
            items.append(f"Contribution in: {topic}")

        if not items:
            items.append("Novel contribution to the research field")

        return TypeSpecificSection(label="Research Contributions", items=items[:6])

    @classmethod
    def _section_study(cls, text, text_lower, topics):
        items = []
        for topic in topics[:5]:
            items.append(f"Understand core principles of {topic}")
        if topics:
            items.append(f"Solve problems related to {topics[0]}")
        return TypeSpecificSection(label="Learning Objectives", items=items[:6])

    @classmethod
    def _section_docs(cls, text, text_lower, topics):
        items = []
        endpoints = re.findall(r'((?:GET|POST|PUT|DELETE|PATCH)\s+/\S+)', text)
        for ep in endpoints[:3]:
            items.append(f"Endpoint: {ep.strip()}")
        for topic in topics[:3]:
            items.append(f"Module: {topic}")
        if not items:
            items.append("Core API and functionality reference")
        return TypeSpecificSection(label="Key Modules", items=items[:6])

    @classmethod
    def _section_book(cls, text, text_lower, topics):
        items = []
        for topic in topics[:4]:
            items.append(f"Master {topic}")
        if re.search(r'\bexercise\b|\bpractice\b', text_lower):
            items.append("Practice with exercises and real-world problems")
        if not items:
            items.append("Develop comprehensive understanding of the subject")
        return TypeSpecificSection(label="What You'll Learn", items=items[:6])

    @classmethod
    def _section_certificate(cls, text, text_lower, concepts):
        items = []
        name_match = re.search(r'(?:certificate\s+of|certification\s+in)\s+(.{5,60}?)(?:\.|,|\n|$)', text_lower)
        if name_match:
            items.append(f"Credential: {name_match.group(1).strip().title()}")
        org_match = re.search(r'(?:issued\s+by|presented\s+by)[:\s]*(.{5,60}?)(?:\.|,|\n|$)', text_lower)
        if org_match:
            items.append(f"Issued by: {org_match.group(1).strip().title()}")
        if not items:
            items.append("Certificate of completion")
        return TypeSpecificSection(label="Certificate Details", items=items[:6])

    @classmethod
    def _section_cheatsheet(cls, text, text_lower, topics, concepts):
        items = []
        if topics:
            items.append(f"Covers: {', '.join(topics[:4])}")
        if concepts:
            items.append(f"Core concepts: {', '.join(concepts[:5])}")
        if not items:
            items.append("Quick reference guide")
        return TypeSpecificSection(label="Quick Reference", items=items[:6])

    @classmethod
    def _section_generic(cls, text, text_lower, topics):
        items = [f"Topic: {t}" for t in topics[:5]]
        if not items:
            items.append("Key points from this document")
        return TypeSpecificSection(label="Key Points", items=items[:6])

    # ── Stage 9: Question Generation (From Concepts) ────────────────────

    @classmethod
    def _generate_questions(cls, topics, concepts, doc_type, text_lower):
        """
        Generate questions from CONCEPTS, not from extracted text.
        Bad:  "Explain Greater Noida." / "Explain Prova et al."
        Good: "What machine learning models are compared?" / "What datasets are used?"
        """
        questions: List[str] = []

        TYPE_QUESTIONS = {
            'resume': [
                "What technologies does this candidate know?",
                "What projects have they built?",
                "What experience do they have?",
            ],
            'research_paper': [
                "What problem is being solved?",
                "What methodology is proposed?",
                "What datasets were used for evaluation?",
                "What are the main findings?",
                "What are the limitations?",
            ],
            'study_material': [
                "What subjects are covered?",
                "What formulas and concepts should I review?",
                "What practice problems are included?",
            ],
            'documentation': [
                "How do I get started?",
                "What are the main API endpoints?",
                "What are the prerequisites?",
            ],
            'book': [
                "What is this book about?",
                "What topics are covered?",
                "Is this suitable for beginners?",
            ],
            'certificate': [
                "What skills does this certificate validate?",
                "What organization issued this certificate?",
            ],
            'cheat_sheet': [
                "What APIs and functions are covered?",
                "What are the common patterns?",
            ],
        }

        type_qs = TYPE_QUESTIONS.get(doc_type, [])
        questions.extend(type_qs)

        # Topic-specific questions (from concepts, NOT raw text)
        for topic in topics[:4]:
            clean = topic.strip()
            if clean and len(clean) > 3:
                # Generate conceptual questions, not "Explain <name>"
                words = clean.split()
                if len(words) >= 2:
                    # Multi-word concept → ask about its role
                    questions.append(f"What is the role of {clean} in this context?")
                else:
                    questions.append(f"How does {clean} relate to the other topics?")

        # Concept-based questions
        for concept in concepts[:3]:
            clean = concept.strip()
            if clean and len(clean) > 3:
                words = clean.split()
                if len(words) >= 2:
                    questions.append(f"What are the key aspects of {clean}?")

        # Deduplicate
        seen: Set[str] = set()
        unique: List[str] = []
        for q in questions:
            key = q.lower().strip()
            if key not in seen and len(q) > 10:
                seen.add(key)
                unique.append(q)

        return unique[:8]

    # ── Stage 10: Knowledge Node Chunking ───────────────────────────────

    @classmethod
    def _chunk_knowledge(cls, text, text_lower, topics, doc_type):
        sections = cls._split_by_headings(text)

        nodes: List[KnowledgeNode] = []
        if len(sections) >= 2:
            for heading, body in sections:
                if len(body.strip()) < 30:
                    continue
                kw = cls._compute_tf(body.lower())
                top_kw = [w for w, _ in sorted(kw.items(), key=lambda x: x[1], reverse=True)
                          if w not in cls.STOP_WORDS and len(w) > 2][:8]
                nodes.append(KnowledgeNode(
                    title=heading,
                    description=cls._summarize_chunk(body),
                    keywords=top_kw,
                    page_numbers=[],
                ))
        else:
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 50]
            chunk_size = max(1, len(paragraphs) // 5) or 1
            for i in range(0, len(paragraphs), chunk_size):
                chunk_paras = paragraphs[i:i + chunk_size]
                chunk = '\n\n'.join(chunk_paras)
                kw = cls._compute_tf(chunk.lower())
                top_kw = [w for w, _ in sorted(kw.items(), key=lambda x: x[1], reverse=True)
                          if w not in cls.STOP_WORDS and len(w) > 2][:8]
                title = chunk_paras[0][:80].strip()
                if len(chunk_paras[0]) > 80:
                    title = title.rsplit(' ', 1)[0] + '...'
                nodes.append(KnowledgeNode(
                    title=title,
                    description=cls._summarize_chunk(chunk),
                    keywords=top_kw,
                    page_numbers=[],
                ))

        return nodes[:15]

    # ── Stage 11: Confidence Validation Loop ────────────────────────────

    @classmethod
    def _validate_output(cls, topics, concepts, doc_type, text_lower) -> Tuple[List[str], List[str]]:
        """
        Before returning, ask internally:
        "If I removed the document and only showed these topics,
        would another person immediately understand what the document is about?"
        If NO → repeat extraction with relaxed filters.
        """
        if not topics and not concepts:
            # Total failure — try relaxed extraction
            return cls._relaxed_extraction(text_lower, doc_type)

        # Check 1: Are topics specific enough?
        # Remove overly generic topics
        generic_topics = {'introduction', 'overview', 'summary', 'background', 'conclusion'}
        topics = [t for t in topics if t.lower() not in generic_topics]

        # Check 2: Do we have domain-specific terms?
        has_domain_specific = False
        for domain_name, domain_concepts in DOMAINS.items():
            for concept in domain_concepts:
                if any(concept in t.lower() for t in topics + concepts):
                    has_domain_specific = True
                    break
            if has_domain_specific:
                break

        # Check 3: If no domain-specific terms, add from text
        if not has_domain_specific:
            for tech in TECHNOLOGIES:
                if tech in text_lower and tech.title() not in concepts:
                    concepts.append(tech.title())
            for algo in ALGORITHMS:
                if algo in text_lower and algo.title() not in concepts:
                    concepts.append(algo.title())

        return topics, concepts

    @classmethod
    def _relaxed_extraction(cls, text_lower, doc_type):
        """Fallback: extract anything meaningful from text."""
        topics: List[str] = []
        concepts: List[str] = []

        # Try to find any technical terms
        for tech in TECHNOLOGIES:
            if tech in text_lower:
                topics.append(tech.title())
        for algo in ALGORITHMS:
            if algo in text_lower:
                topics.append(algo.title())

        # Domain concepts
        for domain_name, domain_concepts in DOMAINS.items():
            for concept in domain_concepts:
                if concept in text_lower:
                    topics.append(concept.title())

        # Deduplicate
        seen: Set[str] = set()
        unique: List[str] = []
        for t in topics:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                unique.append(t)

        return unique[:10], unique[:12]

    # ── Utility Methods ─────────────────────────────────────────────────

    @classmethod
    def _extract_section_headings(cls, text: str) -> List[str]:
        headings: List[str] = []
        for line in text.split('\n'):
            stripped = line.strip()
            if not stripped or len(stripped) < 3 or len(stripped) > 80:
                continue

            m = re.match(r'^#{1,3}\s+(.+)', stripped)
            if m:
                heading = m.group(1).strip()
                if heading:
                    headings.append(heading)
                continue

            m = re.match(r'^(?:Chapter|Unit|Section|Module|Part)\s*\d+[:\.\s]+(.+)', stripped, re.IGNORECASE)
            if m:
                heading = m.group(1).strip()
                if heading:
                    headings.append(heading)
                continue

            m = re.match(r'^\d+(?:\.\d+)*\.?\s+([A-Z].+)', stripped)
            if m:
                heading = m.group(1).strip()
                if heading and len(heading) > 2:
                    headings.append(heading)
                continue

            if (stripped[0].isupper()
                    and 3 < len(stripped) < 60
                    and not stripped.endswith('.')
                    and not stripped.endswith(',')
                    and len(stripped.split()) <= 8):
                words = stripped.split()
                title_count = sum(1 for w in words if w[0].isupper())
                if title_count / max(len(words), 1) >= 0.7:
                    headings.append(stripped)

        return headings

    @classmethod
    def _get_title_line(cls, text: str) -> str:
        for line in text.split('\n')[:10]:
            stripped = line.strip()
            if stripped and len(stripped) > 3 and len(stripped) < 200:
                if not re.match(r'^(?:confidential|copyright|page\s*\d)', stripped.lower()):
                    return stripped
        return ""

    @classmethod
    def _detect_domain(cls, text_lower: str) -> str:
        best_domain = "General"
        best_score = 0
        for domain_name, domain_concepts in DOMAINS.items():
            score = sum(1 for kw in domain_concepts if kw in text_lower)
            if score > best_score:
                best_score = score
                best_domain = domain_name.replace('_', ' ').title()
        return best_domain

    @classmethod
    def _detect_difficulty(cls, text_lower, doc_type):
        if any(sig in text_lower for sig in ['advanced', 'complex', 'theoretical', 'rigorous']):
            return 'Advanced'
        if any(sig in text_lower for sig in ['introduction', 'getting started', 'basics', 'fundamentals']):
            return 'Beginner'
        if any(sig in text_lower for sig in ['intermediate', 'applied', 'practical']):
            return 'Intermediate'
        if doc_type in ('research_paper',):
            return 'Advanced'
        if doc_type in ('tutorial', 'lecture_notes'):
            return 'Beginner'
        return 'General'

    @classmethod
    def _detect_language(cls, text):
        if re.search(r'[\u0900-\u097F]', text):
            return 'Hindi'
        if re.search(r'[\u4e00-\u9fff]', text):
            return 'Chinese'
        return 'English'

    @classmethod
    def _split_by_headings(cls, text):
        sections: List[Tuple[str, str]] = []
        lines = text.split('\n')
        current_heading = "Introduction"
        current_body: List[str] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                current_body.append('')
                continue

            is_heading = False
            new_heading = stripped

            m = re.match(r'^#{1,3}\s+(.+)', stripped)
            if m:
                is_heading = True
                new_heading = m.group(1).strip()
            elif (len(stripped) < 60
                  and stripped[0].isupper()
                  and not stripped.endswith('.')
                  and len(stripped.split()) <= 8):
                words = stripped.split()
                upper_count = sum(1 for w in words if w and w[0].isupper())
                if upper_count / max(len(words), 1) >= 0.7:
                    is_heading = True
                    new_heading = stripped
            elif re.match(r'^\d+(?:\.\d+)*\.?\s+[A-Z]', stripped):
                is_heading = True
                new_heading = re.sub(r'^\d+(?:\.\d+)*\.?\s+', '', stripped)

            if is_heading:
                if current_body:
                    body_text = '\n'.join(current_body).strip()
                    if len(body_text) > 30:
                        sections.append((current_heading, body_text))
                current_heading = new_heading
                current_body = []
            else:
                current_body.append(line)

        if current_body:
            body_text = '\n'.join(current_body).strip()
            if len(body_text) > 30:
                sections.append((current_heading, body_text))

        return sections

    @staticmethod
    def _summarize_chunk(text):
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        for sent in sentences:
            sent = sent.strip()
            if len(sent) > 20 and not sent.startswith('#'):
                return sent[:200] if len(sent) > 200 else sent
        preview = text.strip()[:150]
        return preview.rsplit(' ', 1)[0] + '...' if len(text.strip()) > 150 else preview

    @staticmethod
    def _compute_tf(text_lower):
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        if not words:
            return {}
        counts = Counter(words)
        total = len(words)
        return {word: count / total for word, count in counts.items()}

    @staticmethod
    def _split_sentences(text):
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        parts = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in parts if s.strip() and len(s.strip()) > 15]

    @classmethod
    def _infer_metadata(cls, text, text_lower, doc_type, filename, classification_confidence):
        word_count = len(text.split())
        reading_time_minutes = round(word_count / 200)
        estimated_pages = max(1, round(word_count / 300))

        has_examples = bool(re.search(r'\bexample\b|\bsolved\b|\bworked\b', text_lower))
        has_exercises = bool(re.search(r'\bexercise\b|\bproblem\s*\d|\bpractice\b', text_lower))
        has_formulas = bool(re.search(r'[=∫∑∏√±≤≥≠≈]|formula|equation|theorem', text_lower))

        domain = cls._detect_domain(text_lower)
        difficulty = cls._detect_difficulty(text_lower, doc_type)
        language = cls._detect_language(text)

        TYPE_LABELS = {
            'resume': 'Resume / CV',
            'research_paper': 'Research Paper',
            'book': 'Book',
            'documentation': 'Technical Documentation',
            'tutorial': 'Tutorial / Guide',
            'study_material': 'Study Material',
            'lecture_notes': 'Lecture Notes',
            'certificate': 'Certificate',
            'cheat_sheet': 'Cheat Sheet',
            'general': 'General Document',
        }

        certificate_info = None
        if doc_type == 'certificate':
            certificate_info = cls._extract_certificate_info(text, text_lower)

        return DocumentMetadata(
            type=TYPE_LABELS.get(doc_type, 'General Document'),
            domain=domain,
            difficulty=difficulty,
            estimated_reading_time=f"{reading_time_minutes} minutes",
            pages=estimated_pages,
            contains_examples=has_examples,
            contains_exercises=has_exercises,
            contains_formulas=has_formulas,
            language=language,
            engine_version=cls.ENGINE_VERSION,
            classification_confidence=classification_confidence,
            certificate_info=certificate_info,
        )

    @classmethod
    def _extract_certificate_info(cls, text, text_lower):
        info = {}
        name_match = re.search(r'(?:certificate\s+of|certification\s+in)\s+(.{5,60}?)(?:\.|,|\n|$)', text_lower)
        if name_match:
            info['name'] = name_match.group(1).strip().title()
        org_match = re.search(r'(?:issued\s+by|presented\s+by)[:\s]*(.{5,60}?)(?:\.|,|\n|$)', text_lower)
        if org_match:
            info['organization'] = org_match.group(1).strip().title()
        return info if info else {'name': 'Certificate of Completion'}

    # ── Main Entry Point ────────────────────────────────────────────────

    @classmethod
    def analyze(cls, text: str, filename: str = "") -> DocumentAnalysis:
        """
        Run the full V5 analysis pipeline.
        Semantic understanding, not pattern matching.
        """
        if not text or len(text.strip()) < 50:
            return cls._empty_analysis(text or "")

        # Stage 0: OCR Cleanup
        cleaned = cls._cleanup_ocr(text)
        if len(cleaned) < 50:
            cleaned = text.strip()

        text_lower = cleaned.lower()

        # Stage 1: Document type classification
        doc_type, classification_confidence = cls._classify_document_type(text_lower, filename)

        # Stage 2: Named Entity Recognition
        entities = cls._extract_entities(cleaned, text_lower, doc_type)

        # Stage 3: Semantic concept extraction
        raw_concepts = cls._extract_concepts_semantic(cleaned, text_lower, doc_type)

        # Stage 4: Build concept graph (parent→child)
        concept_graph = cls._build_concept_graph(raw_concepts, text_lower)

        # Stage 5: Rank topics and concepts
        topics, concepts, confidence_scores = cls._rank_topics(
            concept_graph, text_lower, doc_type, entities
        )

        # Stage 6: Validate output quality
        topics, concepts = cls._validate_output(topics, concepts, doc_type, text_lower)

        # Stage 7: Summary generation
        overview = cls._generate_overview(cleaned, text_lower, doc_type, topics, concepts, filename)

        # Stage 8: Keyword extraction
        keywords = cls._extract_keywords(text_lower, doc_type)

        # Stage 9: Type-specific sections
        type_section = cls._generate_type_specific_section(cleaned, text_lower, doc_type, topics, concepts)

        # Stage 10: Question generation (from concepts, not raw text)
        questions = cls._generate_questions(topics, concepts, doc_type, text_lower)

        # Stage 11: Knowledge node chunking
        nodes = cls._chunk_knowledge(cleaned, text_lower, topics, doc_type)

        # Metadata
        metadata = cls._infer_metadata(cleaned, text_lower, doc_type, filename, classification_confidence)

        # Backward compatibility
        learning_objectives = type_section.items

        return DocumentAnalysis(
            document_overview=overview,
            topics_covered=topics,
            key_concepts=concepts,
            keywords=keywords,
            document_metadata=metadata,
            learning_objectives=learning_objectives,
            type_specific_section=type_section,
            suggested_questions=questions,
            knowledge_nodes=nodes,
            confidence_scores=confidence_scores,
        )

    @classmethod
    def _empty_analysis(cls, original_text=""):
        return DocumentAnalysis(
            document_overview="This document appears to contain limited content. It may be a placeholder, an empty file, or a document with primarily non-textual elements.",
            topics_covered=[],
            key_concepts=[],
            keywords=[],
            document_metadata=DocumentMetadata(engine_version=cls.ENGINE_VERSION),
            learning_objectives=[],
            type_specific_section=TypeSpecificSection(label="Key Points", items=[]),
            suggested_questions=["What is this document about?"],
            knowledge_nodes=[],
            confidence_scores={},
        )
