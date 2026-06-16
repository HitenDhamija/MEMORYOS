"""
Bookmark Processor

Processes bookmark files (.url, .webloc, .txt files with URLs).
Extracts URL, page title, and metadata.
"""

import os
import re
from typing import Dict
from app.services.processing.base import DocumentProcessor

try:
    import requests
    from bs4 import BeautifulSoup
    WEB_TOOLS_AVAILABLE = True
except ImportError:
    WEB_TOOLS_AVAILABLE = False


class BookmarkProcessor(DocumentProcessor):
    """Process bookmark files."""
    
    SUPPORTED_EXTENSIONS = {'.url', '.webloc', '.bookmark'}
    
    def can_process(self) -> bool:
        """Check if file exists and is a bookmark format."""
        try:
            ext = os.path.splitext(self.file_path)[1].lower()
            is_supported = (
                os.path.exists(self.file_path) and
                os.path.isfile(self.file_path) and
                ext in self.SUPPORTED_EXTENSIONS
            )
            
            # Also check if it's a .txt file containing a URL
            if not is_supported and ext == '.txt':
                with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Check if content looks like a URL
                    if self._extract_url_from_text(content):
                        return True
            
            return is_supported
        except Exception:
            return False
    
    def extract_text(self) -> str:
        """
        Extract text content from bookmark.
        For .url files: parse InternetShortcut format
        For .webloc: extract URL and fetch page content
        """
        try:
            url = self._extract_url()
            if not url:
                return ""
            
            # Try to fetch page content
            if not WEB_TOOLS_AVAILABLE:
                return f"Bookmark URL: {url}"
            
            try:
                response = requests.get(url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                response.raise_for_status()
                
                # Parse HTML and extract text
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Get text
                text = soup.get_text()
                
                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = ' '.join(chunk for chunk in chunks if chunk)
                
                return text[:5000]  # Limit to first 5000 chars
            except Exception as e:
                # If fetching fails, just return the URL
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Failed to fetch URL content: {str(e)}")
                return f"Bookmark URL: {url}"
        except Exception:
            return ""
    
    def extract_metadata(self) -> Dict[str, any]:
        """Extract bookmark metadata."""
        try:
            metadata = {
                "filename": self.original_filename,
                "file_size_bytes": os.path.getsize(self.file_path),
                "type": "bookmark"
            }
            
            url = self._extract_url()
            if url:
                metadata["url"] = url
                
                # Try to fetch page title
                if WEB_TOOLS_AVAILABLE:
                    try:
                        response = requests.get(url, timeout=5, headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                        })
                        response.raise_for_status()
                        
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract title
                        title = soup.find('title')
                        if title:
                            metadata["page_title"] = title.string
                        
                        # Extract description from meta tags
                        description = soup.find('meta', attrs={'name': 'description'})
                        if description:
                            metadata["page_description"] = description.get('content', '')
                    except Exception:
                        pass  # If fetching fails, continue with just URL
            
            return metadata
        except Exception as e:
            return {"filename": self.original_filename, "error": str(e)}
    
    def extract_structure(self) -> Dict[str, any]:
        """Extract bookmark structure."""
        try:
            url = self._extract_url()
            
            structure = {
                "type": "bookmark",
                "has_url": bool(url),
            }
            
            if url:
                structure["url"] = url
                structure["domain"] = self._extract_domain(url)
            
            return structure
        except Exception:
            return {"type": "bookmark", "has_url": False}
    
    def _extract_url(self) -> str:
        """
        Extract URL from different bookmark formats.
        Supports: .url (Windows), .webloc (macOS), .txt files
        """
        try:
            with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check for .url format (Windows InternetShortcut)
            # Format: [InternetShortcut]
            #         URL=http://example.com
            url_match = re.search(r'URL=(.+?)(?:\r?\n|$)', content)
            if url_match:
                return url_match.group(1).strip()
            
            # Check for .webloc format (macOS plist)
            # Look for URL= pattern in plist
            url_match = re.search(r'URL</key>\s*<string>(.+?)</string>', content)
            if url_match:
                return url_match.group(1).strip()
            
            # Check for plain URL in text
            url = self._extract_url_from_text(content)
            if url:
                return url
            
            return ""
        except Exception:
            return ""
    
    def _extract_url_from_text(self, text: str) -> str:
        """Extract URL from plain text."""
        # Match http(s):// URLs
        url_match = re.search(r'https?://[^\s\n\r<>"{}|\\^`\[\]]+', text)
        if url_match:
            return url_match.group(0)
        return ""
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            # Remove protocol
            domain = url.replace('https://', '').replace('http://', '')
            # Remove path
            domain = domain.split('/')[0]
            return domain
        except Exception:
            return ""
