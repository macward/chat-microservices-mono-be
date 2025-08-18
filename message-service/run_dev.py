#!/usr/bin/env python3
"""Development runner script for the Message Service."""

import os
import sys
import asyncio
import uvicorn

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def setup_development_environment():
    """Set up development environment (databases, indexes, etc.)."""
    logger.info("Setting up development environment...")
    
    try:
        # Import here to avoid circular imports
        from scripts.setup_indexes import create_message_indexes
        
        # Setup MongoDB indexes
        await create_message_indexes()
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error("Failed to setup development environment", error=str(e))
        return False
    
    return True


def main():
    """Main function to run the development server."""
    logger.info("Starting Message Service in development mode")
    
    # Check if .env file exists
    env_file = os.path.join(project_root, ".env")
    if not os.path.exists(env_file):
        logger.warning(".env file not found, copying from .env.example")
        example_file = os.path.join(project_root, ".env.example")
        if os.path.exists(example_file):
            import shutil
            shutil.copy2(example_file, env_file)
            logger.info("Created .env file from .env.example")
        else:
            logger.error("No .env.example file found!")
            return 1
    
    # Setup development environment
    try:
        setup_success = asyncio.run(setup_development_environment())
        if not setup_success:
            logger.error("Development environment setup failed")
            return 1
    except Exception as e:
        logger.warning("Could not setup development environment (this is OK if DBs are not running)", error=str(e))
    
    # Run the development server
    logger.info(f"Starting server on port {settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=True,
        log_level=settings.log_level.lower(),
        access_log=True,
        use_colors=True
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())