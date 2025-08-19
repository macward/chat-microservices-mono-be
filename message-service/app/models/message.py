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




class CreateMessageRequest(BaseModel):
    """Request model for creating a message."""
    conversation_id: str = Field(..., description="ID of the target conversation")
    content: str = Field(..., min_length=1, max_length=50000, description="Message content")
    client_msg_id: Optional[str] = Field(None, description="Client message ID for idempotency")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('content')
    def validate_content(cls, v):
        if not v or not v.strip():
            raise ValueError("Message content cannot be empty")
        return v.strip()


class MessageResponse(BaseModel):
    """Response model for a message."""
    message_id: str
    conversation_id: str
    user_id: str
    character_id: Optional[str] = None
    content: str = Field(..., description="Message content")
    role: MessageRole
    created_at: datetime
    llm_metadata: Optional[Dict[str, Any]] = Field(default=None, description="LLM processing metadata")
    custom_metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ConversationMessagesRequest(BaseModel):
    """Request model for getting conversation messages (internal use only)."""
    limit: int = Field(default=50, ge=1, le=1000)
    cursor: Optional[str] = None
    role: Optional[MessageRole] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_archived: bool = False