"""Pydantic models for API request/response validation."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class MessageRole(str, Enum):
    """Message role enum."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageType(str, Enum):
    """Message type enum."""
    STANDARD = "standard"
    TEMPLATE = "template"
    SYSTEM = "system"


class MessageStatus(str, Enum):
    """Message status enum."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    FLAGGED = "flagged"
    DELETED = "deleted"
    PROCESSING = "processing"


class CreateMessageRequest(BaseModel):
    """Request model for creating a message."""
    conversation_id: str = Field(..., description="ID of the target conversation")
    content: str = Field(..., min_length=1, max_length=50000, description="Message content")
    client_msg_id: Optional[str] = Field(None, description="Client message ID for idempotency")
    message_type: MessageType = Field(default=MessageType.STANDARD)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


class MessageContent(BaseModel):
    """Message content model."""
    text: str
    sanitized_text: Optional[str] = None
    detected_language: Optional[str] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None


class LLMMetadata(BaseModel):
    """LLM metadata model."""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    processing_time_ms: Optional[int] = None


class TokenUsage(BaseModel):
    """Token usage model."""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None


class SafetyMetadata(BaseModel):
    """Safety metadata model."""
    content_filtered: bool = False
    safety_score: Optional[float] = None
    detected_issues: List[str] = Field(default_factory=list)


class MessageTimestamps(BaseModel):
    """Message timestamps model."""
    created_at: datetime
    processed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    """Response model for a message."""
    message_id: str
    conversation_id: str
    user_id: str
    character_id: Optional[str] = None
    content: MessageContent
    role: MessageRole
    message_type: MessageType
    status: MessageStatus
    timestamps: MessageTimestamps
    llm_metadata: Optional[LLMMetadata] = None
    token_usage: Optional[TokenUsage] = None
    safety_metadata: Optional[SafetyMetadata] = None
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcessingStatus(BaseModel):
    """Processing status model."""
    status: str
    queue_position: Optional[int] = None
    estimated_completion: Optional[datetime] = None


class CreateMessageResponse(BaseModel):
    """Response model for creating a message."""
    message_id: str
    conversation_id: str
    user_message: MessageResponse
    assistant_message: Optional[MessageResponse] = None
    processing_status: Optional[ProcessingStatus] = None
    token_usage: Optional[TokenUsage] = None


class ConversationMessagesRequest(BaseModel):
    """Request model for getting conversation messages."""
    limit: int = Field(default=50, ge=1, le=1000)
    cursor: Optional[str] = None
    direction: str = Field(default="next", regex="^(next|prev)$")
    role: Optional[MessageRole] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_archived: bool = False
    format: str = Field(default="full", regex="^(full|summary|llm)$")


class PaginationInfo(BaseModel):
    """Pagination information."""
    total_count: int
    current_page: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    limit: int


class ConversationMessagesResponse(BaseModel):
    """Response model for conversation messages."""
    messages: List[MessageResponse]
    pagination: PaginationInfo
    conversation_metadata: Dict[str, Any] = Field(default_factory=dict)