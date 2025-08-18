"""Character repository for data access."""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from .models import Character


class CharacterRepository:
    """Repository for character data access using SQLAlchemy."""

    def __init__(self, db: Session):
        self.db = db

    def create_character(self, character_data: dict) -> Character:
        """Create a new character."""
        character = Character(**character_data)
        self.db.add(character)
        self.db.commit()
        self.db.refresh(character)
        return character

    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get character by name."""
        stmt = select(Character).where(Character.name == name, Character.is_active == True)
        result = self.db.execute(stmt)
        return result.scalars().first()

    def get_all_active_characters(self) -> List[Character]:
        """Get all active characters."""
        stmt = select(Character).where(Character.is_active == True)
        result = self.db.execute(stmt)
        return result.scalars().all()

    def update_character(self, name: str, updates: dict) -> Optional[Character]:
        """Update character by name."""
        stmt = select(Character).where(Character.name == name)
        result = self.db.execute(stmt)
        character = result.scalars().first()
        if character:
            for key, value in updates.items():
                setattr(character, key, value)
            self.db.commit()
            self.db.refresh(character)
            return character
        return None

    def delete_character(self, name: str) -> bool:
        """Soft delete character by name."""
        stmt = select(Character).where(Character.name == name)
        result = self.db.execute(stmt)
        character = result.scalars().first()
        if character:
            character.is_active = False
            self.db.commit()
            self.db.refresh(character)
            return True
        return False