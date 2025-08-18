"""Message API endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query, Path
from fastapi.responses import JSONResponse

from app.services.message_service import MessageService
from app.models.message import (
    CreateMessageRequest,
    CreateMessageResponse,
    MessageResponse,
    ConversationMessagesRequest,
    ConversationMessagesResponse,
    PaginationInfo
)
from app.core.rate_limiter import rate_limiter
from app.core.exceptions import (
    MessageServiceException,
    ValidationError,
    NotFoundError,
    RateLimitExceeded
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_user_id_from_token(authorization: str = Header(None)) -> str:
    """Extract user ID from JWT token (simplified for MVP)."""
    # TODO: Implement proper JWT validation with Auth Service
    # For now, return a mock user ID
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    # Mock user ID extraction - replace with actual JWT validation
    return "user_test_123"


@router.post("/messages", response_model=CreateMessageResponse)
async def create_message(
    request: CreateMessageRequest,
    user_id: str = Header(alias="x-user-id", default=None),
    authorization: str = Header(None)
):
    """Create a new message."""
    try:
        # Get user ID from token if not provided in header (for testing)
        if not user_id:
            user_id = get_user_id_from_token(authorization)
        
        # Check rate limits
        await rate_limiter.check_rate_limit(user_id)
        
        # Create message
        service = MessageService()
        message = await service.create_message(request, user_id)
        
        return CreateMessageResponse(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            user_message=message,
            processing_status={
                'status': 'completed',
                'queue_position': None,
                'estimated_completion': None
            }
        )
        
    except RateLimitExceeded as e:
        logger.warning("Rate limit exceeded", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except ValidationError as e:
        logger.warning("Validation error", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except Exception as e:
        logger.error("Failed to create message", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
        )


@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    message_id: str = Path(..., description="Message ID"),
    user_id: str = Header(alias="x-user-id", default=None),
    authorization: str = Header(None)
):
    """Get a message by ID."""
    try:
        if not user_id:
            user_id = get_user_id_from_token(authorization)
        
        service = MessageService()
        message = await service.get_message(message_id)
        
        return message
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": e.code, "message": e.message}})
    except Exception as e:
        logger.error("Failed to get message", message_id=message_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
        )


@router.get("/conversations/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    conversation_id: str = Path(..., description="Conversation ID"),
    limit: int = Query(50, ge=1, le=1000, description="Number of messages to return"),
    cursor: str = Query(None, description="Pagination cursor"),
    role: str = Query(None, regex="^(user|assistant|system)$", description="Filter by message role"),
    include_archived: bool = Query(False, description="Include archived messages"),
    user_id: str = Header(alias="x-user-id", default=None),
    authorization: str = Header(None)
):
    """Get messages for a conversation."""
    try:
        if not user_id:
            user_id = get_user_id_from_token(authorization)
        
        # Build request
        request = ConversationMessagesRequest(
            limit=limit,
            cursor=cursor,
            role=role,
            include_archived=include_archived
        )
        
        service = MessageService()
        messages = await service.get_conversation_messages(conversation_id, request)
        
        # TODO: Implement proper pagination with cursors
        pagination = PaginationInfo(
            total_count=len(messages),
            current_page=1,
            total_pages=1,
            has_next=False,
            has_prev=False,
            limit=limit
        )
        
        return ConversationMessagesResponse(
            messages=messages,
            pagination=pagination,
            conversation_metadata={
                "conversation_id": conversation_id,
                "total_messages": len(messages)
            }
        )
        
    except Exception as e:
        logger.error(
            "Failed to get conversation messages",
            conversation_id=conversation_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
        )


@router.patch("/messages/{message_id}/metadata", response_model=MessageResponse)
async def update_message_metadata(
    message_id: str = Path(..., description="Message ID"),
    metadata: Dict[str, Any] = None,
    user_id: str = Header(alias="x-user-id", default=None),
    authorization: str = Header(None)
):
    """Update message metadata."""
    try:
        if not user_id:
            user_id = get_user_id_from_token(authorization)
        
        if not metadata:
            raise ValidationError("Metadata is required", field="metadata")
        
        service = MessageService()
        message = await service.update_message_metadata(message_id, metadata)
        
        return message
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": e.code, "message": e.message}})
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": e.code, "message": e.message, "details": e.details}}
        )
    except Exception as e:
        logger.error("Failed to update message metadata", message_id=message_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
        )


@router.delete("/messages/{message_id}", response_model=Dict[str, Any])
async def archive_message(
    message_id: str = Path(..., description="Message ID"),
    reason: str = Query(None, description="Reason for archiving"),
    user_id: str = Header(alias="x-user-id", default=None),
    authorization: str = Header(None)
):
    """Archive a message (soft delete)."""
    try:
        if not user_id:
            user_id = get_user_id_from_token(authorization)
        
        service = MessageService()
        message = await service.archive_message(message_id)
        
        return {
            "message_id": message_id,
            "status": "archived",
            "archived_at": message.timestamps.get('updated_at'),
            "archive_reason": reason or "user_request",
            "recoverable": True
        }
        
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": e.code, "message": e.message}})
    except Exception as e:
        logger.error("Failed to archive message", message_id=message_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
        )