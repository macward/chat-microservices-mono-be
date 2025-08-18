"""
Global exception handlers for the conversation service.

This module provides centralized exception handling with security logging,
proper error sanitization, and standardized responses.
"""

import logging
from typing import Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pymongo.errors import PyMongoError
from beanie.exceptions import DocumentNotFound

from app.api.exceptions import (
    BaseConversationException,
    ValidationException,
    SecurityException,
    DatabaseException,
    ErrorCode,
    create_validation_error_response,
    log_security_event
)
from app.api.responses import create_error_response

# Set up loggers
logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors with security logging.
    
    Args:
        request: The FastAPI request object
        exc: The validation error exception
        
    Returns:
        Standardized JSON error response
    """
    # Log validation attempt for security monitoring
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Check for potential security issues in validation errors
    error_details = exc.errors()
    suspicious_patterns = ["script", "javascript", "eval", "onload", "<", ">"]
    
    for error in error_details:
        input_value = str(error.get("input", ""))
        if any(pattern in input_value.lower() for pattern in suspicious_patterns):
            log_security_event(
                event_type="SUSPICIOUS_INPUT",
                description="Potentially malicious input detected in validation",
                ip_address=client_ip,
                additional_data={
                    "user_agent": user_agent,
                    "input_sample": input_value[:100],  # Limit for security
                    "field": ".".join(str(loc) for loc in error.get("loc", []))
                }
            )
    
    logger.info(
        f"Validation error from {client_ip}: {len(error_details)} field errors",
        extra={
            "ip_address": client_ip,
            "user_agent": user_agent,
            "error_count": len(error_details),
            "path": request.url.path
        }
    )
    
    response_data = create_validation_error_response(error_details)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def pydantic_validation_exception_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """
    Handle Pydantic model validation errors.
    
    Args:
        request: The FastAPI request object
        exc: The Pydantic validation error
        
    Returns:
        Standardized JSON error response
    """
    error_details = exc.errors()
    response_data = create_validation_error_response(error_details)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )


async def conversation_exception_handler(
    request: Request,
    exc: BaseConversationException
) -> JSONResponse:
    """
    Handle custom conversation service exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The conversation service exception
        
    Returns:
        Standardized JSON error response
    """
    # Additional security logging for security exceptions
    if isinstance(exc, SecurityException):
        client_ip = request.client.host if request.client else "unknown"
        log_security_event(
            event_type="SECURITY_EXCEPTION",
            description=f"Security exception raised: {exc.error_code}",
            ip_address=client_ip,
            additional_data={
                "path": request.url.path,
                "error_code": exc.error_code,
                "message": exc.message
            }
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException
) -> JSONResponse:
    """
    Handle standard HTTP exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The HTTP exception
        
    Returns:
        Standardized JSON error response
    """
    # Map HTTP status codes to error codes
    error_code_mapping = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        409: ErrorCode.CONFLICT,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR
    }
    
    error_code = error_code_mapping.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    
    # Handle different detail formats
    if isinstance(exc.detail, dict):
        response_data = exc.detail
    else:
        response_data = create_error_response(
            error_code=error_code,
            message=str(exc.detail),
            status_code=exc.status_code
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def starlette_http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle Starlette HTTP exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The Starlette HTTP exception
        
    Returns:
        Standardized JSON error response
    """
    if exc.status_code == 404:
        response_data = create_error_response(
            error_code=ErrorCode.NOT_FOUND,
            message="Endpoint not found",
            details={"path": request.url.path}
        )
    elif exc.status_code == 405:
        response_data = create_error_response(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="Method not allowed",
            details={"method": request.method, "path": request.url.path}
        )
    else:
        response_data = create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=str(exc.detail),
            status_code=exc.status_code
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )


async def database_exception_handler(
    request: Request,
    exc: PyMongoError
) -> JSONResponse:
    """
    Handle database-related exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The database exception
        
    Returns:
        Standardized JSON error response
    """
    logger.error(
        f"Database error: {type(exc).__name__}",
        extra={
            "exception_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    # Don't expose internal database errors
    response_data = create_error_response(
        error_code=ErrorCode.DATABASE_ERROR,
        message="Database operation failed",
        details={"operation": "database_operation"}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


async def document_not_found_exception_handler(
    request: Request,
    exc: DocumentNotFound
) -> JSONResponse:
    """
    Handle Beanie document not found exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The document not found exception
        
    Returns:
        Standardized JSON error response
    """
    response_data = create_error_response(
        error_code=ErrorCode.NOT_FOUND,
        message="Resource not found"
    )
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=response_data
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Args:
        request: The FastAPI request object
        exc: The unexpected exception
        
    Returns:
        Standardized JSON error response
    """
    client_ip = request.client.host if request.client else "unknown"
    
    logger.error(
        f"Unexpected error from {client_ip}: {type(exc).__name__}",
        extra={
            "exception_type": type(exc).__name__,
            "ip_address": client_ip,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    # Log as potential security issue if unexpected
    log_security_event(
        event_type="UNEXPECTED_ERROR",
        description=f"Unexpected exception: {type(exc).__name__}",
        ip_address=client_ip,
        additional_data={
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Don't expose internal error details
    response_data = create_error_response(
        error_code=ErrorCode.INTERNAL_ERROR,
        message="An unexpected error occurred"
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    # Validation errors
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    
    # Custom application exceptions
    app.add_exception_handler(BaseConversationException, conversation_exception_handler)
    
    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)
    
    # Database exceptions
    app.add_exception_handler(PyMongoError, database_exception_handler)
    app.add_exception_handler(DocumentNotFound, document_not_found_exception_handler)
    
    # Catch-all for unexpected exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Exception handlers registered successfully")