"""LLM service for integration with external LLM services."""

import asyncio
import time
from typing import Dict, List, Any, Optional
from urllib3.util.retry import Retry
import httpx
from httpx import Timeout

from app.core.config import settings
from app.core.exceptions import LLMError, ValidationError, TimeoutError
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMMessage:
    """Represents a message in LLM conversation format."""
    
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        
    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class LLMResponse:
    """Response from LLM service."""
    
    def __init__(
        self,
        response: str,
        model: str,
        tokens_used: int,
        processing_time: float,
        correlation_id: str
    ):
        self.response = response
        self.model = model
        self.tokens_used = tokens_used
        self.processing_time = processing_time
        self.correlation_id = correlation_id


class LLMService:
    """Service for LLM integration based on the integration guide."""
    
    def __init__(self):
        self.base_url = settings.llm_service_url
        self.timeout = Timeout(settings.request_timeout_seconds)
        self.max_retries = 3
        self.base_delay = 1.0
        
        # Configure HTTP client with connection pooling and retries
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            )
        )
    
    async def send_message(
        self,
        messages: List[LLMMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None
    ) -> LLMResponse:
        """
        Send message to LLM service with retry logic.
        
        Args:
            messages: List of conversation messages
            model: Model name (optional, uses default from config)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            top_p: Top-p sampling parameter
            
        Returns:
            LLMResponse with the generated response
            
        Raises:
            LLMError: For LLM-related errors
            ValidationError: For input validation errors
            TimeoutError: For timeout errors
        """
        start_time = time.time()
        
        # Validate input
        if not messages:
            raise ValidationError("Messages list cannot be empty", field="messages")
        
        if len(messages) > 100:  # Reasonable limit
            raise ValidationError("Too many messages in conversation", field="messages")
        
        # Prepare payload
        payload = {
            "model": model or settings.default_model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": temperature if temperature is not None else settings.default_temperature,
            "max_tokens": max_tokens or settings.max_tokens_per_request,
            "stream": False  # Not implemented yet according to docs
        }
        
        if top_p is not None:
            payload["top_p"] = top_p
        
        logger.info(
            "Sending message to LLM",
            model=payload["model"],
            message_count=len(messages),
            max_tokens=payload["max_tokens"]
        )
        
        # Send with retry logic
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._make_request(payload)
                
                if response:
                    total_time = time.time() - start_time
                    logger.info(
                        "LLM response received",
                        correlation_id=response.correlation_id,
                        tokens_used=response.tokens_used,
                        processing_time=response.processing_time,
                        total_time=total_time
                    )
                    return response
                    
            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM request timeout, retrying in {delay}s",
                        attempt=attempt + 1,
                        max_retries=self.max_retries
                    )
                    await asyncio.sleep(delay)
                    continue
                else:
                    raise TimeoutError("LLM request timed out after multiple attempts")
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt)
                        logger.warning(
                            f"Rate limit exceeded, retrying in {delay}s",
                            attempt=attempt + 1
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise LLMError(
                            "Rate limit exceeded after multiple attempts",
                            error_code="LLM_RATE_LIMIT_ERROR"
                        )
                elif e.response.status_code == 408:  # Timeout
                    if attempt < self.max_retries:
                        logger.warning(
                            f"LLM service timeout, retrying",
                            attempt=attempt + 1
                        )
                        continue
                    else:
                        raise LLMError(
                            "LLM service timeout after multiple attempts",
                            error_code="LLM_TIMEOUT"
                        )
                else:
                    # For other HTTP errors, don't retry
                    error_detail = await self._extract_error_detail(e.response)
                    raise LLMError(
                        f"LLM service error: {error_detail}",
                        error_code="LLM_SERVICE_ERROR"
                    )
                    
            except httpx.ConnectError:
                raise LLMError(
                    "Could not connect to LLM service",
                    error_code="LLM_CONNECTION_ERROR"
                )
            except Exception as e:
                raise LLMError(
                    f"Unexpected LLM error: {str(e)}",
                    error_code="LLM_UNEXPECTED_ERROR"
                )
        
        raise LLMError(
            f"Failed after {self.max_retries} attempts",
            error_code="LLM_MAX_RETRIES_EXCEEDED"
        )
    
    async def _make_request(self, payload: Dict[str, Any]) -> Optional[LLMResponse]:
        """Make HTTP request to LLM service."""
        url = f"{self.base_url}/llm/message"
        
        response = await self.client.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        
        data = response.json()
        
        return LLMResponse(
            response=data["response"],
            model=data["model"],
            tokens_used=data.get("tokens_used", 0),
            processing_time=data.get("processing_time", 0.0),
            correlation_id=data.get("correlation_id", "unknown")
        )
    
    async def _extract_error_detail(self, response: httpx.Response) -> str:
        """Extract error detail from response."""
        try:
            error_data = response.json()
            return error_data.get("detail", f"HTTP {response.status_code}")
        except:
            return f"HTTP {response.status_code}"
    
    async def health_check(self) -> bool:
        """Check if LLM service is healthy."""
        try:
            response = await self.client.get(
                f"{self.base_url}/health",
                timeout=Timeout(5.0)
            )
            return response.status_code == 200
        except:
            return False
    
    async def get_service_info(self) -> Optional[Dict[str, Any]]:
        """Get LLM service information."""
        try:
            response = await self.client.get(
                f"{self.base_url}/",
                timeout=Timeout(5.0)
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class LLMConversation:
    """Helper class for managing LLM conversations with context."""
    
    def __init__(
        self,
        llm_service: LLMService,
        model: str,
        system_prompt: Optional[str] = None
    ):
        self.llm_service = llm_service
        self.model = model
        self.messages: List[LLMMessage] = []
        
        if system_prompt:
            self.messages.append(LLMMessage("system", system_prompt))
    
    def add_user_message(self, content: str):
        """Add user message to conversation."""
        self.messages.append(LLMMessage("user", content))
    
    def add_assistant_message(self, content: str):
        """Add assistant message to conversation."""
        self.messages.append(LLMMessage("assistant", content))
    
    async def send_message(
        self,
        user_message: str,
        **kwargs
    ) -> LLMResponse:
        """Send message and update conversation history."""
        # Add user message
        self.add_user_message(user_message)
        
        # Send to LLM
        response = await self.llm_service.send_message(
            messages=self.messages,
            model=self.model,
            **kwargs
        )
        
        # Add assistant response to history
        self.add_assistant_message(response.response)
        
        return response
    
    def clear_history(self, keep_system_prompt: bool = True):
        """Clear conversation history."""
        if keep_system_prompt and self.messages and self.messages[0].role == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages = []
    
    def get_message_count(self) -> int:
        """Get total message count."""
        return len(self.messages)
    
    def get_conversation_text(self) -> str:
        """Get conversation as formatted text."""
        return "\n".join([
            f"{msg.role.title()}: {msg.content}"
            for msg in self.messages
        ])