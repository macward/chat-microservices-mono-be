"""Message repository for database operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from beanie import PydanticObjectId
from beanie.odm.operators.find.comparison import In
from pymongo import DESCENDING

from app.models.database import Message
from app.models.message import MessageRole, MessageStatus
from app.core.exceptions import NotFoundError, DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MessageRepository:
    """Repository for message database operations."""

    async def create_message(
        self,
        conversation_id: str,
        user_id: str,
        content: str,
        role: MessageRole = MessageRole.USER,
        character_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Create a new message."""
        try:
            message = Message(
                conversation_id=conversation_id,
                user_id=user_id,
                content={'text': content},
                role=role.value,
                character_id=character_id,
                timestamps={'created_at': datetime.utcnow()},
                custom_metadata=metadata or {}
            )
            
            await message.insert()
            logger.info("Message created", message_id=message.message_id)
            return message
            
        except Exception as e:
            logger.error("Failed to create message", error=str(e))
            raise DatabaseError("create_message", f"Failed to create message: {str(e)}")

    async def get_message_by_id(self, message_id: str) -> Optional[Message]:
        """Get a message by its ID."""
        try:
            message = await Message.find_one(Message.message_id == message_id)
            if not message:
                logger.warning("Message not found", message_id=message_id)
            return message
            
        except Exception as e:
            logger.error("Failed to get message", message_id=message_id, error=str(e))
            raise DatabaseError("get_message", f"Failed to get message: {str(e)}")

    async def get_conversation_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        skip: int = 0,
        role: Optional[MessageRole] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_archived: bool = False
    ) -> List[Message]:
        """Get messages for a conversation with filtering."""
        try:
            # Build query
            query = Message.conversation_id == conversation_id
            
            # Add role filter
            if role:
                query = query & (Message.role == role.value)
            
            # Add date range filter
            if start_date:
                query = query & (Message.timestamps['created_at'] >= start_date)
            if end_date:
                query = query & (Message.timestamps['created_at'] <= end_date)
            
            # Add status filter
            if not include_archived:
                query = query & (Message.status == MessageStatus.ACTIVE.value)
            
            # Execute query with pagination and sorting
            messages = await Message.find(query)\
                .sort(-Message.timestamps['created_at'])\
                .skip(skip)\
                .limit(limit)\
                .to_list()
            
            logger.info(
                "Retrieved conversation messages", 
                conversation_id=conversation_id,
                count=len(messages)
            )
            return messages
            
        except Exception as e:
            logger.error(
                "Failed to get conversation messages", 
                conversation_id=conversation_id,
                error=str(e)
            )
            raise DatabaseError("get_conversation_messages", f"Failed to get messages: {str(e)}")

    async def count_conversation_messages(
        self,
        conversation_id: str,
        role: Optional[MessageRole] = None,
        include_archived: bool = False
    ) -> int:
        """Count messages in a conversation."""
        try:
            query = Message.conversation_id == conversation_id
            
            if role:
                query = query & (Message.role == role.value)
            
            if not include_archived:
                query = query & (Message.status == MessageStatus.ACTIVE.value)
            
            count = await Message.find(query).count()
            return count
            
        except Exception as e:
            logger.error(
                "Failed to count conversation messages",
                conversation_id=conversation_id,
                error=str(e)
            )
            raise DatabaseError("count_messages", f"Failed to count messages: {str(e)}")

    async def update_message_metadata(
        self,
        message_id: str,
        metadata: Dict[str, Any]
    ) -> Optional[Message]:
        """Update message custom metadata."""
        try:
            message = await self.get_message_by_id(message_id)
            if not message:
                raise NotFoundError("Message", message_id)
            
            # Update metadata
            message.custom_metadata.update(metadata)
            message.timestamps['updated_at'] = datetime.utcnow()
            
            await message.save()
            logger.info("Message metadata updated", message_id=message_id)
            return message
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Failed to update message metadata",
                message_id=message_id,
                error=str(e)
            )
            raise DatabaseError("update_metadata", f"Failed to update metadata: {str(e)}")

    async def archive_message(self, message_id: str) -> Optional[Message]:
        """Archive a message (soft delete)."""
        try:
            message = await self.get_message_by_id(message_id)
            if not message:
                raise NotFoundError("Message", message_id)
            
            message.status = MessageStatus.ARCHIVED.value
            message.timestamps['updated_at'] = datetime.utcnow()
            
            await message.save()
            logger.info("Message archived", message_id=message_id)
            return message
            
        except NotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to archive message", message_id=message_id, error=str(e))
            raise DatabaseError("archive_message", f"Failed to archive message: {str(e)}")

    async def get_user_messages(
        self,
        user_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Message]:
        """Get messages for a user."""
        try:
            messages = await Message.find(Message.user_id == user_id)\
                .sort(-Message.timestamps['created_at'])\
                .skip(skip)\
                .limit(limit)\
                .to_list()
            
            logger.info("Retrieved user messages", user_id=user_id, count=len(messages))
            return messages
            
        except Exception as e:
            logger.error("Failed to get user messages", user_id=user_id, error=str(e))
            raise DatabaseError("get_user_messages", f"Failed to get user messages: {str(e)}")

    async def search_messages(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Message]:
        """Basic text search in messages."""
        try:
            # Build search query
            search_filter = {"$text": {"$search": query}}
            
            if conversation_id:
                search_filter["conversation_id"] = conversation_id
            if user_id:
                search_filter["user_id"] = user_id
            
            messages = await Message.find(search_filter)\
                .limit(limit)\
                .to_list()
            
            logger.info("Message search completed", query=query, count=len(messages))
            return messages
            
        except Exception as e:
            logger.error("Failed to search messages", query=query, error=str(e))
            raise DatabaseError("search_messages", f"Failed to search messages: {str(e)}")