"""Database models using Beanie ODM for MongoDB."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from beanie import Document, Indexed
from pydantic import BaseModel, Field, validator
import uuid




class Message(Document):
    """Main message document."""
    
    # Core identifiers
    message_id: Indexed(str) = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    conversation_id: Indexed(str)
    user_id: Indexed(str)
    character_id: Optional[str] = None
    
    # Message content - simplified to dict to maintain flexibility
    content: Dict[str, Any] = Field(default_factory=dict)
    
    # Message metadata
    role: str = Field(pattern="^(user|assistant|system)$")
    
    # Timestamps - simplified to dict
    timestamps: Dict[str, Any] = Field(default_factory=dict)
    
    # LLM specific data (only for assistant messages) - simplified to dict
    llm_metadata: Optional[Dict[str, Any]] = None
    
    # Custom extensible metadata
    custom_metadata: Dict[str, Any] = Field(default_factory=dict)
    
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
        
        if len(text) > 50000:
            raise ValueError("Message text exceeds maximum length of 50,000 characters")
        
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