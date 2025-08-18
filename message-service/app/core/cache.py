"""Cache implementation for context windows and other data."""

import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.redis_client import redis_client
from app.core.logging import get_logger

logger = get_logger(__name__)


class ContextCache:
    """Cache for conversation context windows."""
    
    def __init__(self):
        self.cache_prefix = "context"
        self.default_ttl = 600  # 10 minutes
    
    def _make_cache_key(self, conversation_id: str, window_size: int) -> str:
        """Generate cache key for context."""
        return f"{self.cache_prefix}:{conversation_id}:{window_size}"
    
    async def get_context(
        self, 
        conversation_id: str, 
        window_size: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached context window."""
        try:
            cache_key = self._make_cache_key(conversation_id, window_size)
            context = await redis_client.get_json(cache_key)
            
            if context:
                logger.debug(
                    "Context cache hit",
                    conversation_id=conversation_id,
                    window_size=window_size
                )
            else:
                logger.debug(
                    "Context cache miss",
                    conversation_id=conversation_id,
                    window_size=window_size
                )
            
            return context
            
        except Exception as e:
            logger.error(
                "Failed to get cached context",
                conversation_id=conversation_id,
                error=str(e)
            )
            return None
    
    async def set_context(
        self,
        conversation_id: str,
        window_size: int,
        context: List[Dict[str, Any]],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache context window."""
        try:
            cache_key = self._make_cache_key(conversation_id, window_size)
            ttl = ttl or self.default_ttl
            
            success = await redis_client.set_json(cache_key, context, ttl)
            
            if success:
                logger.debug(
                    "Context cached",
                    conversation_id=conversation_id,
                    window_size=window_size,
                    ttl=ttl
                )
            
            return success
            
        except Exception as e:
            logger.error(
                "Failed to cache context",
                conversation_id=conversation_id,
                error=str(e)
            )
            return False
    
    async def invalidate_context(self, conversation_id: str) -> int:
        """Invalidate all cached contexts for a conversation."""
        try:
            # In a production system, you'd use SCAN to find all keys with pattern
            # For now, we'll just delete common window sizes
            common_window_sizes = [10, 15, 20, 25, 30]
            deleted_count = 0
            
            for window_size in common_window_sizes:
                cache_key = self._make_cache_key(conversation_id, window_size)
                deleted_count += await redis_client.delete(cache_key)
            
            logger.debug(
                "Context invalidated",
                conversation_id=conversation_id,
                deleted_keys=deleted_count
            )
            
            return deleted_count
            
        except Exception as e:
            logger.error(
                "Failed to invalidate context",
                conversation_id=conversation_id,
                error=str(e)
            )
            return 0


class MessageCache:
    """Cache for frequently accessed messages."""
    
    def __init__(self):
        self.cache_prefix = "message"
        self.default_ttl = 1800  # 30 minutes
    
    def _make_cache_key(self, message_id: str) -> str:
        """Generate cache key for message."""
        return f"{self.cache_prefix}:{message_id}"
    
    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get cached message."""
        try:
            cache_key = self._make_cache_key(message_id)
            message = await redis_client.get_json(cache_key)
            
            if message:
                logger.debug("Message cache hit", message_id=message_id)
            else:
                logger.debug("Message cache miss", message_id=message_id)
            
            return message
            
        except Exception as e:
            logger.error("Failed to get cached message", message_id=message_id, error=str(e))
            return None
    
    async def set_message(
        self,
        message_id: str,
        message_data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> bool:
        """Cache message."""
        try:
            cache_key = self._make_cache_key(message_id)
            ttl = ttl or self.default_ttl
            
            success = await redis_client.set_json(cache_key, message_data, ttl)
            
            if success:
                logger.debug("Message cached", message_id=message_id, ttl=ttl)
            
            return success
            
        except Exception as e:
            logger.error("Failed to cache message", message_id=message_id, error=str(e))
            return False
    
    async def invalidate_message(self, message_id: str) -> int:
        """Invalidate cached message."""
        try:
            cache_key = self._make_cache_key(message_id)
            deleted = await redis_client.delete(cache_key)
            
            logger.debug("Message cache invalidated", message_id=message_id)
            return deleted
            
        except Exception as e:
            logger.error("Failed to invalidate message cache", message_id=message_id, error=str(e))
            return 0


# Global cache instances
context_cache = ContextCache()
message_cache = MessageCache()