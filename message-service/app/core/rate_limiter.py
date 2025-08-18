"""Rate limiting implementation."""

import time
from typing import Dict, Tuple
from datetime import datetime, timedelta

from app.core.exceptions import RateLimitExceeded
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class InMemoryRateLimiter:
    """Simple in-memory rate limiter for development."""
    
    def __init__(self):
        self._user_requests: Dict[str, Dict[str, list]] = {}
    
    async def check_rate_limit(self, user_id: str) -> None:
        """Check if user has exceeded rate limits."""
        current_time = datetime.utcnow()
        
        # Initialize user tracking if not exists
        if user_id not in self._user_requests:
            self._user_requests[user_id] = {
                'minute': [],
                'hour': [],
                'day': []
            }
        
        user_data = self._user_requests[user_id]
        
        # Clean old requests
        self._clean_old_requests(user_data, current_time)
        
        # Check limits
        minute_count = len(user_data['minute'])
        hour_count = len(user_data['hour'])
        day_count = len(user_data['day'])
        
        # Check per-minute limit
        if minute_count >= settings.max_messages_per_minute:
            reset_time = int((current_time + timedelta(minutes=1)).timestamp())
            raise RateLimitExceeded(
                limit_type="messages_per_minute",
                limit=settings.max_messages_per_minute,
                current=minute_count,
                reset_time=reset_time
            )
        
        # Check per-hour limit
        if hour_count >= settings.max_messages_per_hour:
            reset_time = int((current_time + timedelta(hours=1)).timestamp())
            raise RateLimitExceeded(
                limit_type="messages_per_hour",
                limit=settings.max_messages_per_hour,
                current=hour_count,
                reset_time=reset_time
            )
        
        # Check per-day limit
        if day_count >= settings.max_messages_per_day:
            reset_time = int((current_time + timedelta(days=1)).timestamp())
            raise RateLimitExceeded(
                limit_type="messages_per_day",
                limit=settings.max_messages_per_day,
                current=day_count,
                reset_time=reset_time
            )
        
        # Record this request
        user_data['minute'].append(current_time)
        user_data['hour'].append(current_time)
        user_data['day'].append(current_time)
        
        logger.debug(
            "Rate limit check passed",
            user_id=user_id,
            minute_count=minute_count + 1,
            hour_count=hour_count + 1,
            day_count=day_count + 1
        )
    
    def _clean_old_requests(self, user_data: Dict[str, list], current_time: datetime) -> None:
        """Remove old requests from tracking."""
        minute_ago = current_time - timedelta(minutes=1)
        hour_ago = current_time - timedelta(hours=1)
        day_ago = current_time - timedelta(days=1)
        
        user_data['minute'] = [
            req_time for req_time in user_data['minute'] 
            if req_time > minute_ago
        ]
        user_data['hour'] = [
            req_time for req_time in user_data['hour'] 
            if req_time > hour_ago
        ]
        user_data['day'] = [
            req_time for req_time in user_data['day'] 
            if req_time > day_ago
        ]
    
    async def get_rate_limit_info(self, user_id: str) -> Dict[str, int]:
        """Get current rate limit status for user."""
        current_time = datetime.utcnow()
        
        if user_id not in self._user_requests:
            return {
                'minute_remaining': settings.max_messages_per_minute,
                'hour_remaining': settings.max_messages_per_hour,
                'day_remaining': settings.max_messages_per_day
            }
        
        user_data = self._user_requests[user_id]
        self._clean_old_requests(user_data, current_time)
        
        return {
            'minute_remaining': max(0, settings.max_messages_per_minute - len(user_data['minute'])),
            'hour_remaining': max(0, settings.max_messages_per_hour - len(user_data['hour'])),
            'day_remaining': max(0, settings.max_messages_per_day - len(user_data['day']))
        }


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()