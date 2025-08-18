"""Database connection and initialization."""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.models.database import Message

logger = get_logger(__name__)


class Database:
    """Database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    

database = Database()


async def connect_to_database():
    """Create database connection and initialize Beanie."""
    logger.info("Connecting to MongoDB", url=settings.mongodb_url)
    
    try:
        # Create MongoDB client
        database.client = AsyncIOMotorClient(
            settings.mongodb_url,
            minPoolSize=settings.mongodb_connection_pool_min,
            maxPoolSize=settings.mongodb_connection_pool_max,
        )
        
        # Get database
        db = database.client[settings.mongodb_database]
        
        # Initialize Beanie with document models
        await init_beanie(
            database=db,
            document_models=[Message]
        )
        
        logger.info("Connected to MongoDB successfully")
        
    except Exception as e:
        logger.error("Failed to connect to MongoDB", error=str(e))
        raise


async def close_database_connection():
    """Close database connection."""
    if database.client:
        logger.info("Closing MongoDB connection")
        database.client.close()


async def get_database():
    """Get database instance."""
    if not database.client:
        await connect_to_database()
    return database.client[settings.mongodb_database]