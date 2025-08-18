"""Unit tests for MessageService."""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.message_service import MessageService
from app.models.message import CreateMessageRequest, MessageRole
from app.core.exceptions import ValidationError


class TestMessageService:
    """Test cases for MessageService."""
    
    @pytest.fixture
    def message_service(self):
        """Create MessageService instance."""
        return MessageService()
    
    @pytest.mark.asyncio
    async def test_create_message_success(self, message_service):
        """Test successful message creation."""
        request = CreateMessageRequest(
            conversation_id="conv_test_123",
            content="Test message content",
            metadata={"test": True}
        )
        
        # Mock repository
        with patch.object(message_service.repository, 'create_message') as mock_create:
            mock_message = AsyncMock()
            mock_message.message_id = "msg_test_123"
            mock_message.conversation_id = "conv_test_123"
            mock_message.user_id = "user_test_123"
            mock_message.content = {"text": "Test message content"}
            mock_message.role = "user"
            mock_message.status = "active"
            mock_message.timestamps = {"created_at": "2025-01-15T10:00:00Z"}
            mock_message.custom_metadata = {"test": True}
            
            mock_create.return_value = mock_message
            
            result = await message_service.create_message(request, "user_test_123")
            
            assert result.message_id == "msg_test_123"
            assert result.conversation_id == "conv_test_123"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_message_content_too_long(self, message_service):
        """Test message creation with content too long."""
        request = CreateMessageRequest(
            conversation_id="conv_test_123",
            content="x" * 50001  # Exceeds 50000 character limit
        )
        
        with pytest.raises(ValidationError) as exc_info:
            await message_service.create_message(request, "user_test_123")
        
        assert "exceeds maximum length" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_sanitize_content(self, message_service):
        """Test content sanitization."""
        content_with_html = "<script>alert('xss')</script>Hello <b>world</b>"
        sanitized = message_service._sanitize_content(content_with_html)
        
        assert "<script>" not in sanitized
        assert "<b>" not in sanitized
        assert "Hello world" in sanitized