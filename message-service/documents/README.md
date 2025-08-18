# Message Service

Microservicio especializado en el procesamiento, almacenamiento y gestión de mensajes individuales dentro del ecosistema Character Chat API.

## 📋 Responsabilidades del Servicio

### Responsabilidades Principales
- **Procesamiento de Mensajes**: Validación, sanitización y enriquecimiento de contenido
- **Almacenamiento Escalable**: Persistencia eficiente de grandes volúmenes de mensajes
- **Integración LLM**: Orquestación de llamadas a servicios de IA (LM Studio, OpenAI, etc.)
- **Context Management**: Gestión de ventanas de contexto para conversaciones
- **Token Tracking**: Monitoreo y análisis de uso de tokens
- **Message Analytics**: Estadísticas y métricas de uso de mensajes
- **Content Filtering**: Filtrado y moderación de contenido

### Responsabilidades Secundarias
- **Message Search**: Búsqueda de mensajes por contenido y metadatos
- **Message Export**: Exportación de historial de mensajes
- **Rate Limiting**: Control de frecuencia de envío de mensajes
- **Audit Logging**: Registro de actividad para auditoría
- **Message Templates**: Gestión de plantillas de mensajes predefinidas

## 🚫 Limitaciones del Servicio

### Limitaciones Arquitecturales
- **No gestiona conversaciones**: Las conversaciones son responsabilidad del Conversation Service
- **No maneja autenticación**: Depende del Auth Service para validación de usuarios
- **No gestiona personajes**: Los personajes son responsabilidad del Characters Service
- **No maneja configuraciones**: Las configuraciones de conversación están en Conversation Service

### Limitaciones Técnicas
- **Volumen de mensajes**: Máximo 10,000 mensajes por conversación
- **Tamaño de mensaje**: Máximo 50,000 caracteres por mensaje
- **Retención de datos**: 2 años para mensajes activos, 6 meses para archivados
- **Rate limiting**: 100 mensajes por minuto por usuario
- **Context window**: Máximo 32,000 tokens por contexto
- **Concurrent processing**: Máximo 1000 mensajes concurrentes

### Limitaciones Funcionales
- **No modifica mensajes**: Los mensajes son inmutables una vez creados
- **No elimina mensajes**: Solo archivado lógico (soft delete)
- **No gestiona hilos**: Conversaciones lineales únicamente
- **No maneja archivos**: Solo texto plano y metadatos estructurados

## 🏗️ Arquitectura del Servicio

### Stack Tecnológico
- **Framework**: FastAPI 0.104+
- **Base de datos**: MongoDB con particionamiento por conversación
- **Cache**: Redis para context windows y rate limiting
- **Queue**: Redis Streams para procesamiento asíncrono
- **LLM Integration**: Cliente unificado para múltiples proveedores
- **Monitoring**: Prometheus + Grafana

### Puerto del Servicio
- **Puerto**: 8004 (Message Service)

## 🗄️ Estrategia de Almacenamiento

### Elección de Base de Datos: MongoDB

**Razones para MongoDB:**
- **Flexibilidad de esquema**: Los mensajes pueden tener metadatos variables
- **Escalabilidad horizontal**: Sharding por conversation_id
- **Performance**: Consultas rápidas con índices optimizados
- **Agregaciones**: Analytics complejas con aggregation pipelines
- **TTL**: Expiración automática de mensajes antiguos

### Alternativas Consideradas y Descartadas

**PostgreSQL con JSONB:**
- ❌ **Menos flexible** para esquemas evolutivos
- ❌ **Sharding complejo** comparado con MongoDB
- ✅ **ACID transactions** (no críticas para mensajes)
- ❌ **Agregaciones menos eficientes** que MongoDB

**Cassandra:**
- ✅ **Excelente escalabilidad** para writes
- ❌ **Complejidad operacional** alta
- ❌ **Consultas limitadas** sin agregaciones complejas
- ❌ **Overkill** para el volumen actual

**ElasticSearch:**
- ✅ **Excelente para búsqueda** de texto
- ❌ **No es base de datos primaria** 
- ❌ **Overhead** para operaciones CRUD simples
- ✅ **Se usará como índice secundario**

## 📊 Modelos de Datos

### Colección Principal: messages

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "message_id": "msg_abc123def456",           // UUID único
  "conversation_id": "conv_789xyz123",        // Foreign key a Conversation Service
  "user_id": "user_456def789",               // Foreign key a Auth Service
  "character_id": "char_123abc456",          // Foreign key a Characters Service
  
  "content": {
    "text": "Hello Luna! How are you today?",
    "sanitized_text": "Hello Luna! How are you today?",
    "detected_language": "en",
    "content_hash": "sha256:abc123...",       // Para deduplicación
    "word_count": 6,
    "character_count": 30
  },
  
  "role": "user",                            // user | assistant | system
  "message_type": "standard",                // standard | template | system
  "status": "active",                        // active | archived | flagged
  
  "llm_metadata": {
    "provider": "lmstudio",                  // lmstudio | openai | anthropic
    "model": "google/gemma-3-12b",
    "temperature": 0.7,
    "max_tokens": 2048,
    "stop_sequences": ["\\n\\nHuman:"],
    "request_id": "req_xyz789abc123"
  },
  
  "token_usage": {
    "prompt_tokens": 245,
    "completion_tokens": 67,
    "total_tokens": 312,
    "estimated_cost": 0.00234               // USD
  },
  
  "context_metadata": {
    "context_window_size": 20,
    "messages_in_context": 15,
    "context_tokens": 2890,
    "context_hash": "sha256:def456..."      // Para cache
  },
  
  "processing_metadata": {
    "processing_time_ms": 1234,
    "queue_time_ms": 45,
    "total_latency_ms": 1279,
    "retry_count": 0,
    "error_count": 0
  },
  
  "safety_metadata": {
    "content_filtered": false,
    "safety_score": 0.95,                   // 0-1 (1 = safe)
    "detected_issues": [],
    "moderation_flags": []
  },
  
  "timestamps": {
    "created_at": ISODate("2025-01-15T10:30:00.123Z"),
    "processed_at": ISODate("2025-01-15T10:30:01.456Z"),
    "llm_response_at": ISODate("2025-01-15T10:30:02.789Z")
  },
  
  "client_metadata": {
    "client_msg_id": "client_msg_123",      // Para idempotencia
    "user_agent": "CharacterChat/1.0",
    "ip_address": "192.168.1.100",         // Para rate limiting
    "platform": "web"                      // web | mobile | api
  },
  
  "custom_metadata": {                      // Metadatos extensibles
    "intent": "greeting",
    "sentiment": "positive",
    "topics": ["greeting", "wellbeing"],
    "urgency": "low"
  },
  
  "version": 1,                            // Para versionado de esquema
  "partition_key": "conv_789xyz123"        // Para sharding
}
```

### Índices de MongoDB

```javascript
// Índice primario
db.messages.createIndex({ "_id": 1 })

// Índices para consultas frecuentes
db.messages.createIndex({ 
  "conversation_id": 1, 
  "timestamps.created_at": -1 
})

db.messages.createIndex({ 
  "user_id": 1, 
  "timestamps.created_at": -1 
})

db.messages.createIndex({ 
  "message_id": 1 
}, { unique: true })

// Índices para búsqueda
db.messages.createIndex({ 
  "content.text": "text",
  "custom_metadata.topics": "text"
})

// Índices para analytics
db.messages.createIndex({ 
  "llm_metadata.provider": 1,
  "llm_metadata.model": 1,
  "timestamps.created_at": -1
})

db.messages.createIndex({ 
  "token_usage.total_tokens": 1,
  "timestamps.created_at": -1
})

// Índice TTL para limpieza automática
db.messages.createIndex(
  { "timestamps.created_at": 1 },
  { 
    expireAfterSeconds: 63072000,  // 2 años
    partialFilterExpression: { "status": "archived" }
  }
)

// Índice para sharding
db.messages.createIndex({ 
  "partition_key": "hashed" 
})
```

## 📡 API Endpoints

### Gestión de Mensajes

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/messages` | Enviar nuevo mensaje |
| `GET` | `/messages/{message_id}` | Obtener mensaje específico |
| `GET` | `/conversations/{conv_id}/messages` | Listar mensajes de conversación |
| `PATCH` | `/messages/{message_id}/metadata` | Actualizar metadatos |
| `DELETE` | `/messages/{message_id}` | Archivar mensaje |
| `POST` | `/messages/{message_id}/restore` | Restaurar mensaje archivado |

### Procesamiento LLM

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/llm/process` | Procesar mensaje con LLM |
| `GET` | `/llm/providers` | Listar proveedores disponibles |
| `GET` | `/llm/models` | Listar modelos disponibles |
| `POST` | `/llm/validate` | Validar configuración LLM |

### Analytics y Estadísticas

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/conversations/{conv_id}/stats` | Estadísticas de conversación |
| `GET` | `/users/{user_id}/message-stats` | Estadísticas de usuario |
| `GET` | `/analytics/token-usage` | Análisis de uso de tokens |
| `GET` | `/analytics/performance` | Métricas de rendimiento |

### Búsqueda y Filtrado

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/search/messages` | Búsqueda de mensajes |
| `POST` | `/search/advanced` | Búsqueda avanzada |
| `GET` | `/search/suggestions` | Sugerencias de búsqueda |

### Administración

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/health` | Health check del servicio |
| `GET` | `/metrics` | Métricas de Prometheus |
| `POST` | `/admin/cleanup` | Limpieza de mensajes antiguos |
| `GET` | `/admin/queue-status` | Estado de colas de procesamiento |

## 🔄 Flujos de Trabajo Principales

### 1. Envío de Mensaje

```
1. Cliente → POST /messages
2. Validación y sanitización de contenido
3. Rate limiting check
4. Encolado para procesamiento asíncrono
5. Respuesta inmediata con message_id
6. Procesamiento en background:
   - Obtener contexto de conversación
   - Llamada a LLM Service
   - Generación de respuesta
   - Almacenamiento de ambos mensajes
   - Notificación de completado
```

### 2. Obtención de Mensajes

```
1. Cliente → GET /conversations/{id}/messages
2. Verificación de autorización con Auth Service
3. Consulta optimizada a MongoDB
4. Aplicación de filtros y paginación
5. Enriquecimiento con metadatos
6. Respuesta con mensajes paginados
```

### 3. Procesamiento LLM

```
1. Mensaje encolado → Redis Stream
2. Worker obtiene mensaje de cola
3. Construcción de contexto:
   - Obtener mensajes recientes
   - Aplicar context window
   - Obtener configuración de personaje
4. Llamada a LLM Provider
5. Post-procesamiento de respuesta
6. Almacenamiento con metadatos completos
7. Actualización de métricas
```

## 🔧 Configuración del Servicio

### Variables de Entorno

```bash
# Service Configuration
SERVICE_NAME=message-service
PORT=8004
LOG_LEVEL=INFO
ENVIRONMENT=production

# Database
MONGODB_URL=mongodb://mongodb-cluster:27017
MONGODB_DATABASE=message_service
MONGODB_CONNECTION_POOL_MIN=20
MONGODB_CONNECTION_POOL_MAX=100

# Redis (Cache & Queue)
REDIS_URL=redis://redis-cluster:6379
REDIS_CONNECTION_POOL_MAX=50
CACHE_TTL_SECONDS=3600

# External Services
AUTH_SERVICE_URL=http://auth-service:8001
CONVERSATION_SERVICE_URL=http://conversation-service:8003
CHARACTERS_SERVICE_URL=http://characters-service:8002
LLM_SERVICE_URL=http://llm-service:8005

# LLM Configuration
DEFAULT_LLM_PROVIDER=lmstudio
DEFAULT_MODEL=google/gemma-3-12b
MAX_TOKENS_PER_REQUEST=4096
DEFAULT_TEMPERATURE=0.7
REQUEST_TIMEOUT_SECONDS=60

# Rate Limiting
MAX_MESSAGES_PER_MINUTE=100
MAX_MESSAGES_PER_HOUR=1000
MAX_MESSAGES_PER_DAY=10000

# Content Safety
ENABLE_CONTENT_FILTERING=true
SAFETY_THRESHOLD=0.8
MAX_MESSAGE_LENGTH=50000

# Performance
MAX_CONCURRENT_LLM_REQUESTS=100
MESSAGE_PROCESSING_TIMEOUT=300
BATCH_SIZE_FOR_ANALYTICS=1000

# Data Retention
MESSAGE_RETENTION_DAYS=730
ARCHIVED_MESSAGE_RETENTION_DAYS=180
AUTO_CLEANUP_ENABLED=true
```

## 🏛️ Estructura del Proyecto

```
message-service/
├── app/
│   ├── __init__.py
│   ├── main.py                        # FastAPI application
│   ├── config.py                      # Configuration management
│   ├── database.py                    # MongoDB connection
│   │
│   ├── api/                          # API Layer
│   │   ├── __init__.py
│   │   ├── dependencies.py           # FastAPI dependencies
│   │   ├── middleware.py             # Custom middleware
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── messages.py           # Message endpoints
│   │       ├── llm.py               # LLM processing endpoints
│   │       ├── analytics.py         # Analytics endpoints
│   │       ├── search.py            # Search endpoints
│   │       └── admin.py             # Admin endpoints
│   │
│   ├── services/                     # Service Layer
│   │   ├── __init__.py
│   │   ├── message_service.py        # Core message business logic
│   │   ├── llm_service.py           # LLM integration service
│   │   ├── content_service.py       # Content processing & filtering
│   │   ├── analytics_service.py     # Analytics and metrics
│   │   ├── search_service.py        # Search functionality
│   │   └── external_services.py     # External service clients
│   │
│   ├── repositories/                 # Repository Layer
│   │   ├── __init__.py
│   │   ├── message_repository.py    # Message data access
│   │   ├── analytics_repository.py  # Analytics queries
│   │   ├── search_repository.py     # Search operations
│   │   └── base_repository.py       # Abstract repository
│   │
│   ├── models/                       # Data Models
│   │   ├── __init__.py
│   │   ├── message.py               # Message Pydantic models
│   │   ├── llm.py                   # LLM related models
│   │   ├── analytics.py             # Analytics models
│   │   ├── search.py                # Search models
│   │   ├── requests.py              # API request models
│   │   ├── responses.py             # API response models
│   │   └── database.py              # Beanie MongoDB models
│   │
│   ├── workers/                      # Background Workers
│   │   ├── __init__.py
│   │   ├── message_processor.py     # Async message processing
│   │   ├── llm_worker.py           # LLM processing worker
│   │   ├── analytics_worker.py     # Analytics computation
│   │   └── cleanup_worker.py       # Data cleanup tasks
│   │
│   ├── core/                        # Core Utilities
│   │   ├── __init__.py
│   │   ├── exceptions.py            # Custom exceptions
│   │   ├── security.py              # Security utilities
│   │   ├── cache.py                 # Redis cache wrapper
│   │   ├── queue.py                 # Redis queue wrapper
│   │   ├── logging.py               # Logging configuration
│   │   ├── metrics.py               # Prometheus metrics
│   │   └── rate_limiter.py          # Rate limiting logic
│   │
│   └── utils/                       # General Utilities
│       ├── __init__.py
│       ├── content_utils.py         # Content processing helpers
│       ├── token_utils.py           # Token counting utilities
│       ├── datetime_utils.py        # Date/time helpers
│       ├── pagination.py            # Pagination utilities
│       ├── validators.py            # Custom validators
│       └── text_processing.py       # Text analysis utilities
│
├── tests/                           # Test Suite
│   ├── __init__.py
│   ├── conftest.py                  # Pytest configuration
│   ├── unit/                        # Unit tests
│   │   ├── test_services/
│   │   ├── test_repositories/
│   │   └── test_utils/
│   ├── integration/                 # Integration tests
│   │   ├── test_api/
│   │   ├── test_database/
│   │   └── test_external_services/
│   └── e2e/                        # End-to-end tests
│       └── test_message_workflows/
│
├── scripts/                         # Utility Scripts
│   ├── migrate_messages.py         # Data migration
│   ├── setup_indexes.py            # Database index setup
│   ├── cleanup_old_messages.py     # Data cleanup
│   ├── benchmark_performance.py    # Performance testing
│   └── seed_test_data.py           # Test data generation
│
├── workers/                         # Worker Entry Points
│   ├── message_processor.py        # Message processing worker
│   ├── llm_worker.py              # LLM processing worker
│   ├── analytics_worker.py        # Analytics worker
│   └── scheduler.py               # Task scheduler
│
├── requirements.txt                 # Python dependencies
├── requirements-dev.txt             # Development dependencies
├── requirements-workers.txt         # Worker-specific dependencies
├── Dockerfile                       # Container definition
├── Dockerfile.worker                # Worker container definition
├── docker-compose.yml               # Local development setup
├── .env.example                     # Environment template
├── pyproject.toml                   # Python project configuration
└── monitoring/                      # Monitoring configuration
    ├── prometheus.yml
    └── grafana-dashboard.json
```

## 🔧 Desarrollo Local

### Quick Start

```bash
# 1. Navegar al directorio
cd microservices/message-service

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con configuraciones locales

# 5. Iniciar servicios de dependencias
docker-compose up -d mongodb redis

# 6. Configurar base de datos
python scripts/setup_indexes.py

# 7. Iniciar el servicio
python -m app.main

# 8. Iniciar workers (en terminal separado)
python workers/message_processor.py
```

### Docker Development

```bash
# Ejecutar todo el stack
docker-compose up -d

# Ver logs
docker-compose logs -f message-service

# Ejecutar tests
docker-compose exec message-service pytest
```

## 📊 Monitoreo y Métricas

### Métricas Principales

```python
# Métricas de mensajes
messages_created_total = Counter('messages_created_total', 'Total messages created')
messages_processed_total = Counter('messages_processed_total', 'Total messages processed')
message_processing_time = Histogram('message_processing_seconds', 'Message processing time')
message_queue_size = Gauge('message_queue_size', 'Current message queue size')

# Métricas de LLM
llm_requests_total = Counter('llm_requests_total', 'Total LLM requests', ['provider', 'model'])
llm_response_time = Histogram('llm_response_seconds', 'LLM response time', ['provider'])
llm_tokens_used = Counter('llm_tokens_used_total', 'Total tokens used', ['type'])
llm_errors_total = Counter('llm_errors_total', 'Total LLM errors', ['provider', 'error_type'])

# Métricas de rendimiento
database_query_time = Histogram('database_query_seconds', 'Database query time', ['operation'])
cache_hit_rate = Gauge('cache_hit_rate', 'Cache hit rate percentage')
concurrent_requests = Gauge('concurrent_requests', 'Current concurrent requests')
```

### Health Checks

```python
# Endpoint: GET /health
{
  "status": "healthy",
  "service": "message-service",
  "version": "1.0.0",
  "timestamp": "2025-01-15T17:00:00.000Z",
  "dependencies": {
    "mongodb": {
      "status": "connected",
      "response_time_ms": 15,
      "connection_pool": {
        "active": 25,
        "idle": 15,
        "max": 100
      }
    },
    "redis": {
      "status": "connected",
      "response_time_ms": 3,
      "memory_usage": "45MB"
    },
    "llm_service": {
      "status": "reachable",
      "response_time_ms": 120,
      "queue_size": 5
    },
    "auth_service": {
      "status": "reachable",
      "response_time_ms": 25
    }
  },
  "performance": {
    "avg_message_processing_time_ms": 850,
    "messages_in_queue": 12,
    "cache_hit_rate": 0.87,
    "concurrent_requests": 23
  }
}
```

## 🛡️ Seguridad y Validación

### Content Safety

```python
class ContentSafetyService:
    async def validate_message_content(self, content: str) -> SafetyResult:
        safety_checks = [
            self.check_length_limits(content),
            self.check_harmful_content(content),
            self.check_spam_patterns(content),
            self.check_personal_info(content),
            self.check_language_appropriateness(content)
        ]
        
        return await self.aggregate_safety_results(safety_checks)
```

### Rate Limiting

```python
class MessageRateLimiter:
    async def check_user_limits(self, user_id: str) -> RateLimitResult:
        limits = [
            await self.check_per_minute_limit(user_id),
            await self.check_per_hour_limit(user_id),
            await self.check_per_day_limit(user_id),
            await self.check_concurrent_requests(user_id)
        ]
        
        return self.evaluate_limits(limits)
```

## 📈 Escalabilidad y Performance

### Sharding Strategy

```javascript
// Sharding por conversation_id para distribución uniforme
sh.shardCollection("message_service.messages", {"conversation_id": "hashed"})

// Cada shard maneja un subset de conversaciones
// Consultas por conversación son locales a un shard
// Consultas globales requieren scatter-gather
```

### Caching Strategy

```python
# Context Window Cache
cache_key = f"context:{conversation_id}:{window_size}"
context = await redis.get(cache_key)
if not context:
    context = await build_context_window(conversation_id, window_size)
    await redis.setex(cache_key, 300, context)  # 5 minutos TTL

# LLM Response Cache (para mensajes idénticos)
content_hash = hashlib.sha256(message_content.encode()).hexdigest()
cache_key = f"llm_response:{content_hash}:{model_config_hash}"
cached_response = await redis.get(cache_key)
```

### Performance Optimizations

```python
# Batch processing para analytics
@background_task(schedule="*/5 * * * *")  # Cada 5 minutos
async def compute_analytics_batch():
    batch = await get_unprocessed_messages(limit=1000)
    analytics = await compute_analytics_parallel(batch)
    await store_analytics_batch(analytics)

# Connection pooling optimizado
mongodb_client = AsyncIOMotorClient(
    connection_string,
    minPoolSize=20,
    maxPoolSize=100,
    maxIdleTimeMS=30000,
    serverSelectionTimeoutMS=5000
)
```

## 🚨 Troubleshooting

### Problemas Comunes

| Problema | Síntoma | Solución |
|----------|---------|----------|
| Cola de mensajes creciendo | Queue size > 1000 | Aumentar workers, verificar LLM service |
| Alta latencia LLM | Response time > 5s | Check LLM service, ajustar timeouts |
| Memory leaks | RAM usage creciendo | Revisar context caching, restart workers |
| Database locks | Slow queries | Optimizar índices, revisar sharding |
| Rate limit errors | 429 responses | Ajustar límites, verificar distribución |

### Comandos de Diagnóstico

```bash
# Verificar estado de colas
curl http://message-service:8004/admin/queue-status

# Métricas de performance
curl http://message-service:8004/metrics

# Verificar configuración LLM
curl http://message-service:8004/llm/providers

# Test de conectividad
curl http://message-service:8004/health
```

## 📚 Documentación Adicional

- [API Specification](./API_SPECIFICATION.md) - Documentación detallada de endpoints
- [Database Design](./DATABASE_DESIGN.md) - Esquemas y optimizaciones de MongoDB
- [Architecture](./ARCHITECTURE.md) - Patrones y diseño del servicio
- [Deployment Guide](./DEPLOYMENT.md) - Guía completa de deployment
- [LLM Integration Guide](./LLM_INTEGRATION.md) - Integración con proveedores LLM
- [Performance Tuning](./PERFORMANCE_TUNING.md) - Optimización y escalabilidad

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo LICENSE para más detalles.