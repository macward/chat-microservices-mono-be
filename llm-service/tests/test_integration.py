"""
Integration tests for the complete application flow.
These tests verify that all components work together correctly.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

class TestFullIntegration:
    """Integration tests for complete request/response flow."""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked LLM service."""
        with TestClient(app) as client:
            yield client
    
    @pytest.fixture
    def mock_successful_llm_response(self):
        """Mock a successful LLM response."""
        return {
            "choices": [
                {
                    "message": {
                        "content": "¡Hola! Me alegra poder ayudarte hoy. Estoy funcionando perfectamente y listo para responder cualquier pregunta que tengas."
                    }
                }
            ],
            "usage": {
                "total_tokens": 28,
                "prompt_tokens": 10,
                "completion_tokens": 18
            },
            "model": "test-model-v1"
        }
    
    @patch('app.services.llm_service.llm_service.client')
    def test_complete_message_flow(self, mock_client, client, mock_successful_llm_response):
        """Test complete message flow from API request to response."""
        # Setup
        mock_client.generate_with_messages.return_value = mock_successful_llm_response
        
        # Mock the service as initialized
        with patch('app.services.llm_service.llm_service._initialized', True):
            # Request payload
            request_payload = {
                "model": "test-model-v1",
                "messages": [
                    {
                        "role": "user",
                        "content": "Hola, ¿cómo estás hoy? Me gustaría saber si funcionas correctamente."
                    }
                ],
                "temperature": 0.8,
                "max_tokens": 150,
                "top_p": 0.9
            }
            
            # Make request
            response = client.post("/llm/message", json=request_payload)
            
            # Verify response
            assert response.status_code == 200
            
            response_data = response.json()
            assert "response" in response_data
            assert "processing_time" in response_data
            assert "tokens_used" in response_data
            assert "correlation_id" in response_data
            
            # Verify response content
            assert "alegra" in response_data["response"]
            assert response_data["tokens_used"] == 28
            assert response_data["processing_time"] is not None
            
            # Verify headers
            assert "X-Correlation-ID" in response.headers
            assert "X-Process-Time" in response.headers
            assert "X-Content-Type-Options" in response.headers
            
            # Verify LLM client was called correctly
            mock_client.generate_with_messages.assert_called_once()
            call_args = mock_client.generate_with_messages.call_args
            
            # Check messages format
            messages = call_args[0][0]
            assert len(messages) == 1
            assert messages[0]["role"] == "user"
            assert "funcionas correctamente" in messages[0]["content"]
            
            # Check parameters
            kwargs = call_args[1]
            assert kwargs["temperature"] == 0.8
            assert kwargs["max_tokens"] == 150
            assert kwargs["top_p"] == 0.9
    
    @patch('app.services.llm_service.llm_service.client')
    def test_conversation_flow(self, mock_client, client, mock_successful_llm_response):
        """Test conversation flow with multiple messages."""
        # Setup
        mock_client.generate_with_messages.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "Según las últimas estadísticas, Madrid tiene aproximadamente 6.7 millones de habitantes en su área metropolitana."
                    }
                }
            ],
            "usage": {"total_tokens": 35}
        }
        
        with patch('app.services.llm_service.llm_service._initialized', True):
            # Conversation request
            conversation_payload = {
                "model": "conversational-model",
                "messages": [
                    {
                        "role": "system",
                        "content": "Eres un asistente que proporciona información precisa sobre geografía y demografía."
                    },
                    {
                        "role": "user",
                        "content": "¿Cuál es la capital de España?"
                    },
                    {
                        "role": "assistant",
                        "content": "La capital de España es Madrid."
                    },
                    {
                        "role": "user",
                        "content": "¿Cuántos habitantes tiene?"
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 200
            }
            
            # Make request
            response = client.post("/llm/message", json=conversation_payload)
            
            # Verify response
            assert response.status_code == 200
            
            response_data = response.json()
            assert "6.7 millones" in response_data["response"]
            assert response_data["tokens_used"] == 35
            
            # Verify all messages were sent to LLM
            call_args = mock_client.generate_with_messages.call_args
            messages = call_args[0][0]
            assert len(messages) == 4
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert messages[2]["role"] == "assistant"
            assert messages[3]["role"] == "user"
    
    def test_health_check_integration(self, client):
        """Test health check endpoint integration."""
        with patch('app.services.llm_service.llm_service.health_check', return_value=True):
            with patch('app.services.llm_service.llm_service.get_uptime', return_value=1800.5):
                response = client.get("/health")
                
                assert response.status_code == 200
                
                health_data = response.json()
                assert health_data["status"] == "healthy"
                assert health_data["llm_service"] == "connected"
                assert health_data["uptime"] == 1800.5
                assert "version" in health_data
                assert "timestamp" in health_data
    
    def test_error_handling_integration(self, client):
        """Test error handling across the full stack."""
        from app.exceptions import LLMConnectionError
        
        with patch('app.services.llm_service.llm_service.send_message', 
                  side_effect=LLMConnectionError("Error de conexión de prueba")):
            
            request_payload = {
                "model": "test-model",
                "messages": [{"role": "user", "content": "Test message"}]
            }
            
            response = client.post("/llm/message", json=request_payload)
            
            assert response.status_code == 503
            
            error_data = response.json()
            assert error_data["error_code"] == "LLM_CONNECTION_ERROR"
            assert "temporalmente no disponible" in error_data["error"]
            assert "correlation_id" in error_data
    
    def test_middleware_integration(self, client):
        """Test that all middleware works together correctly."""
        with patch('app.services.llm_service.llm_service._initialized', True):
            with patch('app.services.llm_service.llm_service.client') as mock_client:
                mock_client.generate_with_messages.return_value = {
                    "choices": [{"message": {"content": "Middleware test response"}}]
                }
                
                # Make multiple requests to test rate limiting and logging
                responses = []
                for i in range(3):
                    response = client.post("/llm/message", json={
                        "model": "test",
                        "messages": [{"role": "user", "content": f"Message {i}"}]
                    })
                    responses.append(response)
                
                # All should succeed (rate limit allows more than 3)
                for response in responses:
                    assert response.status_code == 200
                    
                    # Check middleware headers
                    assert "X-Correlation-ID" in response.headers
                    assert "X-Process-Time" in response.headers
                    assert "X-Content-Type-Options" in response.headers
                    assert "X-Frame-Options" in response.headers
                    
                    # Each should have a unique correlation ID
                    assert len(response.headers["X-Correlation-ID"]) > 0
    
    def test_request_size_validation_integration(self, client):
        """Test request size validation in integration context."""
        # Create a request that exceeds the size limit
        large_content = "x" * 12000  # Exceeds default 10000 char limit
        
        request_payload = {
            "model": "test-model",
            "messages": [{"role": "user", "content": large_content}]
        }
        
        response = client.post("/llm/message", json=request_payload)
        
        assert response.status_code == 400
        
        error_data = response.json()
        assert error_data["error_code"] == "LLM_VALIDATION_ERROR"
        assert "demasiado largo" in error_data["detail"]
        assert "correlation_id" in error_data

@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance-related integration tests."""
    
    def test_response_time_acceptable(self, client):
        """Test that response times are within acceptable limits."""
        import time
        
        with patch('app.services.llm_service.llm_service._initialized', True):
            with patch('app.services.llm_service.llm_service.client') as mock_client:
                mock_client.generate_with_messages.return_value = {
                    "choices": [{"message": {"content": "Fast response"}}]
                }
                
                start_time = time.time()
                
                response = client.post("/llm/message", json={
                    "model": "test",
                    "messages": [{"role": "user", "content": "Quick test"}]
                })
                
                end_time = time.time()
                response_time = end_time - start_time
                
                assert response.status_code == 200
                assert response_time < 1.0  # Should respond within 1 second
                
                # Check reported processing time
                process_time = float(response.headers["X-Process-Time"])
                assert process_time < response_time  # Reported time should be less than total