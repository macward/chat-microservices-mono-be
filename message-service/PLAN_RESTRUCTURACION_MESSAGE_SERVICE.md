# Plan de Restructuración del Message Service

## Problemas Identificados

### 1. Arquitectura Actual
- **Mezcla de responsabilidades**: API, lógica de negocio y acceso a datos están muy acoplados
- **Falta de interfaces**: Sin abstracciones claras entre capas
- **Configuración dispersa**: Settings mezclados con lógica de aplicación
- **Manejo de errores inconsistente**: Sin estrategia centralizada
- **Estructura de testing deficiente**: No hay separación clara para tests

### 2. Problemas Específicos
- `MessageService` tiene demasiadas responsabilidades
- Repositorio directamente acoplado a MongoDB/Beanie
- Configuración hardcodeada en múltiples lugares
- Sin dependency injection
- Tests unitarios difíciles de implementar

## Restructuración Propuesta

### 1. Nueva Estructura de Directorios

```
message-service/
├── app/
│   ├── domain/                      # Lógica de negocio pura
│   │   ├── entities/                # Modelos de dominio
│   │   │   ├── __init__.py
│   │   │   ├── message.py
│   │   │   └── conversation.py
│   │   ├── services/                # Servicios de dominio
│   │   │   ├── __init__.py
│   │   │   ├── message_service.py
│   │   │   └── llm_service.py
│   │   ├── repositories/            # Interfaces de repositorio
│   │   │   ├── __init__.py
│   │   │   ├── message_repository.py
│   │   │   └── llm_repository.py
│   │   └── exceptions/              # Excepciones del dominio
│   │       ├── __init__.py
│   │       ├── message_exceptions.py
│   │       └── llm_exceptions.py
│   ├── infrastructure/              # Implementaciones técnicas
│   │   ├── database/                # MongoDB, Beanie
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   └── models/
│   │   │       └── message_model.py
│   │   ├── external/                # LLM service, auth service
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py
│   │   │   └── auth_client.py
│   │   └── repositories/            # Implementaciones de repositorio
│   │       ├── __init__.py
│   │       ├── mongo_message_repository.py
│   │       └── http_llm_repository.py
│   ├── application/                 # Casos de uso
│   │   ├── commands/                # Comandos (crear mensaje)
│   │   │   ├── __init__.py
│   │   │   ├── create_message.py
│   │   │   └── process_llm_message.py
│   │   ├── queries/                 # Consultas (obtener mensajes)
│   │   │   ├── __init__.py
│   │   │   ├── get_conversation_messages.py
│   │   │   └── get_llm_health.py
│   │   └── handlers/                # Manejadores de casos de uso
│   │       ├── __init__.py
│   │       ├── message_handlers.py
│   │       └── llm_handlers.py
│   ├── presentation/                # API Layer
│   │   ├── api/                     # Endpoints FastAPI
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   └── llm.py
│   │   │   └── health.py
│   │   ├── dto/                     # Request/Response models
│   │   │   ├── __init__.py
│   │   │   ├── request_models.py
│   │   │   └── response_models.py
│   │   └── middlewares/             # Middlewares específicos
│   │       ├── __init__.py
│   │       ├── error_handler.py
│   │       └── rate_limiter.py
│   ├── core/                        # Configuración y utilidades
│   │   ├── config/                  # Settings centralizados
│   │   │   ├── __init__.py
│   │   │   ├── settings.py
│   │   │   └── database.py
│   │   ├── exceptions/              # Excepciones base
│   │   │   ├── __init__.py
│   │   │   └── base_exceptions.py
│   │   └── dependencies/            # Dependency injection
│   │       ├── __init__.py
│   │       └── container.py
│   └── main.py                      # Application entry point
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   ├── application/
│   │   └── infrastructure/
│   ├── integration/
│   │   ├── database/
│   │   └── external/
│   ├── e2e/
│   │   └── api/
│   └── fixtures/
├── scripts/
│   ├── setup_database.py
│   └── migrate.py
└── docs/
    ├── architecture.md
    └── api.md
```

### 2. Implementación de Clean Architecture

#### Domain Layer (Lógica de Negocio)
```python
# domain/entities/message.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Message:
    id: Optional[str]
    conversation_id: str
    user_id: str
    content: str
    role: str
    created_at: datetime
    llm_metadata: Optional[Dict[str, Any]] = None
    custom_metadata: Optional[Dict[str, Any]] = None

# domain/repositories/message_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.message import Message

class MessageRepository(ABC):
    @abstractmethod
    async def create(self, message: Message) -> Message:
        pass
    
    @abstractmethod
    async def find_by_conversation_id(self, conversation_id: str, limit: int = 50) -> List[Message]:
        pass
```

#### Application Layer (Casos de Uso)
```python
# application/commands/create_message.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class CreateMessageCommand:
    conversation_id: str
    user_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

# application/handlers/message_handlers.py
from domain.repositories.message_repository import MessageRepository
from domain.entities.message import Message
from application.commands.create_message import CreateMessageCommand

class MessageHandler:
    def __init__(self, message_repo: MessageRepository):
        self.message_repo = message_repo
    
    async def handle_create_message(self, command: CreateMessageCommand) -> Message:
        message = Message(
            id=None,
            conversation_id=command.conversation_id,
            user_id=command.user_id,
            content=command.content,
            role="user",
            created_at=datetime.utcnow(),
            custom_metadata=command.metadata
        )
        return await self.message_repo.create(message)
```

#### Infrastructure Layer (Implementaciones)
```python
# infrastructure/repositories/mongo_message_repository.py
from domain.repositories.message_repository import MessageRepository
from domain.entities.message import Message
from infrastructure.database.models.message_model import MessageModel

class MongoMessageRepository(MessageRepository):
    async def create(self, message: Message) -> Message:
        model = MessageModel.from_entity(message)
        await model.insert()
        return model.to_entity()
    
    async def find_by_conversation_id(self, conversation_id: str, limit: int = 50) -> List[Message]:
        models = await MessageModel.find(
            MessageModel.conversation_id == conversation_id
        ).limit(limit).to_list()
        return [model.to_entity() for model in models]
```

#### Presentation Layer (API)
```python
# presentation/api/v1/llm.py
from fastapi import APIRouter, Depends
from presentation.dto.request_models import LLMProcessRequest
from presentation.dto.response_models import LLMProcessResponse
from core.dependencies.container import get_message_handler

router = APIRouter(prefix="/llm")

@router.post("/process", response_model=LLMProcessResponse)
async def process_message(
    request: LLMProcessRequest,
    handler = Depends(get_message_handler)
):
    command = CreateMessageCommand(
        conversation_id=request.conversation_id,
        user_id=request.user_id,
        content=request.content
    )
    result = await handler.handle_process_llm_message(command)
    return LLMProcessResponse.from_domain(result)
```

### 3. Dependency Injection Container

```python
# core/dependencies/container.py
from dependency_injector import containers, providers
from infrastructure.repositories.mongo_message_repository import MongoMessageRepository
from application.handlers.message_handlers import MessageHandler

class Container(containers.DeclarativeContainer):
    # Repositories
    message_repository = providers.Singleton(MongoMessageRepository)
    
    # Handlers
    message_handler = providers.Factory(
        MessageHandler,
        message_repo=message_repository
    )

# main.py
from core.dependencies.container import Container

container = Container()

def get_message_handler():
    return container.message_handler()
```

### 4. Configuration Management

```python
# core/config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "message_service"
    
    # LLM Service
    LLM_SERVICE_URL: str = "http://localhost:8023"
    DEFAULT_MODEL: str = "google/gemma-3-12b"
    
    # Auth Service
    AUTH_SERVICE_URL: str = "http://localhost:8001"
    
    # Rate Limiting
    MAX_MESSAGES_PER_MINUTE: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

### 5. Error Handling Centralizado

```python
# core/exceptions/base_exceptions.py
class DomainException(Exception):
    def __init__(self, message: str, code: str = "domain_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)

# presentation/middlewares/error_handler.py
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message
            }
        }
    )
```

## Beneficios de la Restructuración

### 1. Mantenibilidad
- **Separación clara de responsabilidades**
- **Código más fácil de entender y modificar**
- **Cambios aislados en capas específicas**

### 2. Testabilidad
- **Tests unitarios reales para domain logic**
- **Mocking fácil de dependencias**
- **Integration tests aislados**

### 3. Escalabilidad
- **Arquitectura preparada para microservicios**
- **Fácil agregar nuevas features**
- **Soporte para múltiples bases de datos**

### 4. Reutilización
- **Componentes independientes**
- **Lógica de negocio reutilizable**
- **Infraestructura intercambiable**

### 5. Debugging
- **Errores fáciles de rastrear**
- **Logging estructurado por capa**
- **Responsabilidades claras**

## Estrategia de Migración

### Fase 1: Preparación (1-2 días)
1. Crear nueva estructura de directorios
2. Configurar dependency injection container
3. Implementar configuration management

### Fase 2: Domain Layer (2-3 días)
1. Migrar entidades de dominio
2. Crear interfaces de repositorio
3. Implementar servicios de dominio

### Fase 3: Application Layer (2-3 días)
1. Crear commands y queries
2. Implementar handlers
3. Migrar lógica de casos de uso

### Fase 4: Infrastructure Layer (3-4 días)
1. Implementar repositorios concretos
2. Migrar clientes externos
3. Actualizar modelos de base de datos

### Fase 5: Presentation Layer (2-3 días)
1. Migrar endpoints API
2. Actualizar DTOs
3. Implementar middlewares

### Fase 6: Testing y Validación (3-4 días)
1. Crear tests unitarios
2. Implementar integration tests
3. Validar funcionalidad completa

## Consideraciones de Implementación

### 1. Backward Compatibility
- Mantener APIs existentes durante transición
- Usar feature flags para rollout gradual

### 2. Data Migration
- Planificar migración de datos si es necesaria
- Crear scripts de migración

### 3. Monitoring
- Implementar logging estructurado
- Agregar métricas de performance

### 4. Documentation
- Documentar nueva arquitectura
- Crear guías de desarrollo

## Conclusión

Esta restructuración transformará el message-service en un microservicio robusto, mantenible y escalable que sigue las mejores prácticas de Clean Architecture y Domain-Driven Design.

**Tiempo estimado total**: 15-20 días de desarrollo
**Riesgo**: Medio (con testing apropiado)
**ROI**: Alto (mejora significativa en mantenibilidad y escalabilidad)