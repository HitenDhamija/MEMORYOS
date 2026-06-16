"""
CSRF protection utilities and middleware.
"""

import secrets
from fastapi import HTTPException, status, Request
from typing import Optional

# CSRF token configuration
CSRF_TOKEN_LENGTH = 32
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_NAME = "csrf_token"
CSRF_EXEMPTED_METHODS = {"GET", "HEAD", "OPTIONS"}  # Safe methods don't need CSRF token


class CSRFTokenGenerator:
    """Generate and validate CSRF tokens."""
    
    @staticmethod
    def generate_token() -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)
    
    @staticmethod
    def validate_token(header_token: str, cookie_token: str) -> bool:
        """Validate CSRF token using double-submit cookie pattern.
        
        Args:
            header_token: CSRF token from request header (X-CSRF-Token)
            cookie_token: CSRF token from cookie
            
        Returns:
            True if tokens match, False otherwise
            
        Note:
            Uses constant-time comparison to prevent timing attacks
        """
        if not header_token or not cookie_token:
            return False
        
        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(header_token, cookie_token)


async def validate_csrf_token(request: Request) -> bool:
    """Validate CSRF token in request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        True if valid, raises HTTPException if invalid
        
    Raises:
        HTTPException: 403 Forbidden if CSRF token invalid or missing
    """
    # Skip CSRF validation for safe methods
    if request.method in CSRF_EXEMPTED_METHODS:
        return True
    
    # Get token from header
    header_token = request.headers.get(CSRF_HEADER_NAME)
    if not header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing in X-CSRF-Token header"
        )
    
    # Get token from cookie
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    if not cookie_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token missing in cookie"
        )
    
    # Validate tokens match
    if not CSRFTokenGenerator.validate_token(header_token, cookie_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token"
        )
    
    return True
