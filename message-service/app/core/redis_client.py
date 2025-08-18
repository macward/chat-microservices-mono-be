"""Redis client configuration and connection management."""

import json
import redis.asyncio as redis
from typing import Optional, Any, Dict
from urllib.parse import urlparse

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import RedisError

logger = get_logger(__name__)


class RedisClient:
    """Redis client wrapper with connection management."""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[redis.ConnectionPool] = None
    
    async def connect(self):
        """Establish Redis connection."""
        try:
            logger.info("Connecting to Redis", url=settings.redis_url)
            
            # Parse Redis URL
            parsed_url = urlparse(settings.redis_url)
            
            # Create connection pool
            self._pool = redis.ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_connection_pool_max,
                decode_responses=True,
                encoding='utf-8'
            )
            
            # Create Redis client
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise RedisError("connect", f"Failed to connect to Redis: {str(e)}")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self._client:
            logger.info("Closing Redis connection")
            await self._client.aclose()
            self._client = None
        
        if self._pool:
            await self._pool.aclose()
            self._pool = None
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis."""
        try:
            if not self._client:
                await self.connect()
            
            value = await self._client.get(key)
            logger.debug("Redis GET", key=key, found=value is not None)
            return value
            
        except Exception as e:
            logger.error("Redis GET failed", key=key, error=str(e))
            raise RedisError("get", f"Failed to get key {key}: {str(e)}")
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in Redis with optional TTL."""
        try:
            if not self._client:
                await self.connect()
            
            ttl = ttl or settings.cache_ttl_seconds
            
            result = await self._client.setex(key, ttl, value)
            logger.debug("Redis SET", key=key, ttl=ttl, success=result)
            return result
            
        except Exception as e:
            logger.error("Redis SET failed", key=key, error=str(e))
            raise RedisError("set", f"Failed to set key {key}: {str(e)}")
    
    async def delete(self, key: str) -> int:
        """Delete key from Redis."""
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.delete(key)
            logger.debug("Redis DELETE", key=key, deleted=result)
            return result
            
        except Exception as e:
            logger.error("Redis DELETE failed", key=key, error=str(e))
            raise RedisError("delete", f"Failed to delete key {key}: {str(e)}")
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error("Redis EXISTS failed", key=key, error=str(e))
            raise RedisError("exists", f"Failed to check key {key}: {str(e)}")
    
    async def set_json(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON value in Redis."""
        try:
            json_value = json.dumps(value, default=str)
            return await self.set(key, json_value, ttl)
            
        except (TypeError, ValueError) as e:
            logger.error("JSON serialization failed", key=key, error=str(e))
            raise RedisError("set_json", f"Failed to serialize value for key {key}: {str(e)}")
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from Redis."""
        try:
            value = await self.get(key)
            if value is None:
                return None
            
            return json.loads(value)
            
        except json.JSONDecodeError as e:
            logger.error("JSON deserialization failed", key=key, error=str(e))
            raise RedisError("get_json", f"Failed to deserialize value for key {key}: {str(e)}")
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter in Redis."""
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.incrby(key, amount)
            logger.debug("Redis INCREMENT", key=key, amount=amount, new_value=result)
            return result
            
        except Exception as e:
            logger.error("Redis INCREMENT failed", key=key, error=str(e))
            raise RedisError("increment", f"Failed to increment key {key}: {str(e)}")
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key."""
        try:
            if not self._client:
                await self.connect()
            
            result = await self._client.expire(key, ttl)
            logger.debug("Redis EXPIRE", key=key, ttl=ttl, success=result)
            return result
            
        except Exception as e:
            logger.error("Redis EXPIRE failed", key=key, error=str(e))
            raise RedisError("expire", f"Failed to set TTL for key {key}: {str(e)}")


# Global Redis client instance
redis_client = RedisClient()