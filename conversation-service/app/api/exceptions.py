"""
Custom exceptions and error handling for the conversation service.

This module provides security-focused exception handling with proper error
categorization and sanitized error responses to prevent information leakage.
"""

from fastapi import HTTPException, status
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging

# Set up security logger
security_logger = logging.getLogger("security")


class ErrorCode(str, Enum):
    """Enumeration of standardized error codes for security tracking."""
    
    # Validation Errors (4xx)
    VALIDATION_ERROR = "VALIDATION_001"
    INVALID_INPUT_FORMAT = "VALIDATION_002"
    FIELD_REQUIRED = "VALIDATION_003"
    FIELD_TOO_LONG = "VALIDATION_004"
    FIELD_TOO_SHORT = "VALIDATION_005"
    INVALID_CHARACTER_SET = "VALIDATION_006"
    DANGEROUS_CONTENT = "VALIDATION_007"
    
    # Authentication/Authorization Errors (4xx)
    UNAUTHORIZED = "AUTH_001"
    FORBIDDEN = "AUTH_002"
    INVALID_TOKEN = "AUTH_003"
    TOKEN_EXPIRED = "AUTH_004"
    AUTHENTICATION_REQUIRED = "AUTH_005"
    INSUFFICIENT_PERMISSIONS = "AUTH_006"
    
    # Resource Errors (4xx)
    NOT_FOUND = "RESOURCE_001"
    ALREADY_EXISTS = "RESOURCE_002"
    CONFLICT = "RESOURCE_003"
    
    # Business Logic Errors (4xx)
    BUSINESS_RULE_VIOLATION = "BUSINESS_001"
    QUOTA_EXCEEDED = "BUSINESS_002"
    INVALID_STATE_TRANSITION = "BUSINESS_003"
    
    # Server Errors (5xx)
    INTERNAL_ERROR = "SERVER_001"
    DATABASE_ERROR = "SERVER_002"
    EXTERNAL_SERVICE_ERROR = "SERVER_003"
    SERVICE_UNAVAILABLE = "SERVER_004"
    SERVICE_TIMEOUT = "SERVER_005"
    INVALID_RESPONSE_FORMAT = "SERVER_006"
    
    # Security Errors (4xx/5xx)
    RATE_LIMIT_EXCEEDED = "SECURITY_001"
    SUSPICIOUS_ACTIVITY = "SECURITY_002"
    INJECTION_ATTEMPT = "SECURITY_003"


class BaseConversationException(HTTPException):
    """Base exception class for conversation service with security logging."""
    
    def __init__(
        self,
        status_code: int,
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        log_level: str = "WARNING"
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        
        # Security logging
        security_logger.log(
            getattr(logging, log_level.upper()),
            f"Exception raised: {error_code} - {message}",
            extra={
                "error_code": error_code,
                "status_code": status_code,
                "details": self._sanitize_details(details),
                "timestamp": self.timestamp.isoformat()
            }
        )
        
        super().__init__(
            status_code=status_code,
            detail=self._create_error_response()
        )
    
    def _sanitize_details(self, details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Sanitize error details to prevent information leakage."""
        if not details:
            return {}
        
        # Remove sensitive keys
        sensitive_keys = {'password', 'token', 'secret', 'key', 'auth', 'session'}
        sanitized = {}
        
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 100:
                sanitized[key] = value[:97] + "..."
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _create_error_response(self) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self._sanitize_details(self.details),
                "timestamp": self.timestamp.isoformat()
            }
        }


class ValidationException(BaseConversationException):
    """Exception for input validation errors."""
    
    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[str] = None,
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR
    ):
        details = {}
        if field:
            details["field"] = field
        if value:
            # Truncate long values for security
            details["value"] = value[:50] + "..." if len(str(value)) > 50 else str(value)
        
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code,
            message=message,
            details=details,
            log_level="INFO"  # Validation errors are expected
        )


class SecurityException(BaseConversationException):
    """Exception for security-related issues."""
    
    def __init__(
        self,
        message: str = "Security violation detected",
        error_code: ErrorCode = ErrorCode.SUSPICIOUS_ACTIVITY,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            message=message,
            details=details,
            log_level="ERROR"  # Security issues are serious
        )


class BusinessLogicException(BaseConversationException):
    """Exception for business rule violations."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.BUSINESS_RULE_VIOLATION,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            error_code=error_code,
            message=message,
            details=details,
            log_level="INFO"
        )


class ResourceNotFoundException(BaseConversationException):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None
    ):
        message = f"{resource_type} not found"
        details = {}
        if resource_id:
            # Only log first few characters of ID for security
            safe_id = resource_id[:8] + "..." if len(resource_id) > 8 else resource_id
            details["resource_id"] = safe_id
        
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=ErrorCode.NOT_FOUND,
            message=message,
            details=details,
            log_level="INFO"
        )


class QuotaExceededException(BaseConversationException):
    """Exception for quota/rate limit violations."""
    
    def __init__(
        self,
        quota_type: str,
        current_value: int,
        max_allowed: int
    ):
        message = f"{quota_type} quota exceeded"
        details = {
            "quota_type": quota_type,
            "current": current_value,
            "maximum": max_allowed
        }
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=ErrorCode.QUOTA_EXCEEDED,
            message=message,
            details=details,
            log_level="WARNING"
        )


class DatabaseException(BaseConversationException):
    """Exception for database-related errors."""
    
    def __init__(
        self,
        operation: str,
        original_error: Optional[str] = None
    ):
        message = f"Database operation failed: {operation}"
        details = {}
        if original_error:
            # Sanitize database errors to prevent information leakage
            details["error_type"] = type(original_error).__name__ if hasattr(original_error, '__name__') else "DatabaseError"
        
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=ErrorCode.DATABASE_ERROR,
            message=message,
            details=details,
            log_level="ERROR"
        )


def create_validation_error_response(
    field_errors: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Create a standardized response for Pydantic validation errors.
    
    Args:
        field_errors: List of field validation errors from Pydantic
        
    Returns:
        Standardized error response dictionary
    """
    # Sanitize field errors to prevent information leakage
    sanitized_errors = []
    for error in field_errors:
        sanitized_error = {
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "validation_error")
        }
        
        # Include input value only if it's safe to expose
        input_value = error.get("input")
        if input_value is not None:
            if isinstance(input_value, str) and len(input_value) <= 50:
                sanitized_error["input"] = input_value
            elif not isinstance(input_value, str):
                sanitized_error["input"] = str(input_value)[:50]
        
        sanitized_errors.append(sanitized_error)
    
    return {
        "error": {
            "code": ErrorCode.VALIDATION_ERROR,
            "message": "Input validation failed",
            "details": {
                "field_errors": sanitized_errors
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    }


def log_security_event(
    event_type: str,
    description: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
):
    """
    Log security events for monitoring and analysis.
    
    Args:
        event_type: Type of security event
        description: Human-readable description
        user_id: User identifier (if available)
        ip_address: Source IP address (if available)
        additional_data: Additional context data
    """
    security_logger.warning(
        f"Security event: {event_type} - {description}",
        extra={
            "event_type": event_type,
            "description": description,
            "user_id": user_id[:8] + "..." if user_id and len(user_id) > 8 else user_id,
            "ip_address": ip_address,
            "additional_data": additional_data or {},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


class ExternalServiceException(BaseConversationException):
    """Exception for external service integration errors."""
    
    def __init__(
        self,
        message: str,
        service_name: str,
        error_code: ErrorCode = ErrorCode.EXTERNAL_SERVICE_ERROR,
        status_code: Optional[int] = None,
        response_data: Optional[str] = None
    ):
        details = {
            "service_name": service_name
        }
        if status_code:
            details["service_status_code"] = status_code
        if response_data:
            # Truncate response data for security
            details["response_sample"] = response_data[:100] + "..." if len(response_data) > 100 else response_data
        
        # Determine HTTP status code based on error type
        http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        if error_code in [ErrorCode.SERVICE_UNAVAILABLE, ErrorCode.SERVICE_TIMEOUT]:
            http_status = status.HTTP_503_SERVICE_UNAVAILABLE
        
        super().__init__(
            status_code=http_status,
            error_code=error_code,
            message=message,
            details=details,
            log_level="ERROR"
        )