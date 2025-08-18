"""Database models using Beanie ODM for MongoDB."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from beanie import Document, Indexed
from pydantic import Field, validator
import uuid


class ContentData(dict):
    """Message content data."""
    text: str
    sanitized_text: Optional[str] = None
    detected_language: Optional[str] = None
    content_hash: Optional[str] = None
    word_count: Optional[int] = None
    character_count: Optional[int] = None


class LLMMetadata(dict):
    """LLM metadata for assistant messages."""
    provider: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    request_id: Optional[str] = None
    processing_time_ms: Optional[int] = None


class TokenUsage(dict):
    """Token usage information."""
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None


class SafetyMetadata(dict):
    """Content safety metadata."""
    content_filtered: bool = False
    safety_score: Optional[float] = None
    detected_issues: List[str] = []


class Timestamps(dict):
    """Timestamp information."""
    created_at: datetime
    processed_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class Message(Document):
    """Main message document."""
    
    # Core identifiers
    message_id: Indexed(str) = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    conversation_id: Indexed(str)
    user_id: Indexed(str)
    character_id: Optional[str] = None
    
    # Message content
    content: ContentData
    
    # Message metadata
    role: str = Field(pattern="^(user|assistant|system)$")
    message_type: str = Field(default="standard")
    status: str = Field(default="active", pattern="^(active|archived|flagged|deleted)$")
    sequence_number: Optional[int] = None
    
    # LLM specific data (only for assistant messages)
    llm_metadata: Optional[LLMMetadata] = None
    token_usage: Optional[TokenUsage] = None
    
    # Safety and content filtering
    safety_metadata: SafetyMetadata = Field(default_factory=dict)
    
    # Timestamps
    timestamps: Timestamps
    
    # Client metadata for traceability
    client_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Custom extensible metadata
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Version for schema evolution
    version: int = Field(default=1)
    
    @validator('message_id', pre=True, always=True)
    def generate_message_id(cls, v):
        return v or f"msg_{uuid.uuid4().hex[:12]}"
    
    @validator('timestamps', pre=True, always=True)
    def set_timestamps(cls, v):
        if isinstance(v, dict):
            if 'created_at' not in v:
                v['created_at'] = datetime.utcnow()
        else:
            v = {'created_at': datetime.utcnow()}
        return v
    
    @validator('content', pre=True)
    def validate_content(cls, v):
        if isinstance(v, str):
            v = {'text': v}
        
        # Basic content validation
        text = v.get('text', '')
        if not text or len(text.strip()) == 0:
            raise ValueError("Message text cannot be empty")
        
        if len(text) > 50000:  # From technical limitations
            raise ValueError("Message text exceeds maximum length of 50,000 characters")
        
        # Set character and word count
        v['character_count'] = len(text)
        v['word_count'] = len(text.split())
        
        return v
    
    class Settings:
        name = "messages"
        indexes = [
            "message_id",
            "conversation_id",
            "user_id",
            [("conversation_id", 1), ("timestamps.created_at", -1)],
            [("user_id", 1), ("timestamps.created_at", -1)],
            [("timestamps.created_at", -1)],
        ]