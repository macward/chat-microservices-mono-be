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
from app.core.exceptions import ValidationError, NotFoundError, LLMError
from app.core.logging import get_logger
from app.core.config import settings
from app.services.llm_service import LLMService, LLMMessage

logger = get_logger(__name__)


class MessageService:
    """Service for message operations."""
    
    def __init__(self):
        self.repository = MessageRepository()
        self.llm_service = LLMService()
    
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
    
    async def process_message_with_llm(
        self,
        request: CreateMessageRequest,
        user_id: str,
        character_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, MessageResponse]:
        """
        Create user message and generate LLM response.
        
        Returns:
            Dict with 'user_message' and 'assistant_message' keys
        """
        logger.info(
            "Processing message with LLM",
            conversation_id=request.conversation_id,
            user_id=user_id,
            character_id=character_id
        )
        
        # Create user message
        user_message = await self.create_message(request, user_id, character_id)
        
        try:
            # Build LLM conversation
            llm_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                llm_messages.append(LLMMessage("system", system_prompt))
            
            # Try to get conversation history for context, but don't fail if it doesn't work
            try:
                conversation_messages = await self.get_conversation_messages(
                    conversation_id=request.conversation_id,
                    request=ConversationMessagesRequest(limit=50)  # Last 50 messages for context
                )
                
                # Add conversation history (exclude the just-created message)
                for msg in conversation_messages[:-1]:  # Exclude the just-created message
                    role = "user" if msg.role == MessageRole.USER else "assistant"
                    llm_messages.append(LLMMessage(role, msg.content["text"]))
                    
                logger.info(
                    "Added conversation history",
                    conversation_id=request.conversation_id,
                    history_count=len(conversation_messages) - 1
                )
            except Exception as e:
                logger.warning(
                    "Failed to get conversation history, proceeding without context",
                    conversation_id=request.conversation_id,
                    error=str(e)
                )
            
            # Add current user message
            llm_messages.append(LLMMessage("user", request.content))
            
            # Send to LLM
            llm_response = await self.llm_service.send_message(
                messages=llm_messages,
                model=model,
                temperature=temperature
            )
            
            # Create assistant message with LLM response
            assistant_message = await self.repository.create_message(
                conversation_id=request.conversation_id,
                user_id="assistant",  # Special user ID for assistant
                content=llm_response.response,
                role=MessageRole.ASSISTANT,
                character_id=character_id,
                metadata={
                    "llm_metadata": {
                        "model": llm_response.model,
                        "correlation_id": llm_response.correlation_id,
                        "processing_time": llm_response.processing_time
                    },
                    "token_usage": {
                        "tokens_used": llm_response.tokens_used,
                        "model": llm_response.model
                    }
                }
            )
            
            logger.info(
                "LLM processing completed",
                correlation_id=llm_response.correlation_id,
                tokens_used=llm_response.tokens_used,
                processing_time=llm_response.processing_time
            )
            
            return {
                "user_message": user_message,
                "assistant_message": self._to_response_model(assistant_message)
            }
            
        except LLMError as e:
            logger.error(
                "LLM processing failed",
                error=str(e),
                error_code=e.code,
                conversation_id=request.conversation_id
            )
            # Return just the user message if LLM fails
            return {
                "user_message": user_message,
                "assistant_message": None,
                "error": {
                    "message": str(e),
                    "code": e.code
                }
            }
        except Exception as e:
            logger.error(
                "Unexpected error in LLM processing",
                error=str(e),
                conversation_id=request.conversation_id
            )
            return {
                "user_message": user_message,
                "assistant_message": None,
                "error": {
                    "message": "Unexpected error in message processing",
                    "code": "PROCESSING_ERROR"
                }
            }
    
    async def get_llm_health_status(self) -> Dict[str, Any]:
        """Get LLM service health status."""
        try:
            is_healthy = await self.llm_service.health_check()
            service_info = await self.llm_service.get_service_info()
            
            return {
                "healthy": is_healthy,
                "service_info": service_info,
                "base_url": settings.llm_service_url
            }
        except Exception as e:
            logger.error("Error checking LLM health", error=str(e))
            return {
                "healthy": False,
                "error": str(e),
                "base_url": settings.llm_service_url
            }
    
    def _to_response_model(self, message: Message) -> MessageResponse:
        """Convert database model to response model."""
        return MessageResponse(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            user_id=message.user_id,
            character_id=message.character_id,
            content={
                'text': message.content.text,
                'sanitized_text': message.content.sanitized_text,
                'detected_language': message.content.detected_language,
                'word_count': message.content.word_count,
                'character_count': message.content.character_count
            },
            role=MessageRole(message.role),
            message_type=message.message_type,
            status=MessageStatus(message.status),
            timestamps={
                'created_at': message.timestamps.created_at,
                'processed_at': message.timestamps.processed_at,
                'updated_at': message.timestamps.updated_at
            },
            llm_metadata=message.llm_metadata.model_dump() if message.llm_metadata else None,
            token_usage=message.token_usage.model_dump() if message.token_usage else None,
            safety_metadata=message.safety_metadata.model_dump() if message.safety_metadata else None,
            custom_metadata=message.custom_metadata
        )