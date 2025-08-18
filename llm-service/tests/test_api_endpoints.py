import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.exceptions import LLMConnectionError, LLMTimeoutError, LLMValidationError

class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_endpoint(self, client: TestClient):
        """Test the root endpoint returns service information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "docs" in data
        assert data["status"] == "running"

class TestHealthEndpoint:
    """Tests for the health endpoint."""
    
    @patch('app.services.llm_service.llm_service.health_check')
    @patch('app.services.llm_service.llm_service.get_uptime')
    def test_health_endpoint_healthy(self, mock_uptime, mock_health, client: TestClient):
        """Test health endpoint when service is healthy."""
        mock_health.return_value = True
        mock_uptime.return_value = 3600.0
        
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["llm_service"] == "connected"
        assert data["uptime"] == 3600.0
        assert "version" in data
        assert "timestamp" in data
    
    @patch('app.services.llm_service.llm_service.health_check')
    @patch('app.services.llm_service.llm_service.get_uptime')
    def test_health_endpoint_unhealthy(self, mock_uptime, mock_health, client: TestClient):
        """Test health endpoint when service is unhealthy."""
        mock_health.return_value = False
        mock_uptime.return_value = 1800.0
        
        response = client.get("/health")
        assert response.status_code == 503
        
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["llm_service"] == "disconnected"
        assert data["uptime"] == 1800.0

class TestLLMMessageEndpoint:
    """Tests for the /llm/message endpoint."""
    
    @patch('app.services.llm_service.llm_service.send_message')
    def test_successful_message_request(self, mock_send_message, client: TestClient, sample_llm_request):
        """Test successful message request."""
        # Mock successful response
        mock_send_message.return_value = AsyncMock(
            response="Esta es una respuesta de prueba",
            model="test-model",
            tokens_used=25,
            processing_time=1.5,
            correlation_id="test-123"
        )
        
        response = client.post("/llm/message", json=sample_llm_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "processing_time" in data
        assert "correlation_id" in data
        
        # Check that correlation ID is in response headers
        assert "X-Correlation-ID" in response.headers
        assert "X-Process-Time" in response.headers
    
    @patch('app.services.llm_service.llm_service.send_message')
    def test_conversation_request(self, mock_send_message, client: TestClient, sample_conversation_request):
        """Test conversation with multiple messages."""
        mock_send_message.return_value = AsyncMock(
            response="Madrid tiene aproximadamente 6.6 millones de habitantes en el área metropolitana",
            model="test-model",
            tokens_used=35,
            processing_time=2.1,
            correlation_id="test-456"
        )
        
        response = client.post("/llm/message", json=sample_conversation_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert data["response"] is not None
    
    def test_invalid_request_empty_messages(self, client: TestClient):
        """Test request with empty messages array."""
        invalid_request = {
            "model": "test-model",
            "messages": [],
            "temperature": 0.7
        }
        
        response = client.post("/llm/message", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_request_missing_content(self, client: TestClient):
        """Test request with missing message content."""
        invalid_request = {
            "model": "test-model",
            "messages": [
                {"role": "user", "content": ""}
            ]
        }
        
        response = client.post("/llm/message", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_temperature_range(self, client: TestClient):
        """Test request with invalid temperature."""
        invalid_request = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
            "temperature": 3.0  # Too high
        }
        
        response = client.post("/llm/message", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_max_tokens(self, client: TestClient):
        """Test request with invalid max_tokens."""
        invalid_request = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 0  # Too low
        }
        
        response = client.post("/llm/message", json=invalid_request)
        assert response.status_code == 422  # Validation error
    
    @patch('app.services.llm_service.llm_service.send_message')
    def test_request_too_large(self, mock_send_message, client: TestClient):
        """Test request that exceeds size limit."""
        large_content = "a" * 15000  # Exceeds default limit of 10000
        large_request = {
            "model": "test-model",
            "messages": [{"role": "user", "content": large_content}]
        }
        
        response = client.post("/llm/message", json=large_request)
        assert response.status_code == 400  # Validation error for size
        
        data = response.json()
        assert data["error_code"] == "LLM_VALIDATION_ERROR"
        assert "demasiado largo" in data["detail"]
    
    @patch('app.services.llm_service.llm_service.send_message')
    def test_connection_error_handling(self, mock_send_message, client: TestClient, sample_llm_request):
        """Test handling of connection errors."""
        mock_send_message.side_effect = LLMConnectionError("No se puede conectar")
        
        response = client.post("/llm/message", json=sample_llm_request)
        assert response.status_code == 503
        
        data = response.json()
        assert data["error_code"] == "LLM_CONNECTION_ERROR"
        assert "temporalmente no disponible" in data["error"]
    
    @patch('app.services.llm_service.llm_service.send_message')
    def test_timeout_error_handling(self, mock_send_message, client: TestClient, sample_llm_request):
        """Test handling of timeout errors."""
        mock_send_message.side_effect = LLMTimeoutError("Timeout en petición")
        
        response = client.post("/llm/message", json=sample_llm_request)
        assert response.status_code == 408
        
        data = response.json()
        assert data["error_code"] == "LLM_TIMEOUT"
        assert "Timeout" in data["error"]
    
    @patch('app.services.llm_service.llm_service.send_message')
    def test_validation_error_handling(self, mock_send_message, client: TestClient, sample_llm_request):
        """Test handling of validation errors."""
        mock_send_message.side_effect = LLMValidationError("Error de validación")
        
        response = client.post("/llm/message", json=sample_llm_request)
        assert response.status_code == 400
        
        data = response.json()
        assert data["error_code"] == "LLM_VALIDATION_ERROR"
        assert "validación" in data["error"]
    
    def test_missing_required_fields(self, client: TestClient):
        """Test request missing required fields."""
        incomplete_request = {
            "messages": [{"role": "user", "content": "Hello"}]
            # Missing model field
        }
        
        response = client.post("/llm/message", json=incomplete_request)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_role(self, client: TestClient):
        """Test request with invalid message role."""
        invalid_request = {
            "model": "test-model",
            "messages": [{"role": "invalid_role", "content": "Hello"}]
        }
        
        response = client.post("/llm/message", json=invalid_request)
        assert response.status_code == 422  # Validation error

class TestMiddleware:
    """Tests for middleware functionality."""
    
    def test_correlation_id_header(self, client: TestClient):
        """Test that correlation ID is added to response headers."""
        response = client.get("/")
        assert "X-Correlation-ID" in response.headers
        assert len(response.headers["X-Correlation-ID"]) > 0
    
    def test_process_time_header(self, client: TestClient):
        """Test that process time is added to response headers."""
        response = client.get("/")
        assert "X-Process-Time" in response.headers
        
        # Process time should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
    
    def test_security_headers(self, client: TestClient):
        """Test that security headers are added."""
        response = client.get("/")
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Referrer-Policy" in response.headers
    
    def test_rate_limiting(self, client: TestClient):
        """Test basic rate limiting functionality."""
        # This test would need more sophisticated setup for proper rate limit testing
        # For now, just verify that requests don't immediately fail
        for i in range(5):
            response = client.get("/")
            assert response.status_code == 200