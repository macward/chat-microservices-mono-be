"""Character data models."""
import uuid
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from app.database import Base

class Character(Base):
    """Character document model (PostgreSQL)."""
    __tablename__ = "characters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    personality = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    traits = Column(ARRAY(String), nullable=False)
    avatar_url = Column(String, nullable=True)
    voice_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    version_number = Column(Integer, default=1, nullable=False)


class CharacterCreate(BaseModel):
    """Character creation request model."""
    name: str
    display_name: str
    description: str
    personality: str
    system_prompt: str
    traits: List[str]
    avatar_url: Optional[str] = None
    voice_settings: Optional[Dict] = None


class CharacterUpdate(BaseModel):
    """Character update request model."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    personality: Optional[str] = None
    system_prompt: Optional[str] = None
    traits: Optional[List[str]] = None
    avatar_url: Optional[str] = None
    voice_settings: Optional[Dict] = None
    is_active: Optional[bool] = None


class CharacterResponse(BaseModel):
    """Character response model."""
    id: uuid.UUID
    name: str
    display_name: str
    description: str
    personality: str
    system_prompt: str
    traits: List[str]
    avatar_url: Optional[str] = None
    is_active: bool
    version_number: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # updated from orm_mode = True