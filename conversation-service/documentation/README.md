# Conversation Service

Microservicio independiente para la gestión del ciclo de vida de conversaciones en el sistema Character Chat API.

## 📋 Responsabilidades

- **Gestión de conversaciones**: Crear, listar, actualizar, archivar y restaurar conversaciones
- **Control de acceso**: Autorización basada en ownership del usuario
- **Metadatos**: Gestión de configuraciones y estadísticas de conversaciones
- **Paginación**: Listado eficiente con cursor-based pagination
- **Integración**: Comunicación con Auth, Characters y Message Services

## 🏗️ Arquitectura

### Stack Tecnológico
- **Framework**: FastAPI 0.104+
- **Base de datos**: MongoDB con Beanie ODM
- **Autenticación**: JWT tokens (integración con Auth Service)
- **Comunicación**: HTTP REST + Circuit Breaker pattern
- **Containerización**: Docker + Docker Compose

### Estructura del Proyecto
```
conversation-service/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── config.py                  # Configuration settings
│   ├── database.py                # MongoDB connection
│   ├── models/
│   │   ├── conversation.py        # Pydantic models
│   │   └── requests.py           # Request/Response models
│   ├── repositories/
│   │   └── conversation_repository.py
│   ├── services/
│   │   ├── conversation_service.py
│   │   └── external_services.py  # Auth/Characters integration
│   └── api/
│       ├── dependencies.py       # FastAPI dependencies
│       └── v1/
│           └── conversations.py   # API endpoints
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── tests/
```

## 🚀 Quick Start

### Prerequisitos
- Python 3.11+
- MongoDB 5.0+
- Docker (opcional)

### Instalación Local

1. **Clonar y navegar**:
```bash
cd microservices/conversation-service
```

2. **Crear entorno virtual**:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Ejecutar el servicio**:
```bash
python -m app.main
```

### Docker Deployment

```bash
# Construcción
docker build -t conversation-service .

# Ejecución
docker-compose up -d
```

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `MONGODB_URL` | URL de conexión MongoDB | `mongodb://localhost:27017` |
| `MONGODB_DATABASE` | Nombre de la base de datos | `conversation_service` |
| `PORT` | Puerto del servicio | `8003` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `AUTH_SERVICE_URL` | URL del Auth Service | `http://auth-service:8001` |
| `CHARACTERS_SERVICE_URL` | URL del Characters Service | `http://characters-service:8002` |
| `MESSAGE_SERVICE_URL` | URL del Message Service | `http://message-service:8004` |
| `JWT_SECRET_KEY` | Clave secreta JWT (compartida) | - |

### Ejemplo .env
```bash
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=conversation_service
PORT=8003
LOG_LEVEL=INFO
ENVIRONMENT=development

# Service URLs
AUTH_SERVICE_URL=http://localhost:8001
CHARACTERS_SERVICE_URL=http://localhost:8002
MESSAGE_SERVICE_URL=http://localhost:8004

# Security
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
```

## 📡 API Endpoints

### Conversaciones

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/conversations` | Listar conversaciones del usuario |
| `POST` | `/conversations` | Crear nueva conversación |
| `GET` | `/conversations/{id}` | Obtener conversación específica |
| `PATCH` | `/conversations/{id}` | Actualizar conversación |
| `DELETE` | `/conversations/{id}` | Archivar conversación |
| `POST` | `/conversations/{id}/restore` | Restaurar conversación |
| `GET` | `/conversations/summary` | Estadísticas del usuario |

### Sistema

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/health` | Health check del servicio |
| `GET` | `/docs` | Documentación interactiva |

## 🔒 Autenticación

El servicio utiliza JWT tokens para autenticación. Todos los endpoints (excepto `/health` y `/docs`) requieren el header:

```
Authorization: Bearer <jwt_token>
```

## 📊 Modelos de Datos

### Conversation
```python
{
  "_id": "ObjectId",
  "user_id": "string",
  "character_id": "string", 
  "title": "string",
  "status": "active|archived|deleted",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_window": 4000
  },
  "metadata": {
    "message_count": 0,
    "last_activity": "2025-01-15T10:30:00Z",
    "total_tokens": 0,
    "created_at": "2025-01-15T10:30:00Z",
    "updated_at": "2025-01-15T10:30:00Z"
  },
  "tags": ["casual", "roleplay"],
  "is_archived": false
}
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/

# Tests específicos
pytest tests/test_conversation_service.py
```

## 📈 Monitoring

### Health Checks
- **Endpoint**: `GET /health`
- **Métricas**: Database connectivity, service status
- **Response**: JSON con estado y timestamp

### Logging
- **Formato**: JSON structured logging
- **Niveles**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Destino**: stdout (configurable)

## 🔄 Integración con Otros Servicios

### Auth Service
- **Validación de tokens JWT**
- **Extracción de user_id**
- **Verificación de permisos**

### Characters Service  
- **Validación de character_id**
- **Obtención de metadatos del personaje**

### Message Service
- **Estadísticas de mensajes**
- **Conteo de tokens**
- **Última actividad**

## 🚨 Error Handling

### Códigos de Error Comunes
- `400`: Validación de datos incorrecta
- `401`: Token JWT inválido o ausente
- `403`: Sin permisos para acceder a la conversación
- `404`: Conversación no encontrada
- `409`: Conflicto de estado (ej. restaurar conversación activa)
- `500`: Error interno del servicio

### Formato de Respuesta de Error
```json
{
  "error": {
    "message": "Conversation not found",
    "code": "CONVERSATION_NOT_FOUND",
    "type": "NotFoundError",
    "error_id": "uuid-for-tracking",
    "timestamp": "2025-01-15T10:30:00.123Z"
  }
}
```

## 📚 Documentación Adicional

- [API Specification](./API_SPECIFICATION.md) - Documentación detallada de endpoints
- [Database Design](./DATABASE_DESIGN.md) - Esquemas y modelos de MongoDB
- [Architecture](./ARCHITECTURE.md) - Patrones y diseño del servicio
- [Deployment Guide](./DEPLOYMENT.md) - Guía completa de deployment
- [Migration Guide](./MIGRATION_GUIDE.md) - Migración desde monolito

## 🤝 Contribución

1. Fork del repositorio
2. Crear branch para feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -am 'Add nueva funcionalidad'`)
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo LICENSE para más detalles.

## 📞 Soporte

Para preguntas o issues:
- **Issues**: GitHub Issues del repositorio principal
- **Documentation**: Revisar documentación en `/docs`
- **API Testing**: Usar `/docs` endpoint para testing interactivo