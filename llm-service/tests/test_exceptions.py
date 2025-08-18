import pytest

from app.exceptions import (
    LLMServiceError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMValidationError,
    LLMModelError,
    LLMRateLimitError
)

class TestLLMServiceError:
    """Tests for the base LLMServiceError exception."""
    
    def test_default_error(self):
        """Test creating exception with default values."""
        error = LLMServiceError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "LLM_SERVICE_ERROR"
    
    def test_custom_error_code(self):
        """Test creating exception with custom error code."""
        error = LLMServiceError("Test error", "CUSTOM_ERROR")
        assert error.message == "Test error"
        assert error.error_code == "CUSTOM_ERROR"

class TestLLMConnectionError:
    """Tests for the LLMConnectionError exception."""
    
    def test_default_message(self):
        """Test default connection error message."""
        error = LLMConnectionError()
        assert "No se pudo conectar con LM Studio" in str(error)
        assert error.error_code == "LLM_CONNECTION_ERROR"
    
    def test_custom_message(self):
        """Test custom connection error message."""
        error = LLMConnectionError("Custom connection error")
        assert str(error) == "Custom connection error"
        assert error.error_code == "LLM_CONNECTION_ERROR"

class TestLLMTimeoutError:
    """Tests for the LLMTimeoutError exception."""
    
    def test_default_message(self):
        """Test default timeout error message."""
        error = LLMTimeoutError()
        assert "Timeout en la petición al LLM" in str(error)
        assert error.error_code == "LLM_TIMEOUT"
    
    def test_custom_message(self):
        """Test custom timeout error message."""
        error = LLMTimeoutError("Custom timeout error")
        assert str(error) == "Custom timeout error"
        assert error.error_code == "LLM_TIMEOUT"

class TestLLMValidationError:
    """Tests for the LLMValidationError exception."""
    
    def test_default_message(self):
        """Test default validation error message."""
        error = LLMValidationError()
        assert "Error de validación en los datos de entrada" in str(error)
        assert error.error_code == "LLM_VALIDATION_ERROR"
    
    def test_custom_message(self):
        """Test custom validation error message."""
        error = LLMValidationError("Custom validation error")
        assert str(error) == "Custom validation error"
        assert error.error_code == "LLM_VALIDATION_ERROR"

class TestLLMModelError:
    """Tests for the LLMModelError exception."""
    
    def test_default_message(self):
        """Test default model error message."""
        error = LLMModelError()
        assert "Error en el modelo LLM" in str(error)
        assert error.error_code == "LLM_MODEL_ERROR"
    
    def test_custom_message(self):
        """Test custom model error message."""
        error = LLMModelError("Custom model error")
        assert str(error) == "Custom model error"
        assert error.error_code == "LLM_MODEL_ERROR"

class TestLLMRateLimitError:
    """Tests for the LLMRateLimitError exception."""
    
    def test_default_message(self):
        """Test default rate limit error message."""
        error = LLMRateLimitError()
        assert "Límite de velocidad excedido" in str(error)
        assert error.error_code == "LLM_RATE_LIMIT_ERROR"
    
    def test_custom_message(self):
        """Test custom rate limit error message."""
        error = LLMRateLimitError("Custom rate limit error")
        assert str(error) == "Custom rate limit error"
        assert error.error_code == "LLM_RATE_LIMIT_ERROR"

class TestExceptionInheritance:
    """Tests for exception inheritance."""
    
    def test_all_inherit_from_base(self):
        """Test that all custom exceptions inherit from LLMServiceError."""
        errors = [
            LLMConnectionError(),
            LLMTimeoutError(),
            LLMValidationError(),
            LLMModelError(),
            LLMRateLimitError()
        ]
        
        for error in errors:
            assert isinstance(error, LLMServiceError)
            assert isinstance(error, Exception)
    
    def test_exception_catching(self):
        """Test that specific exceptions can be caught by base class."""
        try:
            raise LLMConnectionError("Test error")
        except LLMServiceError as e:
            assert isinstance(e, LLMConnectionError)
            assert e.error_code == "LLM_CONNECTION_ERROR"