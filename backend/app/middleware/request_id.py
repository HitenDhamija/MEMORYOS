"""
Request ID middleware for request tracing and correlation.
"""

import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests and responses.
    
    This enables correlation of logs across services and helps with debugging
    and security incident investigation.
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add request ID to request and response.
        
        Args:
            request: FastAPI request
            call_next: Next middleware/handler
            
        Returns:
            Response with request ID header
        """
        # Get request ID from header or generate new one
        request_id = request.headers.get(REQUEST_ID_HEADER)
        if not request_id:
            request_id = str(uuid.uuid4())
        
        # Store request ID in request state for use in handlers
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response header
        response.headers[REQUEST_ID_HEADER] = request_id
        
        return response


def get_request_id(request: Request) -> str:
    """Get request ID from request state.
    
    Args:
        request: FastAPI request
        
    Returns:
        Request ID string
    """
    return getattr(request.state, "request_id", "unknown")
