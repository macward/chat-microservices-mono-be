"""Custom exceptions for the Message Service."""

from typing import Dict, Any, Optional


class MessageServiceException(Exception):
    """Base exception for Message Service."""
    
    def __init__(
        self, 
        message: str, 
        code: str = "MESSAGE_SERVICE_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(MessageServiceException):
    """Validation error."""
    
    def __init__(self, message: str, field: str = None, details: Dict[str, Any] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={**(details or {}), "field": field}
        )


class NotFoundError(MessageServiceException):
    """Resource not found error."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier}
        )


class RateLimitExceeded(MessageServiceException):
    """Rate limit exceeded error."""
    
    def __init__(
        self, 
        limit_type: str, 
        limit: int, 
        current: int, 
        reset_time: int = None
    ):
        super().__init__(
            message=f"Rate limit exceeded: {limit_type}",
            code="RATE_LIMIT_EXCEEDED",
            details={
                "limit_type": limit_type,
                "limit": limit,
                "current": current,
                "reset_time": reset_time
            }
        )


class ContentSafetyViolation(MessageServiceException):
    """Content safety violation error."""
    
    def __init__(self, violations: list, safety_score: float, threshold: float):
        super().__init__(
            message="Message content violates safety guidelines",
            code="CONTENT_SAFETY_VIOLATION",
            details={
                "violations": violations,
                "safety_score": safety_score,
                "threshold": threshold
            }
        )


class LLMServiceError(MessageServiceException):
    """LLM service error."""
    
    def __init__(
        self, 
        provider: str, 
        error_type: str, 
        message: str = "LLM provider error",
        retry_possible: bool = True
    ):
        super().__init__(
            message=message,
            code="LLM_SERVICE_ERROR",
            details={
                "provider": provider,
                "error_type": error_type,
                "retry_possible": retry_possible
            }
        )


class DatabaseError(MessageServiceException):
    """Database operation error."""
    
    def __init__(self, operation: str, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            code="DATABASE_ERROR",
            details={"operation": operation}
        )


class RedisError(MessageServiceException):
    """Redis operation error."""
    
    def __init__(self, operation: str, message: str = "Redis operation failed"):
        super().__init__(
            message=message,
            code="REDIS_ERROR",
            details={"operation": operation}
        )