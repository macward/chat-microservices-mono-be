"""Configuration management for the Message Service."""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service Configuration
    service_name: str = Field(default="message-service", env="SERVICE_NAME")
    port: int = Field(default=8009, env="PORT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    
    # Database Configuration
    mongodb_url: str = Field(env="MONGODB_URL")
    mongodb_database: str = Field(env="MONGODB_DATABASE")
    mongodb_connection_pool_min: int = Field(default=5, env="MONGODB_CONNECTION_POOL_MIN")
    mongodb_connection_pool_max: int = Field(default=20, env="MONGODB_CONNECTION_POOL_MAX")
    
    # Redis Configuration
    redis_url: str = Field(env="REDIS_URL")
    redis_connection_pool_max: int = Field(default=20, env="REDIS_CONNECTION_POOL_MAX")
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")
    
    # External Services
    auth_service_url: str = Field(env="AUTH_SERVICE_URL")
    conversation_service_url: str = Field(env="CONVERSATION_SERVICE_URL")
    characters_service_url: str = Field(env="CHARACTERS_SERVICE_URL")
    llm_service_url: str = Field(env="LLM_SERVICE_URL")
    
    # LLM Configuration
    default_llm_provider: str = Field(default="lmstudio", env="DEFAULT_LLM_PROVIDER")
    default_model: str = Field(default="google/gemma-3-12b", env="DEFAULT_MODEL")
    max_tokens_per_request: int = Field(default=2048, env="MAX_TOKENS_PER_REQUEST")
    default_temperature: float = Field(default=0.7, env="DEFAULT_TEMPERATURE")
    request_timeout_seconds: int = Field(default=30, env="REQUEST_TIMEOUT_SECONDS")
    
    # Rate Limiting
    max_messages_per_minute: int = Field(default=100, env="MAX_MESSAGES_PER_MINUTE")
    max_messages_per_hour: int = Field(default=1000, env="MAX_MESSAGES_PER_HOUR")
    max_messages_per_day: int = Field(default=10000, env="MAX_MESSAGES_PER_DAY")
    
    # Content Safety
    enable_content_filtering: bool = Field(default=True, env="ENABLE_CONTENT_FILTERING")
    safety_threshold: float = Field(default=0.8, env="SAFETY_THRESHOLD")
    max_message_length: int = Field(default=50000, env="MAX_MESSAGE_LENGTH")
    
    # Performance
    max_concurrent_llm_requests: int = Field(default=10, env="MAX_CONCURRENT_LLM_REQUESTS")
    message_processing_timeout: int = Field(default=60, env="MESSAGE_PROCESSING_TIMEOUT")
    batch_size_for_analytics: int = Field(default=100, env="BATCH_SIZE_FOR_ANALYTICS")
    
    # Workers
    worker_count: int = Field(default=2, env="WORKER_COUNT")
    worker_queue_size: int = Field(default=100, env="WORKER_QUEUE_SIZE")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()