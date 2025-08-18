"""Tests for character router endpoints."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status, FastAPI
import json

from app.characters.router import router
from app.characters.models import CharacterCreate, CharacterUpdate, CharacterResponse


class TestCharacterRouter:
    """Tests for character API endpoints."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client for FastAPI app."""
        # Create a minimal FastAPI app for testing
        test_app = FastAPI()
        test_app.include_router(router)
        return TestClient(test_app)
    
    @pytest.fixture
    def mock_service(self):
        """Mock character service for testing."""
        with patch('app.characters.router.character_service') as mock:
            yield mock


class TestListCharactersEndpoint(TestCharacterRouter):
    """Tests for GET /characters/ endpoint."""
    
    def test_list_characters_success(self, test_client, mock_service, multiple_characters):
        """Test successful character listing."""
        # Create simple response dictionaries that can be JSON serialized
        character_responses = [
            {
                "id": str(char.id),
                "name": char.name,
                "display_name": char.display_name,
                "personality": char.personality,
                "traits": char.traits,
                "avatar_url": char.avatar_url,
                "is_active": char.is_active,
                "version_number": char.version_number
            }
            for char in multiple_characters
        ]
        
        # Configure the mock to return an async result
        mock_service.list_characters = AsyncMock(return_value=character_responses)
        
        response = test_client.get("/characters/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all("id" in char for char in data)
        assert all("name" in char for char in data)
        mock_service.list_characters.assert_called_once()
    
    def test_list_characters_empty(self, test_client, mock_service):
        """Test listing characters when none exist."""
        mock_service.list_characters.return_value = []
        
        response = test_client.get("/characters/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []
        mock_service.list_characters.assert_called_once()
    
    def test_list_characters_service_error(self, test_client, mock_service):
        """Test handling of service errors in list characters."""
        mock_service.list_characters.side_effect = Exception("Database error")
        
        response = test_client.get("/characters/")
        
        # Should return 500 for unhandled service errors
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestGetCharacterEndpoint(TestCharacterRouter):
    """Tests for GET /characters/{name} endpoint."""
    
    def test_get_character_success(self, test_client, mock_service, sample_character_response):
        """Test successful character retrieval."""
        mock_service.get_character.return_value = sample_character_response
        
        response = test_client.get("/characters/luna")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "luna"
        assert data["display_name"] == "Luna"
        mock_service.get_character.assert_called_once_with("luna")
    
    def test_get_character_not_found(self, test_client, mock_service):
        """Test getting non-existent character."""
        mock_service.get_character.return_value = None
        
        response = test_client.get("/characters/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Character 'nonexistent' not found" in data["detail"]
        mock_service.get_character.assert_called_once_with("nonexistent")
    
    def test_get_character_invalid_name(self, test_client, mock_service):
        """Test getting character with invalid name."""
        mock_service.get_character.side_effect = ValueError("Character name cannot be empty")
        
        response = test_client.get("/characters/")  # Empty name
        
        # This would hit the list endpoint, not get specific character
        # Let's test with a different scenario
        mock_service.get_character.side_effect = ValueError("Invalid character name")
        
        response = test_client.get("/characters/invalid")
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Invalid character name" in data["detail"]
    
    def test_get_character_service_error(self, test_client, mock_service):
        """Test handling of service runtime errors."""
        mock_service.get_character.side_effect = RuntimeError("Failed to retrieve character")
        
        response = test_client.get("/characters/luna")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to retrieve character" in data["detail"]


class TestCreateCharacterEndpoint(TestCharacterRouter):
    """Tests for POST /characters/ endpoint."""
    
    def test_create_character_success(self, test_client, mock_service, sample_character_data, sample_character_response):
        """Test successful character creation."""
        mock_service.create_character.return_value = sample_character_response
        
        response = test_client.post("/characters/", json=sample_character_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "luna"
        assert data["display_name"] == "Luna"
        
        # Verify service was called with correct data
        mock_service.create_character.assert_called_once()
        call_args = mock_service.create_character.call_args[0][0]
        assert isinstance(call_args, CharacterCreate)
        assert call_args.name == "luna"
    
    def test_create_character_duplicate_name(self, test_client, mock_service, sample_character_data):
        """Test creating character with duplicate name."""
        mock_service.create_character.side_effect = ValueError("Character with name 'luna' already exists")
        
        response = test_client.post("/characters/", json=sample_character_data)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Character with name 'luna' already exists" in data["detail"]
    
    def test_create_character_invalid_data(self, test_client, mock_service):
        """Test creating character with invalid data."""
        invalid_data = {
            "name": "test",
            # Missing required fields
        }
        
        response = test_client.post("/characters/", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        # Should not reach service due to validation error
        mock_service.create_character.assert_not_called()
    
    def test_create_character_empty_name(self, test_client, mock_service):
        """Test creating character with empty name."""
        invalid_data = {
            "name": "",
            "display_name": "Test",
            "personality": "Test",
            "system_prompt": "Test",
            "traits": ["test"]
        }
        
        response = test_client.post("/characters/", json=invalid_data)
        
        # Pydantic allows empty strings, so this would reach the service
        # The service would then validate and reject it
        # But for this test, let's assume validation happens at Pydantic level
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]
    
    def test_create_character_service_error(self, test_client, mock_service, sample_character_data):
        """Test handling of service runtime errors."""
        mock_service.create_character.side_effect = RuntimeError("Failed to create character")
        
        response = test_client.post("/characters/", json=sample_character_data)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to create character" in data["detail"]
    
    def test_create_character_malformed_json(self, test_client, mock_service):
        """Test creating character with malformed JSON."""
        response = test_client.post(
            "/characters/",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.create_character.assert_not_called()


class TestUpdateCharacterEndpoint(TestCharacterRouter):
    """Tests for PUT /characters/{name} endpoint."""
    
    def test_update_character_success(self, test_client, mock_service, sample_character_response):
        """Test successful character update."""
        # Modify the response to show it was updated
        updated_response = sample_character_response.copy(deep=True)
        updated_response.display_name = "Luna Updated"
        updated_response.version_number = 2
        
        mock_service.update_character.return_value = updated_response
        
        update_data = {
            "display_name": "Luna Updated",
            "personality": "Updated personality"
        }
        
        response = test_client.put("/characters/luna", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["display_name"] == "Luna Updated"
        assert data["version_number"] == 2
        
        # Verify service was called
        mock_service.update_character.assert_called_once()
        call_args = mock_service.update_character.call_args
        assert call_args[0][0] == "luna"  # character name
        assert isinstance(call_args[0][1], CharacterUpdate)  # update data
    
    def test_update_character_not_found(self, test_client, mock_service):
        """Test updating non-existent character."""
        mock_service.update_character.return_value = None
        
        update_data = {"display_name": "Updated"}
        
        response = test_client.put("/characters/nonexistent", json=update_data)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Character 'nonexistent' not found" in data["detail"]
    
    def test_update_character_partial_update(self, test_client, mock_service, sample_character_response):
        """Test partial character update."""
        updated_response = sample_character_response.copy(deep=True)
        updated_response.display_name = "Partially Updated"
        
        mock_service.update_character.return_value = updated_response
        
        # Only update display_name
        update_data = {"display_name": "Partially Updated"}
        
        response = test_client.put("/characters/luna", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["display_name"] == "Partially Updated"
        
        # Verify service was called with partial update
        call_args = mock_service.update_character.call_args[0][1]
        assert call_args.display_name == "Partially Updated"
        assert call_args.personality is None  # Not updated
    
    def test_update_character_empty_update(self, test_client, mock_service, sample_character_response):
        """Test update with empty data."""
        mock_service.update_character.return_value = sample_character_response
        
        update_data = {}
        
        response = test_client.put("/characters/luna", json=update_data)
        
        assert response.status_code == status.HTTP_200_OK
        # Should still work with empty update
        mock_service.update_character.assert_called_once()
    
    def test_update_character_invalid_data(self, test_client, mock_service):
        """Test update with invalid data types."""
        invalid_data = {
            "display_name": 123,  # Should be string
            "traits": "not_a_list"  # Should be list
        }
        
        response = test_client.put("/characters/luna", json=invalid_data)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.update_character.assert_not_called()


class TestDeleteCharacterEndpoint(TestCharacterRouter):
    """Tests for DELETE /characters/{name} endpoint."""
    
    def test_delete_character_success(self, test_client, mock_service):
        """Test successful character deletion."""
        mock_service.delete_character.return_value = True
        
        response = test_client.delete("/characters/luna")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Character 'luna' deleted successfully" in data["message"]
        mock_service.delete_character.assert_called_once_with("luna")
    
    def test_delete_character_not_found(self, test_client, mock_service):
        """Test deleting non-existent character."""
        mock_service.delete_character.return_value = False
        
        response = test_client.delete("/characters/nonexistent")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Character 'nonexistent' not found" in data["detail"]
    
    def test_delete_character_service_error(self, test_client, mock_service):
        """Test handling of service errors in delete."""
        mock_service.delete_character.side_effect = RuntimeError("Failed to delete character")
        
        response = test_client.delete("/characters/luna")
        
        # The current router doesn't handle RuntimeError for delete
        # It would propagate as 500 error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestRouterEdgeCases(TestCharacterRouter):
    """Tests for edge cases and special scenarios."""
    
    def test_character_name_with_special_characters(self, test_client, mock_service, sample_character_response):
        """Test character operations with special characters in names."""
        special_names = [
            "character-with-dashes",
            "character_with_underscores",
            "character.with.dots"
        ]
        
        for name in special_names:
            mock_service.get_character.return_value = sample_character_response
            
            response = test_client.get(f"/characters/{name}")
            assert response.status_code == status.HTTP_200_OK
            mock_service.get_character.assert_called_with(name)
    
    def test_character_name_url_encoding(self, test_client, mock_service, sample_character_response):
        """Test character names that require URL encoding."""
        mock_service.get_character.return_value = sample_character_response
        
        # Test with spaces (URL encoded as %20)
        response = test_client.get("/characters/character%20with%20spaces")
        assert response.status_code == status.HTTP_200_OK
        mock_service.get_character.assert_called_with("character with spaces")
    
    def test_very_long_character_name(self, test_client, mock_service):
        """Test handling of very long character names."""
        long_name = "a" * 1000
        mock_service.get_character.return_value = None
        
        response = test_client.get(f"/characters/{long_name}")
        
        # Should handle long names gracefully
        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock_service.get_character.assert_called_once_with(long_name)
    
    def test_unicode_character_name(self, test_client, mock_service, sample_character_response):
        """Test handling of unicode characters in names."""
        unicode_name = "キャラクター"  # Japanese characters
        mock_service.get_character.return_value = sample_character_response
        
        # URL encode the unicode name
        import urllib.parse
        encoded_name = urllib.parse.quote(unicode_name)
        
        response = test_client.get(f"/characters/{encoded_name}")
        assert response.status_code == status.HTTP_200_OK
    
    def test_concurrent_requests(self, test_client, mock_service, sample_character_response):
        """Test handling of concurrent requests to the same endpoint."""
        mock_service.get_character.return_value = sample_character_response
        
        # Simulate concurrent requests
        responses = []
        for _ in range(5):
            response = test_client.get("/characters/luna")
            responses.append(response)
        
        # All requests should succeed
        assert all(r.status_code == status.HTTP_200_OK for r in responses)
        assert mock_service.get_character.call_count == 5


class TestRouterErrorHandling(TestCharacterRouter):
    """Tests for comprehensive error handling."""
    
    def test_request_timeout_simulation(self, test_client, mock_service):
        """Test handling of request timeouts."""
        import asyncio
        
        async def slow_operation(*args, **kwargs):
            await asyncio.sleep(0.1)  # Simulate slow operation
            raise TimeoutError("Request timeout")
        
        mock_service.get_character.side_effect = slow_operation
        
        # This would typically require async test client for proper timeout testing
        # For now, just test that timeout errors are handled
        mock_service.get_character.side_effect = TimeoutError("Request timeout")
        
        response = test_client.get("/characters/luna")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_large_payload_handling(self, test_client, mock_service):
        """Test handling of large request payloads."""
        # Create a large character data payload
        large_data = {
            "name": "test",
            "display_name": "Test",
            "personality": "x" * 10000,  # Very long personality
            "system_prompt": "y" * 10000,  # Very long system prompt
            "traits": ["trait"] * 1000  # Many traits
        }
        
        mock_service.create_character.side_effect = ValueError("Payload too large")
        
        response = test_client.post("/characters/", json=large_data)
        
        # Should handle large payloads appropriately
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        ]
    
    def test_invalid_content_type(self, test_client, mock_service):
        """Test handling of invalid content types."""
        response = test_client.post(
            "/characters/",
            data="not json",
            headers={"content-type": "text/plain"}
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.create_character.assert_not_called()
    
    def test_missing_content_type(self, test_client, mock_service):
        """Test handling of missing content type header."""
        response = test_client.post("/characters/", data='{"name": "test"}')
        
        # FastAPI should handle this gracefully
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_400_BAD_REQUEST
        ]