import logging
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.models.conversation import Conversation

logger = logging.getLogger(__name__)

# Global MongoDB client and database instances
_client: AsyncIOMotorClient = None
_database = None

async def init_mongodb():
    """
    Initialize MongoDB connection with Beanie ODM
    """
    global _client, _database
    
    try:
        _client = AsyncIOMotorClient(settings.mongodb_url, serverSelectionTimeoutMS=5000)
        _database = _client[settings.mongodb_database]
        
        await init_beanie(
            database=_database, 
            document_models=[Conversation]
        )
        logger.info("MongoDB connection initialized successfully")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Service will start without database for testing.")


def get_database():
    """
    Get the MongoDB database instance.
    
    Returns:
        The MongoDB database instance or None if not initialized
    """
    return _database


def get_client():
    """
    Get the MongoDB client instance.
    
    Returns:
        The MongoDB client instance or None if not initialized
    """
    return _client