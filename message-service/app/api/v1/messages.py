"""Message API endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Header, Query, Path
from fastapi.responses import JSONResponse
import httpx

from app.services.message_service import MessageService
from app.models.message import (
    MessageResponse
)
from app.core.exceptions import (
    NotFoundError
)
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)
router = APIRouter()


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










