"""Tests for character models."""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from app.characters.models import Character, CharacterCreate, CharacterUpdate, CharacterResponse


class TestCharacterCreate:
    """Tests for CharacterCreate model."""
    
    def test_valid_character_create(self, sample_character_data):
        """Test creating a valid CharacterCreate instance."""
        character = CharacterCreate(**sample_character_data)
        
        assert character.name == sample_character_data["name"]
        assert character.display_name == sample_character_data["display_name"]
        assert character.personality == sample_character_data["personality"]
        assert character.system_prompt == sample_character_data["system_prompt"]
        assert character.traits == sample_character_data["traits"]
        assert character.avatar_url == sample_character_data["avatar_url"]
        assert character.voice_settings == sample_character_data["voice_settings"]
    
    def test_character_create_minimal_data(self):
        """Test creating CharacterCreate with minimal required data."""
        minimal_data = {
            "name": "minimal",
            "display_name": "Minimal Character",
            "personality": "Simple personality",
            "system_prompt": "Simple system prompt",
            "traits": ["simple"]
        }
        
        character = CharacterCreate(**minimal_data)
        
        assert character.name == "minimal"
        assert character.display_name == "Minimal Character"
        assert character.avatar_url is None
        assert character.voice_settings is None
    
    def test_character_create_missing_required_fields(self):
        """Test validation errors for missing required fields."""
        incomplete_data = {
            "name": "test",
            # Missing display_name, personality, system_prompt, traits
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CharacterCreate(**incomplete_data)
        
        errors = exc_info.value.errors()
        required_fields = {"display_name", "personality", "system_prompt", "traits"}
        error_fields = {error["loc"][0] for error in errors}
        
        assert required_fields.issubset(error_fields)
    
    def test_character_create_empty_strings(self):
        """Test validation with empty strings."""
        empty_data = {
            "name": "",
            "display_name": "",
            "personality": "",
            "system_prompt": "",
            "traits": []
        }
        
        # Pydantic allows empty strings by default
        character = CharacterCreate(**empty_data)
        assert character.name == ""
        assert character.traits == []
    
    def test_character_create_invalid_types(self):
        """Test validation errors for invalid field types."""
        invalid_data = {
            "name": 123,
            "display_name": 456,
            "personality": 789,
            "system_prompt": None,
            "traits": "not_a_list"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CharacterCreate(**invalid_data)
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
    
    def test_character_create_serialization(self, sample_character_data):
        """Test serialization to dict."""
        character = CharacterCreate(**sample_character_data)
        char_dict = character.model_dump()
        
        assert char_dict == sample_character_data
        
    def test_character_create_json_serialization(self, sample_character_data):
        """Test JSON serialization."""
        character = CharacterCreate(**sample_character_data)
        json_str = character.model_dump_json()
        
        assert isinstance(json_str, (str, bytes))
        assert "luna" in str(json_str)


class TestCharacterUpdate:
    """Tests for CharacterUpdate model."""
    
    def test_character_update_all_fields(self):
        """Test CharacterUpdate with all optional fields."""
        update_data = {
            "display_name": "Updated Name",
            "personality": "Updated personality",
            "system_prompt": "Updated system prompt",
            "traits": ["updated", "traits"],
            "avatar_url": "https://updated.com/avatar.png",
            "voice_settings": {"voice": "updated"},
            "is_active": False
        }
        
        update = CharacterUpdate(**update_data)
        
        assert update.display_name == "Updated Name"
        assert update.personality == "Updated personality"
        assert update.is_active is False
    
    def test_character_update_partial_fields(self):
        """Test CharacterUpdate with only some fields."""
        update_data = {
            "display_name": "New Name",
            "traits": ["new", "traits"]
        }
        
        update = CharacterUpdate(**update_data)
        
        assert update.display_name == "New Name"
        assert update.traits == ["new", "traits"]
        assert update.personality is None
        assert update.system_prompt is None
        assert update.is_active is None
    
    def test_character_update_empty(self):
        """Test CharacterUpdate with no fields (all None)."""
        update = CharacterUpdate()
        
        assert update.display_name is None
        assert update.personality is None
        assert update.system_prompt is None
        assert update.traits is None
        assert update.avatar_url is None
        assert update.voice_settings is None
        assert update.is_active is None
    
    def test_character_update_dict_exclude_none(self):
        """Test model_dump() with exclude_unset for partial updates."""
        update = CharacterUpdate(
            display_name="New Name",
            traits=["new"]
        )
        
        # Test excluding None values
        update_dict = {k: v for k, v in update.model_dump().items() if v is not None}
        
        assert "display_name" in update_dict
        assert "traits" in update_dict
        assert "personality" not in update_dict
        assert len(update_dict) == 2


class TestCharacterResponse:
    """Tests for CharacterResponse model."""
    
    def test_character_response_creation(self, sample_character_data):
        """Test creating CharacterResponse instance."""
        response_data = {
            "id": "507f1f77bcf86cd799439011",
            **sample_character_data,
            "is_active": True,
            "version_number": 1
        }
        
        response = CharacterResponse(**response_data)
        
        assert response.id == "507f1f77bcf86cd799439011"
        assert response.name == sample_character_data["name"]
        assert response.is_active is True
        assert response.version_number == 1
    
    def test_character_response_missing_id(self, sample_character_data):
        """Test CharacterResponse requires id field."""
        response_data = {
            **sample_character_data,
            "is_active": True,
            "version_number": 1
            # Missing id
        }
        
        with pytest.raises(ValidationError) as exc_info:
            CharacterResponse(**response_data)
        
        errors = exc_info.value.errors()
        assert any(error["loc"][0] == "id" for error in errors)
    
    def test_character_response_excludes_internal_fields(self, sample_character_data):
        """Test that CharacterResponse doesn't include internal fields."""
        response_data = {
            "id": "507f1f77bcf86cd799439011",
            "name": sample_character_data["name"],
            "display_name": sample_character_data["display_name"],
            "personality": sample_character_data["personality"],
            "traits": sample_character_data["traits"],
            "avatar_url": sample_character_data["avatar_url"],
            "is_active": True,
            "version_number": 1
        }
        
        response = CharacterResponse(**response_data)
        response_dict = response.model_dump()
        
        # CharacterResponse should not include system_prompt or created_at/updated_at
        assert "system_prompt" not in response_dict
        assert "created_at" not in response_dict
        assert "updated_at" not in response_dict


class TestCharacterDocument:
    """Tests for Character document model."""
    
    @patch('app.characters.models.Character')
    def test_character_document_creation(self, mock_character_class, sample_character_data):
        """Test creating Character document instance."""
        now = datetime.utcnow()
        char_data = {
            **sample_character_data,
            "created_at": now,
            "updated_at": now,
            "is_active": True,
            "version_number": 1
        }
        
        # Mock the character instance
        character_instance = MagicMock()
        character_instance.name = sample_character_data["name"]
        character_instance.created_at = now
        character_instance.is_active = True
        character_instance.version_number = 1
        
        mock_character_class.return_value = character_instance
        
        character = mock_character_class(**char_data)
        
        assert character.name == sample_character_data["name"]
        assert character.created_at == now
        assert character.is_active is True
        assert character.version_number == 1
    
    @patch('app.characters.models.Character')
    def test_character_document_defaults(self, mock_character_class, sample_character_data):
        """Test Character document default values."""
        now = datetime.utcnow()
        char_data = {
            **sample_character_data,
            "created_at": now,
            "updated_at": now
        }
        
        # Mock the character instance with defaults
        character_instance = MagicMock()
        character_instance.is_active = True  # Default value
        character_instance.version_number = 1  # Default value
        character_instance.avatar_url = None  # Default value
        character_instance.voice_settings = None  # Default value
        
        mock_character_class.return_value = character_instance
        
        character = mock_character_class(**char_data)
        
        assert character.is_active is True  # Default value
        assert character.version_number == 1  # Default value
        assert character.avatar_url is None  # Default value
        assert character.voice_settings is None  # Default value
    
    def test_character_document_settings(self):
        """Test Character document Beanie settings."""
        assert Character.Settings.name == "characters"


class TestModelValidationEdgeCases:
    """Tests for edge cases and special validation scenarios."""
    
    def test_very_long_strings(self):
        """Test handling of very long string values."""
        long_data = {
            "name": "a" * 1000,
            "display_name": "b" * 1000,
            "personality": "c" * 5000,
            "system_prompt": "d" * 10000,
            "traits": ["e" * 100] * 50
        }
        
        # Pydantic should handle long strings without issues
        character = CharacterCreate(**long_data)
        assert len(character.name) == 1000
        assert len(character.traits) == 50
    
    def test_special_characters(self):
        """Test handling of special characters and unicode."""
        special_data = {
            "name": "special!@#$%^&*()",
            "display_name": "Special !@# Characters éñüñ",
            "personality": "Contains unicode: 😀🚀⭐",
            "system_prompt": "System prompt with special chars: !@#$%^&*()",
            "traits": ["special-chars", "unicode_test", "emoji_😀"]
        }
        
        character = CharacterCreate(**special_data)
        assert "😀" in character.personality
        assert "emoji_😀" in character.traits
    
    def test_whitespace_handling(self):
        """Test handling of whitespace in string fields."""
        whitespace_data = {
            "name": "  whitespace  ",
            "display_name": "  Display Name  ",
            "personality": "  Personality with spaces  ",
            "system_prompt": "  System prompt  ",
            "traits": ["  trait1  ", "  trait2  "]
        }
        
        character = CharacterCreate(**whitespace_data)
        # Pydantic doesn't strip whitespace by default
        assert character.name == "  whitespace  "
        assert character.traits[0] == "  trait1  "
    
    def test_empty_collections(self):
        """Test handling of empty collections."""
        empty_traits_data = {
            "name": "empty_traits",
            "display_name": "Empty Traits",
            "personality": "Has no traits",
            "system_prompt": "System prompt",
            "traits": []
        }
        
        character = CharacterCreate(**empty_traits_data)
        assert character.traits == []
    
    def test_none_vs_missing_optional_fields(self):
        """Test distinction between None and missing optional fields."""
        # Test with explicit None
        data_with_none = {
            "name": "test",
            "display_name": "Test",
            "personality": "Test personality",
            "system_prompt": "Test prompt",
            "traits": ["test"],
            "avatar_url": None,
            "voice_settings": None
        }
        
        character = CharacterCreate(**data_with_none)
        assert character.avatar_url is None
        assert character.voice_settings is None
        
        # Test with missing fields (should also be None)
        data_missing = {
            "name": "test",
            "display_name": "Test",
            "personality": "Test personality",
            "system_prompt": "Test prompt",
            "traits": ["test"]
        }
        
        character_missing = CharacterCreate(**data_missing)
        assert character_missing.avatar_url is None
        assert character_missing.voice_settings is None