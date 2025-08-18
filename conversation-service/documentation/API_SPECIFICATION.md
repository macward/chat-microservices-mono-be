# Conversation Service - API Specification

Documentación completa de la API REST del Conversation Service.

## 📋 Información General

- **Base URL**: `http://conversation-service:8003`
- **Versión**: v1
- **Autenticación**: JWT Bearer Token
- **Content-Type**: `application/json`
- **Rate Limiting**: 100 requests/minute por usuario

## 🔐 Autenticación

Todos los endpoints (excepto `/health` y `/docs`) requieren autenticación JWT:

```http
Authorization: Bearer <jwt_token>
```

### Respuesta de Error de Autenticación
```json
{
  "error": {
    "message": "Invalid or expired token",
    "code": "AUTH_TOKEN_INVALID",
    "type": "AuthenticationError"
  }
}
```

## 📡 Endpoints

### 1. Listar Conversaciones

Obtiene la lista paginada de conversaciones del usuario autenticado.

```http
GET /conversations
```

#### Query Parameters

| Parámetro | Tipo | Requerido | Descripción | Valor por Defecto |
|-----------|------|-----------|-------------|-------------------|
| `limit` | int | No | Número de conversaciones por página (1-100) | 20 |
| `cursor` | string | No | Cursor para paginación | - |
| `status` | string | No | Filtrar por status: `active`, `archived`, `all` | `active` |
| `character_id` | string | No | Filtrar por ID del personaje | - |
| `search` | string | No | Buscar en título de conversaciones | - |
| `sort` | string | No | Ordenar por: `created_at`, `updated_at`, `last_activity` | `last_activity` |
| `order` | string | No | Orden: `asc`, `desc` | `desc` |

#### Ejemplo de Request
```http
GET /conversations?limit=10&status=active&sort=created_at&order=desc
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Ejemplo de Response (200 OK)
```json
{
  "conversations": [
    {
      "id": "507f1f77bcf86cd799439011",
      "user_id": "507f1f77bcf86cd799439012",
      "character_id": "507f1f77bcf86cd799439013",
      "title": "Chat with Luna about philosophy",
      "status": "active",
      "settings": {
        "temperature": 0.7,
        "max_tokens": 2048,
        "context_window": 4000
      },
      "metadata": {
        "message_count": 15,
        "last_activity": "2025-01-15T14:30:00.123Z",
        "total_tokens": 1250,
        "created_at": "2025-01-15T10:00:00.000Z",
        "updated_at": "2025-01-15T14:30:00.123Z"
      },
      "tags": ["philosophy", "deep-talk"],
      "is_archived": false
    }
  ],
  "pagination": {
    "total_count": 42,
    "has_next": true,
    "next_cursor": "eyJpZCI6IjUwN2YxZjc3YmNmODZjZDc5OTQzOTAxMSJ9",
    "limit": 10
  }
}
```

### 2. Crear Conversación

Crea una nueva conversación asociada a un personaje.

```http
POST /conversations
```

#### Request Body
```json
{
  "character_id": "507f1f77bcf86cd799439013",
  "title": "Nueva conversación con Luna",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_window": 4000
  },
  "tags": ["casual", "roleplay"]
}
```

#### Schema de Request
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `character_id` | string | Sí | ID del personaje (debe existir en Characters Service) |
| `title` | string | No | Título de la conversación (auto-generado si se omite) |
| `settings` | object | No | Configuraciones del LLM |
| `settings.temperature` | float | No | Temperatura (0.0-2.0) |
| `settings.max_tokens` | int | No | Máximo tokens por respuesta (1-4096) |
| `settings.context_window` | int | No | Ventana de contexto (1-8192) |
| `tags` | array[string] | No | Etiquetas para organización |

#### Ejemplo de Response (201 Created)
```json
{
  "id": "507f1f77bcf86cd799439014",
  "user_id": "507f1f77bcf86cd799439012",
  "character_id": "507f1f77bcf86cd799439013",
  "title": "Nueva conversación con Luna",
  "status": "active",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_window": 4000
  },
  "metadata": {
    "message_count": 0,
    "last_activity": "2025-01-15T15:00:00.000Z",
    "total_tokens": 0,
    "created_at": "2025-01-15T15:00:00.000Z",
    "updated_at": "2025-01-15T15:00:00.000Z"
  },
  "tags": ["casual", "roleplay"],
  "is_archived": false
}
```

### 3. Obtener Conversación

Obtiene los detalles de una conversación específica.

```http
GET /conversations/{conversation_id}
```

#### Path Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `conversation_id` | string | ID de la conversación |

#### Ejemplo de Response (200 OK)
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "character_id": "507f1f77bcf86cd799439013",
  "title": "Chat with Luna about philosophy",
  "status": "active",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_window": 4000
  },
  "metadata": {
    "message_count": 15,
    "last_activity": "2025-01-15T14:30:00.123Z",
    "total_tokens": 1250,
    "created_at": "2025-01-15T10:00:00.000Z",
    "updated_at": "2025-01-15T14:30:00.123Z"
  },
  "tags": ["philosophy", "deep-talk"],
  "is_archived": false,
  "character": {
    "id": "507f1f77bcf86cd799439013",
    "name": "Luna",
    "description": "AI assistant focused on philosophical discussions"
  }
}
```

### 4. Actualizar Conversación

Actualiza los metadatos de una conversación existente.

```http
PATCH /conversations/{conversation_id}
```

#### Request Body
```json
{
  "title": "Updated conversation title",
  "settings": {
    "temperature": 0.8,
    "max_tokens": 1024
  },
  "tags": ["updated", "philosophy"]
}
```

#### Schema de Request
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `title` | string | No | Nuevo título |
| `settings` | object | No | Configuraciones actualizadas (merge con existentes) |
| `tags` | array[string] | No | Nuevas etiquetas (reemplaza las existentes) |

#### Ejemplo de Response (200 OK)
```json
{
  "id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "character_id": "507f1f77bcf86cd799439013",
  "title": "Updated conversation title",
  "status": "active",
  "settings": {
    "temperature": 0.8,
    "max_tokens": 1024,
    "context_window": 4000
  },
  "metadata": {
    "message_count": 15,
    "last_activity": "2025-01-15T14:30:00.123Z",
    "total_tokens": 1250,
    "created_at": "2025-01-15T10:00:00.000Z",
    "updated_at": "2025-01-15T15:30:00.456Z"
  },
  "tags": ["updated", "philosophy"],
  "is_archived": false
}
```

### 5. Archivar Conversación

Marca una conversación como archivada (soft delete).

```http
DELETE /conversations/{conversation_id}
```

#### Ejemplo de Response (200 OK)
```json
{
  "message": "Conversation archived successfully",
  "conversation_id": "507f1f77bcf86cd799439011",
  "archived_at": "2025-01-15T16:00:00.000Z"
}
```

### 6. Restaurar Conversación

Restaura una conversación archivada al estado activo.

```http
POST /conversations/{conversation_id}/restore
```

#### Ejemplo de Response (200 OK)
```json
{
  "message": "Conversation restored successfully",
  "conversation_id": "507f1f77bcf86cd799439011",
  "restored_at": "2025-01-15T16:30:00.000Z"
}
```

### 7. Resumen del Usuario

Obtiene estadísticas generales de las conversaciones del usuario.

```http
GET /conversations/summary
```

#### Ejemplo de Response (200 OK)
```json
{
  "user_id": "507f1f77bcf86cd799439012",
  "statistics": {
    "total_conversations": 25,
    "active_conversations": 18,
    "archived_conversations": 7,
    "total_messages": 450,
    "total_tokens": 35000,
    "most_used_character": {
      "character_id": "507f1f77bcf86cd799439013",
      "character_name": "Luna",
      "conversation_count": 12
    },
    "recent_activity": {
      "last_conversation_created": "2025-01-15T10:00:00.000Z",
      "last_message_sent": "2025-01-15T14:30:00.123Z",
      "conversations_this_week": 3,
      "messages_this_week": 45
    }
  },
  "generated_at": "2025-01-15T17:00:00.000Z"
}
```

### 8. Health Check

Verifica el estado del servicio y sus dependencias.

```http
GET /health
```

#### Ejemplo de Response (200 OK)
```json
{
  "status": "healthy",
  "service": "conversation-service",
  "version": "1.0.0",
  "timestamp": "2025-01-15T17:00:00.000Z",
  "dependencies": {
    "mongodb": {
      "status": "connected",
      "response_time_ms": 12
    },
    "auth_service": {
      "status": "reachable",
      "response_time_ms": 45
    },
    "characters_service": {
      "status": "reachable", 
      "response_time_ms": 23
    }
  }
}
```

## ❌ Códigos de Error

### 400 - Bad Request
```json
{
  "error": {
    "message": "Validation failed for field 'character_id'",
    "code": "VALIDATION_ERROR",
    "type": "ValidationError",
    "details": {
      "field": "character_id",
      "value": "invalid-id",
      "constraint": "Must be a valid ObjectId"
    }
  }
}
```

### 401 - Unauthorized
```json
{
  "error": {
    "message": "Invalid or expired token",
    "code": "AUTH_TOKEN_INVALID",
    "type": "AuthenticationError"
  }
}
```

### 403 - Forbidden
```json
{
  "error": {
    "message": "You don't have permission to access this conversation",
    "code": "CONVERSATION_ACCESS_DENIED",
    "type": "AuthorizationError"
  }
}
```

### 404 - Not Found
```json
{
  "error": {
    "message": "Conversation not found",
    "code": "CONVERSATION_NOT_FOUND",
    "type": "NotFoundError"
  }
}
```

### 409 - Conflict
```json
{
  "error": {
    "message": "Cannot restore an active conversation",
    "code": "CONVERSATION_STATE_CONFLICT",
    "type": "ConflictError"
  }
}
```

### 422 - Unprocessable Entity
```json
{
  "error": {
    "message": "Character not found in Characters Service",
    "code": "CHARACTER_NOT_EXISTS",
    "type": "ExternalServiceError"
  }
}
```

### 500 - Internal Server Error
```json
{
  "error": {
    "message": "An unexpected error occurred",
    "code": "INTERNAL_ERROR",
    "type": "InternalServerError",
    "error_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

### 503 - Service Unavailable
```json
{
  "error": {
    "message": "Database connection failed",
    "code": "DATABASE_UNAVAILABLE",
    "type": "ServiceUnavailableError"
  }
}
```

## 📊 Rate Limiting

### Límites por Endpoint

| Endpoint | Límite | Ventana |
|----------|--------|---------|
| `GET /conversations` | 60 req/min | Usuario |
| `POST /conversations` | 10 req/min | Usuario |
| `PATCH /conversations/{id}` | 30 req/min | Usuario |
| `DELETE /conversations/{id}` | 20 req/min | Usuario |
| `GET /health` | Sin límite | - |

### Headers de Rate Limiting
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642251600
```

### Respuesta cuando se excede el límite (429)
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "code": "RATE_LIMIT_EXCEEDED",
    "type": "RateLimitError",
    "retry_after": 30
  }
}
```

## 🔄 Integración con Servicios Externos

### Auth Service Integration
```http
POST http://auth-service:8001/validate-token
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Characters Service Integration
```http
GET http://characters-service:8002/characters/{character_id}
Authorization: Bearer <jwt_token>
```

### Message Service Integration
```http
GET http://message-service:8004/conversations/{conversation_id}/stats
Authorization: Bearer <jwt_token>
```

## 📝 Notas de Implementación

### Paginación Cursor-Based
- El `cursor` es un token opaco basado en el último elemento de la página anterior
- Más eficiente que offset-based para grandes datasets
- Permite paginación consistente con datos en tiempo real

### Soft Delete
- Las conversaciones archivadas mantienen `status: "archived"`
- No se eliminan físicamente de la base de datos
- Pueden ser restauradas en cualquier momento

### Validación de Character ID
- Se valida la existencia del personaje en Characters Service
- Cache local de personajes para reducir llamadas externas
- Fallback a validación en tiempo real si cache falla

### Circuit Breaker Pattern
- Protección contra fallos en servicios externos
- Fallback automático cuando servicios no están disponibles
- Recuperación automática cuando servicios vuelven online