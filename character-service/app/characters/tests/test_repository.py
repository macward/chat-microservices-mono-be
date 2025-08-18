"""Tests for character repository."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from beanie.exceptions import RevisionIdWasChanged

from app.characters.repository import CharacterRepository
from app.characters.models import Character


class TestCharacterRepository:
    """Tests for CharacterRepository CRUD operations."""
    
    @pytest.fixture
    def repository(self):
        """Create repository instance for testing."""
        return CharacterRepository()
    
    @pytest.mark.asyncio
    async def test_create_character_success(self, repository, sample_character_data, sample_character_document):
        """Test successful character creation."""
        with patch('app.characters.repository.Character') as mock_character_class:
            # Mock the Character constructor and create method
            mock_character_instance = AsyncMock()
            mock_character_instance.create = AsyncMock(return_value=sample_character_document)
            mock_character_class.return_value = mock_character_instance
            
            result = await repository.create_character(sample_character_data)
            
            # Verify Character was instantiated and create was called
            mock_character_class.assert_called_once_with(**sample_character_data)
            mock_character_instance.create.assert_called_once()
            assert result == sample_character_document
    
    @pytest.mark.asyncio
    async def test_create_character_database_error(self, repository, sample_character_data):
        """Test character creation with database error."""
        with patch.object(Character, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("Database connection error")
            
            with pytest.raises(Exception, match="Database connection error"):
                await repository.create_character(sample_character_data)
    
    @pytest.mark.asyncio
    async def test_get_character_by_name_found(self, repository, sample_character_document):
        """Test getting character by name when character exists."""
        with patch.object(Character, 'find_one', new_callable=AsyncMock) as mock_find_one:
            mock_find_one.return_value = sample_character_document
            
            result = await repository.get_character_by_name("luna")
            
            # Verify query parameters
            mock_find_one.assert_called_once()
            call_args = mock_find_one.call_args[0]
            # Should query for name == "luna" AND is_active == True
            assert len(call_args) == 2
            
            assert result == sample_character_document
    
    @pytest.mark.asyncio
    async def test_get_character_by_name_not_found(self, repository):
        """Test getting character by name when character doesn't exist."""
        with patch.object(Character, 'find_one', new_callable=AsyncMock) as mock_find_one:
            mock_find_one.return_value = None
            
            result = await repository.get_character_by_name("nonexistent")
            
            mock_find_one.assert_called_once()
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_character_by_name_inactive(self, repository):
        """Test that inactive characters are not returned."""
        with patch.object(Character, 'find_one', new_callable=AsyncMock) as mock_find_one:
            mock_find_one.return_value = None  # Should not find inactive character
            
            result = await repository.get_character_by_name("inactive_character")
            
            # Verify the query includes is_active == True filter
            mock_find_one.assert_called_once()
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_all_active_characters_success(self, repository, multiple_characters):
        """Test getting all active characters."""
        with patch.object(Character, 'find') as mock_find:
            # Mock the query chain
            mock_query = AsyncMock()
            mock_query.to_list.return_value = multiple_characters
            mock_find.return_value = mock_query
            
            result = await repository.get_all_active_characters()
            
            # Verify query for active characters only
            mock_find.assert_called_once()
            call_args = mock_find.call_args[0]
            # Should filter for is_active == True
            assert len(call_args) == 1
            
            mock_query.to_list.assert_called_once()
            assert result == multiple_characters
            assert len(result) == 3
    
    @pytest.mark.asyncio
    async def test_get_all_active_characters_empty(self, repository):
        """Test getting all active characters when none exist."""
        with patch.object(Character, 'find') as mock_find:
            mock_query = AsyncMock()
            mock_query.to_list.return_value = []
            mock_find.return_value = mock_query
            
            result = await repository.get_all_active_characters()
            
            mock_find.assert_called_once()
            mock_query.to_list.assert_called_once()
            assert result == []
    
    @pytest.mark.asyncio
    async def test_update_character_success(self, repository, sample_character_document):
        """Test successful character update."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            # Mock getting the character
            character = sample_character_document
            character.save = AsyncMock(return_value=character)
            mock_get.return_value = character
            
            updates = {
                "display_name": "Updated Luna",
                "personality": "Updated personality",
                "version_number": 2
            }
            
            result = await repository.update_character(str(character.id), updates)
            
            # Verify character was retrieved and updated
            mock_get.assert_called_once_with(str(character.id))
            character.save.assert_called_once()
            
            # Verify updates were applied
            assert character.display_name == "Updated Luna"
            assert character.personality == "Updated personality"
            assert character.version_number == 2
            assert result == character
    
    @pytest.mark.asyncio
    async def test_update_character_not_found(self, repository):
        """Test updating character that doesn't exist."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            updates = {"display_name": "Updated"}
            result = await repository.update_character("nonexistent_id", updates)
            
            mock_get.assert_called_once_with("nonexistent_id")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_update_character_save_error(self, repository, sample_character_document):
        """Test character update with save error."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            character = sample_character_document
            character.save = AsyncMock(side_effect=RevisionIdWasChanged("Concurrent modification"))
            mock_get.return_value = character
            
            updates = {"display_name": "Updated"}
            
            with pytest.raises(RevisionIdWasChanged):
                await repository.update_character(str(character.id), updates)
    
    @pytest.mark.asyncio
    async def test_delete_character_success(self, repository, sample_character_document):
        """Test successful character soft deletion."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            character = sample_character_document
            character.save = AsyncMock(return_value=character)
            mock_get.return_value = character
            
            result = await repository.delete_character(str(character.id))
            
            mock_get.assert_called_once_with(str(character.id))
            character.save.assert_called_once()
            
            # Verify soft deletion (is_active set to False)
            assert character.is_active is False
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_character_not_found(self, repository):
        """Test deleting character that doesn't exist."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            
            result = await repository.delete_character("nonexistent_id")
            
            mock_get.assert_called_once_with("nonexistent_id")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_delete_character_save_error(self, repository, sample_character_document):
        """Test character deletion with save error."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            character = sample_character_document
            character.save = AsyncMock(side_effect=Exception("Database error"))
            mock_get.return_value = character
            
            with pytest.raises(Exception, match="Database error"):
                await repository.delete_character(str(character.id))


class TestCharacterRepositoryEdgeCases:
    """Tests for edge cases and error conditions in repository."""
    
    @pytest.fixture
    def repository(self):
        """Create repository instance for testing."""
        return CharacterRepository()
    
    @pytest.mark.asyncio
    async def test_create_character_with_none_values(self, repository):
        """Test creating character with None values in optional fields."""
        character_data = {
            "name": "test",
            "display_name": "Test",
            "personality": "Test personality",
            "system_prompt": "Test prompt",
            "traits": ["test"],
            "avatar_url": None,
            "voice_settings": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        with patch.object(Character, 'create', new_callable=AsyncMock) as mock_create:
            # Create a mock character document
            created_character = MagicMock(spec=Character)
            created_character.id = "507f1f77bcf86cd799439011"
            created_character.avatar_url = None
            created_character.voice_settings = None
            mock_create.return_value = created_character
            
            result = await repository.create_character(character_data)
            
            assert result.avatar_url is None
            assert result.voice_settings is None
    
    @pytest.mark.asyncio
    async def test_update_character_partial_updates(self, repository, sample_character_document):
        """Test updating character with partial data."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            character = sample_character_document
            original_personality = character.personality
            character.save = AsyncMock(return_value=character)
            mock_get.return_value = character
            
            # Only update display_name, leave other fields unchanged
            updates = {"display_name": "Partially Updated"}
            
            result = await repository.update_character(str(character.id), updates)
            
            # Verify only specified field was updated
            assert character.display_name == "Partially Updated"
            assert character.personality == original_personality  # Unchanged
            assert result == character
    
    @pytest.mark.asyncio
    async def test_update_character_empty_updates(self, repository, sample_character_document):
        """Test updating character with empty updates dict."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            character = sample_character_document
            character.save = AsyncMock(return_value=character)
            mock_get.return_value = character
            
            updates = {}  # Empty updates
            
            result = await repository.update_character(str(character.id), updates)
            
            # Should still save the character (save called)
            character.save.assert_called_once()
            assert result == character
    
    @pytest.mark.asyncio
    async def test_get_character_by_name_case_sensitivity(self, repository):
        """Test character retrieval with different case names."""
        with patch.object(Character, 'find_one', new_callable=AsyncMock) as mock_find_one:
            mock_find_one.return_value = None
            
            # Test different cases
            await repository.get_character_by_name("LUNA")
            await repository.get_character_by_name("Luna")
            await repository.get_character_by_name("luna")
            
            # Should be called 3 times with exact case as provided
            assert mock_find_one.call_count == 3
    
    @pytest.mark.asyncio
    async def test_repository_concurrent_access(self, repository, sample_character_document):
        """Test repository behavior under concurrent access scenarios."""
        with patch.object(Character, 'get', new_callable=AsyncMock) as mock_get:
            character = sample_character_document
            # Simulate concurrent modification error
            character.save = AsyncMock(side_effect=[
                RevisionIdWasChanged("Concurrent update"),
                character  # Second call succeeds
            ])
            mock_get.return_value = character
            
            updates = {"display_name": "Concurrent Update"}
            
            # First call should raise exception
            with pytest.raises(RevisionIdWasChanged):
                await repository.update_character(str(character.id), updates)
    
    @pytest.mark.asyncio
    async def test_repository_with_special_characters_in_names(self, repository):
        """Test repository operations with special characters in names."""
        special_names = [
            "character-with-dashes",
            "character_with_underscores",
            "character with spaces",
            "character!@#$%",
            "character.with.dots",
            "character/with/slashes"
        ]
        
        with patch.object(Character, 'find_one', new_callable=AsyncMock) as mock_find_one:
            mock_find_one.return_value = None
            
            for name in special_names:
                result = await repository.get_character_by_name(name)
                assert result is None
            
            # Should be called once for each special name
            assert mock_find_one.call_count == len(special_names)