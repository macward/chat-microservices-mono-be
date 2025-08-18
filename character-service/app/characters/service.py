"""Character service for business logic with repository pattern integration and centralized configuration."""

import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .repository import CharacterRepository
from .models import Character, CharacterCreate, CharacterUpdate, CharacterResponse

from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, CharacterServiceError
)
from app.core.config import Settings

logger = logging.getLogger(__name__)


# Legacy exception classes for backward compatibility
# These are now aliases to the centralized exceptions
CharacterNotFoundError = NotFoundError
CharacterExistsError = ConflictError
CharacterValidationError = ValidationError


class CharacterCache:
    """Simple in-memory cache for characters."""
    
    def __init__(self, ttl_minutes: int = 15):
        self.cache: Dict[str, tuple] = {}  # key: (character, expiry_time)
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, key: str) -> Optional[CharacterResponse]:
        """Get character from cache if not expired."""
        if key in self.cache:
            character, expiry = self.cache[key]
            if datetime.utcnow() < expiry:
                logger.debug(f"Cache hit for character: {key}")
                return character
            else:
                del self.cache[key]
                logger.debug(f"Cache expired for character: {key}")
        return None
    
    def set(self, key: str, character: CharacterResponse):
        """Set character in cache with TTL."""
        expiry = datetime.utcnow() + self.ttl
        self.cache[key] = (character, expiry)
        logger.debug(f"Cached character: {key}")
    
    def invalidate(self, key: str):
        """Remove character from cache."""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Invalidated cache for character: {key}")
    
    def clear(self):
        """Clear all cache."""
        self.cache.clear()
        logger.debug("Cache cleared")


class CharacterService:
    """
    Service for character business logic with repository pattern integration.
    
    Provides comprehensive character management following business logic patterns
    and project conventions. All operations are async and use proper error
    handling with detailed logging for audit trails.
    
    Uses repository pattern for clean data access, providing clean
    separation between business logic and database operations while maintaining
    high performance and scalability.
    
    Key Features:
    - Character name uniqueness validation
    - Case-insensitive character lookups
    - Active character filtering
    - Version management for character updates
    - System prompt optimization with caching
    - Search capabilities
    - Repository pattern for clean data access
    """
    
    def __init__(
        self, 
        db: Session,
        settings: Optional[Settings] = None
    ):
        """
        Initialize CharacterService with repository dependency injection and centralized configuration.
        
        Args:
            db: AsyncSession instance for database access
            settings: Application settings instance for configuration
        """
        self.repository = CharacterRepository(db)
        self.settings = settings
        
        # Configure cache TTL from centralized configuration
        if settings:
            cache_ttl = settings.application.cache_ttl_minutes
        else:
            # Fallback for backward compatibility
            import os
            cache_ttl = int(os.getenv("CHARACTER_CACHE_TTL_MINUTES", "15"))
            logger.warning("CharacterService initialized without settings, using environment fallback")
        
        self.cache = CharacterCache(ttl_minutes=cache_ttl)
        logger.debug(f"CharacterService initialized with repository pattern and cache TTL: {cache_ttl} minutes")
    
    def create_character(self, character_data: CharacterCreate) -> CharacterResponse:
        """
        Create a new character with validation and caching.
        
        Args:
            character_data: Character creation data
            
        Returns:
            CharacterResponse: Created character response
            
        Raises:
            ConflictError: If character name already exists
            CharacterValidationError: If character data validation fails
            CharacterServiceError: For other character creation failures
        """
        try:
            # Prepare character data for repository
            now = datetime.utcnow()
            character_dict = {
                "name": character_data.name.lower().strip(),
                "display_name": character_data.display_name,
                "description": character_data.description,
                "personality": character_data.personality,
                "system_prompt": character_data.system_prompt,
                "traits": character_data.traits,
                "avatar_url": character_data.avatar_url,
                "voice_settings": character_data.voice_settings,
                "created_at": now,
                "updated_at": now,
                "is_active": True,
                "version_number": 1
            }
            
            # Check for existing character name before creating
            existing_character = self.repository.get_character_by_name(character_dict["name"])
            if existing_character:
                raise ConflictError(
                    f"Character with name '{character_dict['name']}' already exists",
                    resource="character",
                    conflict_type="duplicate",
                    error_code="CHARACTER_CREATE_001"
                )

            # Create character using repository
            created_character = self.repository.create_character(character_dict)
            
            logger.info(f"Created character: {character_data.name}")
            
            # Create response and cache it
            response = CharacterResponse.model_validate(created_character)
            self.cache.set(character_data.name.lower(), response)
            return response
            
        except ConflictError:
            raise
            
        except Exception as e:
            logger.error(f"Error creating character '{character_data.name}': {e}")
            raise CharacterServiceError(
                f"Failed to create character: {str(e)}",
                operation="create_character",
                character_name=character_data.name,
                error_code="CHARACTER_CREATE_003"
            )
    
    def get_character(self, name: str) -> Optional[CharacterResponse]:
        """
        Get character by name with caching.
        
        Args:
            name: Character name to search for
            
        Returns:
            Optional[CharacterResponse]: Character if found, None otherwise
            
        Raises:
            CharacterValidationError: If name is invalid
            CharacterServiceError: For other retrieval failures
        """
        try:
            if not name or not name.strip():
                raise ValidationError(
                    "Character name cannot be empty",
                    field="name",
                    error_code="CHARACTER_GET_001"
                )
            
            cache_key = name.lower().strip()
            
            # Check cache first
            cached_character = self.cache.get(cache_key)
            if cached_character:
                return cached_character
            
            # If not in cache, get from repository
            character = self.repository.get_character_by_name(cache_key)
            if character:
                logger.debug(f"Retrieved character from repository: {name}")
                response = CharacterResponse.model_validate(character)
                # Cache the result
                self.cache.set(cache_key, response)
                return response
            
            logger.debug(f"Character not found: {name}")
            return None
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving character '{name}': {e}")
            raise CharacterServiceError(f"Failed to retrieve character: {str(e)}")
    
    def get_system_prompt(self, character_name: str) -> Optional[str]:
        """
        Get system prompt for character with caching optimization.
        
        Args:
            character_name: Character name
            
        Returns:
            Optional[str]: System prompt if character found, None otherwise
            
        Raises:
            CharacterValidationError: If character name is invalid
            CharacterServiceError: For other retrieval failures
        """
        try:
            if not character_name or not character_name.strip():
                raise CharacterValidationError("Character name cannot be empty")
            
            # Use repository to get character and extract system prompt
            character = self.repository.get_character_by_name(character_name.lower().strip())
            
            if character and character.system_prompt:
                logger.debug(f"Retrieved system prompt for: {character_name}")
                return character.system_prompt
            
            logger.warning(f"No system prompt found for character: {character_name}")
            return None
            
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving system prompt for '{character_name}': {e}")
            raise CharacterServiceError(f"Failed to retrieve system prompt: {str(e)}")
    
    def list_characters(self) -> List[CharacterResponse]:
        """
        Get all active characters.
        
        Returns:
            List[CharacterResponse]: List of active characters
            
        Raises:
            CharacterServiceError: For retrieval failures
        """
        try:
            characters = self.repository.get_all_active_characters()
            result = [CharacterResponse.model_validate(char) for char in characters]
            
            logger.debug(f"Retrieved {len(result)} active characters")
            return result
            
        except Exception as e:
            logger.error(f"Error listing characters: {e}")
            raise CharacterServiceError(f"Failed to list characters: {str(e)}")
    
    def update_character(self, name: str, updates: CharacterUpdate) -> Optional[CharacterResponse]:
        """
        Update character by name with validation.
        
        Args:
            name: Character name to update
            updates: Character update data
            
        Returns:
            Optional[CharacterResponse]: Updated character if found and updated
            
        Raises:
            ConflictError: If new name already exists for another character
            CharacterValidationError: If update data is invalid
            CharacterServiceError: For other update failures
        """
        try:
            # Prepare update dictionary from Pydantic model
            update_dict = {k: v for k, v in updates.model_dump().items() if v is not None}
            
            # Normalize name if being updated
            if 'name' in update_dict:
                new_name = update_dict['name'].lower().strip()
                # Check if new name conflicts with existing character (excluding itself)
                existing_character = self.repository.get_character_by_name(new_name)
                if existing_character and existing_character.name != name.lower().strip():
                    raise ConflictError(
                        f"Character with name '{new_name}' already exists",
                        resource="character",
                        conflict_type="duplicate",
                        error_code="CHARACTER_UPDATE_001"
                    )
                update_dict['name'] = new_name
            
            # Increment version number
            update_dict["version_number"] = Character.version_number + 1
            update_dict["updated_at"] = datetime.utcnow()

            # Update character using repository
            updated_character = self.repository.update_character(name.lower().strip(), update_dict)
            
            if not updated_character:
                logger.warning(f"Character not found for update: {name}")
                return None
            
            # Invalidate cache for both old and new names
            self.cache.invalidate(name.lower().strip())
            if 'name' in update_dict:
                self.cache.invalidate(update_dict['name'])
            
            response = CharacterResponse.model_validate(updated_character)
            
            # Cache the updated character
            cache_key = updated_character.name.lower().strip()
            self.cache.set(cache_key, response)
            
            logger.info(f"Updated character: {name}")
            return response
            
        except ConflictError:
            raise
            
        except Exception as e:
            logger.error(f"Error updating character '{name}': {e}")
            raise CharacterServiceError(f"Failed to update character: {str(e)}")
    
    def delete_character(self, name: str) -> bool:
        """
        Delete character by name (soft delete).
        
        Args:
            name: Character name to delete
            
        Returns:
            bool: True if character was deleted successfully
            
        Raises:
            CharacterServiceError: For deletion failures
        """
        try:
            success = self.repository.delete_character(name.lower().strip())
            
            if success:
                # Invalidate cache for this character
                self.cache.invalidate(name.lower().strip())
                logger.info(f"Deleted character: {name}")
            else:
                logger.warning(f"Character not found for deletion: {name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting character '{name}': {e}")
            raise CharacterServiceError(f"Failed to delete character: {str(e)}")
    
    def get_character_version_info(self, name: str) -> Optional[Dict]:
        """
        Get version information for a character.
        
        Args:
            name: Character name
            
        Returns:
            Optional[Dict]: Version information if character found
            
        Raises:
            CharacterServiceError: For retrieval failures
        """
        try:
            character = self.get_character(name)
            if character:
                return {
                    "character_name": character.name,
                    "current_version": character.version_number,
                    "last_updated": character.updated_at,
                    "created_at": character.created_at
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting version info for character '{name}': {e}")
            raise CharacterServiceError(f"Failed to get version info: {str(e)}")
    
    def search_characters(
        self,
        query: str,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> List[CharacterResponse]:
        """
        Search characters by name, description, or personality.
        
        Args:
            query: Search query string
            include_inactive: Whether to include inactive characters
            skip: Number of results to skip
            limit: Maximum number of results to return
            
        Returns:
            List[CharacterResponse]: List of matching characters
            
        Raises:
            CharacterServiceError: For search failures
        """
        try:
            if not query:
                return []
            
            # For now, a simplified in-memory search. A proper implementation
            # would involve adding a search method to the repository.
            all_characters = self.list_characters()
            
            filtered_characters = [
                char for char in all_characters
                if (query.lower() in char.name.lower() or
                    query.lower() in char.description.lower() or
                    query.lower() in char.personality.lower())
                    and (include_inactive or char.is_active)
            ]

            logger.debug(f"Character search returned {len(filtered_characters)} results for query: '{query}'")
            return filtered_characters[skip:skip+limit]
            
        except Exception as e:
            logger.error(f"Error searching characters: {e}")
            raise CharacterServiceError(f"Failed to search characters: {str(e)}")
    
    def get_character_stats(self, include_inactive: bool = False) -> Dict:
        """
        Get comprehensive character statistics.
        
        Args:
            include_inactive: Whether to include inactive characters in statistics
            
        Returns:
            Dict: Character statistics
            
        Raises:
            CharacterServiceError: For statistics generation failures
        """
        logger.warning("get_character_stats not fully implemented for PostgreSQL backend. Returning dummy data.")
        return {"total_characters": 0, "active_characters": 0, "inactive_characters": 0}
    
    def bulk_deactivate_characters(self, character_names: List[str]) -> Dict:
        """
        Bulk deactivate multiple characters.
        
        Args:
            character_names: List of character names to deactivate
            
        Returns:
            Dict: Results of bulk operation
            
        Raises:
            CharacterServiceError: For bulk operation failures
        """
        logger.warning("bulk_deactivate_characters not fully implemented for PostgreSQL backend. Returning dummy data.")
        return {"success_count": 0, "failed_count": len(character_names)}
    
    def activate_character(self, name: str) -> bool:
        """
        Activate a deactivated character.
        
        Args:
            name: Character name to activate
            
        Returns:
            bool: True if character was activated successfully
            
        Raises:
            CharacterServiceError: For activation failures
        """
        try:
            updates = {"is_active": True}
            activated_character = self.repository.update_character(name.lower().strip(), updates)

            if activated_character:
                # Invalidate cache for this character to refresh
                self.cache.invalidate(name.lower().strip())
                logger.info(f"Activated character: {name}")
                return True
            else:
                logger.warning(f"Character not found for activation: {name}")
                return False
            
        except Exception as e:
            logger.error(f"Error activating character '{name}': {e}")
            raise CharacterServiceError(f"Failed to activate character: {str(e)}")
    
    def get_characters_by_version(
        self,
        min_version: int = 1,
        include_inactive: bool = False
    ) -> List[CharacterResponse]:
        """
        Get characters by version number.
        
        Args:
            min_version: Minimum version number to filter by
            include_inactive: Whether to include inactive characters
            
        Returns:
            List[CharacterResponse]: List of characters matching version criteria
            
        Raises:
            CharacterServiceError: For retrieval failures
        """
        logger.warning("get_characters_by_version not fully implemented for PostgreSQL backend. Returning dummy data.")
        return []
    
    def find_characters_by_metadata(
        self,
        metadata_filters: Dict,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 50
    ) -> List[CharacterResponse]:
        """
        Find characters by metadata field criteria.
        
        Args:
            metadata_filters: Dictionary of metadata field filters
            include_inactive: Whether to include inactive characters
            skip: Number of results to skip
            limit: Maximum number of results to return
            
        Returns:
            List[CharacterResponse]: List of matching characters
            
        Raises:
            CharacterServiceError: For search failures
        """
        logger.warning("find_characters_by_metadata not fully implemented for PostgreSQL backend. Returning dummy data.")
        return []