"""
Rate limiting for authentication endpoints.
Uses in-memory store (can be replaced with Redis for production).
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, Optional
from fastapi import HTTPException, status
from collections import defaultdict
import threading


class RateLimiter:
    """Rate limiter using token bucket algorithm.
    
    For production, replace with Redis-based implementation.
    """
    
    def __init__(self):
        self.attempts: Dict[str, list[datetime]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_rate_limited(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int
    ) -> bool:
        """Check if a key is rate limited.
        
        Args:
            key: Rate limit key (e.g., IP address, email)
            max_attempts: Maximum attempts in window
            window_seconds: Time window in seconds
            
        Returns:
            True if rate limited, False otherwise
        """
        with self.lock:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=window_seconds)
            
            # Clean old attempts
            self.attempts[key] = [
                attempt for attempt in self.attempts[key]
                if attempt > window_start
            ]
            
            # Check if rate limited
            if len(self.attempts[key]) >= max_attempts:
                return True
            
            # Record this attempt
            self.attempts[key].append(now)
            return False
    
    def get_remaining_attempts(
        self,
        key: str,
        max_attempts: int,
        window_seconds: int
    ) -> int:
        """Get remaining attempts for a key.
        
        Args:
            key: Rate limit key
            max_attempts: Maximum attempts in window
            window_seconds: Time window in seconds
            
        Returns:
            Number of remaining attempts
        """
        with self.lock:
            now = datetime.now(timezone.utc)
            window_start = now - timedelta(seconds=window_seconds)
            
            # Count recent attempts
            recent_attempts = [
                attempt for attempt in self.attempts[key]
                if attempt > window_start
            ]
            
            return max(0, max_attempts - len(recent_attempts))
    
    def reset_key(self, key: str) -> None:
        """Reset rate limit for a key.
        
        Args:
            key: Rate limit key to reset
        """
        with self.lock:
            if key in self.attempts:
                del self.attempts[key]


# Rate limit configurations
class RateLimitConfig:
    """Rate limit configuration for different operations."""
    
    # Login attempts: 5 per 15 minutes per IP
    LOGIN_ATTEMPTS = 5
    LOGIN_WINDOW = 15 * 60  # 15 minutes
    
    # Registration: 3 per hour per IP (prevents spam)
    REGISTER_ATTEMPTS = 3
    REGISTER_WINDOW = 60 * 60  # 1 hour
    
    # Token refresh: 10 per minute per user (normal: ~0.5/min max)
    REFRESH_ATTEMPTS = 10
    REFRESH_WINDOW = 60  # 1 minute
    
    # Password reset: 3 per hour per email
    PASSWORD_RESET_ATTEMPTS = 3
    PASSWORD_RESET_WINDOW = 60 * 60  # 1 hour


# Global rate limiter instance
_rate_limiter = RateLimiter()


def check_rate_limit(
    key: str,
    operation: str = "default",
) -> None:
    """Check rate limit and raise exception if exceeded.
    
    Args:
        key: Rate limit key (usually IP or user ID)
        operation: Operation type (login, register, etc.)
        
    Raises:
        HTTPException: 429 Too Many Requests if rate limited
    """
    config_map = {
        "login": (RateLimitConfig.LOGIN_ATTEMPTS, RateLimitConfig.LOGIN_WINDOW),
        "register": (RateLimitConfig.REGISTER_ATTEMPTS, RateLimitConfig.REGISTER_WINDOW),
        "refresh": (RateLimitConfig.REFRESH_ATTEMPTS, RateLimitConfig.REFRESH_WINDOW),
        "password_reset": (RateLimitConfig.PASSWORD_RESET_ATTEMPTS, RateLimitConfig.PASSWORD_RESET_WINDOW),
    }
    
    max_attempts, window = config_map.get(operation, (10, 60))
    
    if _rate_limiter.is_rate_limited(key, max_attempts, window):
        remaining_window = RateLimitConfig.LOGIN_WINDOW  # For error message
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many {operation} attempts. Try again in {remaining_window // 60} minutes.",
            headers={"Retry-After": str(remaining_window)}
        )


def get_remaining_attempts(
    key: str,
    operation: str = "default",
) -> int:
    """Get remaining attempts before rate limit.
    
    Args:
        key: Rate limit key
        operation: Operation type
        
    Returns:
        Number of remaining attempts
    """
    config_map = {
        "login": (RateLimitConfig.LOGIN_ATTEMPTS, RateLimitConfig.LOGIN_WINDOW),
        "register": (RateLimitConfig.REGISTER_ATTEMPTS, RateLimitConfig.REGISTER_WINDOW),
        "refresh": (RateLimitConfig.REFRESH_ATTEMPTS, RateLimitConfig.REFRESH_WINDOW),
        "password_reset": (RateLimitConfig.PASSWORD_RESET_ATTEMPTS, RateLimitConfig.PASSWORD_RESET_WINDOW),
    }
    
    max_attempts, window = config_map.get(operation, (10, 60))
    return _rate_limiter.get_remaining_attempts(key, max_attempts, window)


def reset_rate_limit(key: str) -> None:
    """Reset rate limit for a key (e.g., after successful login).
    
    Args:
        key: Rate limit key to reset
    """
    _rate_limiter.reset_key(key)
