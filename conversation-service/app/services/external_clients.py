"""
External service clients for microservice integration.

This module provides HTTP clients for communicating with other microservices
in the Character Chat API ecosystem, including Auth Service and Characters Service.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum

import httpx
from app.config import settings
from app.api.exceptions import (
    ExternalServiceException,
    ValidationException,
    SecurityException,
    ErrorCode
)

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Circuit breaker states for external services."""
    CLOSED = "closed"      # Service is healthy
    OPEN = "open"          # Service is failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service has recovered


class CircuitBreaker:
    """Simple circuit breaker implementation for external service calls."""
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        request_timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.request_timeout = request_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = ServiceStatus.CLOSED
    
    async def call(self, func, *args, **kwargs):
        """Execute a function with circuit breaker protection."""
        if self.state == ServiceStatus.OPEN:
            if self._should_attempt_reset():
                self.state = ServiceStatus.HALF_OPEN
            else:
                raise ExternalServiceException(
                    "Service circuit breaker is OPEN",
                    service_name="external_service",
                    error_code=ErrorCode.SERVICE_UNAVAILABLE
                )
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt service recovery."""
        if not self.last_failure_time:
            return True
        
        return (
            datetime.utcnow() - self.last_failure_time 
            > timedelta(seconds=self.recovery_timeout)
        )
    
    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = ServiceStatus.CLOSED
    
    def _on_failure(self):
        """Handle failure and potentially open circuit."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = ServiceStatus.OPEN
            logger.warning(
                f"Circuit breaker opened due to {self.failure_count} failures"
            )


class AuthServiceClient:
    """Client for Auth Service integration."""
    
    def __init__(self):
        self.base_url = f"http://localhost:{settings.auth_service_port}"
        self.timeout = 30.0
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            request_timeout=30
        )
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token with Auth Service.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Dict containing user information if token is valid
            
        Raises:
            SecurityException: If token is invalid
            ExternalServiceException: If auth service is unavailable
        """
        if not token:
            raise SecurityException(
                "Token is required",
                ErrorCode.AUTHENTICATION_REQUIRED
            )
        
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {token}"}
                
                response = await client.get(
                    f"{self.base_url}/api/v1/auth/validate",
                    headers=headers
                )
                
                if response.status_code == 401:
                    raise SecurityException(
                        "Invalid or expired token",
                        ErrorCode.INVALID_TOKEN
                    )
                
                if response.status_code == 403:
                    raise SecurityException(
                        "Token lacks required permissions",
                        ErrorCode.INSUFFICIENT_PERMISSIONS
                    )
                
                if response.status_code >= 400:
                    raise ExternalServiceException(
                        f"Auth service error: {response.status_code}",
                        service_name="auth_service",
                        status_code=response.status_code,
                        response_data=response.text
                    )
                
                return response.json()
        
        try:
            logger.debug("Validating token with Auth Service")
            result = await self.circuit_breaker.call(_make_request)
            
            # Validate response format and normalize user_id field
            if not isinstance(result, dict):
                raise ExternalServiceException(
                    "Invalid response format from auth service",
                    service_name="auth_service",
                    error_code=ErrorCode.INVALID_RESPONSE_FORMAT
                )
            
            # Handle different user ID field names from auth service
            if "user_id" not in result:
                if "id" in result:
                    # Convert 'id' field to 'user_id' for compatibility
                    result["user_id"] = str(result["id"])
                else:
                    raise ExternalServiceException(
                        "Auth service response missing user identifier",
                        service_name="auth_service",
                        error_code=ErrorCode.INVALID_RESPONSE_FORMAT
                    )
            
            logger.debug(f"Token validated for user {result['user_id'][:8]}...")
            return result
            
        except (SecurityException, ExternalServiceException):
            raise
        except httpx.ConnectError:
            logger.error("Failed to connect to Auth Service")
            raise ExternalServiceException(
                "Auth service is unavailable",
                service_name="auth_service",
                error_code=ErrorCode.SERVICE_UNAVAILABLE
            )
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Auth Service")
            raise ExternalServiceException(
                "Auth service timeout",
                service_name="auth_service",
                error_code=ErrorCode.SERVICE_TIMEOUT
            )
        except Exception as e:
            logger.error(f"Unexpected error validating token: {e}")
            raise ExternalServiceException(
                "Failed to validate token",
                service_name="auth_service",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed user information from Auth Service.
        
        Args:
            user_id: User ID to fetch information for
            
        Returns:
            Dict containing user information or None if not found
            
        Raises:
            ExternalServiceException: If auth service is unavailable
        """
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/users/{user_id}"
                )
                
                if response.status_code == 404:
                    return None
                
                if response.status_code >= 400:
                    raise ExternalServiceException(
                        f"Auth service error: {response.status_code}",
                        service_name="auth_service",
                        status_code=response.status_code,
                        response_data=response.text
                    )
                
                return response.json()
        
        try:
            logger.debug(f"Fetching user info for {user_id[:8]}...")
            return await self.circuit_breaker.call(_make_request)
            
        except ExternalServiceException:
            raise
        except httpx.ConnectError:
            logger.error("Failed to connect to Auth Service")
            raise ExternalServiceException(
                "Auth service is unavailable",
                service_name="auth_service",
                error_code=ErrorCode.SERVICE_UNAVAILABLE
            )
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Auth Service")
            raise ExternalServiceException(
                "Auth service timeout",
                service_name="auth_service",
                error_code=ErrorCode.SERVICE_TIMEOUT
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching user info: {e}")
            raise ExternalServiceException(
                "Failed to fetch user information",
                service_name="auth_service",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )


class CharactersServiceClient:
    """Client for Characters Service integration."""
    
    def __init__(self):
        self.base_url = f"http://localhost:{settings.characters_service_port}"
        self.timeout = 30.0
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            request_timeout=30
        )
    
    async def validate_character_exists(self, character_id: str) -> bool:
        """
        Validate that a character exists in the Characters Service.
        
        Args:
            character_id: Character ID to validate
            
        Returns:
            bool: True if character exists, False otherwise
            
        Raises:
            ExternalServiceException: If characters service is unavailable
        """
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/characters/{character_id}"
                )
                
                if response.status_code == 404:
                    return False
                
                if response.status_code >= 400:
                    raise ExternalServiceException(
                        f"Characters service error: {response.status_code}",
                        service_name="characters_service",
                        status_code=response.status_code,
                        response_data=response.text
                    )
                
                return True
        
        try:
            logger.debug(f"Validating character exists: {character_id[:8]}...")
            return await self.circuit_breaker.call(_make_request)
            
        except ExternalServiceException:
            raise
        except httpx.ConnectError:
            logger.error("Failed to connect to Characters Service")
            raise ExternalServiceException(
                "Characters service is unavailable",
                service_name="characters_service",
                error_code=ErrorCode.SERVICE_UNAVAILABLE
            )
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Characters Service")
            raise ExternalServiceException(
                "Characters service timeout",
                service_name="characters_service",
                error_code=ErrorCode.SERVICE_TIMEOUT
            )
        except Exception as e:
            logger.error(f"Unexpected error validating character: {e}")
            raise ExternalServiceException(
                "Failed to validate character",
                service_name="characters_service",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )
    
    async def get_character_info(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed character information from Characters Service.
        
        Args:
            character_id: Character ID to fetch information for
            
        Returns:
            Dict containing character information or None if not found
            
        Raises:
            ExternalServiceException: If characters service is unavailable
        """
        async def _make_request():
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/characters/{character_id}"
                )
                
                if response.status_code == 404:
                    return None
                
                if response.status_code >= 400:
                    raise ExternalServiceException(
                        f"Characters service error: {response.status_code}",
                        service_name="characters_service",
                        status_code=response.status_code,
                        response_data=response.text
                    )
                
                return response.json()
        
        try:
            logger.debug(f"Fetching character info for {character_id[:8]}...")
            return await self.circuit_breaker.call(_make_request)
            
        except ExternalServiceException:
            raise
        except httpx.ConnectError:
            logger.error("Failed to connect to Characters Service")
            raise ExternalServiceException(
                "Characters service is unavailable",
                service_name="characters_service",
                error_code=ErrorCode.SERVICE_UNAVAILABLE
            )
        except httpx.TimeoutException:
            logger.error("Timeout connecting to Characters Service")
            raise ExternalServiceException(
                "Characters service timeout",
                service_name="characters_service",
                error_code=ErrorCode.SERVICE_TIMEOUT
            )
        except Exception as e:
            logger.error(f"Unexpected error fetching character info: {e}")
            raise ExternalServiceException(
                "Failed to fetch character information",
                service_name="characters_service",
                error_code=ErrorCode.EXTERNAL_SERVICE_ERROR
            )


# Singleton instances for dependency injection
auth_client = AuthServiceClient()
characters_client = CharactersServiceClient()


def get_auth_client() -> AuthServiceClient:
    """Get the singleton Auth Service client instance."""
    return auth_client


def get_characters_client() -> CharactersServiceClient:
    """Get the singleton Characters Service client instance."""
    return characters_client