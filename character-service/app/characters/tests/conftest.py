"""Test configuration and shared fixtures for characters module."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.characters.models import Character, CharacterCreate, CharacterUpdate, CharacterResponse
from app.characters.service import CharacterService, CharacterCache
from app.characters.repository import CharacterRepository


@pytest.fixture
def sample_character_data():
    """Sample character data for testing."""
    return {
        "name": "luna",
        "display_name": "Luna",
        "personality": "Friendly and helpful AI assistant",
        "system_prompt": "You are Luna, a helpful AI assistant.",
        "traits": ["helpful", "friendly", "intelligent"],
        "avatar_url": "https://example.com/avatar.png",
        "voice_settings": {"voice": "en-US-Wavenet-F", "speed": 1.0}
    }


@pytest.fixture
def sample_character_create(sample_character_data):
    """Sample CharacterCreate model for testing."""
    return CharacterCreate(**sample_character_data)


@pytest.fixture
def sample_character_update():
    """Sample CharacterUpdate model for testing."""
    return CharacterUpdate(
        display_name="Luna Updated",
        personality="Updated personality",
        traits=["updated", "helpful"]
    )


@pytest.fixture
def sample_character_document(sample_character_data):
    """Sample Character document for testing."""
    now = datetime.utcnow()
    # Create a mock character document that doesn't require Beanie initialization
    character = MagicMock(spec=Character)
    character.id = "507f1f77bcf86cd799439011"
    character.name = sample_character_data["name"]
    character.display_name = sample_character_data["display_name"]
    character.personality = sample_character_data["personality"]
    character.system_prompt = sample_character_data["system_prompt"]
    character.traits = sample_character_data["traits"]
    character.avatar_url = sample_character_data["avatar_url"]
    character.voice_settings = sample_character_data["voice_settings"]
    character.created_at = now
    character.updated_at = now
    character.is_active = True
    character.version_number = 1
    character.dict.return_value = {
        "id": character.id,
        **sample_character_data,
        "created_at": now,
        "updated_at": now,
        "is_active": True,
        "version_number": 1
    }
    return character


@pytest.fixture
def sample_character_response(sample_character_data):
    """Sample CharacterResponse model for testing."""
    # Create a mock that behaves like CharacterResponse but allows extra attributes
    response = MagicMock(spec=CharacterResponse)
    response.id = "507f1f77bcf86cd799439011"
    response.name = sample_character_data["name"]
    response.display_name = sample_character_data["display_name"]
    response.personality = sample_character_data["personality"]
    response.traits = sample_character_data["traits"]
    response.avatar_url = sample_character_data["avatar_url"]
    response.is_active = True
    response.version_number = 1
    # Add extra fields for testing purposes
    response.system_prompt = sample_character_data["system_prompt"]
    response.created_at = datetime.utcnow()
    response.updated_at = datetime.utcnow()
    return response


@pytest.fixture
def mock_character_repository():
    """Mock CharacterRepository for testing."""
    repository = AsyncMock(spec=CharacterRepository)
    return repository


@pytest.fixture
def character_cache():
    """Real CharacterCache instance for testing."""
    return CharacterCache(ttl_minutes=1)  # Short TTL for testing


@pytest.fixture
def mock_character_service():
    """Mock CharacterService for testing."""
    service = AsyncMock(spec=CharacterService)
    return service


@pytest.fixture
def multiple_characters():
    """Multiple character data for list testing."""
    base_data = {
        "personality": "Test personality",
        "system_prompt": "Test system prompt",
        "traits": ["test"],
        "avatar_url": None,
        "voice_settings": None
    }
    
    now = datetime.utcnow()
    
    characters = []
    for i in range(1, 4):
        character = MagicMock(spec=Character)
        character.id = f"507f1f77bcf86cd79943901{i}"
        character.name = f"character{i}"
        character.display_name = f"Character {i}"
        character.personality = base_data["personality"]
        character.system_prompt = base_data["system_prompt"]
        character.traits = base_data["traits"]
        character.avatar_url = base_data["avatar_url"]
        character.voice_settings = base_data["voice_settings"]
        character.created_at = now
        character.updated_at = now
        character.is_active = True
        character.version_number = 1
        character.dict.return_value = {
            "id": character.id,
            "name": character.name,
            "display_name": character.display_name,
            **base_data,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "version_number": 1
        }
        characters.append(character)
    
    return characters


@pytest.fixture
def invalid_character_data():
    """Invalid character data for validation testing."""
    return [
        # Missing required fields
        {
            "name": "test",
            # missing display_name, personality, system_prompt, traits
        },
        # Empty strings
        {
            "name": "",
            "display_name": "",
            "personality": "",
            "system_prompt": "",
            "traits": []
        },
        # Invalid types
        {
            "name": 123,
            "display_name": 456,
            "personality": 789,
            "system_prompt": None,
            "traits": "not_a_list"
        }
    ]


@pytest.fixture
def edge_case_character_data():
    """Edge case character data for testing."""
    return [
        # Very long strings
        {
            "name": "a" * 1000,
            "display_name": "b" * 1000,
            "personality": "c" * 5000,
            "system_prompt": "d" * 10000,
            "traits": ["e" * 100] * 50
        },
        # Special characters
        {
            "name": "special!@#$%^&*()",
            "display_name": "Special !@# Characters",
            "personality": "Contains special chars: !@#$%^&*()",
            "system_prompt": "System prompt with unicode: éñüñ",
            "traits": ["special-chars", "unicode_test", "emoji_😀"]
        },
        # Whitespace handling
        {
            "name": "  whitespace  ",
            "display_name": "  Display Name  ",
            "personality": "  Personality with spaces  ",
            "system_prompt": "  System prompt  ",
            "traits": ["  trait1  ", "  trait2  "]
        }
    ]


@pytest.fixture
async def async_client():
    """Async HTTP client for testing FastAPI endpoints."""
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_datetime():
    """Mock datetime for consistent testing."""
    mock_dt = MagicMock()
    mock_dt.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
    return mock_dt


# Database mocking fixtures
@pytest.fixture
def mock_beanie_character():
    """Mock Beanie Character class for database operations."""
    mock_char = AsyncMock()
    mock_char.create = AsyncMock()
    mock_char.find_one = AsyncMock()
    mock_char.find = AsyncMock()
    mock_char.get = AsyncMock()
    mock_char.save = AsyncMock()
    return mock_char


@pytest.fixture
def mock_motor_collection():
    """Mock Motor collection for MongoDB operations."""
    collection = AsyncMock()
    collection.insert_one = AsyncMock()
    collection.find_one = AsyncMock()
    collection.find = AsyncMock()
    collection.update_one = AsyncMock()
    collection.delete_one = AsyncMock()
    return collection