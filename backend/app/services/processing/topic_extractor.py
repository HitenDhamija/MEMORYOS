"""
Topic Extractor

Rule-based topic extraction from text.
Identifies technologies, general topics, and categories.
"""

from typing import Dict, List
import re


class TopicExtractor:
    """Extract topics from text using keyword matching."""
    
    # Technology keywords
    TECHNOLOGIES = {
        'backend': [
            'fastapi', 'django', 'flask', 'spring', 'springboot',
            'node', 'express', 'koa', 'nest', 'nestjs',
            'java', 'golang', 'go', 'rust', 'ruby', 'rails',
            'php', 'laravel', 'symfony', '.net', 'dotnet', 'c#',
            'elixir', 'phoenix', 'scala', 'play', 'akka'
        ],
        'frontend': [
            'react', 'reactjs', 'vue', 'vuejs', 'angular', 'angularjs',
            'svelte', 'ember', 'backbone', 'preact', 'solid',
            'nextjs', 'next.js', 'nuxt', 'sveltekit', 'remix',
            'html', 'css', 'javascript', 'typescript', 'jsx', 'tsx',
            'webpack', 'vite', 'rollup', 'parcel', 'esbuild',
            'sass', 'tailwind', 'bootstrap', 'material', 'semantic ui'
        ],
        'database': [
            'postgresql', 'postgres', 'mysql', 'mariadb',
            'mongodb', 'firebase', 'firestore', 'dynamodb',
            'redis', 'memcached', 'elasticsearch', 'solr',
            'neo4j', 'cassandra', 'cockroachdb', 'supabase',
            'clickhouse', 'timescaledb', 'influxdb', 'prometheus',
            'sql', 'nosql', 'graph db', 'graphql', 'sql server'
        ],
        'devops': [
            'docker', 'kubernetes', 'k8s', 'helm', 'docker compose',
            'jenkins', 'gitlab', 'github', 'github actions', 'circleci',
            'travis ci', 'travis', 'aws', 'azure', 'gcp', 'google cloud',
            'terraform', 'ansible', 'vagrant', 'linux', 'nginx', 'apache',
            'prometheus', 'grafana', 'elk stack', 'logstash', 'datadog'
        ],
        'auth': [
            'jwt', 'oauth', 'oauth2', 'openid', 'saml', 'kerberos',
            'ldap', 'active directory', 'mfa', '2fa', 'two-factor',
            'authentication', 'authorization', 'rbac', 'abac', 'acl'
        ],
        'data': [
            'machine learning', 'ml', 'deep learning', 'tensorflow', 'pytorch',
            'scikit-learn', 'keras', 'pandas', 'numpy', 'scipy',
            'jupyter', 'anaconda', 'apache spark', 'hadoop', 'hive',
            'data science', 'data engineering', 'etl', 'analytics',
            'tableau', 'power bi', 'looker', 'qlik'
        ],
        'cloud': [
            'aws', 'ec2', 's3', 'lambda', 'dynamodb',
            'azure', 'app service', 'cosmos db',
            'gcp', 'bigquery', 'cloud functions', 'gke',
            'cloud', 'serverless', 'faas', 'paas', 'iaas', 'saas'
        ],
        'messaging': [
            'kafka', 'rabbitmq', 'activemq', 'nats', 'zeromq',
            'mqtt', 'amqp', 'message broker', 'event streaming',
            'redis pub/sub', 'gcp pubsub', 'aws sqs', 'aws sns'
        ],
        'testing': [
            'pytest', 'unittest', 'jest', 'mocha', 'jasmine',
            'rspec', 'junit', 'cucumber', 'selenium', 'cypress',
            'playwright', 'testing library', 'enzyme', 'vitest',
            'test', 'unit test', 'integration test', 'e2e', 'tdd'
        ],
        'other': [
            'python', 'javascript', 'typescript', 'golang', 'go', 'rust',
            'java', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'scala', 'elixir', 'clojure', 'r', 'matlab'
        ]
    }
    
    # General topics
    GENERAL_TOPICS = {
        'architecture': [
            'design', 'pattern', 'architecture', 'microservices',
            'monolithic', 'soa', 'event-driven', 'cqrs', 'ddd',
            'clean architecture', 'hexagonal', 'layered'
        ],
        'security': [
            'security', 'encryption', 'tls', 'ssl', 'https',
            'vulnerability', 'penetration', 'pentest', 'xss', 'sql injection',
            'csrf', 'cors', 'certificate', 'ssl certificate', 'https'
        ],
        'performance': [
            'optimization', 'caching', 'performance', 'benchmark',
            'profiling', 'tuning', 'latency', 'throughput', 'scalability',
            'load balancing', 'horizontal scale', 'vertical scale'
        ],
        'quality': [
            'quality', 'code review', 'lint', 'formatter', 'coverage',
            'refactor', 'refactoring', 'technical debt', 'maintainability'
        ],
        'documentation': [
            'documentation', 'readme', 'doc', 'guide', 'tutorial',
            'api doc', 'swagger', 'openapi', 'javadoc', 'sphinx'
        ],
        'development': [
            'development', 'coding', 'programming', 'build', 'compile',
            'debug', 'debugging', 'deploy', 'release', 'ci/cd'
        ]
    }
    
    @classmethod
    def extract_topics(cls, text: str) -> Dict[str, List[str]]:
        """
        Extract topics from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with technology and general topics found
        """
        if not text:
            return {"technologies": [], "general": []}
        
        # Lowercase for matching
        text_lower = text.lower()
        
        technologies = cls._find_keywords(text_lower, cls.TECHNOLOGIES)
        general = cls._find_keywords(text_lower, cls.GENERAL_TOPICS)
        
        return {
            "technologies": sorted(technologies),
            "general": sorted(general)
        }
    
    @classmethod
    def _find_keywords(cls, text: str, keyword_dict: Dict[str, List[str]]) -> List[str]:
        """
        Find keywords in text.
        
        Args:
            text: Lowercase text to search
            keyword_dict: Dictionary of categories with keywords
            
        Returns:
            List of found topics (no duplicates)
        """
        found = set()
        
        for category, keywords in keyword_dict.items():
            for keyword in keywords:
                # Search for keyword as whole word
                # Use word boundaries: \b for word start/end
                if re.search(r'\b' + re.escape(keyword) + r'\b', text):
                    found.add(keyword)
        
        return list(found)
