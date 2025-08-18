from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Service Configuration
    service_name: str = "conversation-service"
    host: str = "0.0.0.0"
    port: int = 8003
    environment: str = "development"
    
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "conversation_service"
    
    # External Services
    auth_service_port: int = 8001
    characters_service_port: int = 8002

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()