"""
Character API router with direct service instantiation.

Simple and reliable approach using direct service instantiation.
Maintains all existing functionality.
"""

import logging
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session # Changed from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .service import CharacterService
from .models import CharacterCreate, CharacterUpdate, CharacterResponse
from app.core.exceptions import (
    ValidationError, NotFoundError, ConflictError, CharacterServiceError
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/characters", tags=["characters"])


@router.get("/", response_model=List[CharacterResponse])
def list_characters(db: Session = Depends(get_db)): # Changed async def to def, AsyncSession to Session
    """Get all active characters."""
    character_service = CharacterService(db)
    return character_service.list_characters() # Removed await


@router.get("/{name}", response_model=CharacterResponse)
def get_character(name: str, db: Session = Depends(get_db)): # Changed async def to def, AsyncSession to Session
    """Get specific character by name."""
    try:
        character_service = CharacterService(db)
        character = character_service.get_character(name) # Removed await
        if not character:
            raise NotFoundError(
                "Character",
                name,
                error_code="CHARACTER_GET_001"
            )
        return character
    except (ValidationError, NotFoundError, CharacterServiceError):
        # Let global exception handler manage the response
        raise
    except Exception as e:
        logger.error(f"Character retrieval failed: {e}")
        # Let global exception handler manage the response
        raise


@router.post("/", response_model=CharacterResponse)
def create_character(character_data: CharacterCreate, db: Session = Depends(get_db)): # Changed async def to def, AsyncSession to Session
    """Create new character."""
    try:
        character_service = CharacterService(db)
        return character_service.create_character(character_data) # Removed await
    except (ValidationError, ConflictError, CharacterServiceError):
        # Let global exception handler manage the response
        raise
    except Exception as e:
        logger.error(f"Character creation failed: {e}")
        # Let global exception handler manage the response
        raise


@router.put("/{name}", response_model=CharacterResponse)
def update_character(name: str, updates: CharacterUpdate, db: Session = Depends(get_db)): # Changed async def to def, AsyncSession to Session
    """Update character by name."""
    try:
        character_service = CharacterService(db)
        character = character_service.update_character(name, updates) # Removed await
        if not character:
            raise NotFoundError(
                "Character",
                name,
                error_code="CHARACTER_UPDATE_001"
            )
        return character
    except (ValidationError, NotFoundError, ConflictError, CharacterServiceError):
        # Let global exception handler manage the response
        raise
    except Exception as e:
        logger.error(f"Character update failed: {e}")
        # Let global exception handler manage the response
        raise


@router.delete("/{name}")
def delete_character(name: str, db: Session = Depends(get_db)): # Changed async def to def, AsyncSession to Session
    """Delete character by name."""
    try:
        character_service = CharacterService(db)
        success = character_service.delete_character(name) # Removed await
        if not success:
            raise NotFoundError(
                "Character",
                name,
                error_code="CHARACTER_DELETE_001"
            )
        return {"message": f"Character \'{name}\' deleted successfully"}
    except (NotFoundError, CharacterServiceError):
        # Let global exception handler manage the response
        raise
    except Exception as e:
        logger.error(f"Character deletion failed: {e}")
        # Let global exception handler manage the response
        raise