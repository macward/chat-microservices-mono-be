"""
Standardized response utilities for the conversation service.

This module provides utilities for creating consistent API responses
with proper error handling and security considerations.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from app.api.exceptions import ErrorCode


class SuccessResponse(BaseModel):
    """Standardized success response model."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    success: bool = Field(True, description="Indicates successful operation")
    data: Any = Field(description="Response data")
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata about the response"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )


class ErrorResponse(BaseModel):
    """Standardized error response model."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    success: bool = Field(False, description="Indicates failed operation")
    error: Dict[str, Any] = Field(description="Error details")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'
    )
    
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")
    pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there are more pages")
    has_prev: bool = Field(description="Whether there are previous pages")


def create_success_response(
    data: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: The response data
        metadata: Optional metadata about the response
        
    Returns:
        Standardized success response dictionary
    """
    response = SuccessResponse(
        data=data,
        metadata=metadata
    )
    return response.model_dump()


def create_error_response(
    error_code: ErrorCode,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_code: Standardized error code
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code (for logging purposes)
        
    Returns:
        Standardized error response dictionary
    """
    error_data = {
        "code": error_code,
        "message": message,
        "details": details or {}
    }
    
    response = ErrorResponse(error=error_data)
    return response.model_dump()


def create_list_response(
    items: List[Any],
    page: int = 1,
    per_page: int = 20,
    total: Optional[int] = None
) -> Dict[str, Any]:
    """
    Create a standardized list response with pagination.
    
    Args:
        items: List of items to return
        page: Current page number
        per_page: Items per page
        total: Total number of items (if known)
        
    Returns:
        Standardized list response with pagination metadata
    """
    if total is None:
        total = len(items)
    
    pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    pagination = PaginationMetadata(
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )
    
    return create_success_response(
        data=items,
        metadata={"pagination": pagination.model_dump()}
    )


def create_created_response(
    resource: Any,
    resource_id: str,
    resource_type: str = "resource"
) -> Dict[str, Any]:
    """
    Create a standardized response for resource creation.
    
    Args:
        resource: The created resource
        resource_id: ID of the created resource
        resource_type: Type of resource created
        
    Returns:
        Standardized creation response
    """
    metadata = {
        "created": True,
        "resource_type": resource_type,
        "resource_id": resource_id
    }
    
    return create_success_response(
        data=resource,
        metadata=metadata
    )


def create_updated_response(
    resource: Any,
    resource_id: str,
    resource_type: str = "resource",
    modified_fields: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a standardized response for resource updates.
    
    Args:
        resource: The updated resource
        resource_id: ID of the updated resource
        resource_type: Type of resource updated
        modified_fields: List of fields that were modified
        
    Returns:
        Standardized update response
    """
    metadata = {
        "updated": True,
        "resource_type": resource_type,
        "resource_id": resource_id
    }
    
    if modified_fields:
        metadata["modified_fields"] = modified_fields
    
    return create_success_response(
        data=resource,
        metadata=metadata
    )


def create_deleted_response(
    resource_id: str,
    resource_type: str = "resource"
) -> Dict[str, Any]:
    """
    Create a standardized response for resource deletion.
    
    Args:
        resource_id: ID of the deleted resource
        resource_type: Type of resource deleted
        
    Returns:
        Standardized deletion response
    """
    metadata = {
        "deleted": True,
        "resource_type": resource_type,
        "resource_id": resource_id
    }
    
    return create_success_response(
        data=None,
        metadata=metadata
    )


def sanitize_response_data(data: Any) -> Any:
    """
    Sanitize response data to prevent information leakage.
    
    Args:
        data: Response data to sanitize
        
    Returns:
        Sanitized response data
    """
    if isinstance(data, dict):
        sanitized = {}
        sensitive_keys = {
            'password', 'secret', 'token', 'key', 'auth', 'session',
            'private_key', 'api_key', 'access_token', 'refresh_token'
        }
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, (dict, list)):
                sanitized[key] = sanitize_response_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    elif isinstance(data, list):
        return [sanitize_response_data(item) for item in data]
    
    else:
        return data


def validate_pagination_params(
    page: int,
    per_page: int,
    max_per_page: int = 100
) -> tuple[int, int]:
    """
    Validate and sanitize pagination parameters.
    
    Args:
        page: Requested page number
        per_page: Requested items per page
        max_per_page: Maximum allowed items per page
        
    Returns:
        Tuple of validated (page, per_page)
        
    Raises:
        ValueError: If parameters are invalid
    """
    if page < 1:
        raise ValueError("Page number must be greater than 0")
    
    if per_page < 1:
        raise ValueError("Items per page must be greater than 0")
    
    if per_page > max_per_page:
        raise ValueError(f"Items per page cannot exceed {max_per_page}")
    
    return page, per_page