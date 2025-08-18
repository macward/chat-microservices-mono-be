"""
Custom Exception Classes for FastAPI Character Chat API

Production-grade exception hierarchy following OWASP security guidelines and ASVS Level 2 requirements.
Implements security-conscious error handling with proper classification, audit logging, and sanitized error messages.

Security Features:
- No sensitive data exposure in error messages
- Consistent error response format across all endpoints
- Proper HTTP status code mapping
- Security-focused audit logging
- Rate limiting error response capability
- Request context tracking for security monitoring

Exception Hierarchy:
- BaseAppException: Root exception with common security features
- Domain-specific exceptions: AuthenticationError, ValidationError, etc.
- Service-specific exceptions: UserServiceError, ConversationServiceError, etc.

Usage:
    # In services - raise domain-specific exceptions
    raise AuthenticationError("Invalid credentials")
    raise ValidationError("Invalid email format", field="email")
    raise NotFoundError("User", user_id)
    
    # Global handlers will catch and convert to proper HTTP responses
    # with sanitized error messages and security logging
"""

import logging
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum


logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for security monitoring and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification and monitoring."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    RATE_LIMIT = "rate_limit"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    INTERNAL = "internal"
    SECURITY = "security"


class BaseAppException(Exception):
    """
    Base exception for all application errors.
    
    Provides consistent error handling with security-focused features:
    - Sanitized error messages for client responses
    - Detailed logging for security monitoring
    - Proper HTTP status code mapping
    - Request context tracking
    - Severity classification for alerting
    
    Security Considerations:
    - Never exposes sensitive data in user-facing messages
    - Logs detailed information for audit trails
    - Supports rate limiting for repeated errors
    - Tracks error patterns for security monitoring
    """
    
    def __init__(
        self,
        message: str,
        *,
        error_code: str = "APP_ERROR_001",
        status_code: int = 500,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        user_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        log_security_event: bool = False,
        include_traceback: bool = False
    ):
        """
        Initialize base application exception.
        
        Args:
            message: Internal error message for logging (may contain sensitive data)
            error_code: Unique error code for tracking and documentation
            status_code: HTTP status code for the error response
            severity: Error severity level for monitoring and alerting
            category: Error category for classification
            user_message: Sanitized message safe for client response
            details: Additional error details for logging (not sent to client)
            log_security_event: Whether to log this as a security event
            include_traceback: Whether to include traceback in logs
        """
        super().__init__(message)
        
        self.internal_message = message
        # Provide message property for backward compatibility
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.severity = severity
        self.category = category
        self.user_message = user_message or "An error occurred while processing your request"
        self.details = details or {}
        self.log_security_event = log_security_event
        self.include_traceback = include_traceback
        
        # Generate unique error ID for tracking
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.now(timezone.utc)
        
        # Add error context
        self.details.update({
            "error_id": self.error_id,
            "timestamp": self.timestamp.isoformat(),
            "error_type": self.__class__.__name__,
            "severity": self.severity.value,
            "category": self.category.value
        })
        
        # Log the exception immediately for audit trail
        self._log_exception()
    
    def _log_exception(self):
        """Log exception with appropriate level and security context."""
        log_data = {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "error_type": self.__class__.__name__,
            "status_code": self.status_code,
            "severity": self.severity.value,
            "category": self.category.value,
            "error_message": self.internal_message,
            "details": self.details
        }
        
        # Include traceback if requested
        if self.include_traceback:
            log_data["traceback"] = traceback.format_exc()
        
        # Log based on severity
        if self.severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {self.internal_message}", extra=log_data)
        elif self.severity == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {self.internal_message}", extra=log_data)
        elif self.severity == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {self.internal_message}", extra=log_data)
        else:
            logger.info(f"Low severity error: {self.internal_message}", extra=log_data)
        
        # Log security events separately for monitoring
        if self.log_security_event:
            security_logger = logging.getLogger("security")
            security_logger.warning(
                f"Security event: {self.category.value} - {self.message}",
                extra={**log_data, "security_event": True}
            )
    
    def to_dict(self, include_internal_details: bool = False) -> Dict[str, Any]:
        """
        Convert exception to dictionary for API response.
        
        Args:
            include_internal_details: Whether to include internal details (for debugging)
            
        Returns:
            Dict containing sanitized error information for client response
        """
        result = {
            "error": {
                "message": self.user_message,
                "code": self.error_code,
                "type": self.__class__.__name__,
                "error_id": self.error_id,
                "timestamp": self.timestamp.isoformat()
            }
        }
        
        # Include internal details only if explicitly requested (dev mode)
        if include_internal_details:
            result["error"]["internal_message"] = self.internal_message
            result["error"]["details"] = self.details
            result["error"]["severity"] = self.severity.value
            result["error"]["category"] = self.category.value
        
        return result


# ============================================================================
# AUTHENTICATION & AUTHORIZATION EXCEPTIONS
# ============================================================================

class AuthenticationError(BaseAppException):
    """
    Exception for authentication failures.
    
    Used when user credentials are invalid, tokens are expired/invalid,
    or authentication is required but not provided.
    
    Security Features:
    - Generic error messages to prevent user enumeration
    - Automatic security event logging
    - Support for rate limiting on repeated failures
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        *,
        error_code: str = "AUTH_001",
        user_message: str = "Invalid credentials",
        auth_method: Optional[str] = None,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        details = {
            "auth_method": auth_method,
            "user_id": user_id,
            "ip_address": ip_address
        }
        
        super().__init__(
            message,
            error_code=error_code,
            status_code=401,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHENTICATION,
            user_message=user_message,
            details=details,
            log_security_event=True
        )


class AuthorizationError(BaseAppException):
    """
    Exception for authorization failures.
    
    Used when authenticated user lacks permission to access a resource
    or perform an action.
    """
    
    def __init__(
        self,
        message: str = "Access denied",
        *,
        error_code: str = "AUTH_002",
        user_message: str = "You don't have permission to access this resource",
        resource: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        details = {
            "resource": resource,
            "action": action,
            "user_id": user_id
        }
        
        super().__init__(
            message,
            error_code=error_code,
            status_code=403,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHORIZATION,
            user_message=user_message,
            details=details,
            log_security_event=True
        )


class TokenError(AuthenticationError):
    """Exception for JWT token-related errors."""
    
    def __init__(
        self,
        message: str = "Invalid or expired token",
        *,
        error_code: str = "AUTH_003",
        token_type: Optional[str] = None
    ):
        details = {"token_type": token_type}
        
        super().__init__(
            message,
            error_code=error_code,
            user_message="Invalid or expired authentication token",
            auth_method="jwt",
            details=details
        )


# ============================================================================
# VALIDATION EXCEPTIONS
# ============================================================================

class ValidationError(BaseAppException):
    """
    Exception for input validation errors.
    
    Used when user input doesn't meet validation requirements,
    has invalid format, or contains malicious content.
    """
    
    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        value: Optional[str] = None,
        error_code: str = "VALIDATION_001",
        validation_type: Optional[str] = None
    ):
        # Sanitize sensitive values for logging
        safe_value = "[REDACTED]" if value and len(value) > 50 else value
        
        details = {
            "field": field,
            "validation_type": validation_type,
            "value_provided": bool(value),
            "value_length": len(value) if value else 0
        }
        
        # Create user-friendly message
        if field:
            user_message = f"Invalid value for field '{field}': {message}"
        else:
            user_message = f"Validation error: {message}"
        
        super().__init__(
            f"Validation failed for field '{field}': {message} (value: {safe_value})",
            error_code=error_code,
            status_code=422,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            user_message=user_message,
            details=details
        )


class SecurityValidationError(ValidationError):
    """
    Exception for security-related validation failures.
    
    Used when input validation fails due to security concerns
    (e.g., potential injection attempts, malicious content).
    """
    
    def __init__(
        self,
        message: str,
        *,
        field: Optional[str] = None,
        error_code: str = "VALIDATION_002",
        security_rule: Optional[str] = None
    ):
        details = {"security_rule": security_rule}
        
        super().__init__(
            message,
            field=field,
            error_code=error_code,
            validation_type="security",
            details=details
        )
        
        # Override base settings for security validation
        self.severity = ErrorSeverity.HIGH
        self.log_security_event = True
        self.user_message = "Input validation failed for security reasons"


# ============================================================================
# RESOURCE EXCEPTIONS
# ============================================================================

class NotFoundError(BaseAppException):
    """
    Exception for resource not found errors.
    
    Used when requested resource doesn't exist or user doesn't have
    permission to view it (prevent information disclosure).
    """
    
    def __init__(
        self,
        resource: str,
        identifier: Optional[str] = None,
        *,
        error_code: str = "NOT_FOUND_001",
        user_message: Optional[str] = None
    ):
        # Sanitize identifier to prevent information disclosure
        safe_identifier = identifier[:8] + "..." if identifier and len(identifier) > 8 else identifier
        
        internal_message = f"{resource} not found"
        if identifier:
            internal_message = f"{resource} with id '{identifier}' not found"
        
        # Generic user message to prevent enumeration
        if not user_message:
            user_message = f"The requested {resource.lower()} was not found"
        
        details = {
            "resource_type": resource,
            "identifier_provided": bool(identifier),
            "identifier_length": len(identifier) if identifier else 0
        }
        
        super().__init__(
            internal_message,
            error_code=error_code,
            status_code=404,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.NOT_FOUND,
            user_message=user_message,
            details=details
        )


class ConflictError(BaseAppException):
    """
    Exception for resource conflict errors.
    
    Used when operation cannot be completed due to resource state
    or uniqueness constraints.
    """
    
    def __init__(
        self,
        message: str,
        *,
        resource: Optional[str] = None,
        error_code: str = "CONFLICT_001",
        conflict_type: Optional[str] = None
    ):
        details = {
            "resource_type": resource,
            "conflict_type": conflict_type
        }
        
        super().__init__(
            message,
            error_code=error_code,
            status_code=409,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.CONFLICT,
            user_message=message,  # Usually safe to show conflict messages
            details=details
        )


# ============================================================================
# RATE LIMITING EXCEPTIONS
# ============================================================================

class RateLimitError(BaseAppException):
    """
    Exception for rate limit violations.
    
    Used when user exceeds allowed request rate for API protection
    and abuse prevention.
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        retry_after: Optional[int] = None,
        error_code: str = "RATE_LIMIT_001",
        limit_type: Optional[str] = None
    ):
        details = {
            "limit": limit,
            "window_seconds": window,
            "retry_after_seconds": retry_after,
            "limit_type": limit_type
        }
        
        user_message = "Rate limit exceeded. Please try again later."
        if retry_after:
            user_message = f"Rate limit exceeded. Please try again in {retry_after} seconds."
        
        super().__init__(
            message,
            error_code=error_code,
            status_code=429,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.RATE_LIMIT,
            user_message=user_message,
            details=details,
            log_security_event=True  # Rate limit violations are security events
        )


# ============================================================================
# SERVICE-SPECIFIC EXCEPTIONS
# ============================================================================

class UserServiceError(BaseAppException):
    """Exception for user service operations."""
    
    def __init__(
        self,
        message: str,
        *,
        error_code: str = "USER_SERVICE_001",
        operation: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        details = {
            "service": "user",
            "operation": operation,
            "user_id": user_id
        }
        
        super().__init__(
            message,
            error_code=error_code,
            status_code=500,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.BUSINESS_LOGIC,
            user_message="User service is temporarily unavailable",
            details=details,
            include_traceback=True
        )


class ConversationServiceError(BaseAppException):
    """Exception for conversation service operations."""
    
    def __init__(
        self,
        message: str,
        *,
        error_code: str = "CONVERSATION_SERVICE_001",
        operation: Optional[str] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        details = {
            "service": "conversation",
            "operation": operation,
            "conversation_id": conversation_id,
            "user_id": user_id
        }
        
        super().__init__(
            message,
            error_code=error_code,
            status_code=500,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.BUSINESS_LOGIC,
            user_message="Conversation service is temporarily unavailable",
            details=details,
            include_traceback=True
        )


class CharacterServiceError(BaseAppException):
    """Exception for character service operations."""
    
    def __init__(
        self,
        message: str,
        *,
        error_code: str = "CHARACTER_SERVICE_001",
        operation: Optional[str] = None,
        character_name: Optional[str] = None
    ):
        details = {
            "service": "character",
            "operation": operation,
            "character_name": character_name
        }
        
        super().__init__(
            message,
            error_code=error_code,
            status_code=500,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.BUSINESS_LOGIC,
            user_message="Character service is temporarily unavailable",
            details=details,
            include_traceback=True
        )


class ExternalServiceError(BaseAppException):
    """Exception for external service failures."""
    
    def __init__(
        self,
        message: str,
        *,
        service_name: str,
        error_code: str = "EXTERNAL_SERVICE_001",
        operation: Optional[str] = None,
        status_code: int = 503
    ):
        details = {
            "external_service": service_name,
            "operation": operation
        }
        
        super().__init__(
            message,
            error_code=error_code,
            status_code=status_code,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.EXTERNAL_SERVICE,
            user_message=f"{service_name} service is temporarily unavailable",
            details=details,
            include_traceback=True
        )


# ============================================================================
# SPECIALIZED DOMAIN EXCEPTIONS
# ============================================================================

class MessageSendingError(ConversationServiceError):
    """Exception for message sending failures."""
    
    def __init__(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        llm_error: bool = False
    ):
        error_code = "MESSAGE_SEND_002" if llm_error else "MESSAGE_SEND_001"
        user_message = "Failed to send message. Please try again."
        
        super().__init__(
            message,
            error_code=error_code,
            operation="send_message",
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        self.user_message = user_message
        if llm_error:
            self.details["llm_error"] = True


class ConversationStateError(ConversationServiceError):
    """Exception for invalid conversation state transitions."""
    
    def __init__(
        self,
        message: str,
        *,
        conversation_id: Optional[str] = None,
        current_state: Optional[str] = None,
        attempted_action: Optional[str] = None
    ):
        details = {
            "current_state": current_state,
            "attempted_action": attempted_action
        }
        
        super().__init__(
            message,
            error_code="CONVERSATION_STATE_001",
            operation="state_transition",
            conversation_id=conversation_id
        )
        
        self.status_code = 422  # Override to use 422 for state errors
        self.user_message = "Invalid operation for current conversation state"
        self.details.update(details)


# ============================================================================
# ERROR UTILITIES
# ============================================================================

def create_error_response(
    exception: BaseAppException,
    request_path: Optional[str] = None,
    request_id: Optional[str] = None,
    include_debug_info: bool = False
) -> Dict[str, Any]:
    """
    Create standardized error response from exception.
    
    Args:
        exception: The BaseAppException instance
        request_path: The request path for context
        request_id: Unique request ID for tracking
        include_debug_info: Whether to include debug information
        
    Returns:
        Standardized error response dictionary
    """
    response = exception.to_dict(include_internal_details=include_debug_info)
    
    # Add request context
    if request_path:
        response["error"]["path"] = request_path
    
    if request_id:
        response["error"]["request_id"] = request_id
    
    return response


def log_unhandled_exception(
    exc: Exception,
    request_path: Optional[str] = None,
    user_id: Optional[str] = None
) -> str:
    """
    Log unhandled exception and return error ID for tracking.
    
    Args:
        exc: The unhandled exception
        request_path: Request path where error occurred
        user_id: User ID if available
        
    Returns:
        Error ID for client tracking
    """
    error_id = str(uuid.uuid4())
    
    log_data = {
        "error_id": error_id,
        "error_type": type(exc).__name__,
        "message": str(exc),
        "request_path": request_path,
        "user_id": user_id,
        "traceback": traceback.format_exc()
    }
    
    logger.critical(f"Unhandled exception: {str(exc)}", extra=log_data)
    
    # Also log as security event for monitoring
    security_logger = logging.getLogger("security")
    security_logger.error(
        f"Unhandled exception in application: {type(exc).__name__}",
        extra={**log_data, "security_event": True}
    )
    
    return error_id