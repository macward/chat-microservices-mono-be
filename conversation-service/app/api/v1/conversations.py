from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from typing import List, Optional

from app.models.conversation import (
    ConversationCreate, 
    ConversationUpdate, 
    ConversationResponse, 
    ConversationStatus,
    ConversationSearchFilters,
    PaginatedConversationResponse,
    UserStats
)
from app.services.conversation_service import ConversationService
from app.middleware.auth import get_current_user_id

def get_conversation_service() -> ConversationService:
    """Get ConversationService instance for dependency injection."""
    return ConversationService()
from app.api.responses import (
    create_success_response,
    create_list_response,
    create_created_response,
    create_updated_response,
    create_deleted_response
)
from app.api.exceptions import (
    ValidationException,
    ResourceNotFoundException,
    SecurityException,
    BusinessLogicException
)

router = APIRouter()

def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    return request.client.host if request.client else "unknown"


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Create a new conversation.
    
    - **character_id**: ID of the character for this conversation
    - **title**: Optional title for the conversation
    - **tags**: Optional list of tags for categorization
    """
    ip_address = get_client_ip(request)
    
    created_conversation = await conversation_service.create_conversation(
        user_id=user_id,
        data=conversation,
        ip_address=ip_address
    )
    
    return create_created_response(
        resource=created_conversation.model_dump(),
        resource_id=created_conversation.id,
        resource_type="conversation"
    )

@router.get("/", response_model=dict)
async def list_conversations(
    request: Request,
    status_filter: Optional[ConversationStatus] = Query(None, alias="status", description="Filter by conversation status"),
    character_id: Optional[str] = Query(None, description="Filter by character ID"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    List conversations for the authenticated user with optional filtering.
    
    - **status**: Filter by conversation status (active, archived, deleted)
    - **character_id**: Filter by character ID
    - **page**: Page number for pagination
    - **per_page**: Number of items per page (max 100)
    """
    ip_address = get_client_ip(request)
    
    # Calculate skip value for pagination
    skip = (page - 1) * per_page
    
    conversations = await conversation_service.list_conversations(
        user_id=user_id,
        status=status_filter,
        character_id=character_id,
        limit=per_page,
        skip=skip,
        ip_address=ip_address
    )
    
    # Convert to dict format for response
    conversations_data = [conv.model_dump() for conv in conversations]
    
    return create_list_response(
        items=conversations_data,
        page=page,
        per_page=per_page
    )

@router.get("/{conversation_id}", response_model=dict)
async def get_conversation(
    conversation_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get a specific conversation by ID.
    
    - **conversation_id**: Unique identifier of the conversation
    """
    ip_address = get_client_ip(request)
    
    conversation = await conversation_service.get_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        ip_address=ip_address
    )
    
    return create_success_response(
        data=conversation.model_dump()
    )

@router.patch("/{conversation_id}", response_model=dict)
async def update_conversation(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Update a conversation partially.
    
    - **conversation_id**: Unique identifier of the conversation
    - **title**: Updated title (optional)
    - **status**: Updated status (optional)
    - **tags**: Updated tags list (optional)
    """
    ip_address = get_client_ip(request)
    
    updated_conversation = await conversation_service.update_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        data=conversation_update,
        ip_address=ip_address
    )
    
    return create_updated_response(
        resource=updated_conversation.model_dump(),
        resource_id=conversation_id,
        resource_type="conversation"
    )

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_conversation(
    conversation_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Archive a conversation (soft delete).
    
    This endpoint archives the conversation by setting its status to 'archived'
    rather than permanently deleting it. Archived conversations can be restored.
    
    - **conversation_id**: Unique identifier of the conversation
    """
    ip_address = get_client_ip(request)
    
    await conversation_service.archive_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        ip_address=ip_address
    )
    
    # Return 204 No Content for successful archival

@router.post("/{conversation_id}/restore", response_model=dict)
async def restore_conversation(
    conversation_id: str,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Restore an archived conversation.
    
    This endpoint restores a previously archived conversation by setting
    its status back to 'active'.
    
    - **conversation_id**: Unique identifier of the conversation to restore
    """
    ip_address = get_client_ip(request)
    
    restored_conversation = await conversation_service.restore_conversation(
        conversation_id=conversation_id,
        user_id=user_id,
        ip_address=ip_address
    )
    
    return create_updated_response(
        resource=restored_conversation.model_dump(),
        resource_id=conversation_id,
        resource_type="conversation",
        modified_fields=["status"]
    )


# Advanced Features Endpoints

@router.get("/advanced", response_model=dict)
async def list_conversations_advanced(
    request: Request,
    # Search and filtering parameters
    search: Optional[str] = Query(None, min_length=1, max_length=100, description="Search in conversation titles"),
    status_filter: Optional[ConversationStatus] = Query(None, alias="status", description="Filter by status"),
    character_id: Optional[str] = Query(None, description="Filter by character ID"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags (max 5)"),
    
    # Cursor pagination parameters
    after: Optional[str] = Query(None, description="Cursor for forward pagination"),
    before: Optional[str] = Query(None, description="Cursor for backward pagination"), 
    first: Optional[int] = Query(None, ge=1, le=100, description="Number of items to fetch forward"),
    last: Optional[int] = Query(None, ge=1, le=100, description="Number of items to fetch backward"),
    
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    List conversations with advanced filtering, search, and cursor-based pagination.
    
    This endpoint provides powerful search and filtering capabilities:
    
    **Search & Filters:**
    - `search`: Search in conversation titles (case-insensitive)
    - `status`: Filter by conversation status  
    - `character_id`: Filter by character ID
    - `tags`: Filter by tags (conversations must have ALL specified tags)
    
    **Cursor Pagination:**
    - `first` + `after`: Forward pagination (get N items after cursor)
    - `last` + `before`: Backward pagination (get N items before cursor)
    - Default: `first=20` (20 items from the start)
    
    **Response includes:**
    - List of conversations matching criteria
    - Pagination cursors for next/previous pages
    - Total count (on first page only)
    """
    ip_address = get_client_ip(request)
    
    # Build search filters
    filters = ConversationSearchFilters(
        search=search,
        status=status_filter,
        character_id=character_id,
        tags=tags,
        after=after,
        before=before,
        first=first,
        last=last
    )
    
    result = await conversation_service.list_conversations_advanced(
        user_id=user_id,
        filters=filters,
        ip_address=ip_address
    )
    
    return create_success_response(data=result.model_dump())


@router.get("/search", response_model=dict)
async def search_conversations(
    request: Request,
    q: str = Query(description="Search query for conversation titles", min_length=2, max_length=100),
    status_filter: Optional[ConversationStatus] = Query(None, alias="status", description="Filter by status"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of results"),
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Search conversations by title with text matching.
    
    - **q**: Search query to match against conversation titles
    - **status**: Optional status filter (active, archived, deleted)
    - **limit**: Maximum number of results (1-50, default 20)
    
    Returns conversations with titles containing the search query (case-insensitive).
    """
    ip_address = get_client_ip(request)
    
    conversations = await conversation_service.search_conversations(
        user_id=user_id,
        search_term=q,
        status=status_filter,
        limit=limit,
        ip_address=ip_address
    )
    
    return create_success_response(data={
        "conversations": [conv.model_dump() for conv in conversations],
        "search_query": q,
        "result_count": len(conversations)
    })


@router.get("/by-tags", response_model=dict)
async def get_conversations_by_tags(
    request: Request,
    tags: List[str] = Query(description="Tags to filter by (max 5)"),
    match_all: bool = Query(True, description="If true, must match ALL tags. If false, match ANY tag"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Find conversations by tags with flexible matching.
    
    - **tags**: List of tags to filter by (maximum 5 tags)
    - **match_all**: 
      - `true`: Conversations must have ALL specified tags (AND logic)
      - `false`: Conversations must have ANY specified tag (OR logic)
    - **limit**: Maximum number of results (1-100, default 50)
    
    Examples:
    - `?tags=fantasy&tags=rpg&match_all=true`: Conversations with both 'fantasy' AND 'rpg' tags
    - `?tags=python&tags=tutorial&match_all=false`: Conversations with 'python' OR 'tutorial' tags
    """
    ip_address = get_client_ip(request)
    
    conversations = await conversation_service.get_conversations_by_tags(
        user_id=user_id,
        tags=tags,
        match_all=match_all,
        limit=limit,
        ip_address=ip_address
    )
    
    return create_success_response(data={
        "conversations": [conv.model_dump() for conv in conversations],
        "filter_tags": tags,
        "match_all": match_all,
        "result_count": len(conversations)
    })


@router.get("/stats", response_model=dict)
async def get_user_statistics(
    request: Request,
    user_id: str = Depends(get_current_user_id),
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Get comprehensive statistics for the authenticated user's conversations.
    
    Returns detailed metrics including:
    - **Total conversations** by status (active, archived, deleted)
    - **Tag analysis**: Most used tags and total unique tags
    - **Character interactions**: Number of unique characters chatted with
    - **Timeline**: Oldest and newest conversation dates
    
    This endpoint provides insights into conversation patterns and usage.
    """
    ip_address = get_client_ip(request)
    
    stats = await conversation_service.get_user_statistics(
        user_id=user_id,
        ip_address=ip_address
    )
    
    return create_success_response(data=stats.model_dump())