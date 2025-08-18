import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.services.llm_service import llm_service
from app.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client

@pytest.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_llm_client():
    """Mock the LM Studio client."""
    mock_client = MagicMock()
    mock_client.generate_with_messages = MagicMock(return_value={
        "choices": [
            {
                "message": {
                    "content": "Esta es una respuesta de prueba del LLM"
                }
            }
        ],
        "usage": {
            "total_tokens": 25
        }
    })
    return mock_client

@pytest.fixture
async def mock_llm_service(mock_llm_client):
    """Mock the LLM service with a mocked client."""
    original_client = llm_service.client
    original_initialized = llm_service._initialized
    
    # Mock the service
    llm_service.client = mock_llm_client
    llm_service._initialized = True
    
    yield llm_service
    
    # Restore original state
    llm_service.client = original_client
    llm_service._initialized = original_initialized

@pytest.fixture
def sample_llm_request():
    """Sample LLM request for testing."""
    return {
        "model": "test-model",
        "messages": [
            {"role": "user", "content": "Hola, ¿cómo estás?"}
        ],
        "temperature": 0.7,
        "max_tokens": 100,
        "top_p": 0.9,
        "stream": False
    }

@pytest.fixture
def sample_conversation_request():
    """Sample conversation request with multiple messages."""
    return {
        "model": "test-model",
        "messages": [
            {"role": "system", "content": "Eres un asistente útil"},
            {"role": "user", "content": "¿Cuál es la capital de España?"},
            {"role": "assistant", "content": "La capital de España es Madrid"},
            {"role": "user", "content": "¿Y la población?"}
        ],
        "temperature": 0.5,
        "max_tokens": 150
    }