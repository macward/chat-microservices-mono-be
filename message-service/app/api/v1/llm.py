"""LLM processing API endpoints."""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header, Query, Path
from pydantic import BaseModel, Field
import httpx

from app.services.message_service import MessageService
from app.models.message import CreateMessageRequest, MessageResponse
from app.core.rate_limiter import rate_limiter
from app.core.exceptions import (
    MessageServiceException,
    ValidationError,
    NotFoundError,
    RateLimitExceeded,
    LLMError
)
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/llm", tags=["LLM Processing"])


class LLMProcessRequest(BaseModel):
    """Request for LLM processing."""
    content: str = Field(..., min_length=1, max_length=50000, description="Message content")
    conversation_id: str = Field(..., description="Conversation ID")
    character_id: Optional[str] = Field(None, description="Character ID for personalization")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    model: Optional[str] = Field(None, description="LLM model to use")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=4000, description="Maximum tokens to generate")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class LLMProcessResponse(BaseModel):
    """Response from LLM processing."""
    user_message: MessageResponse
    assistant_message: Optional[MessageResponse] = None
    processing_status: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None
    llm_metadata: Optional[Dict[str, Any]] = None


class LLMHealthResponse(BaseModel):
    """LLM service health response."""
    healthy: bool
    service_info: Optional[Dict[str, Any]] = None
    base_url: str
    error: Optional[str] = None


async def get_user_id_from_token(authorization: str = Header(None)) -> str:
    """Extract user ID from JWT token by validating with Auth Service."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    try:
        # Call auth service to validate token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.auth_service_url}/api/v1/auth/validate",
                headers={"Authorization": authorization},
                timeout=10.0
            )
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get("username") or user_data.get("id") or user_data.get("user_id") or user_data.get("sub")
                if user_id:
                    return user_id
                else:
                    logger.error("No user_id found in auth response", response=user_data)
                    raise HTTPException(status_code=401, detail="Invalid token: no user ID")
            elif response.status_code == 401:
                logger.warning("Token validation failed", status=response.status_code)
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            else:
                logger.error("Auth service error", status=response.status_code, response=response.text)
                raise HTTPException(status_code=503, detail="Authentication service unavailable")
                
    except httpx.TimeoutException:
        logger.error("Auth service timeout")
        raise HTTPException(status_code=503, detail="Authentication service timeout")
    except httpx.RequestError as e:
        logger.error("Auth service connection error", error=str(e))
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected auth error", error=str(e))
        raise HTTPException(status_code=500, detail="Authentication error")


@router.post("/process", response_model=LLMProcessResponse)
async def process_message_with_llm(
    request: LLMProcessRequest,
    user_id: str = Header(alias="x-user-id", default=None),
    authorization: str = Header(None)
):
    """
    Process a message with LLM and generate a response.
    
    This endpoint:
    1. Creates a user message in the conversation
    2. Sends the conversation context to the LLM service
    3. Creates an assistant message with the LLM response
    4. Returns both messages with processing metadata
    """
    try:
        # Get user ID from token if not provided in header (for testing)
        if not user_id:
            user_id = await get_user_id_from_token(authorization)
        
        # Check rate limits
        await rate_limiter.check_rate_limit(user_id)
        
        # Process message with LLM
        service = MessageService()
        
        # Convert to CreateMessageRequest
        message_request = CreateMessageRequest(
            conversation_id=request.conversation_id,
            content=request.content,
            metadata=request.metadata
        )
        
        result = await service.process_message_with_llm(
            request=message_request,
            user_id=user_id,
            character_id=request.character_id,
            system_prompt=request.system_prompt,
            model=request.model,
            temperature=request.temperature
        )
        
        # Prepare response
        processing_status = {
            "status": "completed" if result.get("assistant_message") else "failed",
            "llm_service_healthy": True,
            "processing_time": None
        }
        
        # Add LLM metadata if available
        llm_metadata = None
        if result.get("assistant_message"):
            llm_metadata = result["assistant_message"].llm_metadata
            if llm_metadata:
                processing_status["processing_time"] = llm_metadata.get("processing_time")
        
        return LLMProcessResponse(
            user_message=result["user_message"],
            assistant_message=result.get("assistant_message"),
            processing_status=processing_status,
            error=result.get("error"),
            llm_metadata=llm_metadata
        )
        
    except RateLimitExceeded as e:
        logger.warning("Rate limit exceeded", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=429,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except ValidationError as e:
        logger.warning("Validation error", error=str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "details": e.details
                }
            }
        )
    except LLMError as e:
        logger.error("LLM service error", error=str(e), error_code=e.code)
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "service": "llm",
                    "retry_possible": True
                }
            }
        )
    except Exception as e:
        logger.error("Failed to process message with LLM", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}}
        )


@router.get("/health", response_model=LLMHealthResponse)
async def get_llm_health():
    """
    Check LLM service health status.
    
    This endpoint provides information about:
    - LLM service connectivity
    - Service version and status
    - Configuration details
    """
    try:
        service = MessageService()
        health_status = await service.get_llm_health_status()
        
        return LLMHealthResponse(**health_status)
        
    except Exception as e:
        logger.error("Failed to check LLM health", error=str(e))
        return LLMHealthResponse(
            healthy=False,
            base_url=settings.llm_service_url,
            error=str(e)
        )


@router.get("/models")
async def get_available_models():
    """
    Get available LLM models.
    
    Returns the list of models that can be used for processing.
    """
    try:
        # For now, return the configured default model
        # In the future, this could query the LLM service for available models
        return {
            "default_model": settings.default_model,
            "available_models": [
                settings.default_model,
                "google/gemma-3-12b",
                "microsoft/DialoGPT-medium",
                "openai/gpt-3.5-turbo",
                "anthropic/claude-3-haiku"
            ],
            "model_capabilities": {
                settings.default_model: {
                    "max_tokens": settings.max_tokens_per_request,
                    "supports_system_prompt": True,
                    "supports_conversation": True,
                    "temperature_range": [0.0, 2.0]
                }
            }
        }
        
    except Exception as e:
        logger.error("Failed to get available models", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Failed to get models"}}
        )


@router.get("/config")
async def get_llm_config():
    """
    Get current LLM configuration.
    
    Returns the current LLM service configuration for debugging.
    """
    try:
        return {
            "llm_service_url": settings.llm_service_url,
            "default_model": settings.default_model,
            "default_temperature": settings.default_temperature,
            "max_tokens_per_request": settings.max_tokens_per_request,
            "request_timeout_seconds": settings.request_timeout_seconds,
            "max_concurrent_llm_requests": settings.max_concurrent_llm_requests,
            "rate_limits": {
                "max_messages_per_minute": settings.max_messages_per_minute,
                "max_messages_per_hour": settings.max_messages_per_hour,
                "max_messages_per_day": settings.max_messages_per_day
            }
        }
        
    except Exception as e:
        logger.error("Failed to get LLM config", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "INTERNAL_ERROR", "message": "Failed to get config"}}
        )