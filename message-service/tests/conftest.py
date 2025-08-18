"""Pytest configuration and fixtures."""

import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture
async def test_db():
    """Create a test database connection."""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[f"{settings.mongodb_database}_test"]
    
    yield db
    
    # Cleanup
    await client.drop_database(f"{settings.mongodb_database}_test")
    client.close()


@pytest.fixture
def sample_message_data():
    """Sample message data for testing."""
    return {
        "conversation_id": "conv_test_123",
        "content": "This is a test message",
        "metadata": {
            "test": True,
            "platform": "test"
        }
    }