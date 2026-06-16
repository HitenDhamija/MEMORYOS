"""
Markdown Processor

Processes Markdown files (.md, .markdown).
Extracts text, headers, and code blocks.
"""

import os
import re
from typing import Dict, List
from app.services.processing.base import DocumentProcessor


class MarkdownProcessor(DocumentProcessor):
    """Process Markdown files."""
    
    def can_process(self) -> bool:
        """Check if file exists and has markdown extension."""
        try:
            ext = os.path.splitext(self.file_path)[1].lower()
            return (
                os.path.exists(self.file_path) and
                os.path.isfile(self.file_path) and
                ext in ['.md', '.markdown']
            )
        except Exception:
            return False
    
    def extract_text(self) -> str:
        """
        Extract plain text from markdown.
        Preserves content but removes markdown syntax.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                markdown_text = f.read()
            
            # Remove markdown syntax but preserve content
            text = markdown_text
            
            # Remove code blocks (```...```) - content not needed
            text = re.sub(r'```[\s\S]*?```', '', text)
            
            # Remove inline code (`...`) - preserve content
            text = re.sub(r'`([^`]+)`', r'\1', text)
            
            # Remove headers markdown (# ## ###) - preserve content
            text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
            
            # Remove bold/italic (**text**, *text*, __text__, _text_)
            text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
            text = re.sub(r'\*([^\*]+)\*', r'\1', text)
            text = re.sub(r'__([^_]+)__', r'\1', text)
            text = re.sub(r'_([^_]+)_', r'\1', text)
            
            # Remove links [text](url) - preserve text
            text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
            
            # Remove images ![alt](url)
            text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', text)
            
            # Remove list markers (-, *, +, or numbers)
            text = re.sub(r'^[\s]*[-*+]\s+', '', text, flags=re.MULTILINE)
            text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
            
            # Remove blockquote markers (>)
            text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
            
            # Remove horizontal rules (---, ***, ___)
            text = re.sub(r'^[-*_]{3,}', '', text, flags=re.MULTILINE)
            
            # Clean up extra whitespace
            text = re.sub(r'\n\n+', '\n', text)
            text = text.strip()
            
            return text
        except Exception as e:
            raise ValueError(f"Failed to extract text from markdown: {str(e)}")
    
    def extract_metadata(self) -> Dict[str, any]:
        """Extract markdown metadata."""
        try:
            metadata = {
                "filename": self.original_filename,
                "file_size_bytes": os.path.getsize(self.file_path),
                "format": "markdown"
            }
            
            # Try to extract front matter (YAML)
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract YAML front matter if present
            if content.startswith('---'):
                match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                if match:
                    metadata["has_front_matter"] = True
            
            return metadata
        except Exception as e:
            return {"filename": self.original_filename, "error": str(e)}
    
    def extract_structure(self) -> Dict[str, any]:
        """
        Extract markdown structure.
        Includes headers and code blocks.
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract headers
            headers = []
            for match in re.finditer(r'^(#+)\s+(.+)$', content, re.MULTILINE):
                level = len(match.group(1))  # Number of # symbols
                text = match.group(2)
                headers.append({
                    "level": level,
                    "text": text,
                    "position": match.start()
                })
            
            # Extract code blocks
            code_blocks = []
            for match in re.finditer(r'```(\w*)\n([\s\S]*?)```', content):
                language = match.group(1) or "unknown"
                code_content = match.group(2).strip()
                code_blocks.append({
                    "language": language,
                    "lines": len(code_content.split('\n')),
                    "preview": code_content[:100]
                })
            
            # Count paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            return {
                "headers": headers,
                "code_blocks": code_blocks,
                "paragraph_count": len(paragraphs),
                "max_header_level": max([h["level"] for h in headers]) if headers else 0
            }
        except Exception:
            return {"headers": [], "code_blocks": [], "paragraph_count": 0}
