import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.llm_service import LLMService
from app.models import LLMRequest, Message, MessageRole
from app.exceptions import LLMConnectionError, LLMTimeoutError, LLMServiceError, LLMModelError

class TestLLMService:
    """Tests for the LLMService class."""
    
    @pytest.fixture
    def llm_service(self):
        """Create a fresh LLMService instance for testing."""
        return LLMService()
    
    @pytest.fixture
    def mock_client(self):
        """Mock LM Studio client."""
        mock = MagicMock()
        mock.generate_with_messages = MagicMock()
        return mock
    
    @pytest.fixture
    def sample_request(self):
        """Sample LLM request for testing."""
        return LLMRequest(
            model="test-model",
            messages=[
                Message(role=MessageRole.USER, content="Hola, ¿cómo estás?")
            ],
            temperature=0.7,
            max_tokens=100
        )
    
    @pytest.mark.asyncio
    async def test_initialization_success(self, llm_service, mock_client):
        """Test successful service initialization."""
        with patch('app.services.llm_service.LMStudioClient', return_value=mock_client):
            with patch.object(llm_service, '_test_connection', new_callable=AsyncMock):
                await llm_service.initialize()
                
                assert llm_service.client == mock_client
                assert llm_service._initialized is True
    
    @pytest.mark.asyncio
    async def test_initialization_failure(self, llm_service):
        """Test failed service initialization."""
        with patch('app.services.llm_service.LMStudioClient', side_effect=Exception("Connection failed")):
            with pytest.raises(LLMConnectionError) as exc_info:
                await llm_service.initialize()
            
            assert "No se pudo conectar a LM Studio" in str(exc_info.value)
            assert llm_service._initialized is False
    
    @pytest.mark.asyncio
    async def test_send_message_success(self, llm_service, mock_client, sample_request):
        """Test successful message sending."""
        # Setup mock response
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "¡Hola! Estoy muy bien, gracias por preguntar."
                    }
                }
            ],
            "usage": {
                "total_tokens": 15
            }
        }
        mock_client.generate_with_messages.return_value = mock_response
        
        # Setup service
        llm_service.client = mock_client
        llm_service._initialized = True
        
        # Test
        response = await llm_service.send_message(sample_request, "test-correlation-123")
        
        assert response.response == "¡Hola! Estoy muy bien, gracias por preguntar."
        assert response.model == "test-model"
        assert response.tokens_used == 15
        assert response.correlation_id == "test-correlation-123"
        assert response.processing_time > 0
    
    @pytest.mark.asyncio
    async def test_send_message_with_system_prompt(self, llm_service, mock_client):
        """Test message sending with system prompt."""
        request = LLMRequest(
            model="test-model",
            messages=[
                Message(role=MessageRole.SYSTEM, content="Eres un asistente útil"),
                Message(role=MessageRole.USER, content="¿Cuál es la capital de España?")
            ]
        )
        
        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "La capital de España es Madrid."
                    }
                }
            ]
        }
        mock_client.generate_with_messages.return_value = mock_response
        
        llm_service.client = mock_client
        llm_service._initialized = True
        
        response = await llm_service.send_message(request)
        
        # Verify that both system and user messages were sent
        call_args = mock_client.generate_with_messages.call_args
        sent_messages = call_args[0][0]
        
        assert len(sent_messages) == 2
        assert sent_messages[0]["role"] == "system"
        assert sent_messages[1]["role"] == "user"
        assert "útil" in sent_messages[0]["content"]
        assert "España" in sent_messages[1]["content"]
    
    @pytest.mark.asyncio
    async def test_send_message_with_parameters(self, llm_service, mock_client, sample_request):
        """Test message sending with generation parameters."""
        sample_request.temperature = 0.9
        sample_request.max_tokens = 200
        sample_request.top_p = 0.95
        
        mock_response = {"choices": [{"message": {"content": "Test response"}}]}
        mock_client.generate_with_messages.return_value = mock_response
        
        llm_service.client = mock_client
        llm_service._initialized = True
        
        await llm_service.send_message(sample_request)
        
        # Verify parameters were passed
        call_args = mock_client.generate_with_messages.call_args
        kwargs = call_args[1]
        
        assert kwargs["temperature"] == 0.9
        assert kwargs["max_tokens"] == 200
        assert kwargs["top_p"] == 0.95
    
    @pytest.mark.asyncio
    async def test_send_message_timeout(self, llm_service, mock_client, sample_request):
        """Test timeout handling in message sending."""
        mock_client.generate_with_messages.side_effect = asyncio.TimeoutError()
        
        llm_service.client = mock_client
        llm_service._initialized = True
        
        with pytest.raises(LLMTimeoutError) as exc_info:
            await llm_service.send_message(sample_request)
        
        assert "Timeout en la petición al LLM" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_message_model_error(self, llm_service, mock_client, sample_request):
        """Test model error handling."""
        mock_client.generate_with_messages.side_effect = Exception("Model not found")
        
        llm_service.client = mock_client
        llm_service._initialized = True
        
        with patch.object(llm_service, '_send_with_retry', side_effect=LLMModelError("Model error")):
            with pytest.raises(LLMServiceError) as exc_info:
                await llm_service.send_message(sample_request)
            
            assert "Error procesando petición" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_message_auto_initialize(self, llm_service, mock_client, sample_request):
        """Test automatic initialization when not initialized."""
        mock_response = {"choices": [{"message": {"content": "Auto-init response"}}]}
        mock_client.generate_with_messages.return_value = mock_response
        
        with patch('app.services.llm_service.LMStudioClient', return_value=mock_client):
            with patch.object(llm_service, '_test_connection', new_callable=AsyncMock):
                response = await llm_service.send_message(sample_request)
                
                assert llm_service._initialized is True
                assert response.response == "Auto-init response"
    
    @pytest.mark.asyncio
    async def test_retry_logic_success(self, llm_service, mock_client, sample_request):
        """Test retry logic with eventual success."""
        # First call fails, second succeeds
        mock_client.generate_with_messages.side_effect = [
            Exception("Temporary failure"),
            {"choices": [{"message": {"content": "Success after retry"}}]}
        ]
        
        llm_service.client = mock_client
        llm_service._initialized = True
        
        response = await llm_service.send_message(sample_request)
        
        assert response.response == "Success after retry"
        assert mock_client.generate_with_messages.call_count == 2
    
    @pytest.mark.asyncio
    async def test_retry_logic_exhausted(self, llm_service, mock_client, sample_request):
        """Test retry logic when all retries are exhausted."""
        mock_client.generate_with_messages.side_effect = Exception("Persistent failure")
        
        llm_service.client = mock_client
        llm_service._initialized = True
        
        with pytest.raises(LLMServiceError):
            await llm_service.send_message(sample_request)
        
        # Should retry max_retries times + initial attempt
        expected_calls = 4  # 1 initial + 3 retries (default)
        assert mock_client.generate_with_messages.call_count == expected_calls
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, llm_service, mock_client):
        """Test successful health check."""
        mock_client.generate_with_messages.return_value = {"test": "response"}
        
        llm_service.client = mock_client
        llm_service._initialized = True
        
        is_healthy = await llm_service.health_check()
        
        assert is_healthy is True
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, llm_service, mock_client):
        """Test failed health check."""
        mock_client.generate_with_messages.side_effect = Exception("Health check failed")
        
        llm_service.client = mock_client
        llm_service._initialized = True
        
        is_healthy = await llm_service.health_check()
        
        assert is_healthy is False
    
    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, llm_service):
        """Test health check when service not initialized."""
        is_healthy = await llm_service.health_check()
        
        assert is_healthy is False
    
    def test_get_uptime(self, llm_service):
        """Test uptime calculation."""
        import time
        
        # Wait a small amount to ensure uptime > 0
        time.sleep(0.01)
        
        uptime = llm_service.get_uptime()
        
        assert uptime > 0
        assert isinstance(uptime, float)
    
    def test_extract_response_content_openai_format(self, llm_service):
        """Test response content extraction from OpenAI format."""
        response_data = {
            "choices": [
                {
                    "message": {
                        "content": "OpenAI format response"
                    }
                }
            ]
        }
        
        content = llm_service._extract_response_content(response_data)
        assert content == "OpenAI format response"
    
    def test_extract_response_content_direct_format(self, llm_service):
        """Test response content extraction from direct format."""
        response_data = {
            "text": "Direct text response"
        }
        
        content = llm_service._extract_response_content(response_data)
        assert content == "Direct text response"
    
    def test_extract_response_content_fallback(self, llm_service):
        """Test response content extraction fallback."""
        response_data = {"unknown": "format"}
        
        content = llm_service._extract_response_content(response_data)
        assert content == str(response_data)
    
    def test_extract_tokens_used_success(self, llm_service):
        """Test successful token extraction."""
        response_data = {
            "usage": {
                "total_tokens": 42
            }
        }
        
        tokens = llm_service._extract_tokens_used(response_data)
        assert tokens == 42
    
    def test_extract_tokens_used_missing(self, llm_service):
        """Test token extraction when usage info is missing."""
        response_data = {"choices": [{"message": {"content": "response"}}]}
        
        tokens = llm_service._extract_tokens_used(response_data)
        assert tokens is None