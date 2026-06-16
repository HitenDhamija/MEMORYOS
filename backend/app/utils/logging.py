"""
Structured logging for security events and debugging.
"""

import logging
import json
from datetime import datetime
from typing import Any, Optional, Dict
from enum import Enum


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SecurityEventType(str, Enum):
    """Security event types for audit trail."""
    USER_REGISTERED = "USER_REGISTERED"
    USER_LOGIN_SUCCESS = "USER_LOGIN_SUCCESS"
    USER_LOGIN_FAILED = "USER_LOGIN_FAILED"
    USER_LOGIN_LOCKED = "USER_LOGIN_LOCKED"  # Too many attempts
    USER_LOGOUT = "USER_LOGOUT"
    USER_PASSWORD_CHANGED = "USER_PASSWORD_CHANGED"
    USER_PASSWORD_RESET = "USER_PASSWORD_RESET"
    USER_EMAIL_VERIFIED = "USER_EMAIL_VERIFIED"
    USER_DEACTIVATED = "USER_DEACTIVATED"
    USER_REACTIVATED = "USER_REACTIVATED"
    
    TOKEN_ISSUED = "TOKEN_ISSUED"
    TOKEN_REFRESHED = "TOKEN_REFRESHED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    
    INVALID_CSRF_TOKEN = "INVALID_CSRF_TOKEN"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    
    UNAUTHORIZED_ACCESS_ATTEMPT = "UNAUTHORIZED_ACCESS_ATTEMPT"
    PERMISSION_DENIED = "PERMISSION_DENIED"


class SecurityLogger:
    """Structured security logging."""
    
    def __init__(self, name: str = "security"):
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger with JSON formatting."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
        severity: LogLevel = LogLevel.INFO,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log a security event with structured data.
        
        Args:
            event_type: Type of security event
            user_id: User ID if applicable
            request_id: Request correlation ID
            severity: Log severity level
            details: Additional context details
            ip_address: Client IP address
            user_agent: Client user agent
        """
        event_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "request_id": request_id,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {}
        }
        
        log_message = json.dumps(event_data)
        
        if severity == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif severity == LogLevel.INFO:
            self.logger.info(log_message)
        elif severity == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif severity == LogLevel.ERROR:
            self.logger.error(log_message)
        elif severity == LogLevel.CRITICAL:
            self.logger.critical(log_message)
    
    def log_auth_attempt(
        self,
        email: str,
        success: bool,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Log authentication attempt.
        
        Args:
            email: User email
            success: Whether authentication succeeded
            request_id: Request correlation ID
            ip_address: Client IP address
            reason: Reason for failure (if applicable)
        """
        event_type = (
            SecurityEventType.USER_LOGIN_SUCCESS 
            if success 
            else SecurityEventType.USER_LOGIN_FAILED
        )
        
        self.log_security_event(
            event_type=event_type,
            request_id=request_id,
            ip_address=ip_address,
            severity=LogLevel.INFO if success else LogLevel.WARNING,
            details={
                "email": email,
                "failure_reason": reason
            }
        )
    
    def log_token_event(
        self,
        event_type: SecurityEventType,
        user_id: int,
        token_type: str,  # "access" or "refresh"
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log token-related events.
        
        Args:
            event_type: Type of token event
            user_id: User ID
            token_type: Token type (access/refresh)
            request_id: Request correlation ID
            ip_address: Client IP address
        """
        self.log_security_event(
            event_type=event_type,
            user_id=user_id,
            request_id=request_id,
            ip_address=ip_address,
            details={
                "token_type": token_type
            }
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        severity: LogLevel = LogLevel.WARNING,
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log suspicious activity for security monitoring.
        
        Args:
            activity_type: Description of suspicious activity
            severity: Log severity
            user_id: User ID if applicable
            request_id: Request correlation ID
            ip_address: Client IP address
            details: Additional context
        """
        self.log_security_event(
            event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
            user_id=user_id,
            request_id=request_id,
            severity=severity,
            ip_address=ip_address,
            details={
                "activity_type": activity_type,
                **(details or {})
            }
        )


# Global security logger instance
security_logger = SecurityLogger()
