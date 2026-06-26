"""
Topic Extractor

Enhanced rule-based topic extraction with TF-IDF-like scoring,
n-gram support, and confidence scores.
Identifies technologies, general topics, document type, and categories.
"""

from typing import Dict, List, Tuple
import re
import math
from collections import Counter


class TopicExtractor:
    """Extract topics from text using keyword matching with TF-IDF scoring."""

    # Technology keywords (expanded)
    TECHNOLOGIES = {
        'backend': [
            'fastapi', 'django', 'flask', 'spring', 'springboot', 'spring boot',
            'node', 'nodejs', 'node.js', 'express', 'expressjs', 'koa', 'nestjs', 'nest.js',
            'java', 'golang', 'go', 'rust', 'ruby', 'rails', 'ruby on rails',
            'php', 'laravel', 'symfony', '.net', 'dotnet', 'c#',
            'elixir', 'phoenix', 'scala', 'play', 'akka',
            'graphql', 'grpc', 'rest api', 'restful', 'websocket',
            'celery', 'rq', 'sidekiq', 'background jobs', 'task queue',
        ],
        'frontend': [
            'react', 'reactjs', 'react.js', 'vue', 'vuejs', 'vue.js', 'angular', 'angularjs',
            'svelte', 'sveltekit', 'ember', 'backbone', 'preact', 'solid', 'solidjs',
            'nextjs', 'next.js', 'nuxt', 'nuxtjs', 'remix', 'astro',
            'html', 'css', 'javascript', 'typescript', 'jsx', 'tsx',
            'webpack', 'vite', 'rollup', 'parcel', 'esbuild', 'turbopack',
            'sass', 'scss', 'less', 'tailwind', 'tailwindcss', 'bootstrap',
            'material ui', 'mui', 'chakra ui', 'ant design', 'shadcn',
            'redux', 'zustand', 'jotai', 'recoil', 'mobx', 'pinia', 'vuex',
            'tanstack', 'react query', 'swr', 'axios', 'fetch api',
            'web components', 'pwa', 'progressive web app', 'spa', 'ssr', 'ssg',
        ],
        'database': [
            'postgresql', 'postgres', 'mysql', 'mariadb', 'sqlite',
            'mongodb', 'firebase', 'firestore', 'dynamodb', 'couchdb',
            'redis', 'memcached', 'elasticsearch', 'solr', 'meilisearch',
            'neo4j', 'cassandra', 'cockroachdb', 'supabase', 'planetscale',
            'clickhouse', 'timescaledb', 'influxdb', 'prometheus',
            'sql', 'nosql', 'graph db', 'graphql', 'orm', 'prisma', 'drizzle',
            'sqlalchemy', 'sequelize', 'typeorm', 'mongoose',
        ],
        'devops': [
            'docker', 'kubernetes', 'k8s', 'helm', 'docker compose', 'dockerfile',
            'jenkins', 'gitlab', 'github', 'github actions', 'circleci', 'travis',
            'aws', 'azure', 'gcp', 'google cloud', 'digitalocean', 'heroku', 'vercel', 'netlify',
            'terraform', 'ansible', 'vagrant', 'pulumi', 'cloudformation',
            'linux', 'nginx', 'apache', 'caddy', 'haproxy',
            'prometheus', 'grafana', 'elk stack', 'logstash', 'datadog', 'sentry',
            'ci/cd', 'cicd', 'continuous integration', 'continuous deployment',
            'infrastructure', 'monitoring', 'logging', 'alerting',
        ],
        'auth': [
            'jwt', 'oauth', 'oauth2', 'openid', 'saml', 'kerberos',
            'ldap', 'active directory', 'mfa', '2fa', 'two-factor',
            'authentication', 'authorization', 'rbac', 'abac', 'acl',
            'session', 'cookie', 'token', 'sso', 'single sign-on',
            'passport', 'keycloak', 'auth0', 'clerk', 'supabase auth',
        ],
        'ai_ml': [
            'artificial intelligence', 'ai', 'machine learning', 'ml',
            'deep learning', 'neural network', 'nlp', 'natural language processing',
            'computer vision', 'cv', 'generative ai', 'gen ai', 'genai',
            'large language model', 'llm', 'gpt', 'bert', 'transformer', 'attention',
            'chatbot', 'recommendation system', 'opencv', 'langchain', 'llamaindex',
            'rag', 'retrieval augmented generation', 'embedding', 'vector database',
            'fine-tuning', 'finetuning', 'lora', 'qlora', 'peft',
            'diffusion model', 'stable diffusion', 'midjourney', 'dalle',
            'hugging face', 'huggingface', 'openai', 'anthropic', 'claude',
            'pytorch', 'tensorflow', 'keras', 'scikit-learn', 'sklearn',
            'transformers', 'tokenization', 'word2vec', 'glove',
            'agent', 'ai agent', 'multi-agent', 'function calling', 'tool use',
            'prompt engineering', 'prompt engineering', 'chain of thought', 'cot',
            'vector store', 'chromadb', 'pinecone', 'weaviate', 'qdrant', 'milvus',
        ],
        'data': [
            'pandas', 'numpy', 'scipy', 'jupyter', 'anaconda',
            'apache spark', 'hadoop', 'hive', 'kafka', 'flink',
            'data science', 'data engineering', 'etl', 'analytics',
            'tableau', 'power bi', 'looker', 'qlik', 'metabase',
            'data pipeline', 'data warehouse', 'data lake', 'bigquery',
        ],
        'cloud': [
            'aws', 'ec2', 's3', 'lambda', 'dynamodb', 'rds', 'sqs', 'sns',
            'azure', 'app service', 'cosmos db', 'azure functions',
            'gcp', 'bigquery', 'cloud functions', 'gke', 'cloud run',
            'cloud', 'serverless', 'faas', 'paas', 'iaas', 'saas',
            'edge computing', 'cdn', 'cloudflare', 'akamai',
        ],
        'messaging': [
            'kafka', 'rabbitmq', 'activemq', 'nats', 'zeromq',
            'mqtt', 'amqp', 'message broker', 'event streaming',
            'redis pub/sub', 'gcp pubsub', 'aws sqs', 'aws sns',
            'socket.io', 'server-sent events', 'sse', 'websocket',
        ],
        'testing': [
            'pytest', 'unittest', 'jest', 'mocha', 'jasmine', 'vitest',
            'rspec', 'junit', 'cucumber', 'selenium', 'cypress', 'playwright',
            'testing library', 'enzyme', 'supertest', 'httpx',
            'test', 'unit test', 'integration test', 'e2e', 'tdd', 'bdd',
            'coverage', 'mocking', 'test driven', 'behavior driven',
        ],
        'mobile': [
            'react native', 'flutter', 'swift', 'kotlin', 'dart',
            'ios', 'android', 'xamarin', 'ionic', 'capacitor',
            'expo', 'react native', 'mobile development', 'cross-platform',
            'swiftui', 'jetpack compose', 'xcode', 'android studio',
        ],
        'languages': [
            'python', 'javascript', 'typescript', 'golang', 'go', 'rust',
            'java', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'scala', 'elixir', 'clojure', 'r', 'matlab', 'dart',
            'perl', 'haskell', 'lua', 'assembly', 'bash', 'shell', 'powershell',
        ],
        'other': [
            'git', 'version control', 'agile', 'scrum', 'kanban',
            'jira', 'confluence', 'notion', 'figma', 'sketch',
            'photoshop', 'illustrator', 'postman', 'swagger',
            'api', 'rest', 'microservices', 'monolith', 'monolithic',
            'design pattern', 'architecture', 'system design',
        ],
    }

    # General topics (expanded)
    GENERAL_TOPICS = {
        'architecture': [
            'design', 'pattern', 'architecture', 'microservices',
            'monolithic', 'soa', 'event-driven', 'cqrs', 'ddd',
            'clean architecture', 'hexagonal', 'layered', 'mvc', 'mvvm',
            'domain driven', 'event sourcing', 'saga pattern',
        ],
        'security': [
            'security', 'encryption', 'tls', 'ssl', 'https',
            'vulnerability', 'penetration', 'pentest', 'xss', 'sql injection',
            'csrf', 'cors', 'certificate', 'ssl certificate',
            'zero trust', 'firewall', 'waf', 'owasp', 'security audit',
        ],
        'performance': [
            'optimization', 'caching', 'performance', 'benchmark',
            'profiling', 'tuning', 'latency', 'throughput', 'scalability',
            'load balancing', 'horizontal scale', 'vertical scale',
            'bottleneck', 'memory leak', 'cpu usage', 'response time',
        ],
        'quality': [
            'quality', 'code review', 'lint', 'formatter', 'coverage',
            'refactor', 'refactoring', 'technical debt', 'maintainability',
            'readability', 'clean code', 'solid principles', 'dry', 'kiss',
        ],
        'documentation': [
            'documentation', 'readme', 'doc', 'guide', 'tutorial',
            'api doc', 'swagger', 'openapi', 'javadoc', 'sphinx',
            'changelog', 'contributing', 'architecture decision',
        ],
        'development': [
            'development', 'coding', 'programming', 'build', 'compile',
            'debug', 'debugging', 'deploy', 'release', 'ci/cd',
            'agile', 'sprint', 'standup', 'retrospective', 'planning',
        ],
        'education': [
            'bachelor', 'master', 'phd', 'degree', 'university',
            'college', 'gpa', 'cgpa', 'sgpa', 'coursework',
            'semester', 'year', 'graduation', 'diploma', 'thesis',
        ],
        'career': [
            'experience', 'internship', 'full-time', 'part-time',
            'freelance', 'remote', 'onsite', 'hybrid',
            'team lead', 'manager', 'developer', 'engineer',
            'intern', 'senior', 'junior', 'lead', 'placement',
        ],
        'interview': [
            'interview', 'coding interview', 'system design interview',
            'behavioral', 'dsa', 'data structures', 'algorithms',
            'leetcode', 'competitive programming', 'problem solving',
            'aptitude', 'technical interview', 'hr interview',
        ],
    }

    # Document type indicators (expanded)
    DOC_TYPE_INDICATORS = {
        'resume': [
            'resume', 'curriculum vitae', 'cv', 'personal details',
            'work experience', 'education', 'skills', 'projects',
            'certifications', 'references', 'declaration', 'objective',
            'career objective', 'professional summary', 'profile',
            'technical skills', 'key skills', 'core competencies',
            'employment history', 'work history',
        ],
        'research_paper': [
            'abstract', 'introduction', 'methodology', 'results',
            'discussion', 'conclusion', 'references', 'literature review',
            'hypothesis', 'experiment', 'findings', 'doi',
            'paper', 'published', 'journal', 'conference',
        ],
        'report': [
            'executive summary', 'findings', 'recommendations',
            'analysis', 'metrics', 'kpi', 'quarterly', 'annual',
            'revenue', 'profit', 'growth', 'market', 'financial',
        ],
        'article': [
            'author', 'published', 'editor', 'newsletter',
            'blog', 'opinion', 'editorial', 'feature',
            'read time', 'min read',
        ],
        'tutorial': [
            'tutorial', 'guide', 'how to', 'step by step',
            'getting started', 'introduction to', 'learn',
            'prerequisites', 'installation', 'setup', 'quickstart',
        ],
        'documentation': [
            'api reference', 'documentation', 'usage', 'examples',
            'parameters', 'return value', 'method', 'class',
            'function', 'module', 'library', 'framework',
            'getting started', 'installation',
        ],
        'notes': [
            'notes', 'lecture notes', 'class notes', 'study notes',
            'handwritten', 'summary', 'key points', 'takeaways',
            'important', 'remember', 'mnemonic', 'formula',
        ],
        'interview_prep': [
            'interview questions', 'interview preparation', 'placement',
            'coding questions', 'dsa', 'aptitude', 'mock interview',
            'behavioral questions', 'technical questions',
        ],
    }

    # Common English stop words for TF-IDF
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
    def extract_topics(cls, text: str) -> Dict[str, List[str]]:
        """
        Extract topics from text with confidence scoring.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with technologies, general topics, document type, and confidence
        """
        if not text:
            return {"technologies": [], "general": [], "document_type": "other", "confidence": 0.0}

        text_lower = text.lower()

        # TF-IDF-like keyword frequency scoring
        word_freq = cls._compute_term_frequencies(text_lower)

        technologies = cls._find_keywords_scored(text_lower, cls.TECHNOLOGIES, word_freq)
        general = cls._find_keywords_scored(text_lower, cls.GENERAL_TOPICS, word_freq)
        doc_type = cls._detect_document_type(text_lower)

        # Calculate confidence based on keyword density
        total_words = len(text_lower.split())
        matched_words = sum(len(tech) for tech in technologies.values()) + sum(len(gen) for gen in general.values())
        confidence = min(1.0, (matched_words / max(total_words, 1)) * 10)

        # Flatten to sorted lists
        tech_list = sorted(set(t for cats in technologies.values() for t in cats))
        gen_list = sorted(set(g for cats in general.values() for g in cats))

        return {
            "technologies": tech_list,
            "general": gen_list,
            "document_type": doc_type,
            "confidence": round(confidence, 3),
        }

    @classmethod
    def _compute_term_frequencies(cls, text: str) -> Dict[str, float]:
        """Compute TF-IDF-like term frequencies (TF only, IDF approximated by inverse length)."""
        words = re.findall(r'\b[a-z0-9+#.]+\b', text)
        if not words:
            return {}

        # Count raw frequencies
        word_counts = Counter(words)
        total = len(words)

        # TF normalization
        tf = {word: count / total for word, count in word_counts.items()}

        # Filter stop words and very short words
        tf = {w: score for w, score in tf.items() if w not in cls.STOP_WORDS and len(w) > 1}

        return tf

    @classmethod
    def _find_keywords_scored(
        cls, text: str, keyword_dict: Dict[str, List[str]], word_freq: Dict[str, float]
    ) -> Dict[str, List[str]]:
        """
        Find keywords with TF-IDF-like scoring and category grouping.

        Returns:
            Dict mapping category -> list of matched keywords (sorted by relevance)
        """
        result = {}

        for category, keywords in keyword_dict.items():
            matched = []
            for keyword in keywords:
                # Exact word match
                if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                    # Score: TF of the keyword multiplied by length bonus
                    score = word_freq.get(keyword, 0.0)
                    # Bonus for multi-word keywords
                    if ' ' in keyword:
                        score += 0.01
                    matched.append((keyword, score))
                # Also check for compound forms (e.g., "react.js" matches "react")
                elif '.' in keyword:
                    base = keyword.split('.')[0]
                    if re.search(r'\b' + re.escape(base) + r'\b', text):
                        score = word_freq.get(base, 0.0)
                        matched.append((keyword, score))

            if matched:
                # Sort by score descending
                matched.sort(key=lambda x: x[1], reverse=True)
                result[category] = [kw for kw, _ in matched]

        return result

    @classmethod
    def _detect_document_type(cls, text: str) -> str:
        """Detect the type of document with improved scoring."""
        scores = {}
        for doc_type, indicators in cls.DOC_TYPE_INDICATORS.items():
            score = 0
            for indicator in indicators:
                # Exact phrase match (higher weight)
                if re.search(r'\b' + re.escape(indicator) + r'\b', text):
                    score += 2
                # Partial match (lower weight)
                elif indicator.split()[0] in text:
                    score += 0.5
            if score > 0:
                scores[doc_type] = score

        if not scores:
            return "other"

        # Require minimum confidence
        best_type = max(scores, key=scores.get)
        if scores[best_type] < 2:
            return "other"
        return best_type

    @classmethod
    def extract_keywords_with_frequency(cls, text: str, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Extract top keywords with frequency scores.
        Useful for tag generation and search indexing.

        Args:
            text: Text to analyze
            top_n: Number of top keywords to return

        Returns:
            List of (keyword, score) tuples sorted by relevance
        """
        text_lower = text.lower()
        word_freq = cls._compute_term_frequencies(text_lower)

        # Collect all matched keywords across all categories
        all_keywords = {}
        for category_dict in [cls.TECHNOLOGIES, cls.GENERAL_TOPICS]:
            for category, keywords in category_dict.items():
                for keyword in keywords:
                    if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                        score = word_freq.get(keyword, 0.0)
                        if keyword not in all_keywords or score > all_keywords[keyword]:
                            all_keywords[keyword] = score

        # Sort by score and return top N
        sorted_kw = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)
        return sorted_kw[:top_n]
