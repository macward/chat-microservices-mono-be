# Patrones y Prácticas Estándar para Microservicios

*Guía de patrones y prácticas estándar para garantizar coherencia arquitectónica en todos los microservicios*

## Objetivo

Establecer **estándares arquitectónicos uniformes** para todos los microservicios del ecosistema Character Chat API, asegurando:

- **Consistencia** en patrones de diseño
- **Mantenibilidad** del código
- **Escalabilidad** horizontal
- **Observabilidad** distribuida
- **Seguridad** robusta

## Estructura Estándar de Microservicio

### Arquitectura de Directorios Obligatoria

```
service-name/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration management (OBLIGATORIO)
│   ├── api/                       # API Layer
│   │   ├── __init__.py
│   │   ├── exceptions.py          # API exception handlers
│   │   ├── dependencies.py        # FastAPI dependencies
│   │   └── v1/                    # API version 1
│   │       ├── __init__.py
│   │       ├── health.py          # Health check endpoints (OBLIGATORIO)
│   │       └── {domain}.py        # Domain-specific endpoints
│   ├── core/                      # Core utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py          # Custom exceptions (OBLIGATORIO)
│   │   ├── security.py            # Security utilities
│   │   ├── logging.py             # Logging configuration (OBLIGATORIO)
│   │   └── middleware.py          # Custom middleware
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   ├── database.py            # Database models (SQLAlchemy/Beanie)
│   │   └── schemas.py             # Pydantic models
│   ├── services/                  # Business Logic Layer (OBLIGATORIO)
│   │   ├── __init__.py
│   │   ├── {domain}_service.py    # Business logic implementation
│   │   └── external_clients.py    # External service clients
│   ├── repositories/              # Data Access Layer (OBLIGATORIO)
│   │   ├── __init__.py
│   │   └── {domain}_repository.py # Data access implementation
│   ├── workers/                   # Background workers (si aplica)
│   │   ├── __init__.py
│   │   └── {task}_worker.py
│   └── database.py                # Database connection setup
├── tests/                         # Test suite (OBLIGATORIO)
│   ├── __init__.py
│   ├── conftest.py               # Pytest configuration
│   ├── unit/                     # Unit tests
│   │   └── test_{domain}_service.py
│   └── integration/              # Integration tests
│       └── test_{domain}_endpoints.py
├── scripts/                      # Utility scripts
│   ├── setup_db.py              # Database setup
│   └── migrate.py               # Data migration scripts
├── alembic/                     # Database migrations (para SQL)
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── .env.example                 # Environment template (OBLIGATORIO)
├── docker-compose.yml           # Local development
├── Dockerfile                   # Container image
├── CLAUDE.md                    # Claude Code instructions
└── README.md                    # Service documentation
```

## Patrones Arquitectónicos Obligatorios

### 1. Patrón de 3 Capas

**TODAS las operaciones deben seguir este flujo:**

```
API Layer → Service Layer → Repository Layer → Database
```

#### API Layer (app/api/)
- **Responsabilidad**: Manejo de requests/responses HTTP
- **NO debe contener**: Lógica de negocio
- **Debe incluir**: Validación de entrada, serialización de respuesta

```python
# ✅ CORRECTO - API Layer
@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
) -> UserResponse:
    """Create new user."""
    return await user_service.create_user(user_data)

# ❌ INCORRECTO - Lógica de negocio en API Layer
@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Validación en API layer - MAL
    if await db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(400, "Email already exists")
    # ... más lógica de negocio - MAL
```

#### Service Layer (app/services/)
- **Responsabilidad**: Lógica de negocio, coordinación entre repositories
- **NO debe contener**: Detalles de base de datos, HTTP handling
- **Debe incluir**: Validaciones de negocio, orchestration

```python
# ✅ CORRECTO - Service Layer
class UserService:
    def __init__(self):
        self.user_repository = UserRepository()
        self.notification_service = NotificationService()
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create user with business logic."""
        # Business validation
        await self._validate_user_data(user_data)
        
        # Create user
        user = await self.user_repository.create(user_data)
        
        # Business orchestration
        await self.notification_service.send_welcome_email(user.email)
        
        return UserResponse.from_orm(user)
```

#### Repository Layer (app/repositories/)
- **Responsabilidad**: Acceso a datos, queries específicas
- **NO debe contener**: Lógica de negocio
- **Debe incluir**: CRUD operations, queries complejas

```python
# ✅ CORRECTO - Repository Layer
class UserRepository:
    def __init__(self):
        self.db: Session = next(get_db())
    
    async def create(self, user_data: UserCreate) -> User:
        """Create user in database."""
        db_user = User(**user_data.model_dump())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
```

### 2. Configuration Management Estándar

**Todos los servicios DEBEN implementar:**

```python
# app/config.py
from pydantic import BaseSettings, validator
from typing import List, Optional
import os

class Settings(BaseSettings):
    # App Settings (OBLIGATORIO en todos los servicios)
    app_name: str = "Service Name"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    
    # Server Settings (OBLIGATORIO)
    host: str = "0.0.0.0"
    port: int = 8000  # Cambiar según servicio
    
    # Database Settings (OBLIGATORIO si usa DB)
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 30
    
    # Security Settings (OBLIGATORIO para servicios con auth)
    secret_key: str = os.urandom(32).hex()
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # External Services (OBLIGATORIO)
    auth_service_url: str = "http://localhost:8024"
    character_service_url: str = "http://localhost:8020"
    conversation_service_url: str = "http://localhost:8003"
    message_service_url: str = "http://localhost:9"
    llm_service_url: str = "http://localhost:8022"
    
    # Rate Limiting (OBLIGATORIO)
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # Logging (OBLIGATORIO)
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Health Check (OBLIGATORIO)
    health_check_timeout: int = 5
    
    @validator('environment')
    def validate_environment(cls, v):
        if v not in ['development', 'staging', 'production', 'testing']:
            raise ValueError('Invalid environment')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### 3. Exception Handling Estándar

**Jerarquía de excepciones obligatoria:**

```python
# app/core/exceptions.py
from typing import Optional, Dict, Any

class ServiceException(Exception):
    """Base exception for service errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: str = "GENERIC_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(ServiceException):
    """Validation error."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {},
            status_code=400
        )

class NotFoundError(ServiceException):
    """Resource not found error."""
    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found",
            error_code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            status_code=404
        )

class ConflictError(ServiceException):
    """Resource conflict error."""
    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT",
            details={"resource": resource} if resource else {},
            status_code=409
        )

class ExternalServiceError(ServiceException):
    """External service error."""
    def __init__(self, service_name: str, message: str):
        super().__init__(
            message=f"External service error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name},
            status_code=503
        )

class SecurityError(ServiceException):
    """Security related error."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            status_code=401
        )
```

### 4. Health Checks Obligatorios

**Todos los servicios DEBEN implementar:**

```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from typing import Dict, Any
import time

from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def basic_health_check() -> Dict[str, Any]:
    """Basic health check - OBLIGATORIO en todos los servicios."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment
    }

@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with dependencies - RECOMENDADO."""
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment,
        "dependencies": {}
    }
    
    # Database check (si aplica)
    try:
        await check_database_health()
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # External services check
    external_services = [
        ("auth_service", settings.auth_service_url),
        ("character_service", settings.character_service_url),
        # ... otros servicios
    ]
    
    for service_name, service_url in external_services:
        try:
            # Implementar check específico
            health_status["dependencies"][service_name] = "healthy"
        except Exception:
            health_status["dependencies"][service_name] = "unhealthy"
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
    
    return health_status

@router.get("/readiness")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe - OBLIGATORIO para deployment."""
    # Verificar que el servicio está listo para recibir tráfico
    return {"status": "ready"}

@router.get("/liveness")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe - OBLIGATORIO para deployment."""
    # Verificar que el servicio está vivo
    return {"status": "alive"}
```

### 5. Logging Estructurado Obligatorio

```python
# app/core/logging.py
import logging
import sys
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class StructuredLogger:
    """Structured logger with correlation ID support."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.logger = logging.getLogger(service_name)
        self._setup_formatter()
    
    def _setup_formatter(self):
        """Setup JSON formatter."""
        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "service": self.service_name,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                
                # Add correlation ID if available
                if hasattr(record, 'correlation_id'):
                    log_data["correlation_id"] = record.correlation_id
                
                # Add extra fields
                if hasattr(record, 'extra'):
                    log_data.update(record.extra)
                
                return json.dumps(log_data)
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def info(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        """Log info message."""
        extra = {"correlation_id": correlation_id, "extra": kwargs}
        self.logger.info(message, extra=extra)
    
    def error(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        """Log error message."""
        extra = {"correlation_id": correlation_id, "extra": kwargs}
        self.logger.error(message, extra=extra)
    
    def warning(self, message: str, correlation_id: Optional[str] = None, **kwargs):
        """Log warning message."""
        extra = {"correlation_id": correlation_id, "extra": kwargs}
        self.logger.warning(message, extra=extra)

# Singleton instance
logger = StructuredLogger(settings.app_name)
```

### 6. External Service Clients Estándar

**Patrón obligatorio para comunicación entre servicios:**

```python
# app/services/external_clients.py
import asyncio
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.exceptions import ExternalServiceError
from app.core.logging import logger

class CircuitBreaker:
    """Circuit breaker pattern - OBLIGATORIO para external calls."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half_open"
            else:
                raise ExternalServiceError("external_service", "Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if should attempt reset."""
        if not self.last_failure_time:
            return True
        return datetime.utcnow() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= self.failure_threshold:
            self.state = "open"

class BaseServiceClient:
    """Base class for service clients - USAR PARA TODOS LOS CLIENTS."""
    
    def __init__(self, service_name: str, base_url: str, timeout: int = 30):
        self.service_name = service_name
        self.base_url = base_url
        self.timeout = timeout
        self.circuit_breaker = CircuitBreaker()
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        correlation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with standard handling."""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.get("headers", {})
        
        if correlation_id:
            headers["X-Correlation-ID"] = correlation_id
        
        kwargs["headers"] = headers
        
        async def _request():
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        
        try:
            return await self.circuit_breaker.call(_request)
        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error from {self.service_name}",
                correlation_id=correlation_id,
                status_code=e.response.status_code,
                endpoint=endpoint
            )
            raise ExternalServiceError(self.service_name, f"HTTP {e.response.status_code}")
        except httpx.ConnectError:
            logger.error(
                f"Connection error to {self.service_name}",
                correlation_id=correlation_id,
                endpoint=endpoint
            )
            raise ExternalServiceError(self.service_name, "Connection failed")
        except httpx.TimeoutException:
            logger.error(
                f"Timeout error from {self.service_name}",
                correlation_id=correlation_id,
                endpoint=endpoint
            )
            raise ExternalServiceError(self.service_name, "Request timeout")

# Ejemplo de implementación específica
class AuthServiceClient(BaseServiceClient):
    """Client for Auth Service."""
    
    def __init__(self):
        super().__init__("auth_service", settings.auth_service_url)
    
    async def validate_token(self, token: str, correlation_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate JWT token."""
        return await self._make_request(
            "GET",
            "/api/v1/auth/validate",
            correlation_id=correlation_id,
            headers={"Authorization": f"Bearer {token}"}
        )
```

## Database Patterns

### 7. SQLAlchemy Models Estándar

```python
# app/models/database.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    """Base model with standard fields - HEREDAR EN TODOS LOS MODELS."""
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# Ejemplo de modelo específico
class User(BaseModel):
    __tablename__ = "users"
    
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    credits = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime, nullable=True)
```

### 8. MongoDB/Beanie Models Estándar

```python
# app/models/database.py (para servicios con MongoDB)
from datetime import datetime
from typing import Optional
from beanie import Document
from pydantic import Field
import uuid

class BaseDocument(Document):
    """Base document with standard fields - HEREDAR EN TODOS LOS DOCUMENTS."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    class Settings:
        use_enum_values = True

# Ejemplo de documento específico
class Message(BaseDocument):
    conversation_id: str
    user_id: str
    content: str
    role: str
    character_id: Optional[str] = None
    
    class Settings:
        name = "messages"
        indexes = [
            "conversation_id",
            "user_id",
            "created_at"
        ]
```

## Security Patterns

### 9. Authentication Middleware Estándar

```python
# app/core/middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import uuid

from app.services.external_clients import AuthServiceClient
from app.core.logging import logger

class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware - IMPLEMENTAR EN SERVICIOS QUE REQUIEREN AUTH."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.auth_client = AuthServiceClient()
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Extract and validate token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(401, "Authentication required")
        
        token = auth_header[7:]
        
        try:
            user_data = await self.auth_client.validate_token(token, correlation_id)
            request.state.user = user_data
            request.state.user_id = user_data["user_id"]
        except Exception as e:
            logger.error(
                "Authentication failed",
                correlation_id=correlation_id,
                error=str(e)
            )
            raise HTTPException(401, "Invalid token")
        
        return await call_next(request)
```

### 10. Rate Limiting Estándar

```python
# app/core/middleware.py
import time
from collections import defaultdict
from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware - IMPLEMENTAR EN TODOS LOS SERVICIOS."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self.clients[client_ip] = [
            req_time for req_time in self.clients[client_ip]
            if current_time - req_time < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(429, "Rate limit exceeded")
        
        # Record request
        self.clients[client_ip].append(current_time)
        
        return await call_next(request)
```

## Testing Patterns

### 11. Test Structure Estándar

```python
# tests/conftest.py - OBLIGATORIO en todos los servicios
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.config import settings

@pytest.fixture(scope="session")
def test_db():
    """Test database fixture."""
    # Setup test database
    engine = create_engine(settings.test_database_url)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """Test client fixture."""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    """Authenticated headers fixture."""
    # Create test user and get token
    # Return headers with Bearer token
    pass
```

## Deployment Patterns

### 12. Docker Configuration Estándar

```dockerfile
# Dockerfile - USAR EN TODOS LOS SERVICIOS
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Run application
CMD ["python", "-m", "app.main"]
```

### 13. Docker Compose Estándar

```yaml
# docker-compose.yml - TEMPLATE para todos los servicios
version: '3.8'

services:
  service-name:
    build: .
    ports:
      - "${PORT}:${PORT}"
    environment:
      - ENVIRONMENT=development
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - database
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --reload
    
  database:
    image: postgres:15
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "${DB_PORT}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Checklist de Implementación

### ✅ Checklist de Conformidad

Cada microservicio DEBE cumplir:

#### Arquitectura
- [ ] Estructura de directorios estándar implementada
- [ ] Patrón de 3 capas (API → Service → Repository)
- [ ] Service layer con lógica de negocio
- [ ] Repository layer para acceso a datos
- [ ] Configuration management con pydantic

#### API
- [ ] Health checks (/health, /health/detailed, /readiness, /liveness)
- [ ] Exception handling centralizado
- [ ] Response models consistentes
- [ ] OpenAPI documentation
- [ ] Versioning (/api/v1/)

#### Security
- [ ] Authentication middleware (si aplica)
- [ ] Rate limiting middleware
- [ ] CORS configuration
- [ ] Input validation con Pydantic
- [ ] No hardcoded secrets

#### Observability
- [ ] Structured logging con JSON
- [ ] Correlation ID support
- [ ] Error tracking
- [ ] Performance metrics
- [ ] Health monitoring

#### External Integration
- [ ] Circuit breaker pattern
- [ ] Service clients con retry logic
- [ ] Timeout configuration
- [ ] Error propagation

#### Testing
- [ ] Unit tests (>80% coverage)
- [ ] Integration tests
- [ ] Test fixtures
- [ ] Mock external services
- [ ] CI/CD pipeline

#### Deployment
- [ ] Dockerfile optimizado
- [ ] Docker Compose para desarrollo
- [ ] Environment configuration
- [ ] Database migrations
- [ ] Rolling deployment support

## Herramientas de Validación

### Automated Checks

```bash
# Script para validar conformidad (crear en scripts/validate_conformity.sh)
#!/bin/bash

echo "🔍 Validating microservice conformity..."

# Check directory structure
if [ ! -d "app/api/v1" ]; then
    echo "❌ Missing app/api/v1 directory"
    exit 1
fi

if [ ! -d "app/services" ]; then
    echo "❌ Missing app/services directory"
    exit 1
fi

if [ ! -d "app/repositories" ]; then
    echo "❌ Missing app/repositories directory"
    exit 1
fi

# Check required files
required_files=(
    "app/config.py"
    "app/core/exceptions.py"
    "app/core/logging.py"
    "app/api/v1/health.py"
    "tests/conftest.py"
    ".env.example"
    "requirements.txt"
    "Dockerfile"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

# Check for health endpoints
if ! grep -q "/health" app/api/v1/health.py; then
    echo "❌ Missing health endpoints"
    exit 1
fi

# Check for proper exception handling
if ! grep -q "ServiceException" app/core/exceptions.py; then
    echo "❌ Missing standard exceptions"
    exit 1
fi

echo "✅ Microservice conformity validated successfully!"
```

## Conclusión

Estos patrones y prácticas **DEBEN ser implementados** en todos los microservicios para garantizar:

1. **Consistencia arquitectónica** entre servicios
2. **Mantenibilidad** del código
3. **Escalabilidad** horizontal
4. **Observabilidad** distribuida
5. **Seguridad** robusta
6. **Testing** confiable
7. **Deployment** estandarizado

La implementación de estos estándares es **obligatoria** para nuevos servicios y **altamente recomendada** para servicios existentes durante su próxima refactorización.

---

*Documento de estándares creado el 19 de agosto de 2025*  
*Versión 1.0 - Aplicable a todos los microservicios del ecosistema*