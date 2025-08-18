from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import base64
import json
import re
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from app.models.conversation import (
    Conversation, 
    ConversationStatus, 
    ConversationSearchFilters,
    CursorInfo,
    UserStats
)

class ConversationRepository:
    async def create(self, conversation: Conversation) -> Conversation:
        """
        Create a new conversation in the database
        """
        await conversation.insert()
        return conversation

    async def find_by_user_id(
        self, 
        user_id: str, 
        status: Optional[ConversationStatus] = None,
        character_id: Optional[str] = None,
        limit: int = 50,
        skip: int = 0
    ) -> List[Conversation]:
        """
        Find conversations by user ID with filtering and pagination
        """
        query_filters = [Conversation.user_id == user_id]
        
        # Add status filter
        if status:
            query_filters.append(Conversation.status == status)
        else:
            # By default, exclude deleted conversations
            query_filters.append(Conversation.status != ConversationStatus.DELETED)
        
        # Add character filter
        if character_id:
            query_filters.append(Conversation.character_id == character_id)
        
        return await Conversation.find(*query_filters).sort("-created_at").skip(skip).limit(limit).to_list()

    async def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Find a conversation by ID
        """
        return await Conversation.get(conversation_id)

    async def update(self, conversation_id: str, update_data: Dict[str, Any]) -> Optional[Conversation]:
        """
        Update a conversation with new data
        """
        conversation = await self.find_by_id(conversation_id)
        if not conversation:
            return None
        
        # Update fields
        for field, value in update_data.items():
            setattr(conversation, field, value)
        
        await conversation.save()
        return conversation

    async def delete(self, conversation_id: str) -> bool:
        """
        Soft delete a conversation by marking it as deleted
        """
        conversation = await self.find_by_id(conversation_id)
        if not conversation:
            return False
        
        conversation.status = ConversationStatus.DELETED
        conversation.updated_at = datetime.utcnow()
        await conversation.save()
        return True

    async def archive(self, conversation_id: str) -> Optional[Conversation]:
        """
        Archive a conversation by setting status to archived
        """
        conversation = await self.find_by_id(conversation_id)
        if not conversation:
            return None
        
        if conversation.status == ConversationStatus.ARCHIVED:
            return conversation  # Already archived
        
        conversation.status = ConversationStatus.ARCHIVED
        conversation.updated_at = datetime.utcnow()
        await conversation.save()
        return conversation

    async def restore(self, conversation_id: str) -> Optional[Conversation]:
        """
        Restore an archived conversation by setting status to active
        """
        conversation = await self.find_by_id(conversation_id)
        if not conversation:
            return None
        
        if conversation.status != ConversationStatus.ARCHIVED:
            return None  # Can only restore archived conversations
        
        conversation.status = ConversationStatus.ACTIVE
        conversation.updated_at = datetime.utcnow()
        await conversation.save()
        return conversation

    async def count_user_conversations(self, user_id: str) -> int:
        """
        Count active conversations for a user
        """
        return await Conversation.find(
            Conversation.user_id == user_id,
            Conversation.status == ConversationStatus.ACTIVE
        ).count()

    async def count_total(
        self, 
        user_id: str, 
        status: Optional[ConversationStatus] = None,
        character_id: Optional[str] = None
    ) -> int:
        """
        Count total conversations matching filters
        """
        query_filters = [Conversation.user_id == user_id]
        
        if status:
            query_filters.append(Conversation.status == status)
        else:
            query_filters.append(Conversation.status != ConversationStatus.DELETED)
        
        if character_id:
            query_filters.append(Conversation.character_id == character_id)
        
        return await Conversation.find(*query_filters).count()
    
    # Advanced Features Methods
    
    def _encode_cursor(self, conversation: Conversation) -> str:
        """Encode conversation data into a cursor string."""
        cursor_data = {
            "id": str(conversation.id),
            "created_at": conversation.created_at.isoformat()
        }
        cursor_json = json.dumps(cursor_data, sort_keys=True)
        return base64.b64encode(cursor_json.encode()).decode()
    
    def _decode_cursor(self, cursor: str) -> Dict[str, Any]:
        """Decode cursor string into conversation data."""
        try:
            cursor_json = base64.b64decode(cursor.encode()).decode()
            return json.loads(cursor_json)
        except Exception:
            raise ValueError("Invalid cursor format")
    
    async def find_with_cursor_pagination(
        self,
        user_id: str,
        filters: ConversationSearchFilters
    ) -> Tuple[List[Conversation], CursorInfo]:
        """
        Find conversations with cursor-based pagination and advanced filtering.
        
        Returns:
            Tuple of (conversations, cursor_info)
        """
        query_filters = [Conversation.user_id == user_id]
        
        # Apply status filter
        if filters.status:
            query_filters.append(Conversation.status == filters.status)
        else:
            query_filters.append(Conversation.status != ConversationStatus.DELETED)
        
        # Apply character filter
        if filters.character_id:
            query_filters.append(Conversation.character_id == filters.character_id)
        
        # Apply search filter
        if filters.search:
            # Case-insensitive search in title
            search_pattern = re.escape(filters.search)
            query_filters.append(
                Conversation.title.regex(search_pattern, "i")
            )
        
        # Apply tags filter (conversations must have ALL specified tags)
        if filters.tags:
            for tag in filters.tags:
                query_filters.append(Conversation.tags.contains(tag))
        
        # Build base query
        query = Conversation.find(*query_filters)
        
        # Handle cursor-based pagination
        if filters.after:
            # Forward pagination
            cursor_data = self._decode_cursor(filters.after)
            cursor_date = datetime.fromisoformat(cursor_data["created_at"])
            cursor_id = ObjectId(cursor_data["id"])
            
            # Find items after this cursor (older items)
            query = query.find(
                {
                    "$or": [
                        {"created_at": {"$lt": cursor_date}},
                        {
                            "created_at": cursor_date,
                            "_id": {"$lt": cursor_id}
                        }
                    ]
                }
            )
        
        elif filters.before:
            # Backward pagination
            cursor_data = self._decode_cursor(filters.before)
            cursor_date = datetime.fromisoformat(cursor_data["created_at"])
            cursor_id = ObjectId(cursor_data["id"])
            
            # Find items before this cursor (newer items)
            query = query.find(
                {
                    "$or": [
                        {"created_at": {"$gt": cursor_date}},
                        {
                            "created_at": cursor_date,
                            "_id": {"$gt": cursor_id}
                        }
                    ]
                }
            )
        
        # Apply sorting and limits
        if filters.first:
            # Forward pagination - newest first (descending)
            query = query.sort([("created_at", DESCENDING), ("_id", DESCENDING)])
            limit = filters.first + 1  # +1 to check if there are more items
            conversations = await query.limit(limit).to_list()
            
            has_next_page = len(conversations) > filters.first
            if has_next_page:
                conversations = conversations[:-1]  # Remove extra item
            
            has_previous_page = filters.after is not None
            
        else:  # filters.last
            # Backward pagination - oldest first (ascending)
            query = query.sort([("created_at", ASCENDING), ("_id", ASCENDING)])
            limit = filters.last + 1
            conversations = await query.limit(limit).to_list()
            
            has_previous_page = len(conversations) > filters.last
            if has_previous_page:
                conversations = conversations[:-1]
            
            # Reverse order to get newest first
            conversations.reverse()
            has_next_page = filters.before is not None
        
        # Generate cursor info
        start_cursor = self._encode_cursor(conversations[0]) if conversations else None
        end_cursor = self._encode_cursor(conversations[-1]) if conversations else None
        
        cursor_info = CursorInfo(
            has_next_page=has_next_page,
            has_previous_page=has_previous_page,
            start_cursor=start_cursor,
            end_cursor=end_cursor
        )
        
        return conversations, cursor_info
    
    async def search_conversations(
        self,
        user_id: str,
        search_term: str,
        status: Optional[ConversationStatus] = None,
        limit: int = 20
    ) -> List[Conversation]:
        """
        Search conversations by title with text matching.
        
        Args:
            user_id: User identifier
            search_term: Text to search for in conversation titles
            status: Optional status filter
            limit: Maximum number of results
            
        Returns:
            List of matching conversations
        """
        query_filters = [Conversation.user_id == user_id]
        
        # Apply status filter
        if status:
            query_filters.append(Conversation.status == status)
        else:
            query_filters.append(Conversation.status != ConversationStatus.DELETED)
        
        # Apply search filter with case-insensitive regex
        if search_term:
            # Escape special regex characters for security
            escaped_term = re.escape(search_term.strip())
            query_filters.append(
                Conversation.title.regex(escaped_term, "i")
            )
        
        return await Conversation.find(*query_filters).sort("-created_at").limit(limit).to_list()
    
    async def get_conversations_by_tags(
        self,
        user_id: str,
        tags: List[str],
        match_all: bool = True,
        limit: int = 50
    ) -> List[Conversation]:
        """
        Find conversations by tags.
        
        Args:
            user_id: User identifier
            tags: List of tags to match
            match_all: If True, conversation must have all tags. If False, any tag.
            limit: Maximum number of results
            
        Returns:
            List of conversations matching tag criteria
        """
        query_filters = [
            Conversation.user_id == user_id,
            Conversation.status != ConversationStatus.DELETED
        ]
        
        if match_all:
            # Conversation must have ALL specified tags
            for tag in tags:
                query_filters.append(Conversation.tags.contains(tag))
        else:
            # Conversation must have ANY of the specified tags
            query_filters.append(Conversation.tags.in_(tags))
        
        return await Conversation.find(*query_filters).sort("-created_at").limit(limit).to_list()
    
    async def get_user_statistics(self, user_id: str) -> UserStats:
        """
        Generate comprehensive statistics for a user's conversations.
        
        Args:
            user_id: User identifier
            
        Returns:
            UserStats object with user's conversation statistics
        """
        # Get all user's conversations (including deleted for complete stats)
        all_conversations = await Conversation.find(
            Conversation.user_id == user_id
        ).to_list()
        
        if not all_conversations:
            return UserStats(
                total_conversations=0,
                active_conversations=0,
                archived_conversations=0,
                deleted_conversations=0,
                total_tags=0,
                most_used_tags=[],
                characters_chatted_with=0,
                oldest_conversation_date=None,
                newest_conversation_date=None
            )
        
        # Count by status
        status_counts = {
            ConversationStatus.ACTIVE: 0,
            ConversationStatus.ARCHIVED: 0,
            ConversationStatus.DELETED: 0
        }
        
        # Collect data for analysis
        all_tags = []
        character_ids = set()
        dates = []
        
        for conv in all_conversations:
            status_counts[conv.status] += 1
            all_tags.extend(conv.tags)
            character_ids.add(conv.character_id)
            dates.append(conv.created_at)
        
        # Analyze tags frequency
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Get top 5 most used tags
        most_used_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        most_used_tags = [tag for tag, count in most_used_tags]
        
        # Date analysis
        oldest_date = min(dates) if dates else None
        newest_date = max(dates) if dates else None
        
        return UserStats(
            total_conversations=len(all_conversations),
            active_conversations=status_counts[ConversationStatus.ACTIVE],
            archived_conversations=status_counts[ConversationStatus.ARCHIVED],
            deleted_conversations=status_counts[ConversationStatus.DELETED],
            total_tags=len(set(all_tags)),
            most_used_tags=most_used_tags,
            characters_chatted_with=len(character_ids),
            oldest_conversation_date=oldest_date,
            newest_conversation_date=newest_date
        )