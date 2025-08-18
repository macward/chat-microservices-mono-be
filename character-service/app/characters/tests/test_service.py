"""Tests for character service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import os

from app.characters.service import CharacterService, CharacterCache
from app.characters.models import Character, CharacterCreate, CharacterUpdate, CharacterResponse


class TestCharacterCache:
    """Tests for CharacterCache functionality."""
    
    def test_cache_initialization(self):
        """Test cache initialization with default and custom TTL."""
        # Default TTL
        cache = CharacterCache()
        assert cache.ttl == timedelta(minutes=15)
        assert cache.cache == {}
        
        # Custom TTL
        cache_custom = CharacterCache(ttl_minutes=30)
        assert cache_custom.ttl == timedelta(minutes=30)
    
    def test_cache_set_and_get_hit(self, sample_character_response):
        """Test setting and getting cached character (cache hit)."""
        cache = CharacterCache(ttl_minutes=1)
        
        cache.set("luna", sample_character_response)
        
        result = cache.get("luna")
        assert result == sample_character_response
        assert "luna" in cache.cache
    
    def test_cache_get_miss(self):
        """Test cache miss for non-existent key."""
        cache = CharacterCache()
        
        result = cache.get("nonexistent")
        assert result is None
    
    @patch('app.characters.service.datetime')
    def test_cache_expiration(self, mock_datetime, sample_character_response):
        """Test cache expiration after TTL."""
        cache = CharacterCache(ttl_minutes=1)
        
        # Set initial time
        now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = now
        
        cache.set("luna", sample_character_response)
        
        # Advance time beyond TTL
        expired_time = now + timedelta(minutes=2)
        mock_datetime.utcnow.return_value = expired_time
        
        result = cache.get("luna")
        assert result is None
        assert "luna" not in cache.cache  # Should be removed after expiration
    
    def test_cache_invalidate(self, sample_character_response):
        """Test cache invalidation."""
        cache = CharacterCache()
        
        cache.set("luna", sample_character_response)
        assert cache.get("luna") == sample_character_response
        
        cache.invalidate("luna")
        assert cache.get("luna") is None
        assert "luna" not in cache.cache
    
    def test_cache_invalidate_nonexistent(self):
        """Test invalidating non-existent cache entry."""
        cache = CharacterCache()
        
        # Should not raise error
        cache.invalidate("nonexistent")
    
    def test_cache_clear(self, sample_character_response):
        """Test clearing entire cache."""
        cache = CharacterCache()
        
        cache.set("luna", sample_character_response)
        cache.set("other", sample_character_response)
        assert len(cache.cache) == 2
        
        cache.clear()
        assert len(cache.cache) == 0
        assert cache.get("luna") is None


class TestCharacterService:
    """Tests for CharacterService business logic."""
    
    @pytest.fixture
    def service_with_mock_repo(self, mock_character_repository):
        """Create service with mocked repository."""
        with patch('app.characters.service.CharacterRepository') as mock_repo_class:
            mock_repo_class.return_value = mock_character_repository
            service = CharacterService()
            service.repository = mock_character_repository
            return service
    
    @pytest.mark.asyncio
    async def test_create_character_success(self, service_with_mock_repo, sample_character_create, sample_character_document):
        """Test successful character creation."""
        service = service_with_mock_repo
        
        # Mock repository methods
        service.repository.get_character_by_name.return_value = None  # Name not taken
        service.repository.create_character.return_value = sample_character_document
        
        with patch('app.characters.service.datetime') as mock_datetime:
            now = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = now
            
            result = await service.create_character(sample_character_create)
            
            # Verify repository calls
            service.repository.get_character_by_name.assert_called_once_with("luna")
            service.repository.create_character.assert_called_once()
            
            # Verify character data
            create_call_args = service.repository.create_character.call_args[0][0]
            assert create_call_args["name"] == "luna"
            assert create_call_args["created_at"] == now
            assert create_call_args["updated_at"] == now
            assert create_call_args["version_number"] == 1
            
            # Verify response
            assert isinstance(result, CharacterResponse)
            assert result.name == "luna"
            
            # Verify caching
            cached = service.cache.get("luna")
            assert cached == result
    
    @pytest.mark.asyncio
    async def test_create_character_duplicate_name(self, service_with_mock_repo, sample_character_create, sample_character_document):
        """Test creating character with duplicate name."""
        service = service_with_mock_repo
        
        # Mock existing character
        service.repository.get_character_by_name.return_value = sample_character_document
        
        with pytest.raises(ValueError, match="Character with name 'luna' already exists"):
            await service.create_character(sample_character_create)
        
        # Should not attempt to create
        service.repository.create_character.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_character_repository_error(self, service_with_mock_repo, sample_character_create):
        """Test character creation with repository error."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = None
        service.repository.create_character.side_effect = Exception("Database error")
        
        with pytest.raises(RuntimeError, match="Failed to create character"):
            await service.create_character(sample_character_create)
    
    @pytest.mark.asyncio
    async def test_get_character_cache_hit(self, service_with_mock_repo, sample_character_response):
        """Test getting character from cache (cache hit)."""
        service = service_with_mock_repo
        
        # Pre-populate cache
        service.cache.set("luna", sample_character_response)
        
        result = await service.get_character("luna")
        
        assert result == sample_character_response
        # Repository should not be called
        service.repository.get_character_by_name.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_character_cache_miss_db_hit(self, service_with_mock_repo, sample_character_document):
        """Test getting character from database (cache miss)."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = sample_character_document
        
        result = await service.get_character("luna")
        
        # Verify repository call
        service.repository.get_character_by_name.assert_called_once_with("luna")
        
        # Verify result
        assert isinstance(result, CharacterResponse)
        assert result.name == "luna"
        
        # Verify caching
        cached = service.cache.get("luna")
        assert cached == result
    
    @pytest.mark.asyncio
    async def test_get_character_not_found(self, service_with_mock_repo):
        """Test getting non-existent character."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = None
        
        result = await service.get_character("nonexistent")
        
        assert result is None
        service.repository.get_character_by_name.assert_called_once_with("nonexistent")
    
    @pytest.mark.asyncio
    async def test_get_character_empty_name(self, service_with_mock_repo):
        """Test getting character with empty name."""
        service = service_with_mock_repo
        
        with pytest.raises(ValueError, match="Character name cannot be empty"):
            await service.get_character("")
        
        with pytest.raises(ValueError, match="Character name cannot be empty"):
            await service.get_character("   ")
    
    @pytest.mark.asyncio
    async def test_get_character_name_normalization(self, service_with_mock_repo, sample_character_document):
        """Test character name normalization (lowercase, strip)."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = sample_character_document
        
        # Test with uppercase and whitespace
        await service.get_character("  LUNA  ")
        
        # Should normalize to lowercase and strip
        service.repository.get_character_by_name.assert_called_once_with("luna")
    
    @pytest.mark.asyncio
    async def test_get_system_prompt_success(self, service_with_mock_repo, sample_character_response):
        """Test getting system prompt for character."""
        service = service_with_mock_repo
        
        # Mock get_character to return character
        with patch.object(service, 'get_character', return_value=sample_character_response):
            result = await service.get_system_prompt("luna")
            
            assert result == sample_character_response.system_prompt
    
    @pytest.mark.asyncio
    async def test_get_system_prompt_character_not_found(self, service_with_mock_repo):
        """Test getting system prompt for non-existent character."""
        service = service_with_mock_repo
        
        with patch.object(service, 'get_character', return_value=None):
            result = await service.get_system_prompt("nonexistent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_list_characters(self, service_with_mock_repo, multiple_characters):
        """Test listing all active characters."""
        service = service_with_mock_repo
        
        service.repository.get_all_active_characters.return_value = multiple_characters
        
        result = await service.list_characters()
        
        assert len(result) == 3
        assert all(isinstance(char, CharacterResponse) for char in result)
        service.repository.get_all_active_characters.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_character_success(self, service_with_mock_repo, sample_character_document, sample_character_update):
        """Test successful character update."""
        service = service_with_mock_repo
        
        # Mock repository methods
        service.repository.get_character_by_name.return_value = sample_character_document
        
        updated_character = Character(**sample_character_document.dict())
        updated_character.display_name = "Luna Updated"
        updated_character.version_number = 2
        service.repository.update_character.return_value = updated_character
        
        with patch('app.characters.service.datetime') as mock_datetime:
            now = datetime(2024, 1, 1, 12, 0, 0)
            mock_datetime.utcnow.return_value = now
            
            result = await service.update_character("luna", sample_character_update)
            
            # Verify repository calls
            service.repository.get_character_by_name.assert_called_once_with("luna")
            service.repository.update_character.assert_called_once()
            
            # Verify update data
            update_call_args = service.repository.update_character.call_args[0]
            update_dict = update_call_args[1]
            assert update_dict["updated_at"] == now
            assert update_dict["version_number"] == 2  # Incremented
            
            # Verify result
            assert isinstance(result, CharacterResponse)
            assert result.display_name == "Luna Updated"
    
    @pytest.mark.asyncio
    async def test_update_character_not_found(self, service_with_mock_repo, sample_character_update):
        """Test updating non-existent character."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = None
        
        result = await service.update_character("nonexistent", sample_character_update)
        
        assert result is None
        service.repository.update_character.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_update_character_cache_invalidation(self, service_with_mock_repo, sample_character_document, sample_character_update, sample_character_response):
        """Test cache invalidation on character update."""
        service = service_with_mock_repo
        
        # Pre-populate cache
        service.cache.set("luna", sample_character_response)
        
        # Mock repository
        service.repository.get_character_by_name.return_value = sample_character_document
        updated_character = Character(**sample_character_document.dict())
        updated_character.version_number = 2
        service.repository.update_character.return_value = updated_character
        
        await service.update_character("luna", sample_character_update)
        
        # Verify cache was updated (old entry invalidated, new one cached)
        cached = service.cache.get("luna")
        assert cached is not None
        assert cached.version_number == 2
    
    @pytest.mark.asyncio
    async def test_delete_character_success(self, service_with_mock_repo, sample_character_document):
        """Test successful character deletion."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = sample_character_document
        service.repository.delete_character.return_value = True
        
        result = await service.delete_character("luna")
        
        assert result is True
        service.repository.get_character_by_name.assert_called_once_with("luna")
        service.repository.delete_character.assert_called_once_with(str(sample_character_document.id))
    
    @pytest.mark.asyncio
    async def test_delete_character_not_found(self, service_with_mock_repo):
        """Test deleting non-existent character."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = None
        
        result = await service.delete_character("nonexistent")
        
        assert result is False
        service.repository.delete_character.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_character_cache_invalidation(self, service_with_mock_repo, sample_character_document, sample_character_response):
        """Test cache invalidation on character deletion."""
        service = service_with_mock_repo
        
        # Pre-populate cache
        service.cache.set("luna", sample_character_response)
        
        service.repository.get_character_by_name.return_value = sample_character_document
        service.repository.delete_character.return_value = True
        
        await service.delete_character("luna")
        
        # Verify cache was invalidated
        cached = service.cache.get("luna")
        assert cached is None
    
    @pytest.mark.asyncio
    async def test_get_character_version_info(self, service_with_mock_repo, sample_character_response):
        """Test getting character version information."""
        service = service_with_mock_repo
        
        # Add missing datetime fields to response
        sample_character_response.created_at = datetime(2024, 1, 1, 10, 0, 0)
        sample_character_response.updated_at = datetime(2024, 1, 1, 12, 0, 0)
        
        with patch.object(service, 'get_character', return_value=sample_character_response):
            result = await service.get_character_version_info("luna")
            
            assert result == {
                "character_name": "luna",
                "current_version": 1,
                "last_updated": sample_character_response.updated_at,
                "created_at": sample_character_response.created_at
            }
    
    @pytest.mark.asyncio
    async def test_get_character_version_info_not_found(self, service_with_mock_repo):
        """Test getting version info for non-existent character."""
        service = service_with_mock_repo
        
        with patch.object(service, 'get_character', return_value=None):
            result = await service.get_character_version_info("nonexistent")
            
            assert result is None


class TestCharacterServiceConfiguration:
    """Tests for service configuration and environment variables."""
    
    @patch.dict(os.environ, {"CHARACTER_CACHE_TTL_MINUTES": "30"})
    def test_cache_ttl_from_environment(self):
        """Test cache TTL configuration from environment variable."""
        with patch('app.characters.service.CharacterRepository'):
            service = CharacterService()
            assert service.cache.ttl == timedelta(minutes=30)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_cache_ttl_default_value(self):
        """Test default cache TTL when environment variable not set."""
        with patch('app.characters.service.CharacterRepository'):
            service = CharacterService()
            assert service.cache.ttl == timedelta(minutes=15)
    
    @patch.dict(os.environ, {"CHARACTER_CACHE_TTL_MINUTES": "invalid"})
    def test_cache_ttl_invalid_value(self):
        """Test handling of invalid cache TTL environment variable."""
        with patch('app.characters.service.CharacterRepository'):
            with pytest.raises(ValueError):
                CharacterService()


class TestCharacterServiceErrorHandling:
    """Tests for error handling in character service."""
    
    @pytest.fixture
    def service_with_mock_repo(self, mock_character_repository):
        """Create service with mocked repository."""
        with patch('app.characters.service.CharacterRepository') as mock_repo_class:
            mock_repo_class.return_value = mock_character_repository
            service = CharacterService()
            service.repository = mock_character_repository
            return service
    
    @pytest.mark.asyncio
    async def test_get_character_repository_error(self, service_with_mock_repo):
        """Test handling of repository errors in get_character."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.side_effect = Exception("Database connection error")
        
        with pytest.raises(RuntimeError, match="Failed to retrieve character"):
            await service.get_character("luna")
    
    @pytest.mark.asyncio
    async def test_update_character_repository_error(self, service_with_mock_repo, sample_character_document, sample_character_update):
        """Test handling of repository errors in update_character."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = sample_character_document
        service.repository.update_character.side_effect = Exception("Update failed")
        
        with pytest.raises(RuntimeError, match="Failed to update character"):
            await service.update_character("luna", sample_character_update)
    
    @pytest.mark.asyncio
    async def test_delete_character_repository_error(self, service_with_mock_repo, sample_character_document):
        """Test handling of repository errors in delete_character."""
        service = service_with_mock_repo
        
        service.repository.get_character_by_name.return_value = sample_character_document
        service.repository.delete_character.side_effect = Exception("Delete failed")
        
        with pytest.raises(RuntimeError, match="Failed to delete character"):
            await service.delete_character("luna")


class TestCharacterServiceConcurrency:
    """Tests for concurrent operations in character service."""
    
    @pytest.fixture
    def service_with_mock_repo(self, mock_character_repository):
        """Create service with mocked repository."""
        with patch('app.characters.service.CharacterRepository') as mock_repo_class:
            mock_repo_class.return_value = mock_character_repository
            service = CharacterService()
            service.repository = mock_character_repository
            return service
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self, service_with_mock_repo, sample_character_response):
        """Test concurrent access to cache."""
        service = service_with_mock_repo
        
        # Simulate concurrent set operations
        service.cache.set("luna1", sample_character_response)
        service.cache.set("luna2", sample_character_response)
        service.cache.set("luna3", sample_character_response)
        
        # All should be cached
        assert service.cache.get("luna1") == sample_character_response
        assert service.cache.get("luna2") == sample_character_response
        assert service.cache.get("luna3") == sample_character_response