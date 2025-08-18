#!/usr/bin/env python3
"""Script to set up MongoDB indexes based on the database design documentation."""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def create_message_indexes():
    """Create indexes for the messages collection."""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    messages_collection = db.messages
    
    logger.info("Creating MongoDB indexes for messages collection")
    
    try:
        # Unique index for message_id
        await messages_collection.create_index(
            [("message_id", 1)],
            unique=True,
            name="idx_message_id_unique"
        )
        logger.info("Created unique index for message_id")
        
        # Index for conversation queries (most frequent)
        await messages_collection.create_index(
            [("conversation_id", 1), ("timestamps.created_at", -1)],
            name="idx_conversation_chronological"
        )
        logger.info("Created index for conversation queries")
        
        # Index for user queries
        await messages_collection.create_index(
            [("user_id", 1), ("timestamps.created_at", -1)],
            name="idx_user_chronological"
        )
        logger.info("Created index for user queries")
        
        # Index for temporal pagination
        await messages_collection.create_index(
            [("timestamps.created_at", -1), ("_id", 1)],
            name="idx_temporal_pagination"
        )
        logger.info("Created index for temporal pagination")
        
        # Compound index for conversation filtering
        await messages_collection.create_index(
            [
                ("conversation_id", 1),
                ("role", 1),
                ("message_type", 1),
                ("status", 1)
            ],
            name="idx_conversation_filtering"
        )
        logger.info("Created index for conversation filtering")
        
        # Text search index
        await messages_collection.create_index(
            [("content.text", "text"), ("custom_metadata.topics", "text")],
            name="idx_text_search",
            weights={
                "content.text": 10,
                "custom_metadata.topics": 5
            }
        )
        logger.info("Created text search index")
        
        # Index for analytics queries
        await messages_collection.create_index(
            [
                ("user_id", 1),
                ("llm_metadata.provider", 1),
                ("llm_metadata.model", 1),
                ("timestamps.created_at", -1)
            ],
            name="idx_analytics_queries",
            sparse=True
        )
        logger.info("Created index for analytics queries")
        
        # Index for safety audit
        await messages_collection.create_index(
            [
                ("safety_metadata.content_filtered", 1),
                ("timestamps.created_at", -1)
            ],
            name="idx_safety_audit"
        )
        logger.info("Created index for safety audit")
        
        # Single field indexes
        await messages_collection.create_index([("conversation_id", 1)], name="idx_conversation_id")
        await messages_collection.create_index([("user_id", 1)], name="idx_user_id")
        await messages_collection.create_index([("status", 1)], name="idx_status")
        await messages_collection.create_index([("role", 1)], name="idx_role")
        
        logger.info("Created single field indexes")
        
        # List all indexes for verification
        indexes = await messages_collection.list_indexes().to_list(length=None)
        logger.info("Current indexes in messages collection:")
        for idx in indexes:
            logger.info(f"  - {idx['name']}: {idx.get('key', {})}")
        
    except Exception as e:
        logger.error("Failed to create indexes", error=str(e))
        raise
    finally:
        client.close()


async def main():
    """Main function to set up all indexes."""
    logger.info("Starting MongoDB index setup")
    
    try:
        await create_message_indexes()
        logger.info("MongoDB index setup completed successfully")
    except Exception as e:
        logger.error("Index setup failed", error=str(e))
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.path.append("/Users/maxward/Developer/LLMS/Projects/micro_services_be/message-service")
    exit_code = asyncio.run(main())
    sys.exit(exit_code)