# Character Management System

## Overview

The Character Management System is a robust, scalable solution for creating, managing, and interacting with virtual characters in a conversational AI application. This module provides a comprehensive set of features for defining, storing, and retrieving character profiles with advanced caching and persistence mechanisms.

## Architecture

### Components

1. **Models** (`models.py`):
   - Define data structures for characters
   - Supports MongoDB persistence with Beanie ODM
   - Flexible schema for character attributes

2. **Repository** (`repository.py`):
   - Low-level data access layer
   - CRUD operations for characters
   - Direct interaction with MongoDB

3. **Service** (`service.py`):
   - Business logic and caching layer
   - Handles character operations with built-in caching
   - Manages character lifecycle and version tracking

4. **Router** (`router.py`):
   - FastAPI endpoints for character management
   - RESTful API for character operations
   - Error handling and validation

### Key Features

- In-memory caching with Time-To-Live (TTL)
- Unique character name constraints
- Automatic version tracking
- Soft delete mechanism
- Comprehensive logging

## Data Models

### Character (MongoDB Document)

Represents a fully defined character with persistent storage.

| Field           | Type           | Description                              | Required | Default     |
|----------------|----------------|------------------------------------------|----------|-------------|
| name           | str            | Unique identifier for the character       | ✓        | -           |
| display_name   | str            | Friendly name displayed to users          | ✓        | -           |
| personality    | str            | Detailed personality description          | ✓        | -           |
| system_prompt  | str            | Base context for character interactions   | ✓        | -           |
| traits         | List[str]      | Character's defining personality traits   | ✓        | -           |
| avatar_url     | Optional[str]  | URL to character's avatar image           | ✗        | None        |
| voice_settings | Optional[Dict] | Configuration for character's voice       | ✗        | None        |
| created_at     | datetime       | Timestamp of character creation           | ✓        | Current UTC |
| updated_at     | datetime       | Timestamp of last update                  | ✓        | Current UTC |
| is_active      | bool           | Character's active/inactive status        | ✗        | True        |
| version_number | int            | Version tracking for the character        | ✗        | 1           |

### Additional Models

1. **CharacterCreate**:
   - Used for creating new characters
   - Excludes system-managed fields

2. **CharacterUpdate**:
   - Allows partial updates to character
   - All fields are optional

3. **CharacterResponse**:
   - Safe representation for API responses
   - Includes ID and version information

## Caching System

### CharacterCache

- In-memory cache with configurable Time-To-Live (default 15 minutes)
- Automatic cache invalidation
- Prevents repeated database queries
- Configurable via `CHARACTER_CACHE_TTL_MINUTES` environment variable

## API Endpoints

### GET /characters

- **Description**: Retrieve all active characters
- **Response**: List of CharacterResponse objects
- **Status Codes**:
  - 200: Successful retrieval
  - 500: Server error

### GET /characters/{name}

- **Description**: Retrieve a specific character by name
- **Parameters**: Character name (case-insensitive)
- **Response**: CharacterResponse object
- **Status Codes**:
  - 200: Character found
  - 400: Invalid name
  - 404: Character not found
  - 500: Server error

### POST /characters

- **Description**: Create a new character
- **Request Body**: CharacterCreate object
- **Response**: CharacterResponse object
- **Validations**:
  - Unique character name
  - All required fields present
- **Status Codes**:
  - 200: Character created
  - 400: Invalid character data
  - 500: Creation failed

### PUT /characters/{name}

- **Description**: Update an existing character
- **Parameters**: Character name
- **Request Body**: CharacterUpdate object
- **Response**: Updated CharacterResponse object
- **Status Codes**:
  - 200: Character updated
  - 404: Character not found
  - 500: Update failed

### DELETE /characters/{name}

- **Description**: Soft delete a character
- **Parameters**: Character name
- **Response**: Deletion confirmation message
- **Status Codes**:
  - 200: Character deleted
  - 404: Character not found
  - 500: Deletion failed

## Usage Examples

### Creating a Character

```python
from app.characters.models import CharacterCreate

luna_character = CharacterCreate(
    name="luna",
    display_name="Luna",
    personality="Friendly AI assistant",
    system_prompt="You are Luna, a helpful and cheerful AI...",
    traits=["helpful", "creative", "patient"],
    avatar_url="https://example.com/luna_avatar.png"
)
```

### Retrieving a Character

```python
from app.characters.service import CharacterService

service = CharacterService()
luna = await service.get_character("luna")
print(luna.display_name)  # Output: Luna
```

## Best Practices

1. Always use unique, lowercase character names
2. Provide comprehensive system prompts
3. Use meaningful traits
4. Leverage caching for performance
5. Handle potential exceptions in character operations

## Performance Considerations

- Character retrieval is cached for 15 minutes by default
- Modify `CHARACTER_CACHE_TTL_MINUTES` to adjust cache duration
- Each character update increments the version number

## Error Handling

- Comprehensive logging for all character operations
- Specific exception types for different error scenarios
- RESTful error responses with appropriate status codes

## Extensibility

The modular architecture allows easy extension of:
- Character attributes
- Caching mechanisms
- Persistence layers
- Validation rules

## Dependencies

- FastAPI
- Beanie ODM
- MongoDB
- Pydantic