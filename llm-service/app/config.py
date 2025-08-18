from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # Configuración del Servidor
    app_name: str = Field("LLM Service", description="Nombre de la aplicación")
    app_version: str = Field("1.0.0", description="Versión de la aplicación")
    debug: bool = Field(False, description="Modo debug")
    host: str = Field("0.0.0.0", description="Host del servidor")
    port: int = Field(8000, description="Puerto del servidor")
    
    # Configuración de LM Studio
    lm_studio_host: str = Field("localhost", description="Host de LM Studio")
    lm_studio_port: int = Field(1234, description="Puerto de LM Studio")
    lm_studio_timeout: int = Field(30, description="Timeout de peticiones a LM Studio en segundos")
    lm_studio_max_retries: int = Field(3, description="Número máximo de reintentos")
    
    # Configuración de la API
    max_request_size: int = Field(10000, description="Tamaño máximo de petición en caracteres")
    rate_limit_requests: int = Field(100, description="Peticiones por minuto por cliente")
    
    # Configuración de Logging
    log_level: str = Field("INFO", description="Nivel de logging")
    log_format: str = Field("json", description="Formato de logging (json o text)")
    
    # Configuración de Seguridad
    allowed_origins: list = Field(["*"], description="Orígenes permitidos para CORS")
    trusted_hosts: list = Field(["*"], description="Hosts de confianza")
    
    # Modelo por defecto (usar el nombre exacto de LM Studio)
    default_model: str = Field(
        "dirty-muse-writer-v01-uncensored-erotica-nsfw",
        description="Modelo LLM por defecto"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "LLM_SERVICE_"

# Instancia global de configuración
settings = Settings()