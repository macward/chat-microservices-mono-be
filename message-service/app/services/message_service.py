"""Message service for business logic."""

from datetime import datetime
from typing import List, Optional, Dict, Any
import bleach

from app.repositories.message_repository import MessageRepository
from app.models.database import Message
from app.models.message import (
    CreateMessageRequest, 
    MessageResponse, 
    ConversationMessagesRequest,
    MessageRole,
    MessageStatus
)
from app.core.exceptions import ValidationError, NotFoundError
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class MessageService:
    """Service for message operations."""
    
    def __init__(self):
        self.repository = MessageRepository()
    
    async def create_message(
        self,
        request: CreateMessageRequest,
        user_id: str,
        character_id: Optional[str] = None
    ) -> MessageResponse:
        """Create a new message."""
        logger.info(
            "Creating message",
            conversation_id=request.conversation_id,
            user_id=user_id
        )
        
        # Sanitize content
        sanitized_content = self._sanitize_content(request.content)
        
        # Validate content length
        if len(sanitized_content) > settings.max_message_length:
            raise ValidationError(
                f"Message content exceeds maximum length of {settings.max_message_length} characters",
                field="content"
            )
        
        # Create message in database
        message = await self.repository.create_message(
            conversation_id=request.conversation_id,
            user_id=user_id,
            content=sanitized_content,
            role=MessageRole.USER,
            character_id=character_id,
            metadata=request.metadata
        )
        
        return self._to_response_model(message)
    
    async def get_message(self, message_id: str) -> MessageResponse:
        """Get a message by ID."""
        logger.info("Getting message", message_id=message_id)
        
        message = await self.repository.get_message_by_id(message_id)
        if not message:
            raise NotFoundError("Message", message_id)
        
        return self._to_response_model(message)
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        request: ConversationMessagesRequest
    ) -> List[MessageResponse]:
        """Get messages for a conversation."""
        logger.info(
            "Getting conversation messages",
            conversation_id=conversation_id,
            limit=request.limit
        )
        
        messages = await self.repository.get_conversation_messages(
            conversation_id=conversation_id,
            limit=request.limit,
            skip=0,  # TODO: Implement cursor-based pagination
            role=request.role,
            start_date=request.start_date,
            end_date=request.end_date,
            include_archived=request.include_archived
        )
        
        return [self._to_response_model(msg) for msg in messages]
    
    async def archive_message(self, message_id: str) -> MessageResponse:
        """Archive a message."""
        logger.info("Archiving message", message_id=message_id)
        
        message = await self.repository.archive_message(message_id)
        if not message:
            raise NotFoundError("Message", message_id)
        
        return self._to_response_model(message)
    
    async def update_message_metadata(
        self,
        message_id: str,
        metadata: Dict[str, Any]
    ) -> MessageResponse:
        """Update message metadata."""
        logger.info("Updating message metadata", message_id=message_id)
        
        message = await self.repository.update_message_metadata(message_id, metadata)
        if not message:
            raise NotFoundError("Message", message_id)
        
        return self._to_response_model(message)
    
    def _sanitize_content(self, content: str) -> str:
        """Sanitize message content."""
        # Basic HTML sanitization
        sanitized = bleach.clean(
            content,
            tags=[],  # Remove all HTML tags
            attributes={},  # Remove all attributes
            strip=True
        )
        
        # Remove extra whitespace
        sanitized = ' '.join(sanitized.split())
        
        return sanitized
    
    def _to_response_model(self, message: Message) -> MessageResponse:
        """Convert database model to response model."""
        return MessageResponse(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            user_id=message.user_id,
            character_id=message.character_id,
            content={
                'text': message.content.get('text', ''),
                'sanitized_text': message.content.get('sanitized_text'),
                'detected_language': message.content.get('detected_language'),
                'word_count': message.content.get('word_count'),
                'character_count': message.content.get('character_count')
            },
            role=MessageRole(message.role),
            message_type=message.message_type,
            status=MessageStatus(message.status),
            timestamps={
                'created_at': message.timestamps.get('created_at'),
                'processed_at': message.timestamps.get('processed_at'),
                'updated_at': message.timestamps.get('updated_at')
            },
            llm_metadata=message.llm_metadata,
            token_usage=message.token_usage,
            safety_metadata=message.safety_metadata,
            custom_metadata=message.custom_metadata
        )