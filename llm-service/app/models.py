from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000, description="Message content")

    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty or whitespace only')
        return v.strip()

class LLMRequest(BaseModel):
    model: str = Field(..., description="El ID del modelo LLM a usar")
    messages: List[Message] = Field(..., min_items=1, description="Lista de mensajes de la conversación")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Temperatura de muestreo (0.0-2.0)")
    max_tokens: Optional[int] = Field(1000, ge=1, le=4000, description="Número máximo de tokens a generar")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probabilidad acumulada para muestreo (0.0-1.0)")
    stream: Optional[bool] = Field(False, description="Si transmitir la respuesta como eventos")

    @validator('messages')
    def validate_messages(cls, v):
        if not v:
            raise ValueError('At least one message is required')
        return v

class LLMResponse(BaseModel):
    response: str = Field(..., description="Respuesta generada por el LLM")
    model: Optional[str] = Field(None, description="Modelo utilizado")
    tokens_used: Optional[int] = Field(None, description="Tokens utilizados en la respuesta")
    processing_time: Optional[float] = Field(None, description="Tiempo de procesamiento en segundos")
    correlation_id: Optional[str] = Field(None, description="ID de correlación de la petición")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Mensaje de error")
    error_code: str = Field(..., description="Código de error para manejo por el cliente")
    detail: Optional[str] = Field(None, description="Información detallada del error")
    correlation_id: Optional[str] = Field(None, description="ID de correlación de la petición")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Estado del servicio")
    timestamp: float = Field(..., description="Timestamp del check")
    version: str = Field(..., description="Versión de la aplicación")
    llm_service: str = Field(..., description="Estado del servicio LLM")
    uptime: Optional[float] = Field(None, description="Tiempo activo en segundos")