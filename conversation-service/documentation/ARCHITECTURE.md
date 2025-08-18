# Conversation Service - Architecture

Documentación completa de la arquitectura del Conversation Service en el ecosistema de microservicios.

## 📋 Visión General

El Conversation Service es un microservicio independiente responsable de la gestión completa del ciclo de vida de conversaciones en el sistema Character Chat API. Opera como parte de una arquitectura de microservicios distribuida, comunicándose con otros servicios mediante APIs REST.

## 🏗️ Arquitectura del Sistema

### Contexto en el Ecosistema

```
┌─────────────────────────────────────────────────────────────┐
│                     API Gateway                             │
│              (Nginx/Kong/AWS ALB)                          │
└─────────────┬───────────────┬───────────────┬──────────────┘
              │               │               │
    ┌─────────▼─────────┐   ┌─▼─────────┐   ┌─▼────────────┐
    │  Auth Service     │   │Characters │   │LLM Service   │
    │    Port: 8001     │   │ Service   │   │ Port: 8005   │
    │                   │   │Port: 8002 │   │              │
    └─────────┬─────────┘   └─┬─────────┘   └─┬────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Conversation      │
                    │   Service         │
                    │  Port: 8003       │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Message Service   │
                    │  Port: 8004       │
                    └─────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │ Storage Service   │
                    │  Port: 8006       │
                    └───────────────────┘
```

## 🔧 Arquitectura Interna

### Patrón de Capas (3-Layer Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ FastAPI     │  │ Middleware  │  │ Dependencies│         │
│  │ Routers     │  │ (Auth, CORS)│  │ (Injection) │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Service Layer                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Conversation │  │ External    │  │ Validation  │         │
│  │ Service     │  │ Services    │  │ Service     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                Repository Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Conversation │  │ MongoDB     │  │ Connection  │         │
│  │ Repository  │  │ Client      │  │ Pool        │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### Estructura de Directorios

```
conversation-service/
├── app/
│   ├── __init__.py
│   ├── main.py                         # FastAPI application entry point
│   ├── config.py                       # Configuration management
│   ├── database.py                     # MongoDB connection setup
│   │
│   ├── api/                           # API Layer
│   │   ├── __init__.py
│   │   ├── dependencies.py            # FastAPI dependencies
│   │   ├── middleware.py              # Custom middleware
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── conversations.py       # Conversation endpoints
│   │
│   ├── services/                      # Service Layer
│   │   ├── __init__.py
│   │   ├── conversation_service.py    # Core business logic
│   │   ├── external_services.py       # External service clients
│   │   ├── validation_service.py      # Input validation
│   │   └── circuit_breaker.py         # Circuit breaker implementation
│   │
│   ├── repositories/                  # Repository Layer
│   │   ├── __init__.py
│   │   ├── conversation_repository.py # Data access layer
│   │   ├── base_repository.py         # Abstract repository
│   │   └── mongodb_client.py          # MongoDB client wrapper
│   │
│   ├── models/                        # Data Models
│   │   ├── __init__.py
│   │   ├── conversation.py            # Conversation Pydantic models
│   │   ├── requests.py                # API request models
│   │   ├── responses.py               # API response models
│   │   └── database.py                # Beanie MongoDB models
│   │
│   ├── core/                          # Core Utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py              # Custom exceptions
│   │   ├── security.py                # Security utilities
│   │   ├── logging.py                 # Logging configuration
│   │   └── metrics.py                 # Metrics collection
│   │
│   └── utils/                         # General Utilities
│       ├── __init__.py
│       ├── datetime_utils.py          # Date/time helpers
│       ├── pagination.py              # Pagination utilities
│       └── validators.py              # Custom validators
│
├── tests/                             # Test Suite
│   ├── __init__.py
│   ├── conftest.py                    # Pytest configuration
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   └── e2e/                          # End-to-end tests
│
├── scripts/                           # Utility Scripts
│   ├── migrate_data.py                # Data migration
│   ├── setup_indexes.py               # Database index setup
│   └── health_check.py                # Health check script
│
├── requirements.txt                   # Python dependencies
├── requirements-dev.txt               # Development dependencies
├── Dockerfile                         # Container definition
├── docker-compose.yml                 # Local development setup
├── .env.example                       # Environment template
└── pyproject.toml                     # Python project configuration
```

## 🔄 Patrones de Diseño

### 1. Repository Pattern

**Propósito**: Abstraer el acceso a datos y proporcionar una interfaz común para operaciones CRUD.

```python
# app/repositories/base_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any
from beanie import Document

class BaseRepository(ABC):
    def __init__(self, model: Document):
        self.model = model
    
    @abstractmethod
    async def create(self, data: dict) -> Document:
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Document]:
        pass
    
    @abstractmethod
    async def update(self, id: str, data: dict) -> Optional[Document]:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass

# app/repositories/conversation_repository.py
class ConversationRepository(BaseRepository):
    async def get_by_user_id(self, user_id: str, filters: dict) -> List[Conversation]:
        # Implementation specific to conversations
        pass
```

### 2. Service Layer Pattern

**Propósito**: Encapsular la lógica de negocio y orquestar operaciones entre repositorios y servicios externos.

```python
# app/services/conversation_service.py
class ConversationService:
    def __init__(
        self,
        conversation_repo: ConversationRepository,
        auth_service: AuthService,
        character_service: CharacterService
    ):
        self.conversation_repo = conversation_repo
        self.auth_service = auth_service
        self.character_service = character_service
    
    async def create_conversation(self, user_id: str, data: ConversationCreate) -> Conversation:
        # 1. Validate character exists
        await self.character_service.validate_character(data.character_id)
        
        # 2. Create conversation
        conversation_data = {
            "user_id": user_id,
            **data.dict()
        }
        
        # 3. Save to database
        return await self.conversation_repo.create(conversation_data)
```

### 3. Dependency Injection

**Propósito**: Inyectar dependencias para facilitar testing y desacoplamiento.

```python
# app/api/dependencies.py
from fastapi import Depends
from app.repositories.conversation_repository import ConversationRepository
from app.services.conversation_service import ConversationService

def get_conversation_repository() -> ConversationRepository:
    return ConversationRepository()

def get_conversation_service(
    repo: ConversationRepository = Depends(get_conversation_repository)
) -> ConversationService:
    return ConversationService(repo)
```

### 4. Circuit Breaker Pattern

**Propósito**: Prevenir cascading failures cuando servicios externos fallan.

```python
# app/services/circuit_breaker.py
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenException()
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
```

### 5. Strategy Pattern

**Propósito**: Permitir diferentes estrategias de paginación y filtrado.

```python
# app/utils/pagination.py
from abc import ABC, abstractmethod

class PaginationStrategy(ABC):
    @abstractmethod
    async def paginate(self, query, cursor: str, limit: int):
        pass

class CursorPaginationStrategy(PaginationStrategy):
    async def paginate(self, query, cursor: str, limit: int):
        # Cursor-based pagination implementation
        pass

class OffsetPaginationStrategy(PaginationStrategy):
    async def paginate(self, query, cursor: str, limit: int):
        # Offset-based pagination implementation  
        pass
```

## 🔌 Comunicación entre Servicios

### 1. HTTP REST API

**Outbound Calls** (Conversation Service → Otros Servicios):

```python
# app/services/external_services.py
import httpx
from app.core.circuit_breaker import CircuitBreaker

class AuthService:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)
        self.circuit_breaker = CircuitBreaker()
    
    async def validate_token(self, token: str) -> dict:
        return await self.circuit_breaker.call(
            self._validate_token_request, token
        )
    
    async def _validate_token_request(self, token: str) -> dict:
        response = await self.client.post(
            f"{self.base_url}/validate-token",
            json={"token": token}
        )
        response.raise_for_status()
        return response.json()

class CharacterService:
    async def get_character(self, character_id: str) -> dict:
        # Similar implementation for character validation
        pass
```

### 2. Event-Driven Communication (Futuro)

**Preparación para Eventos Asíncronos**:

```python
# app/events/event_publisher.py
class EventPublisher:
    def __init__(self, broker_url: str):
        self.broker_url = broker_url
    
    async def publish_conversation_created(self, conversation: dict):
        event = {
            "event_type": "conversation.created",
            "data": conversation,
            "timestamp": datetime.utcnow().isoformat(),
            "service": "conversation-service"
        }
        # Publish to Redis/RabbitMQ/Kafka
        pass
    
    async def publish_conversation_archived(self, conversation_id: str):
        # Similar event publishing
        pass
```

## 🔒 Seguridad

### 1. Autenticación JWT

```python
# app/core/security.py
from jose import JWTError, jwt
from datetime import datetime, timedelta

class JWTHandler:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def decode_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            raise InvalidTokenException()
    
    def extract_user_id(self, token: str) -> str:
        payload = self.decode_token(token)
        return payload.get("user_id")
```

### 2. Autorización de Recursos

```python
# app/services/authorization_service.py
class AuthorizationService:
    async def verify_conversation_access(
        self, 
        user_id: str, 
        conversation_id: str
    ) -> bool:
        conversation = await self.conversation_repo.get_by_id(conversation_id)
        if not conversation:
            raise ConversationNotFoundException()
        
        if conversation.user_id != user_id:
            raise ConversationAccessDeniedException()
        
        return True
```

### 3. Validación de Entrada

```python
# app/core/validators.py
from pydantic import validator
import re

class ConversationCreateRequest(BaseModel):
    character_id: str
    title: Optional[str] = None
    settings: Optional[ConversationSettings] = None
    tags: Optional[List[str]] = []
    
    @validator('title')
    def validate_title(cls, v):
        if v and len(v) > 200:
            raise ValueError('Title too long')
        if v and not re.match(r'^[a-zA-Z0-9\s\-_.,!?]+$', v):
            raise ValueError('Title contains invalid characters')
        return v
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Too many tags')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag too long')
        return v
```

## 📊 Monitoreo y Observabilidad

### 1. Logging Estructurado

```python
# app/core/logging.py
import structlog
import logging.config

def configure_logging():
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

logger = structlog.get_logger()

# Usage in services
async def create_conversation(self, data):
    logger.info(
        "Creating conversation",
        user_id=data.user_id,
        character_id=data.character_id
    )
```

### 2. Métricas

```python
# app/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Métricas de aplicación
conversation_created_counter = Counter(
    'conversations_created_total',
    'Total conversations created'
)

conversation_response_time = Histogram(
    'conversation_request_duration_seconds',
    'Time spent processing conversation requests',
    ['method', 'endpoint']
)

active_conversations_gauge = Gauge(
    'active_conversations_total',
    'Total active conversations'
)
```

### 3. Health Checks

```python
# app/api/v1/health.py
from fastapi import APIRouter
from app.core.health import HealthChecker

router = APIRouter()

@router.get("/health")
async def health_check():
    health_checker = HealthChecker()
    
    health_status = {
        "status": "healthy",
        "service": "conversation-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "dependencies": {
            "mongodb": await health_checker.check_mongodb(),
            "auth_service": await health_checker.check_auth_service(),
            "characters_service": await health_checker.check_characters_service()
        }
    }
    
    # Determine overall status
    all_healthy = all(
        dep["status"] == "healthy" 
        for dep in health_status["dependencies"].values()
    )
    
    if not all_healthy:
        health_status["status"] = "degraded"
    
    return health_status
```

## 🔄 Patrones de Resilencia

### 1. Retry Pattern

```python
# app/core/retry.py
import asyncio
from typing import Callable, Any
import random

async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
) -> Any:
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            delay = min(base_delay * (exponential_base ** attempt), max_delay)
            if jitter:
                delay *= (0.5 + random.random() * 0.5)
            
            await asyncio.sleep(delay)
```

### 2. Timeout Pattern

```python
# app/core/timeout.py
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def timeout(seconds: float):
    try:
        async with asyncio.timeout(seconds):
            yield
    except asyncio.TimeoutError:
        raise ServiceTimeoutException(f"Operation timed out after {seconds} seconds")
```

### 3. Bulkhead Pattern

```python
# app/core/connection_pool.py
import asyncio
from typing import Dict

class ConnectionPool:
    def __init__(self):
        self.pools: Dict[str, asyncio.Semaphore] = {
            "database": asyncio.Semaphore(20),      # Database connections
            "auth_service": asyncio.Semaphore(10),   # Auth service calls
            "character_service": asyncio.Semaphore(5) # Character service calls
        }
    
    async def acquire(self, pool_name: str):
        return await self.pools[pool_name].acquire()
    
    def release(self, pool_name: str):
        self.pools[pool_name].release()
```

## 🧪 Testing Strategy

### 1. Arquitectura de Testing

```
tests/
├── unit/                              # Unit tests
│   ├── test_services/
│   ├── test_repositories/
│   └── test_models/
├── integration/                       # Integration tests
│   ├── test_api_endpoints/
│   └── test_database_operations/
└── e2e/                              # End-to-end tests
    └── test_full_workflows/
```

### 2. Test Doubles

```python
# tests/mocks/external_services.py
class MockAuthService:
    async def validate_token(self, token: str) -> dict:
        if token == "valid_token":
            return {"user_id": "test_user_123"}
        raise InvalidTokenException()

class MockCharacterService:
    async def get_character(self, character_id: str) -> dict:
        if character_id == "valid_character":
            return {"id": character_id, "name": "Test Character"}
        raise CharacterNotFoundException()
```

## 🚀 Deployment Architecture

### 1. Container Strategy

```dockerfile
# Multi-stage build for optimization
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
EXPOSE 8003
CMD ["python", "-m", "app.main"]
```

### 2. Configuration Management

```python
# app/config.py
from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Service Configuration
    service_name: str = "conversation-service"
    port: int = 8003
    log_level: str = "INFO"
    environment: str = "development"
    
    # Database
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "conversation_service"
    
    # External Services
    auth_service_url: str = "http://auth-service:8001"
    characters_service_url: str = "http://characters-service:8002"
    message_service_url: str = "http://message-service:8004"
    
    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    
    # Performance
    connection_pool_min: int = 5
    connection_pool_max: int = 20
    request_timeout: float = 30.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 3. Service Mesh Ready

```python
# app/middleware/service_mesh.py
class ServiceMeshMiddleware:
    async def __call__(self, request: Request, call_next):
        # Add distributed tracing headers
        trace_id = request.headers.get("x-trace-id", str(uuid4()))
        request.state.trace_id = trace_id
        
        # Add service mesh headers
        response = await call_next(request)
        response.headers["x-service-name"] = "conversation-service"
        response.headers["x-service-version"] = "1.0.0"
        response.headers["x-trace-id"] = trace_id
        
        return response
```

## 📈 Performance Optimization

### 1. Database Query Optimization

```python
# app/repositories/optimized_queries.py
class OptimizedConversationRepository:
    async def get_user_conversations_paginated(
        self, 
        user_id: str, 
        filters: dict,
        limit: int = 20
    ):
        # Use compound index for optimal performance
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "status": filters.get("status", "active")
            }},
            {"$sort": {"metadata.last_activity": -1}},
            {"$limit": limit},
            {"$project": {
                "title": 1,
                "character_id": 1, 
                "metadata.last_activity": 1,
                "metadata.message_count": 1,
                "tags": 1
            }}
        ]
        
        return await self.model.aggregate(pipeline).to_list()
```

### 2. Caching Strategy

```python
# app/core/cache.py
import redis.asyncio as redis
import json
from typing import Optional, Any

class CacheService:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def get_character_cache(self, character_id: str) -> Optional[dict]:
        cached = await self.redis.get(f"character:{character_id}")
        if cached:
            return json.loads(cached)
        return None
    
    async def set_character_cache(self, character_id: str, data: dict, ttl: int = 300):
        await self.redis.setex(
            f"character:{character_id}",
            ttl,
            json.dumps(data)
        )
```

## 🔮 Extensibilidad

### 1. Plugin Architecture

```python
# app/core/plugins.py
from abc import ABC, abstractmethod

class ConversationPlugin(ABC):
    @abstractmethod
    async def before_create(self, data: dict) -> dict:
        pass
    
    @abstractmethod  
    async def after_create(self, conversation: dict) -> None:
        pass

class AnalyticsPlugin(ConversationPlugin):
    async def before_create(self, data: dict) -> dict:
        # Add analytics metadata
        data["metadata"]["analytics_id"] = str(uuid4())
        return data
    
    async def after_create(self, conversation: dict) -> None:
        # Send analytics event
        await self.analytics_service.track_conversation_created(conversation)
```

### 2. Feature Flags

```python
# app/core/feature_flags.py
class FeatureFlags:
    def __init__(self):
        self.flags = {
            "enable_conversation_analytics": False,
            "enable_conversation_templates": True,
            "enable_bulk_operations": False
        }
    
    def is_enabled(self, flag_name: str) -> bool:
        return self.flags.get(flag_name, False)

# Usage in services
if feature_flags.is_enabled("enable_conversation_analytics"):
    await self.analytics_plugin.after_create(conversation)
```

Esta arquitectura proporciona una base sólida, escalable y mantenible para el Conversation Service, con clara separación de responsabilidades, patrones de resiliencia, y preparación para el crecimiento futuro del sistema.