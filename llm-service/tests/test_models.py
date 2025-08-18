import pytest
from pydantic import ValidationError

from app.models import Message, LLMRequest, LLMResponse, ErrorResponse, HealthResponse, MessageRole

class TestMessage:
    """Tests for the Message model."""
    
    def test_valid_message(self):
        """Test creating a valid message."""
        message = Message(role=MessageRole.USER, content="Hello world")
        assert message.role == MessageRole.USER
        assert message.content == "Hello world"
    
    def test_message_content_stripped(self):
        """Test that message content is stripped of whitespace."""
        message = Message(role=MessageRole.USER, content="  Hello world  ")
        assert message.content == "Hello world"
    
    def test_empty_content_validation(self):
        """Test that empty content raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role=MessageRole.USER, content="")
        assert "Message content cannot be empty" in str(exc_info.value)
    
    def test_whitespace_only_content_validation(self):
        """Test that whitespace-only content raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            Message(role=MessageRole.USER, content="   ")
        assert "Message content cannot be empty" in str(exc_info.value)
    
    def test_content_length_validation(self):
        """Test content length validation."""
        # Valid length
        message = Message(role=MessageRole.USER, content="a" * 100)
        assert len(message.content) == 100
        
        # Too long content
        with pytest.raises(ValidationError):
            Message(role=MessageRole.USER, content="a" * 10001)

class TestLLMRequest:
    """Tests for the LLMRequest model."""
    
    def test_valid_request(self):
        """Test creating a valid LLM request."""
        request = LLMRequest(
            model="test-model",
            messages=[Message(role=MessageRole.USER, content="Hello")],
            temperature=0.7,
            max_tokens=100
        )
        assert request.model == "test-model"
        assert len(request.messages) == 1
        assert request.temperature == 0.7
        assert request.max_tokens == 100
    
    def test_empty_messages_validation(self):
        """Test that empty messages list raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            LLMRequest(model="test-model", messages=[])
        assert "At least one message is required" in str(exc_info.value)
    
    def test_temperature_range_validation(self):
        """Test temperature range validation."""
        # Valid temperature
        request = LLMRequest(
            model="test-model",
            messages=[Message(role=MessageRole.USER, content="Hello")],
            temperature=1.5
        )
        assert request.temperature == 1.5
        
        # Invalid temperature (too low)
        with pytest.raises(ValidationError):
            LLMRequest(
                model="test-model",
                messages=[Message(role=MessageRole.USER, content="Hello")],
                temperature=-0.1
            )
        
        # Invalid temperature (too high)
        with pytest.raises(ValidationError):
            LLMRequest(
                model="test-model",
                messages=[Message(role=MessageRole.USER, content="Hello")],
                temperature=2.1
            )
    
    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        # Valid max_tokens
        request = LLMRequest(
            model="test-model",
            messages=[Message(role=MessageRole.USER, content="Hello")],
            max_tokens=1000
        )
        assert request.max_tokens == 1000
        
        # Invalid max_tokens (too low)
        with pytest.raises(ValidationError):
            LLMRequest(
                model="test-model",
                messages=[Message(role=MessageRole.USER, content="Hello")],
                max_tokens=0
            )
        
        # Invalid max_tokens (too high)
        with pytest.raises(ValidationError):
            LLMRequest(
                model="test-model",
                messages=[Message(role=MessageRole.USER, content="Hello")],
                max_tokens=4001
            )
    
    def test_top_p_validation(self):
        """Test top_p range validation."""
        # Valid top_p
        request = LLMRequest(
            model="test-model",
            messages=[Message(role=MessageRole.USER, content="Hello")],
            top_p=0.9
        )
        assert request.top_p == 0.9
        
        # Invalid top_p (too low)
        with pytest.raises(ValidationError):
            LLMRequest(
                model="test-model",
                messages=[Message(role=MessageRole.USER, content="Hello")],
                top_p=-0.1
            )
        
        # Invalid top_p (too high)
        with pytest.raises(ValidationError):
            LLMRequest(
                model="test-model",
                messages=[Message(role=MessageRole.USER, content="Hello")],
                top_p=1.1
            )

class TestLLMResponse:
    """Tests for the LLMResponse model."""
    
    def test_valid_response(self):
        """Test creating a valid LLM response."""
        response = LLMResponse(
            response="Hello there!",
            model="test-model",
            tokens_used=10,
            processing_time=1.5,
            correlation_id="test-123"
        )
        assert response.response == "Hello there!"
        assert response.model == "test-model"
        assert response.tokens_used == 10
        assert response.processing_time == 1.5
        assert response.correlation_id == "test-123"
    
    def test_minimal_response(self):
        """Test creating response with only required fields."""
        response = LLMResponse(response="Hello!")
        assert response.response == "Hello!"
        assert response.model is None
        assert response.tokens_used is None
        assert response.processing_time is None
        assert response.correlation_id is None

class TestErrorResponse:
    """Tests for the ErrorResponse model."""
    
    def test_valid_error_response(self):
        """Test creating a valid error response."""
        error = ErrorResponse(
            error="Test error",
            error_code="TEST_ERROR",
            detail="Detailed error information",
            correlation_id="test-123"
        )
        assert error.error == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.detail == "Detailed error information"
        assert error.correlation_id == "test-123"
    
    def test_minimal_error_response(self):
        """Test creating error response with only required fields."""
        error = ErrorResponse(error="Test error", error_code="TEST_ERROR")
        assert error.error == "Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.detail is None
        assert error.correlation_id is None

class TestHealthResponse:
    """Tests for the HealthResponse model."""
    
    def test_valid_health_response(self):
        """Test creating a valid health response."""
        health = HealthResponse(
            status="healthy",
            timestamp=1234567890.0,
            version="1.0.0",
            llm_service="connected",
            uptime=3600.0
        )
        assert health.status == "healthy"
        assert health.timestamp == 1234567890.0
        assert health.version == "1.0.0"
        assert health.llm_service == "connected"
        assert health.uptime == 3600.0