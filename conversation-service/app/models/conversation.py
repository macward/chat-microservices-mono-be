from beanie import Document, Indexed
from pydantic import Field, field_validator, model_validator
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum
from typing import Optional, List
from typing_extensions import Self
import re
from bson import ObjectId

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class Conversation(Document):
    user_id: Indexed(str) = Field(
        description="User identifier - ObjectId, UUID, or numeric format",
        min_length=1,   # Allow single digit IDs
        max_length=36   # Maximum for UUID
    )
    character_id: str = Field(
        description="Character identifier - ObjectId, UUID, or alphanumeric format", 
        min_length=1,
        max_length=50
    )
    title: Optional[str] = Field(
        None, 
        min_length=1,
        max_length=200,
        description="Conversation title - alphanumeric, spaces, and basic punctuation only"
    )
    status: ConversationStatus = Field(
        default=ConversationStatus.ACTIVE,
        description="Current status of the conversation"
    )
    tags: List[str] = Field(
        default_factory=list, 
        max_length=10,
        description="List of tags for categorization - max 10 tags"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when conversation was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when conversation was last updated"
    )

    @field_validator('user_id', 'character_id')
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        """Validate that user_id and character_id are valid ID formats."""
        v = str(v).strip()  # Convert to string and strip whitespace
        if not v:
            raise ValueError('ID cannot be empty')
        
        # Check for ObjectId format (24 hex characters)
        if re.match(r'^[0-9a-fA-F]{24}$', v):
            return v
        
        # Check for UUID format (with or without hyphens)
        uuid_pattern = r'^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$'
        if re.match(uuid_pattern, v):
            return v
        
        # Check for numeric ID (common in auth services)
        if re.match(r'^\d+$', v):
            return v
        
        # Check for alphanumeric IDs (flexible format)
        if re.match(r'^[a-zA-Z0-9_-]+$', v) and len(v) >= 1 and len(v) <= 50:
            return v
        
        raise ValueError('ID must be a valid ObjectId, UUID, numeric, or alphanumeric format (1-50 characters)')
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title contains only safe characters and isn't just whitespace."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None  # Convert empty string to None
        
        # Allow alphanumeric, spaces, and basic punctuation only
        if not re.match(r'^[a-zA-Z0-9\s\-_.,!?()\[\]]+$', v):
            raise ValueError('Title contains invalid characters. Only alphanumeric, spaces, and basic punctuation allowed')
        
        # Prevent potential XSS patterns
        dangerous_patterns = ['<script', 'javascript:', 'on\w+=']
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, v_lower):
                raise ValueError('Title contains potentially dangerous content')
        
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags format and content."""
        if not v:
            return []
        
        validated_tags = []
        for tag in v:
            tag = tag.strip().lower()
            if not tag:
                continue  # Skip empty tags
            
            # Validate tag format - alphanumeric and underscores only
            if not re.match(r'^[a-zA-Z0-9_]{1,20}$', tag):
                raise ValueError(f'Tag "{tag}" is invalid. Tags must be 1-20 characters, alphanumeric and underscores only')
            
            if tag not in validated_tags:  # Prevent duplicates
                validated_tags.append(tag)
        
        if len(validated_tags) > 10:
            raise ValueError('Maximum 10 unique tags allowed')
        
        return validated_tags
    
    @model_validator(mode='after')
    def validate_conversation(self) -> Self:
        """Perform cross-field validation."""
        # Ensure user_id and character_id are different
        if self.user_id == self.character_id:
            raise ValueError('User ID and Character ID must be different')
        
        # Ensure updated_at is not before created_at
        if self.updated_at < self.created_at:
            raise ValueError('Updated timestamp cannot be before created timestamp')
        
        return self

    class Settings:
        name = "conversations"  # Collection name in MongoDB

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "character_id": "character456",
                "title": "My First Conversation",
                "status": "active",
                "tags": ["intro", "test"]
            }
        }

# Request and Response Models
class ConversationCreate(BaseModel):
    """Model for creating a new conversation with comprehensive validation."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'  # Prevent additional fields for security
    )
    
    character_id: str = Field(
        description="Character identifier - ObjectId or UUID format",
        min_length=12,
        max_length=36,
        examples=["60f1b2b3c9e77c001f123456", "123e4567-e89b-12d3-a456-426614174000"]
    )
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Optional conversation title",
        examples=["My Chat with Gandalf", "Learning Python"]
    )
    tags: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Optional tags for categorization",
        examples=[["fantasy", "learning"], ["coding", "tutorial"]]
    )
    
    @field_validator('character_id')
    @classmethod
    def validate_character_id(cls, v: str) -> str:
        """Validate character_id format and security."""
        v = str(v).strip()
        if not v:
            raise ValueError('Character ID is required')
        
        # Check for ObjectId format (24 hex characters)
        if re.match(r'^[0-9a-fA-F]{24}$', v):
            return v
        
        # Check for UUID format (with or without hyphens)
        uuid_pattern = r'^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$'
        if re.match(uuid_pattern, v):
            return v
        
        # Check for numeric ID (common in auth services)
        if re.match(r'^\d+$', v):
            return v
        
        # Check for alphanumeric IDs (flexible format)
        if re.match(r'^[a-zA-Z0-9_-]+$', v) and len(v) >= 1 and len(v) <= 50:
            return v
        
        raise ValueError('Character ID must be a valid ObjectId, UUID, numeric, or alphanumeric format (1-50 characters)')
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title content and security."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # Security: Check for potentially dangerous content
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, v_lower):
                raise ValueError('Title contains potentially dangerous content')
        
        # Allow only safe characters
        if not re.match(r'^[a-zA-Z0-9\s\-_.,!?()\[\]]+$', v):
            raise ValueError('Title contains invalid characters')
        
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags format and security."""
        if not v:
            return []
        
        validated_tags = []
        for tag in v:
            tag = tag.strip().lower()
            if not tag:
                continue
            
            # Security: Only allow alphanumeric and underscores
            if not re.match(r'^[a-zA-Z0-9_]{1,20}$', tag):
                raise ValueError(f'Tag "{tag}" is invalid. Only alphanumeric and underscores allowed, 1-20 characters')
            
            if tag not in validated_tags:
                validated_tags.append(tag)
        
        if len(validated_tags) > 10:
            raise ValueError('Maximum 10 unique tags allowed')
        
        return validated_tags

class ConversationUpdate(BaseModel):
    """Model for updating conversation fields."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Updated conversation title"
    )
    status: Optional[ConversationStatus] = Field(
        None,
        description="Updated conversation status"
    )
    tags: Optional[List[str]] = Field(
        None,
        max_length=10,
        description="Updated tags list"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title content and security."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # Apply same security validations as ConversationCreate
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>'
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, v_lower):
                raise ValueError('Title contains potentially dangerous content')
        
        if not re.match(r'^[a-zA-Z0-9\s\-_.,!?()\[\]]+$', v):
            raise ValueError('Title contains invalid characters')
        
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags format and security."""
        if v is None:
            return v
        
        validated_tags = []
        for tag in v:
            tag = tag.strip().lower()
            if not tag:
                continue
            
            if not re.match(r'^[a-zA-Z0-9_]{1,20}$', tag):
                raise ValueError(f'Tag "{tag}" is invalid. Only alphanumeric and underscores allowed, 1-20 characters')
            
            if tag not in validated_tags:
                validated_tags.append(tag)
        
        if len(validated_tags) > 10:
            raise ValueError('Maximum 10 unique tags allowed')
        
        return validated_tags


class ConversationResponse(BaseModel):
    """Response model for conversation data."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True
    )
    
    id: str = Field(description="Conversation unique identifier")
    user_id: str = Field(description="User identifier")
    character_id: str = Field(description="Character identifier")
    title: Optional[str] = Field(description="Conversation title")
    status: ConversationStatus = Field(description="Current conversation status")
    tags: List[str] = Field(description="Conversation tags")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")


# Advanced Features Models

class CursorInfo(BaseModel):
    """Information about cursor pagination."""
    has_next_page: bool = Field(description="Whether there are more items after this page")
    has_previous_page: bool = Field(description="Whether there are more items before this page")
    start_cursor: Optional[str] = Field(description="Cursor pointing to the start of this page")
    end_cursor: Optional[str] = Field(description="Cursor pointing to the end of this page")


class PaginatedConversationResponse(BaseModel):
    """Response model for paginated conversation data."""
    model_config = ConfigDict(validate_assignment=True)
    
    conversations: List[ConversationResponse] = Field(description="List of conversations")
    page_info: CursorInfo = Field(description="Pagination information")
    total_count: Optional[int] = Field(None, description="Total number of conversations (optional)")


class ConversationSearchFilters(BaseModel):
    """Search and filter parameters for conversations."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    # Basic filters
    status: Optional[ConversationStatus] = Field(None, description="Filter by status")
    character_id: Optional[str] = Field(None, description="Filter by character")
    
    # Search
    search: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=100,
        description="Search in conversation title"
    )
    
    # Tags
    tags: Optional[List[str]] = Field(
        None, 
        max_length=5,
        description="Filter by tags (max 5 tags)"
    )
    
    # Cursor pagination
    after: Optional[str] = Field(None, description="Cursor for getting items after")
    before: Optional[str] = Field(None, description="Cursor for getting items before")
    first: Optional[int] = Field(None, ge=1, le=100, description="Number of items to fetch forward")
    last: Optional[int] = Field(None, ge=1, le=100, description="Number of items to fetch backward")
    
    @field_validator('search')
    @classmethod
    def validate_search(cls, v: Optional[str]) -> Optional[str]:
        """Validate search term for security."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # Security: Prevent regex injection and dangerous characters
        dangerous_chars = ['$', '{', '}', '[', ']', '(', ')', '*', '+', '?', '^', '|', '\\']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f'Search term contains invalid character: {char}')
        
        # Allow only alphanumeric, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_.,!?]+$', v):
            raise ValueError('Search term contains invalid characters')
        
        return v
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tag filters."""
        if v is None:
            return v
        
        validated_tags = []
        for tag in v:
            tag = tag.strip().lower()
            if not tag:
                continue
            
            if not re.match(r'^[a-zA-Z0-9_]{1,20}$', tag):
                raise ValueError(f'Tag "{tag}" is invalid')
            
            if tag not in validated_tags:
                validated_tags.append(tag)
        
        return validated_tags if validated_tags else None
    
    @model_validator(mode='after')
    def validate_pagination(self) -> Self:
        """Validate cursor pagination parameters."""
        # Can't use both forward and backward pagination
        if (self.first is not None and self.last is not None):
            raise ValueError('Cannot specify both first and last parameters')
        
        # Can't use both after and before cursors
        if (self.after is not None and self.before is not None):
            raise ValueError('Cannot specify both after and before cursors')
        
        # Default to forward pagination if no parameters specified
        if all(param is None for param in [self.first, self.last, self.after, self.before]):
            self.first = 20  # Default page size
        
        # Ensure cursor direction matches pagination direction
        if self.first is not None and self.before is not None:
            raise ValueError('Cannot use before cursor with first parameter')
        
        if self.last is not None and self.after is not None:
            raise ValueError('Cannot use after cursor with last parameter')
        
        return self


class UserStats(BaseModel):
    """User statistics model."""
    model_config = ConfigDict(validate_assignment=True)
    
    total_conversations: int = Field(description="Total number of conversations")
    active_conversations: int = Field(description="Number of active conversations")
    archived_conversations: int = Field(description="Number of archived conversations")
    deleted_conversations: int = Field(description="Number of deleted conversations")
    total_tags: int = Field(description="Number of unique tags used")
    most_used_tags: List[str] = Field(description="Top 5 most used tags")
    characters_chatted_with: int = Field(description="Number of unique characters chatted with")
    oldest_conversation_date: Optional[datetime] = Field(description="Date of oldest conversation")
    newest_conversation_date: Optional[datetime] = Field(description="Date of newest conversation")