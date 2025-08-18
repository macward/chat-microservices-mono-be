"""
Authentication middleware for JWT token validation with Auth Service integration.

This middleware handles JWT token extraction, validation with Auth Service,
and user context injection into requests.
"""

import logging
from typing import Optional, Callable
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.external_clients import auth_client
from app.api.exceptions import SecurityException, ExternalServiceException, ErrorCode

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class AuthContext:
    """Container for authenticated user context."""
    
    def __init__(self, user_id: str, user_data: dict):
        self.user_id = user_id
        self.user_data = user_data
        self.permissions = user_data.get("permissions", [])
        self.roles = user_data.get("roles", [])
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role."""
        return role in self.roles


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication using Auth Service.
    
    This middleware:
    1. Extracts JWT token from Authorization header
    2. Validates token with Auth Service
    3. Injects user context into request state
    4. Handles authentication errors gracefully
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/docs", 
            "/redoc",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable):
        """Process request through authentication pipeline."""
        
        # Skip authentication for excluded paths
        if self._should_skip_auth(request.url.path):
            return await call_next(request)
        
        try:
            # Extract and validate token
            auth_context = await self._authenticate_request(request)
            
            # Inject user context into request state
            request.state.auth = auth_context
            request.state.user_id = auth_context.user_id
            
            # Log successful authentication
            logger.debug(
                f"User authenticated: {auth_context.user_id[:8]}...",
                extra={
                    "user_id": auth_context.user_id[:8] + "...",
                    "path": request.url.path,
                    "method": request.method,
                    "ip": request.client.host if request.client else "unknown"
                }
            )
            
        except SecurityException as e:
            logger.warning(
                f"Authentication failed: {e.message}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "ip": request.client.host if request.client else "unknown",
                    "error_code": e.error_code
                }
            )
            raise HTTPException(
                status_code=e.status_code,
                detail=e.detail
            )
        
        except ExternalServiceException as e:
            logger.error(
                f"Auth service error: {e.message}",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "ip": request.client.host if request.client else "unknown",
                    "service": e.details.get("service_name")
                }
            )
            # Return 503 for external service failures
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "Authentication service temporarily unavailable"
                    }
                }
            )
        
        return await call_next(request)
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if path should skip authentication."""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def _authenticate_request(self, request: Request) -> AuthContext:
        """
        Extract and validate JWT token from request.
        
        Returns:
            AuthContext: Authenticated user context
            
        Raises:
            SecurityException: If authentication fails
            ExternalServiceException: If auth service is unavailable
        """
        # Extract Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise SecurityException(
                "Authorization header is required",
                ErrorCode.AUTHENTICATION_REQUIRED
            )
        
        # Parse Bearer token
        if not auth_header.startswith("Bearer "):
            raise SecurityException(
                "Invalid authorization header format",
                ErrorCode.INVALID_TOKEN
            )
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        if not token.strip():
            raise SecurityException(
                "Token is required",
                ErrorCode.INVALID_TOKEN
            )
        
        # Validate token with Auth Service
        try:
            user_data = await auth_client.validate_token(token)
            
            # Create auth context
            return AuthContext(
                user_id=user_data["user_id"],
                user_data=user_data
            )
            
        except SecurityException:
            # Re-raise security exceptions as-is
            raise
        except ExternalServiceException:
            # Re-raise service exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected authentication error: {e}")
            raise SecurityException(
                "Authentication failed",
                ErrorCode.INVALID_TOKEN
            )


async def get_current_user(request: Request) -> AuthContext:
    """
    Dependency function to get current authenticated user.
    
    Args:
        request: FastAPI request object
        
    Returns:
        AuthContext: Current user context
        
    Raises:
        HTTPException: If user is not authenticated
    """
    auth_context = getattr(request.state, "auth", None)
    if not auth_context:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "AUTHENTICATION_REQUIRED",
                    "message": "Authentication is required"
                }
            }
        )
    
    return auth_context


async def get_current_user_id(request: Request) -> str:
    """
    Dependency function to get current user ID.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Current user ID
        
    Raises:
        HTTPException: If user is not authenticated
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "AUTHENTICATION_REQUIRED", 
                    "message": "Authentication is required"
                }
            }
        )
    
    return user_id


def require_permission(permission: str):
    """
    Dependency factory for permission-based authorization.
    
    Args:
        permission: Required permission string
        
    Returns:
        Dependency function that checks permission
    """
    async def permission_dependency(request: Request):
        auth_context = await get_current_user(request)
        
        if not auth_context.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": f"Permission '{permission}' is required"
                    }
                }
            )
        
        return auth_context
    
    return permission_dependency


def require_role(role: str):
    """
    Dependency factory for role-based authorization.
    
    Args:
        role: Required role string
        
    Returns:
        Dependency function that checks role
    """
    async def role_dependency(request: Request):
        auth_context = await get_current_user(request)
        
        if not auth_context.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_PERMISSIONS",
                        "message": f"Role '{role}' is required"
                    }
                }
            )
        
        return auth_context
    
    return role_dependency