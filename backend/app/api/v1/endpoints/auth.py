"""
Authentication endpoints with CSRF protection, rate limiting, and logging.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.schemas import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    AccessTokenResponse,
    RefreshTokenRequest,
)
from app.models.models import User
from app.services.auth_service import AuthService
from app.api.deps import get_refresh_token_user
from app.utils.csrf import CSRFTokenGenerator, validate_csrf_token
from app.utils.rate_limit import check_rate_limit, reset_rate_limit
from app.utils.logging import security_logger, SecurityEventType, LogLevel
from app.middleware.request_id import get_request_id

router = APIRouter(prefix="/auth", tags=["auth"])


def get_client_ip(request: Request) -> str:
    """Extract client IP from request.
    
    Checks X-Forwarded-For (from proxies) before using direct connection.
    """
    if "x-forwarded-for" in request.headers:
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
) -> User:
    """Register a new user with CSRF and rate limiting.
    
    Rate limited to prevent registration spam.
    Returns CSRF token in response for use in subsequent requests.
    """
    client_ip = get_client_ip(request)
    request_id = get_request_id(request)
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Check rate limit
    try:
        check_rate_limit(client_ip, operation="register")
    except HTTPException as e:
        security_logger.log_suspicious_activity(
            activity_type="registration_rate_limit",
            user_id=None,
            request_id=request_id,
            ip_address=client_ip,
            details={"email": user_data.email}
        )
        raise
    
    try:
        user = AuthService.register(db, user_data)
        
        security_logger.log_security_event(
            event_type=SecurityEventType.USER_REGISTERED,
            user_id=user.id,
            request_id=request_id,
            ip_address=client_ip,
            user_agent=user_agent,
            details={"email": user.email, "username": user.username}
        )
        
        # Generate and set CSRF token for next request
        csrf_token = CSRFTokenGenerator.generate_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            max_age=3600,  # 1 hour
            secure=True,
            httponly=False,  # JavaScript needs to read it
            samesite="strict"
        )
        
        return user
    except HTTPException:
        security_logger.log_suspicious_activity(
            activity_type="registration_failed",
            request_id=request_id,
            ip_address=client_ip,
            details={"email": user_data.email}
        )
        raise


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Login user with CSRF and rate limiting.
    
    Rate limited to prevent brute force attacks.
    """
    client_ip = get_client_ip(request)
    request_id = get_request_id(request)
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Check rate limit
    try:
        check_rate_limit(client_ip, operation="login")
    except HTTPException:
        security_logger.log_suspicious_activity(
            activity_type="login_rate_limit",
            request_id=request_id,
            ip_address=client_ip,
            details={"email": credentials.email}
        )
        raise
    
    try:
        user = AuthService.authenticate(db, credentials.email, credentials.password)
        tokens = AuthService.create_tokens(user.id)
        
        # Log successful login
        security_logger.log_auth_attempt(
            email=credentials.email,
            success=True,
            request_id=request_id,
            ip_address=client_ip
        )
        
        # Reset rate limit on successful login
        reset_rate_limit(client_ip)
        
        # Log token issuance
        security_logger.log_token_event(
            event_type=SecurityEventType.TOKEN_ISSUED,
            user_id=user.id,
            token_type="access_and_refresh",
            request_id=request_id,
            ip_address=client_ip
        )
        
        # Generate and set CSRF token
        csrf_token = CSRFTokenGenerator.generate_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            max_age=3600,
            secure=True,
            httponly=False,
            samesite="strict"
        )
        
        return tokens
    except HTTPException as e:
        # Log failed login
        security_logger.log_auth_attempt(
            email=credentials.email,
            success=False,
            request_id=request_id,
            ip_address=client_ip,
            reason=e.detail
        )
        raise


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    request_data: RefreshTokenRequest = Depends(),
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Refresh access token with rate limiting and logging.
    
    Rate limited to detect stolen refresh tokens being abused.
    """
    client_ip = get_client_ip(request)
    request_id = get_request_id(request)
    
    # Check rate limit on refresh endpoint
    try:
        check_rate_limit(client_ip, operation="refresh")
    except HTTPException:
        security_logger.log_suspicious_activity(
            activity_type="token_refresh_rate_limit",
            request_id=request_id,
            ip_address=client_ip
        )
        raise
    
    try:
        user = await get_refresh_token_user(request_data.refresh_token, db)
        tokens = AuthService.refresh_access_token(user.id)
        
        security_logger.log_token_event(
            event_type=SecurityEventType.TOKEN_REFRESHED,
            user_id=user.id,
            token_type="access",
            request_id=request_id,
            ip_address=client_ip
        )
        
        # Generate and set CSRF token
        csrf_token = CSRFTokenGenerator.generate_token()
        response.set_cookie(
            key="csrf_token",
            value=csrf_token,
            max_age=3600,
            secure=True,
            httponly=False,
            samesite="strict"
        )
        
        return tokens
    except HTTPException:
        security_logger.log_suspicious_activity(
            activity_type="token_refresh_failed",
            request_id=request_id,
            ip_address=client_ip
        )
        raise


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    request: Request,
    response: Response,
) -> dict[str, str]:
    """Logout user and clear CSRF token.
    
    Token cleanup happens primarily on client side.
    """
    request_id = get_request_id(request)
    client_ip = get_client_ip(request)
    
    security_logger.log_security_event(
        event_type=SecurityEventType.USER_LOGOUT,
        request_id=request_id,
        ip_address=client_ip,
        severity=LogLevel.INFO
    )
    
    # Clear CSRF token
    response.delete_cookie(
        key="csrf_token",
        secure=True,
        httponly=False,
        samesite="strict"
    )
    
    return {"message": "Successfully logged out. Please remove tokens from client."}


