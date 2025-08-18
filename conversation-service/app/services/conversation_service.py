from typing import List, Optional
from datetime import datetime
import re
import logging

from app.models.conversation import (
    Conversation, 
    ConversationCreate, 
    ConversationUpdate,
    ConversationResponse, 
    ConversationStatus,
    ConversationSearchFilters,
    PaginatedConversationResponse,
    UserStats
)
from app.repositories.conversation_repository import ConversationRepository
from app.api.exceptions import (
    ValidationException,
    SecurityException,
    BusinessLogicException,
    ResourceNotFoundException,
    QuotaExceededException,
    ErrorCode
)
from app.utils.logging import get_audit_logger
from app.config import settings

# Business rules constants
MAX_CONVERSATIONS_PER_USER = 100
MAX_TITLE_LENGTH = 200
MAX_TAGS_PER_CONVERSATION = 10
MAX_TAG_LENGTH = 20

logger = logging.getLogger(__name__)
# TODO: Fix audit logger initialization issue
# audit_logger = get_audit_logger()


class ConversationService:
    """Service layer for conversation management with comprehensive validation and security."""
    
    def __init__(self):
        self.repository = ConversationRepository()
        self.dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>',
            r'<object[^>]*>',
            r'<embed[^>]*>',
            r'<form[^>]*>',
            r'<input[^>]*>'
        ]

    async def create_conversation(
        self, 
        user_id: str, 
        data: ConversationCreate,
        ip_address: Optional[str] = None
    ) -> ConversationResponse:
        """
        Create a new conversation with comprehensive validation and security checks.
        
        Args:
            user_id: The ID of the user creating the conversation
            data: Conversation creation data
            ip_address: Client IP address for security logging
            
        Returns:
            ConversationResponse: The created conversation
            
        Raises:
            ValidationException: If input validation fails
            SecurityException: If security violations are detected
            BusinessLogicException: If business rules are violated
            QuotaExceededException: If user has too many conversations
        """
        # Validate user ID format
        logger.debug(f"Starting user ID validation for {user_id[:8]}...")
        await self._validate_user_id(user_id)
        logger.debug("User ID validation completed")
        
        # Validate character ID format (already done by Pydantic, but double-check)
        logger.debug(f"Starting character ID validation for {data.character_id[:8]}...")
        await self._validate_character_id(data.character_id)
        logger.debug("Character ID validation completed")
        
        # Security validation for title and tags
        if data.title:
            logger.debug(f"Starting title security validation...")
            await self._validate_title_security(data.title)
            logger.debug("Title security validation completed")
        
        logger.debug("Starting tags security validation...")
        await self._validate_tags_security(data.tags)
        logger.debug("Tags security validation completed")
        
        # Business logic validations
        # TODO: Re-enable for production
        # await self._check_user_conversation_quota(user_id)
        # TODO: Re-enable when Characters Service is running
        # await self._validate_character_exists(data.character_id)
        
        # Log the creation attempt
        logger.info(
            f"Creating conversation for user {user_id[:8]}...",
            extra={
                "user_id": user_id[:8] + "...",
                "character_id": data.character_id[:8] + "...",
                "ip_address": ip_address
            }
        )
        
        try:
            # Create the conversation
            conversation_data = Conversation(
                user_id=user_id,
                character_id=data.character_id,
                title=data.title.strip() if data.title else None,
                tags=data.tags or []
            )
            
            created_conversation = await self.repository.create(conversation_data)
            
            # Log successful creation
            # TODO: Fix audit logger
            # audit_logger.log_conversation_created(
            #     conversation_id=str(created_conversation.id),
            #     user_id=user_id,
            #     character_id=data.character_id,
            #     ip_address=ip_address
            # )
            
            # Convert MongoDB document to response format
            conversation_dict = created_conversation.model_dump()
            conversation_dict["id"] = str(created_conversation.id)
            return ConversationResponse.model_validate(conversation_dict)
            
        except Exception as e:
            logger.error(
                f"Failed to create conversation for user {user_id[:8]}...",
                extra={
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to create conversation",
                details={"operation": "create_conversation"}
            )

    async def list_conversations(
        self, 
        user_id: str,
        status: Optional[ConversationStatus] = None,
        character_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0,
        ip_address: Optional[str] = None
    ) -> List[ConversationResponse]:
        """
        List conversations for a user with pagination and filtering.
        
        Args:
            user_id: The ID of the user
            status: Optional status filter
            character_id: Optional character ID filter
            limit: Maximum number of conversations to return
            skip: Number of conversations to skip
            ip_address: Client IP address for security logging
            
        Returns:
            List[ConversationResponse]: List of conversations
            
        Raises:
            ValidationException: If input validation fails
        """
        # Validate user ID
        await self._validate_user_id(user_id)
        
        # Validate pagination parameters
        if limit <= 0 or limit > 100:
            raise ValidationException(
                "Limit must be between 1 and 100",
                field="limit",
                value=str(limit)
            )
        
        if skip < 0:
            raise ValidationException(
                "Skip must be non-negative",
                field="skip",
                value=str(skip)
            )
        
        # Log access attempt
        # audit_logger.log_access_attempt(
        #     user_id=user_id,
        #     resource_type="conversations",
        #     resource_id="list",
        #     action="list",
        #     success=True,
        #     ip_address=ip_address
        # )
        
        try:
            conversations = await self.repository.find_by_user_id(
                user_id, 
                status=status,
                character_id=character_id,
                limit=limit, 
                skip=skip
            )
            
            # Convert MongoDB documents to response format
            conversation_responses = []
            for conv in conversations:
                # Convert ObjectId to string for Pydantic validation
                conv_dict = conv.model_dump()
                conv_dict["id"] = str(conv.id)
                conversation_responses.append(ConversationResponse.model_validate(conv_dict))
            
            return conversation_responses
            
        except Exception as e:
            logger.error(
                f"Failed to list conversations for user {user_id[:8]}...",
                extra={
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to retrieve conversations",
                details={"operation": "list_conversations"}
            )
    
    async def get_conversation(
        self,
        conversation_id: str,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> ConversationResponse:
        """
        Get a specific conversation by ID with ownership validation.
        
        Args:
            conversation_id: The conversation ID
            user_id: The user ID (for ownership validation)
            ip_address: Client IP address for security logging
            
        Returns:
            ConversationResponse: The conversation
            
        Raises:
            ValidationException: If input validation fails
            ResourceNotFoundException: If conversation not found
            SecurityException: If user doesn't own the conversation
        """
        # Validate IDs
        await self._validate_conversation_id(conversation_id)
        await self._validate_user_id(user_id)
        
        # Log access attempt
        # audit_logger.log_access_attempt(
        #     user_id=user_id,
        #     resource_type="conversation",
        #     resource_id=conversation_id,
        #     action="get",
        #     success=False,  # Will be updated if successful
        #     ip_address=ip_address
        # )
        
        try:
            conversation = await self.repository.find_by_id(conversation_id)
            
            if not conversation:
                raise ResourceNotFoundException(
                    "Conversation",
                    conversation_id
                )
            
            # Verify ownership
            if conversation.user_id != user_id:
                # audit_logger.log_security_event(
                #     event_type="UNAUTHORIZED_ACCESS_ATTEMPT",
                #     description=f"User attempted to access conversation they don't own",
                #     severity="high",
                #     user_id=user_id,
                #     ip_address=ip_address,
                #     additional_data={
                #         "conversation_id": conversation_id,
                #         "conversation_owner": conversation.user_id[:8] + "..."
                #     }
                # )
                raise SecurityException(
                    "Access denied: conversation not owned by user",
                    ErrorCode.FORBIDDEN
                )
            
            # Log successful access
            # audit_logger.log_access_attempt(
            #     user_id=user_id,
            #     resource_type="conversation",
            #     resource_id=conversation_id,
            #     action="get",
            #     success=True,
            #     ip_address=ip_address
            # )
            
            return ConversationResponse.model_validate(conversation)
            
        except (ResourceNotFoundException, SecurityException):
            raise
        except Exception as e:
            logger.error(
                f"Failed to get conversation {conversation_id[:8]}... for user {user_id[:8]}...",
                extra={
                    "conversation_id": conversation_id[:8] + "...",
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to retrieve conversation",
                details={"operation": "get_conversation"}
            )
    
    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        data: ConversationUpdate,
        ip_address: Optional[str] = None
    ) -> ConversationResponse:
        """
        Update a conversation with validation and ownership checks.
        
        Args:
            conversation_id: The conversation ID
            user_id: The user ID (for ownership validation)
            data: Update data
            ip_address: Client IP address for security logging
            
        Returns:
            ConversationResponse: The updated conversation
            
        Raises:
            ValidationException: If input validation fails
            ResourceNotFoundException: If conversation not found
            SecurityException: If user doesn't own the conversation
        """
        # Get the existing conversation (includes ownership validation)
        conversation = await self.get_conversation(conversation_id, user_id, ip_address)
        
        # Security validation for updated fields
        if data.title:
            await self._validate_title_security(data.title)
        
        if data.tags:
            await self._validate_tags_security(data.tags)
        
        # Build update data
        update_data = {"updated_at": datetime.utcnow()}
        modified_fields = []
        
        if data.title is not None:
            update_data["title"] = data.title.strip() if data.title else None
            modified_fields.append("title")
        
        if data.status is not None:
            update_data["status"] = data.status
            modified_fields.append("status")
        
        if data.tags is not None:
            update_data["tags"] = data.tags
            modified_fields.append("tags")
        
        try:
            updated_conversation = await self.repository.update(
                conversation_id, 
                update_data
            )
            
            # Log the update
            # audit_logger.log_conversation_updated(
            #     conversation_id=conversation_id,
            #     user_id=user_id,
            #     modified_fields=modified_fields,
            #     ip_address=ip_address
            # )
            
            return ConversationResponse.model_validate(updated_conversation)
            
        except Exception as e:
            logger.error(
                f"Failed to update conversation {conversation_id[:8]}... for user {user_id[:8]}...",
                extra={
                    "conversation_id": conversation_id[:8] + "...",
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to update conversation",
                details={"operation": "update_conversation"}
            )
    
    async def delete_conversation(
        self,
        conversation_id: str,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Delete a conversation with ownership validation.
        
        Args:
            conversation_id: The conversation ID
            user_id: The user ID (for ownership validation)
            ip_address: Client IP address for security logging
            
        Returns:
            bool: True if deleted successfully
            
        Raises:
            ValidationException: If input validation fails
            ResourceNotFoundException: If conversation not found
            SecurityException: If user doesn't own the conversation
        """
        # Get the existing conversation (includes ownership validation)
        await self.get_conversation(conversation_id, user_id, ip_address)
        
        try:
            success = await self.repository.delete(conversation_id)
            
            if success:
                # Log the deletion
                # audit_logger.log_conversation_deleted(
                #     conversation_id=conversation_id,
                #     user_id=user_id,
                #     ip_address=ip_address
                # )
                pass
            
            return success
            
        except Exception as e:
            logger.error(
                f"Failed to delete conversation {conversation_id[:8]}... for user {user_id[:8]}...",
                extra={
                    "conversation_id": conversation_id[:8] + "...",
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to delete conversation",
                details={"operation": "delete_conversation"}
            )

    async def archive_conversation(
        self,
        conversation_id: str,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> ConversationResponse:
        """
        Archive a conversation with ownership validation.
        
        Args:
            conversation_id: The conversation ID
            user_id: The user ID (for ownership validation)
            ip_address: Client IP address for security logging
            
        Returns:
            ConversationResponse: The archived conversation
            
        Raises:
            ValidationException: If input validation fails
            ResourceNotFoundException: If conversation not found
            SecurityException: If user doesn't own the conversation
            BusinessLogicException: If conversation is already archived or deleted
        """
        # Get the existing conversation (includes ownership validation)
        existing_conversation = await self.get_conversation(conversation_id, user_id, ip_address)
        
        # Check if conversation can be archived
        if existing_conversation.status == ConversationStatus.ARCHIVED:
            raise BusinessLogicException(
                "Conversation is already archived",
                ErrorCode.INVALID_STATE_TRANSITION,
                details={"current_status": existing_conversation.status}
            )
        
        if existing_conversation.status == ConversationStatus.DELETED:
            raise BusinessLogicException(
                "Cannot archive deleted conversation",
                ErrorCode.INVALID_STATE_TRANSITION,
                details={"current_status": existing_conversation.status}
            )
        
        try:
            archived_conversation = await self.repository.archive(conversation_id)
            
            if not archived_conversation:
                raise BusinessLogicException(
                    "Failed to archive conversation",
                    details={"operation": "archive_conversation"}
                )
            
            # Log the archival
            # audit_logger.log_conversation_updated(
            #     conversation_id=conversation_id,
            #     user_id=user_id,
            #     modified_fields=["status"],
            #     additional_data={"action": "archived"},
            #     ip_address=ip_address
            # )
            
            return ConversationResponse.model_validate(archived_conversation)
            
        except (ValidationException, SecurityException, BusinessLogicException):
            raise
        except Exception as e:
            logger.error(
                f"Failed to archive conversation {conversation_id[:8]}... for user {user_id[:8]}...",
                extra={
                    "conversation_id": conversation_id[:8] + "...",
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to archive conversation",
                details={"operation": "archive_conversation"}
            )

    async def restore_conversation(
        self,
        conversation_id: str,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> ConversationResponse:
        """
        Restore an archived conversation with ownership validation.
        
        Args:
            conversation_id: The conversation ID
            user_id: The user ID (for ownership validation)
            ip_address: Client IP address for security logging
            
        Returns:
            ConversationResponse: The restored conversation
            
        Raises:
            ValidationException: If input validation fails
            ResourceNotFoundException: If conversation not found
            SecurityException: If user doesn't own the conversation
            BusinessLogicException: If conversation is not archived
        """
        # Get the existing conversation (includes ownership validation)
        existing_conversation = await self.get_conversation(conversation_id, user_id, ip_address)
        
        # Check if conversation can be restored
        if existing_conversation.status != ConversationStatus.ARCHIVED:
            raise BusinessLogicException(
                "Only archived conversations can be restored",
                ErrorCode.INVALID_STATE_TRANSITION,
                details={"current_status": existing_conversation.status}
            )
        
        try:
            restored_conversation = await self.repository.restore(conversation_id)
            
            if not restored_conversation:
                raise BusinessLogicException(
                    "Failed to restore conversation",
                    details={"operation": "restore_conversation"}
                )
            
            # Log the restoration
            # audit_logger.log_conversation_updated(
            #     conversation_id=conversation_id,
            #     user_id=user_id,
            #     modified_fields=["status"],
            #     additional_data={"action": "restored"},
            #     ip_address=ip_address
            # )
            
            return ConversationResponse.model_validate(restored_conversation)
            
        except (ValidationException, SecurityException, BusinessLogicException):
            raise
        except Exception as e:
            logger.error(
                f"Failed to restore conversation {conversation_id[:8]}... for user {user_id[:8]}...",
                extra={
                    "conversation_id": conversation_id[:8] + "...",
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to restore conversation",
                details={"operation": "restore_conversation"}
            )
    
    # Private validation methods
    
    async def _validate_user_id(self, user_id: str) -> None:
        """Validate user ID format."""
        if not user_id or not str(user_id).strip():
            raise ValidationException(
                "User ID is required",
                field="user_id",
                error_code=ErrorCode.FIELD_REQUIRED
            )
        
        user_id = str(user_id).strip()
        
        # Check various ID formats: ObjectId, UUID, numeric, or alphanumeric
        if not (re.match(r'^[0-9a-fA-F]{24}$', user_id) or 
                re.match(r'^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$', user_id) or
                re.match(r'^\d+$', user_id) or
                (re.match(r'^[a-zA-Z0-9_-]+$', user_id) and 1 <= len(user_id) <= 50)):
            raise ValidationException(
                "Invalid user ID format",
                field="user_id",
                value=user_id,
                error_code=ErrorCode.INVALID_INPUT_FORMAT
            )
    
    async def _validate_character_id(self, character_id: str) -> None:
        """Validate character ID format."""
        if not character_id or not str(character_id).strip():
            raise ValidationException(
                "Character ID is required",
                field="character_id",
                error_code=ErrorCode.FIELD_REQUIRED
            )
        
        character_id = str(character_id).strip()
        
        # Check various ID formats: ObjectId, UUID, numeric, or alphanumeric
        if not (re.match(r'^[0-9a-fA-F]{24}$', character_id) or 
                re.match(r'^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$', character_id) or
                re.match(r'^\d+$', character_id) or
                (re.match(r'^[a-zA-Z0-9_-]+$', character_id) and 1 <= len(character_id) <= 50)):
            raise ValidationException(
                "Invalid character ID format",
                field="character_id",
                value=character_id,
                error_code=ErrorCode.INVALID_INPUT_FORMAT
            )
    
    async def _validate_conversation_id(self, conversation_id: str) -> None:
        """Validate conversation ID format."""
        if not conversation_id or not conversation_id.strip():
            raise ValidationException(
                "Conversation ID is required",
                field="conversation_id",
                error_code=ErrorCode.FIELD_REQUIRED
            )
        
        conversation_id = conversation_id.strip()
        
        # Check format (ObjectId or UUID)
        if not (re.match(r'^[0-9a-fA-F]{24}$', conversation_id) or 
                re.match(r'^[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}$', conversation_id)):
            raise ValidationException(
                "Invalid conversation ID format",
                field="conversation_id",
                value=conversation_id,
                error_code=ErrorCode.INVALID_INPUT_FORMAT
            )
    
    async def _validate_title_security(self, title: str) -> None:
        """Validate title for security issues."""
        if not title:
            return
        
        title_lower = title.lower()
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, title_lower):
                # audit_logger.log_security_event(
                #     event_type="DANGEROUS_CONTENT_DETECTED",
                #     description=f"Potentially dangerous content in title",
                #     severity="high",
                #     additional_data={
                #         "field": "title",
                #         "pattern_matched": pattern,
                #         "content_sample": title[:50]
                #     }
                # )
                raise SecurityException(
                    "Title contains potentially dangerous content",
                    ErrorCode.DANGEROUS_CONTENT
                )
    
    async def _validate_tags_security(self, tags: List[str]) -> None:
        """Validate tags for security issues."""
        if not tags:
            return
        
        for tag in tags:
            tag_lower = tag.lower()
            
            # Check for dangerous patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, tag_lower):
                    # audit_logger.log_security_event(
                    #     event_type="DANGEROUS_CONTENT_DETECTED",
                    #     description=f"Potentially dangerous content in tag",
                    #     severity="high",
                    #     additional_data={
                    #         "field": "tags",
                    #         "pattern_matched": pattern,
                    #         "content_sample": tag[:50]
                    #     }
                    # )
                    raise SecurityException(
                        "Tag contains potentially dangerous content",
                        ErrorCode.DANGEROUS_CONTENT
                    )
    
    async def _check_user_conversation_quota(self, user_id: str) -> None:
        """Check if user has exceeded conversation quota."""
        try:
            count = await self.repository.count_user_conversations(user_id)
            
            if count >= MAX_CONVERSATIONS_PER_USER:
                # audit_logger.log_security_event(
                #     event_type="QUOTA_EXCEEDED",
                #     description=f"User exceeded conversation quota",
                #     severity="medium",
                #     user_id=user_id,
                #     additional_data={
                #         "current_count": count,
                #         "max_allowed": MAX_CONVERSATIONS_PER_USER
                #     }
                # )
                raise QuotaExceededException(
                    "conversations",
                    count,
                    MAX_CONVERSATIONS_PER_USER
                )
                
        except QuotaExceededException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to check conversation quota for user {user_id[:8]}...",
                extra={"user_id": user_id[:8] + "...", "error": str(e)},
                exc_info=True
            )
            # Don't fail the operation due to quota check failure
            pass
    
    async def _validate_character_exists(self, character_id: str) -> None:
        """Validate that the character exists using Characters Service."""
        from app.services.external_clients import characters_client
        
        try:
            exists = await characters_client.validate_character_exists(character_id)
            if not exists:
                raise ValidationException(
                    "Character not found",
                    field="character_id",
                    value=character_id,
                    error_code=ErrorCode.NOT_FOUND
                )
        except ValidationException:
            raise
        except Exception as e:
            logger.warning(
                f"Character validation failed for {character_id[:8]}..., continuing without validation",
                extra={
                    "character_id": character_id[:8] + "...",
                    "error": str(e)
                }
            )
            # In case of external service failure, we allow the operation to continue
            # This is a business decision - we don't want external service failures
            # to completely block conversation creation
    
    # Advanced Features Methods
    
    async def list_conversations_advanced(
        self,
        user_id: str,
        filters: ConversationSearchFilters,
        ip_address: Optional[str] = None
    ) -> PaginatedConversationResponse:
        """
        List conversations with advanced filtering, search, and cursor-based pagination.
        
        Args:
            user_id: The user ID
            filters: Search and filter parameters
            ip_address: Client IP address for security logging
            
        Returns:
            PaginatedConversationResponse: Paginated list with cursor information
            
        Raises:
            ValidationException: If input validation fails
        """
        # Validate user ID
        await self._validate_user_id(user_id)
        
        # Log access attempt
        # audit_logger.log_access_attempt(
        #     user_id=user_id,
        #     resource_type="conversations",
        #     resource_id="advanced_list",
        #     action="list_advanced",
        #     success=True,
        #     ip_address=ip_address
        # )
        
        try:
            conversations, cursor_info = await self.repository.find_with_cursor_pagination(
                user_id, filters
            )
            
            # Convert to response models
            conversation_responses = [
                ConversationResponse.model_validate(conv) 
                for conv in conversations
            ]
            
            # Get total count if requested (for first page only to avoid performance issues)
            total_count = None
            if filters.after is None and filters.before is None:
                # Only calculate total for first page
                total_count = await self.repository.count_total(
                    user_id,
                    status=filters.status,
                    character_id=filters.character_id
                )
            
            return PaginatedConversationResponse(
                conversations=conversation_responses,
                page_info=cursor_info,
                total_count=total_count
            )
            
        except Exception as e:
            logger.error(
                f"Failed to list conversations for user {user_id[:8]}...",
                extra={
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to retrieve conversations",
                details={"operation": "list_conversations_advanced"}
            )
    
    async def search_conversations(
        self,
        user_id: str,
        search_term: str,
        status: Optional[ConversationStatus] = None,
        limit: int = 20,
        ip_address: Optional[str] = None
    ) -> List[ConversationResponse]:
        """
        Search conversations by title with text matching.
        
        Args:
            user_id: The user ID
            search_term: Text to search for in conversation titles
            status: Optional status filter
            limit: Maximum number of results (max 50)
            ip_address: Client IP address for security logging
            
        Returns:
            List[ConversationResponse]: List of matching conversations
            
        Raises:
            ValidationException: If input validation fails
        """
        # Validate user ID
        await self._validate_user_id(user_id)
        
        # Validate search term
        if not search_term or not search_term.strip():
            raise ValidationException(
                "Search term is required",
                field="search_term",
                error_code=ErrorCode.FIELD_REQUIRED
            )
        
        search_term = search_term.strip()
        if len(search_term) < 2:
            raise ValidationException(
                "Search term must be at least 2 characters",
                field="search_term",
                value=search_term
            )
        
        if len(search_term) > 100:
            raise ValidationException(
                "Search term is too long",
                field="search_term",
                value=search_term[:50] + "..."
            )
        
        # Validate limit
        if limit <= 0 or limit > 50:
            raise ValidationException(
                "Limit must be between 1 and 50",
                field="limit",
                value=str(limit)
            )
        
        # Security validation for search term
        dangerous_chars = ['$', '{', '}', '(', ')', '*', '+', '?', '^', '|', '\\']
        for char in dangerous_chars:
            if char in search_term:
                raise SecurityException(
                    f"Search term contains invalid character: {char}",
                    ErrorCode.DANGEROUS_CONTENT
                )
        
        # Log search attempt
        # audit_logger.log_access_attempt(
        #     user_id=user_id,
        #     resource_type="conversations",
        #     resource_id="search",
        #     action="search",
        #     success=True,
        #     ip_address=ip_address,
        #     additional_data={"search_term": search_term[:50]}
        # )
        
        try:
            conversations = await self.repository.search_conversations(
                user_id, search_term, status, limit
            )
            
            return [
                ConversationResponse.model_validate(conv) 
                for conv in conversations
            ]
            
        except Exception as e:
            logger.error(
                f"Failed to search conversations for user {user_id[:8]}...",
                extra={
                    "user_id": user_id[:8] + "...",
                    "search_term": search_term[:50],
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to search conversations",
                details={"operation": "search_conversations"}
            )
    
    async def get_conversations_by_tags(
        self,
        user_id: str,
        tags: List[str],
        match_all: bool = True,
        limit: int = 50,
        ip_address: Optional[str] = None
    ) -> List[ConversationResponse]:
        """
        Find conversations by tags with flexible matching.
        
        Args:
            user_id: The user ID
            tags: List of tags to match
            match_all: If True, must have all tags. If False, any tag.
            limit: Maximum number of results
            ip_address: Client IP address for security logging
            
        Returns:
            List[ConversationResponse]: List of conversations matching tag criteria
            
        Raises:
            ValidationException: If input validation fails
        """
        # Validate user ID
        await self._validate_user_id(user_id)
        
        # Validate tags
        if not tags:
            raise ValidationException(
                "At least one tag is required",
                field="tags",
                error_code=ErrorCode.FIELD_REQUIRED
            )
        
        if len(tags) > 5:
            raise ValidationException(
                "Maximum 5 tags allowed for search",
                field="tags",
                value=str(len(tags))
            )
        
        # Validate each tag
        validated_tags = []
        for tag in tags:
            tag = tag.strip().lower()
            if not tag:
                continue
            
            if not re.match(r'^[a-zA-Z0-9_]{1,20}$', tag):
                raise ValidationException(
                    f"Tag '{tag}' is invalid",
                    field="tags",
                    value=tag
                )
            
            if tag not in validated_tags:
                validated_tags.append(tag)
        
        if not validated_tags:
            raise ValidationException(
                "No valid tags provided",
                field="tags",
                error_code=ErrorCode.FIELD_REQUIRED
            )
        
        # Validate limit
        if limit <= 0 or limit > 100:
            raise ValidationException(
                "Limit must be between 1 and 100",
                field="limit",
                value=str(limit)
            )
        
        # Log search attempt
        # audit_logger.log_access_attempt(
        #     user_id=user_id,
        #     resource_type="conversations",
        #     resource_id="tags_search",
        #     action="search_by_tags",
        #     success=True,
        #     ip_address=ip_address,
        #     additional_data={
        #         "tags": validated_tags,
        #         "match_all": match_all
        #     }
        # )
        
        try:
            conversations = await self.repository.get_conversations_by_tags(
                user_id, validated_tags, match_all, limit
            )
            
            return [
                ConversationResponse.model_validate(conv) 
                for conv in conversations
            ]
            
        except Exception as e:
            logger.error(
                f"Failed to get conversations by tags for user {user_id[:8]}...",
                extra={
                    "user_id": user_id[:8] + "...",
                    "tags": validated_tags,
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to get conversations by tags",
                details={"operation": "get_conversations_by_tags"}
            )
    
    async def get_user_statistics(
        self,
        user_id: str,
        ip_address: Optional[str] = None
    ) -> UserStats:
        """
        Get comprehensive statistics for a user's conversations.
        
        Args:
            user_id: The user ID
            ip_address: Client IP address for security logging
            
        Returns:
            UserStats: User's conversation statistics
            
        Raises:
            ValidationException: If input validation fails
        """
        # Validate user ID
        await self._validate_user_id(user_id)
        
        # Log access attempt
        # audit_logger.log_access_attempt(
        #     user_id=user_id,
        #     resource_type="user_stats",
        #     resource_id=user_id,
        #     action="get_stats",
        #     success=True,
        #     ip_address=ip_address
        # )
        
        try:
            stats = await self.repository.get_user_statistics(user_id)
            
            logger.info(
                f"Generated statistics for user {user_id[:8]}...",
                extra={
                    "user_id": user_id[:8] + "...",
                    "total_conversations": stats.total_conversations,
                    "ip_address": ip_address
                }
            )
            
            return stats
            
        except Exception as e:
            logger.error(
                f"Failed to get statistics for user {user_id[:8]}...",
                extra={
                    "user_id": user_id[:8] + "...",
                    "error": str(e),
                    "ip_address": ip_address
                },
                exc_info=True
            )
            raise BusinessLogicException(
                "Failed to get user statistics",
                details={"operation": "get_user_statistics"}
            )