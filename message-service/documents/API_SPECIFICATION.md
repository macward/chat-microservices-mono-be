# Message Service - API Specification

Documentación completa de la API REST del Message Service para procesamiento y gestión de mensajes.

## 📋 Información General

- **Base URL**: `http://message-service:8004`
- **Versión**: v1
- **Autenticación**: JWT Bearer Token
- **Content-Type**: `application/json`
- **Rate Limiting**: 100 requests/minute por usuario

## 🔐 Autenticación

Todos los endpoints (excepto `/health` y `/metrics`) requieren autenticación JWT:

```http
Authorization: Bearer <jwt_token>
```

## 📡 Endpoints Principales

### 1. Enviar Mensaje

Envía un nuevo mensaje y lo procesa con el LLM correspondiente.

```http
POST /messages
```

#### Request Body
```json
{
  "conversation_id": "conv_789xyz123",
  "content": "Hello Luna! How are you today?",
  "client_msg_id": "client_msg_123",
  "message_type": "standard",
  "config_override": {
    "temperature": 0.8,
    "max_tokens": 1024
  },
  "metadata": {
    "intent": "greeting",
    "platform": "web",
    "user_agent": "CharacterChat/1.0"
  }
}
```

#### Schema de Request
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `conversation_id` | string | Sí | ID de la conversación de destino |
| `content` | string | Sí | Contenido del mensaje (1-50,000 chars) |
| `client_msg_id` | string | No | ID del cliente para idempotencia |
| `message_type` | string | No | Tipo: `standard`, `template`, `system` |
| `config_override` | object | No | Configuración temporal para este mensaje |
| `metadata` | object | No | Metadatos adicionales del mensaje |

#### Ejemplo de Response (202 Accepted)
```json
{
  "message_id": "msg_abc123def456",
  "conversation_id": "conv_789xyz123",
  "user_message": {
    "message_id": "msg_abc123def456",
    "content": "Hello Luna! How are you today?",
    "role": "user",
    "status": "processing",
    "created_at": "2025-01-15T10:30:00.123Z"
  },
  "processing_status": {
    "status": "queued",
    "queue_position": 3,
    "estimated_completion": "2025-01-15T10:30:05.000Z"
  },
  "tracking": {
    "request_id": "req_xyz789abc123",
    "idempotent": false
  }
}
```

#### Response cuando Procesamiento Completo (200 OK)
```json
{
  "message_id": "msg_abc123def456",
  "conversation_id": "conv_789xyz123",
  "user_message": {
    "message_id": "msg_abc123def456",
    "content": "Hello Luna! How are you today?",
    "role": "user",
    "status": "active",
    "created_at": "2025-01-15T10:30:00.123Z",
    "processed_at": "2025-01-15T10:30:01.456Z"
  },
  "assistant_message": {
    "message_id": "msg_def456ghi789",
    "content": "Hello! I'm doing wonderfully, thank you for asking! I've been thinking about interesting topics to discuss. How has your day been so far?",
    "role": "assistant",
    "status": "active",
    "created_at": "2025-01-15T10:30:02.789Z",
    "llm_metadata": {
      "provider": "lmstudio",
      "model": "google/gemma-3-12b",
      "temperature": 0.7,
      "processing_time_ms": 1234
    }
  },
  "token_usage": {
    "prompt_tokens": 245,
    "completion_tokens": 67,
    "total_tokens": 312,
    "estimated_cost": 0.00234
  },
  "context_metadata": {
    "messages_in_context": 15,
    "context_tokens": 2890,
    "context_window_size": 20
  },
  "processing_metadata": {
    "total_processing_time_ms": 2567,
    "queue_time_ms": 234,
    "llm_processing_time_ms": 1234,
    "post_processing_time_ms": 89
  }
}
```

### 2. Obtener Mensaje

Obtiene los detalles de un mensaje específico.

```http
GET /messages/{message_id}
```

#### Path Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `message_id` | string | ID único del mensaje |

#### Query Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `include_context` | boolean | Incluir información de contexto |
| `include_metadata` | boolean | Incluir metadatos completos |

#### Ejemplo de Response (200 OK)
```json
{
  "message_id": "msg_abc123def456",
  "conversation_id": "conv_789xyz123",
  "user_id": "user_456def789",
  "character_id": "char_123abc456",
  "content": {
    "text": "Hello Luna! How are you today?",
    "sanitized_text": "Hello Luna! How are you today?",
    "detected_language": "en",
    "word_count": 6,
    "character_count": 30
  },
  "role": "user",
  "message_type": "standard",
  "status": "active",
  "timestamps": {
    "created_at": "2025-01-15T10:30:00.123Z",
    "processed_at": "2025-01-15T10:30:01.456Z"
  },
  "safety_metadata": {
    "content_filtered": false,
    "safety_score": 0.95,
    "detected_issues": []
  },
  "custom_metadata": {
    "intent": "greeting",
    "platform": "web"
  }
}
```

### 3. Listar Mensajes de Conversación

Obtiene los mensajes de una conversación con paginación avanzada.

```http
GET /conversations/{conversation_id}/messages
```

#### Query Parameters
| Parámetro | Tipo | Descripción | Valor por Defecto |
|-----------|------|-------------|-------------------|
| `limit` | int | Mensajes por página (1-1000) | 50 |
| `cursor` | string | Cursor de paginación | - |
| `direction` | string | Dirección: `next`, `prev` | `next` |
| `role` | string | Filtrar por rol: `user`, `assistant`, `system` | - |
| `start_date` | datetime | Mensajes desde esta fecha | - |
| `end_date` | datetime | Mensajes hasta esta fecha | - |
| `include_archived` | boolean | Incluir mensajes archivados | false |
| `format` | string | Formato: `full`, `summary`, `llm` | `full` |
| `sort` | string | Ordenar por: `created_at`, `processed_at` | `created_at` |
| `order` | string | Orden: `asc`, `desc` | `asc` |

#### Ejemplo de Response (200 OK)
```json
{
  "messages": [
    {
      "message_id": "msg_001",
      "content": {
        "text": "Hello Luna!",
        "word_count": 2
      },
      "role": "user",
      "created_at": "2025-01-15T10:30:00.123Z",
      "token_usage": null
    },
    {
      "message_id": "msg_002", 
      "content": {
        "text": "Hello! How can I help you today?",
        "word_count": 7
      },
      "role": "assistant",
      "created_at": "2025-01-15T10:30:02.456Z",
      "token_usage": {
        "prompt_tokens": 45,
        "completion_tokens": 12,
        "total_tokens": 57
      },
      "llm_metadata": {
        "provider": "lmstudio",
        "model": "google/gemma-3-12b"
      }
    }
  ],
  "pagination": {
    "total_count": 245,
    "current_page": 1,
    "total_pages": 5,
    "has_next": true,
    "has_prev": false,
    "next_cursor": "eyJjcmVhdGVkX2F0IjoiMjAyNS0wMS0xNVQxMDozMDowMi40NTZaIn0=",
    "prev_cursor": null,
    "limit": 50
  },
  "conversation_metadata": {
    "conversation_id": "conv_789xyz123",
    "total_messages": 245,
    "total_tokens": 15432,
    "date_range": {
      "first_message": "2025-01-10T09:00:00.000Z",
      "last_message": "2025-01-15T10:30:02.456Z"
    }
  }
}
```

### 4. Actualizar Metadatos de Mensaje

Actualiza los metadatos personalizados de un mensaje.

```http
PATCH /messages/{message_id}/metadata
```

#### Request Body
```json
{
  "metadata": {
    "intent": "question",
    "topics": ["technology", "ai"],
    "sentiment": "curious",
    "urgency": "low",
    "custom_tags": ["important", "follow-up"]
  },
  "merge_mode": "update"
}
```

#### Schema de Request
| Campo | Tipo | Descripción |
|-------|------|-------------|
| `metadata` | object | Nuevos metadatos a aplicar |
| `merge_mode` | string | Modo: `replace`, `update`, `merge` |

#### Ejemplo de Response (200 OK)
```json
{
  "message_id": "msg_abc123def456",
  "metadata_updated": true,
  "updated_at": "2025-01-15T11:00:00.000Z",
  "updated_fields": ["intent", "topics", "sentiment", "urgency", "custom_tags"],
  "current_metadata": {
    "intent": "question",
    "topics": ["technology", "ai"],
    "sentiment": "curious",
    "urgency": "low",
    "custom_tags": ["important", "follow-up"],
    "platform": "web",
    "original_timestamp": "2025-01-15T10:30:00.123Z"
  }
}
```

### 5. Archivar Mensaje

Archiva un mensaje (soft delete).

```http
DELETE /messages/{message_id}
```

#### Query Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `reason` | string | Motivo del archivado |

#### Ejemplo de Response (200 OK)
```json
{
  "message_id": "msg_abc123def456",
  "status": "archived",
  "archived_at": "2025-01-15T11:30:00.000Z",
  "archive_reason": "user_request",
  "recoverable": true,
  "recovery_deadline": "2025-04-15T11:30:00.000Z"
}
```

## 🤖 Endpoints de Procesamiento LLM

### 1. Procesar Mensaje con LLM

Procesa un mensaje específico con configuración LLM personalizada.

```http
POST /llm/process
```

#### Request Body
```json
{
  "conversation_id": "conv_789xyz123",
  "message_content": "Explain quantum computing in simple terms",
  "llm_config": {
    "provider": "lmstudio",
    "model": "google/gemma-3-12b",
    "temperature": 0.5,
    "max_tokens": 1500,
    "stop_sequences": ["Human:", "Assistant:"],
    "top_p": 0.9
  },
  "context_config": {
    "window_size": 25,
    "include_system_messages": true,
    "context_compression": false
  },
  "processing_options": {
    "priority": "normal",
    "async": false,
    "timeout_seconds": 60
  }
}
```

#### Ejemplo de Response (200 OK)
```json
{
  "request_id": "req_xyz789abc123",
  "processing_status": "completed",
  "response": {
    "content": "Quantum computing is like having a super-powerful computer that can explore many possibilities at once...",
    "finish_reason": "stop",
    "safety_filtered": false
  },
  "token_usage": {
    "prompt_tokens": 156,
    "completion_tokens": 289,
    "total_tokens": 445,
    "estimated_cost": 0.00334
  },
  "performance_metrics": {
    "total_time_ms": 2340,
    "time_to_first_token_ms": 890,
    "tokens_per_second": 34.2,
    "context_build_time_ms": 234
  },
  "model_metadata": {
    "provider": "lmstudio",
    "model": "google/gemma-3-12b",
    "version": "1.2.3",
    "context_length": 4096,
    "effective_temperature": 0.5
  }
}
```

### 2. Listar Proveedores LLM

Obtiene la lista de proveedores LLM disponibles.

```http
GET /llm/providers
```

#### Ejemplo de Response (200 OK)
```json
{
  "providers": [
    {
      "name": "lmstudio",
      "display_name": "LM Studio",
      "status": "available",
      "default": true,
      "base_url": "http://lm-studio:1234",
      "capabilities": {
        "streaming": true,
        "function_calling": false,
        "image_input": false,
        "max_context_length": 8192
      },
      "models": [
        {
          "id": "google/gemma-3-12b",
          "name": "Gemma 3 12B",
          "context_length": 8192,
          "cost_per_token": 0.0000075
        }
      ]
    },
    {
      "name": "openai",
      "display_name": "OpenAI",
      "status": "available",
      "default": false,
      "capabilities": {
        "streaming": true,
        "function_calling": true,
        "image_input": true,
        "max_context_length": 128000
      },
      "models": [
        {
          "id": "gpt-4-turbo",
          "name": "GPT-4 Turbo",
          "context_length": 128000,
          "cost_per_token": 0.00003
        }
      ]
    }
  ],
  "default_provider": "lmstudio",
  "total_providers": 2,
  "healthy_providers": 2
}
```

### 3. Listar Modelos Disponibles

Obtiene todos los modelos disponibles de todos los proveedores.

```http
GET /llm/models
```

#### Query Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `provider` | string | Filtrar por proveedor |
| `available_only` | boolean | Solo modelos disponibles |

#### Ejemplo de Response (200 OK)
```json
{
  "models": [
    {
      "id": "google/gemma-3-12b",
      "provider": "lmstudio",
      "name": "Gemma 3 12B",
      "description": "Advanced language model with 12B parameters",
      "status": "available",
      "capabilities": {
        "context_length": 8192,
        "max_tokens": 4096,
        "supports_streaming": true,
        "supports_functions": false
      },
      "performance": {
        "avg_tokens_per_second": 45.2,
        "avg_response_time_ms": 1200,
        "uptime_percentage": 99.8
      },
      "pricing": {
        "cost_per_input_token": 0.0000075,
        "cost_per_output_token": 0.0000075,
        "currency": "USD"
      }
    }
  ],
  "total_models": 12,
  "available_models": 10,
  "providers_represented": 3
}
```

### 4. Validar Configuración LLM

Valida una configuración LLM antes de usarla.

```http
POST /llm/validate
```

#### Request Body
```json
{
  "provider": "lmstudio",
  "model": "google/gemma-3-12b",
  "temperature": 0.7,
  "max_tokens": 2048,
  "top_p": 0.9,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0,
  "stop_sequences": ["Human:", "Assistant:"]
}
```

#### Ejemplo de Response (200 OK)
```json
{
  "valid": true,
  "provider_available": true,
  "model_available": true,
  "configuration_valid": true,
  "warnings": [],
  "suggestions": [
    {
      "field": "temperature",
      "current": 0.7,
      "suggested": 0.8,
      "reason": "Higher temperature recommended for creative responses"
    }
  ],
  "estimated_cost_per_request": 0.00234,
  "max_context_tokens": 8192,
  "effective_max_tokens": 2048
}
```

## 📊 Endpoints de Analytics

### 1. Estadísticas de Conversación

Obtiene estadísticas detalladas de una conversación.

```http
GET /conversations/{conversation_id}/stats
```

#### Query Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `period` | string | Período: `day`, `week`, `month`, `all` |
| `include_tokens` | boolean | Incluir análisis de tokens |
| `include_performance` | boolean | Incluir métricas de rendimiento |

#### Ejemplo de Response (200 OK)
```json
{
  "conversation_id": "conv_789xyz123",
  "statistics": {
    "message_counts": {
      "total_messages": 245,
      "user_messages": 123,
      "assistant_messages": 122,
      "system_messages": 0
    },
    "token_usage": {
      "total_tokens": 45678,
      "input_tokens": 23456,
      "output_tokens": 22222,
      "estimated_total_cost": 0.34234
    },
    "timing_stats": {
      "conversation_duration_hours": 72.5,
      "avg_response_time_ms": 1234,
      "fastest_response_ms": 456,
      "slowest_response_ms": 3456,
      "messages_per_hour": 3.4
    },
    "content_analysis": {
      "avg_message_length": 125,
      "total_words": 8765,
      "unique_topics": ["technology", "science", "philosophy"],
      "dominant_language": "en",
      "sentiment_distribution": {
        "positive": 0.65,
        "neutral": 0.25,
        "negative": 0.10
      }
    },
    "llm_usage": {
      "primary_provider": "lmstudio",
      "primary_model": "google/gemma-3-12b",
      "provider_distribution": {
        "lmstudio": 0.95,
        "openai": 0.05
      },
      "avg_temperature": 0.72,
      "context_efficiency": 0.87
    }
  },
  "generated_at": "2025-01-15T17:00:00.000Z",
  "period_analyzed": "all"
}
```

### 2. Estadísticas de Usuario

Obtiene estadísticas globales de mensajes para un usuario.

```http
GET /users/{user_id}/message-stats
```

#### Query Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `timeframe` | string | Marco temporal: `7d`, `30d`, `90d`, `1y` |
| `group_by` | string | Agrupar por: `day`, `week`, `month` |

#### Ejemplo de Response (200 OK)
```json
{
  "user_id": "user_456def789",
  "timeframe": "30d",
  "statistics": {
    "message_activity": {
      "total_messages_sent": 1234,
      "total_responses_received": 1198,
      "avg_messages_per_day": 41.1,
      "most_active_day": "2025-01-10",
      "messages_most_active_day": 87
    },
    "conversation_patterns": {
      "total_conversations": 45,
      "avg_messages_per_conversation": 27.4,
      "longest_conversation_messages": 156,
      "favorite_character": "Luna",
      "character_distribution": {
        "Luna": 0.67,
        "Claude": 0.23,
        "Custom": 0.10
      }
    },
    "content_insights": {
      "total_words_typed": 23456,
      "avg_words_per_message": 19.0,
      "preferred_topics": ["technology", "creative writing", "science"],
      "communication_style": "conversational",
      "complexity_score": 0.72
    },
    "usage_costs": {
      "total_tokens_consumed": 156789,
      "estimated_total_cost": 1.17,
      "avg_cost_per_conversation": 0.026,
      "cost_trend": "decreasing"
    },
    "performance_metrics": {
      "avg_response_time_experienced": 1456,
      "satisfaction_indicators": {
        "completion_rate": 0.97,
        "long_conversations": 0.34,
        "repeat_usage": 0.89
      }
    }
  },
  "activity_timeline": [
    {
      "date": "2025-01-15",
      "messages_sent": 23,
      "responses_received": 22,
      "tokens_used": 2345,
      "conversations_active": 3
    }
  ],
  "generated_at": "2025-01-15T17:00:00.000Z"
}
```

### 3. Análisis de Uso de Tokens

Obtiene análisis detallado del uso de tokens en el sistema.

```http
GET /analytics/token-usage
```

#### Query Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `period` | string | Período de análisis |
| `group_by` | string | Agrupar por campo |
| `provider` | string | Filtrar por proveedor |
| `model` | string | Filtrar por modelo |

#### Ejemplo de Response (200 OK)
```json
{
  "analysis_period": {
    "start_date": "2025-01-01T00:00:00.000Z",
    "end_date": "2025-01-15T23:59:59.999Z",
    "duration_days": 15
  },
  "token_usage_summary": {
    "total_tokens": 2456789,
    "input_tokens": 1234567,
    "output_tokens": 1222222,
    "total_requests": 12345,
    "avg_tokens_per_request": 199.1,
    "estimated_total_cost": 18.43
  },
  "provider_breakdown": [
    {
      "provider": "lmstudio",
      "tokens_used": 2234567,
      "percentage": 91.0,
      "requests": 11234,
      "avg_tokens_per_request": 199.0,
      "cost": 16.76
    },
    {
      "provider": "openai",
      "tokens_used": 222222,
      "percentage": 9.0,
      "requests": 1111,
      "avg_tokens_per_request": 200.0,
      "cost": 1.67
    }
  ],
  "model_breakdown": [
    {
      "model": "google/gemma-3-12b",
      "provider": "lmstudio",
      "tokens_used": 2234567,
      "requests": 11234,
      "avg_response_time_ms": 1234,
      "cost": 16.76
    }
  ],
  "usage_trends": [
    {
      "date": "2025-01-15",
      "tokens": 189234,
      "requests": 987,
      "cost": 1.42
    }
  ],
  "efficiency_metrics": {
    "avg_tokens_per_minute": 234.5,
    "peak_usage_hour": "14:00-15:00",
    "context_utilization_rate": 0.72,
    "response_quality_score": 0.89
  }
}
```

## 🔍 Endpoints de Búsqueda

### 1. Búsqueda de Mensajes

Realiza búsqueda de texto en mensajes.

```http
GET /search/messages
```

#### Query Parameters
| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `q` | string | Término de búsqueda |
| `user_id` | string | Filtrar por usuario |
| `conversation_id` | string | Filtrar por conversación |
| `role` | string | Filtrar por rol |
| `start_date` | datetime | Desde fecha |
| `end_date` | datetime | Hasta fecha |
| `limit` | int | Resultados por página |
| `offset` | int | Desplazamiento |

#### Ejemplo de Response (200 OK)
```json
{
  "query": "quantum computing",
  "results": [
    {
      "message_id": "msg_search_001",
      "conversation_id": "conv_abc123",
      "content_snippet": "...Quantum computing is a revolutionary technology that...",
      "match_score": 0.95,
      "match_highlights": [
        {
          "field": "content",
          "highlights": ["<mark>quantum computing</mark>"]
        }
      ],
      "created_at": "2025-01-15T10:30:00.123Z",
      "role": "assistant",
      "context": {
        "previous_message": "Can you explain quantum computing?",
        "next_message": "That's very interesting! Tell me more..."
      }
    }
  ],
  "pagination": {
    "total_results": 156,
    "current_page": 1,
    "total_pages": 16,
    "has_next": true,
    "limit": 10,
    "offset": 0
  },
  "search_metadata": {
    "search_time_ms": 45,
    "total_documents_searched": 2456789,
    "filters_applied": ["date_range"],
    "suggestions": ["quantum mechanics", "quantum algorithms"]
  }
}
```

### 2. Búsqueda Avanzada

Realiza búsqueda avanzada con múltiples filtros y criterios.

```http
POST /search/advanced
```

#### Request Body
```json
{
  "query": {
    "text": "artificial intelligence",
    "fields": ["content.text", "custom_metadata.topics"],
    "operator": "AND"
  },
  "filters": {
    "user_id": "user_456def789",
    "role": ["user", "assistant"],
    "date_range": {
      "start": "2025-01-01T00:00:00.000Z",
      "end": "2025-01-15T23:59:59.999Z"
    },
    "token_range": {
      "min": 50,
      "max": 500
    },
    "metadata_filters": {
      "custom_metadata.topics": ["technology", "ai"],
      "llm_metadata.provider": "lmstudio"
    }
  },
  "sorting": {
    "field": "timestamps.created_at",
    "order": "desc"
  },
  "aggregations": {
    "by_conversation": true,
    "by_date": "day",
    "by_topics": true
  },
  "options": {
    "include_context": true,
    "highlight_matches": true,
    "max_results": 100
  }
}
```

#### Ejemplo de Response (200 OK)
```json
{
  "results": [
    {
      "message_id": "msg_adv_001",
      "score": 0.92,
      "content": {
        "text": "Artificial intelligence has transformed how we...",
        "highlighted": "Artificial <mark>intelligence</mark> has transformed..."
      },
      "metadata": {
        "conversation_id": "conv_xyz789",
        "created_at": "2025-01-15T14:30:00.123Z",
        "token_count": 234
      },
      "context": {
        "conversation_title": "AI Discussion",
        "surrounding_messages": 3
      }
    }
  ],
  "aggregations": {
    "by_conversation": {
      "conv_xyz789": 12,
      "conv_abc123": 8,
      "conv_def456": 5
    },
    "by_date": {
      "2025-01-15": 15,
      "2025-01-14": 8,
      "2025-01-13": 2
    },
    "by_topics": {
      "artificial intelligence": 18,
      "machine learning": 12,
      "technology": 25
    }
  },
  "statistics": {
    "total_matches": 25,
    "search_time_ms": 127,
    "filters_applied": 6,
    "relevance_threshold": 0.7
  }
}
```

## 🛠️ Endpoints de Administración

### 1. Health Check

Verifica el estado del servicio y dependencias.

```http
GET /health
```

#### Ejemplo de Response (200 OK)
```json
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
      "memory_usage": "45MB",
      "connected_clients": 12
    },
    "auth_service": {
      "status": "reachable",
      "response_time_ms": 25
    },
    "conversation_service": {
      "status": "reachable",
      "response_time_ms": 30
    },
    "llm_service": {
      "status": "reachable",
      "response_time_ms": 120,
      "queue_size": 5
    }
  },
  "performance": {
    "avg_message_processing_time_ms": 850,
    "messages_in_queue": 12,
    "cache_hit_rate": 0.87,
    "concurrent_requests": 23,
    "memory_usage_mb": 256,
    "cpu_usage_percent": 34.5
  },
  "storage": {
    "total_messages": 2456789,
    "messages_today": 1234,
    "db_size_mb": 1234.5,
    "index_size_mb": 234.6
  }
}
```

### 2. Estado de Colas

Obtiene información sobre las colas de procesamiento.

```http
GET /admin/queue-status
```

#### Ejemplo de Response (200 OK)
```json
{
  "queues": {
    "message_processing": {
      "name": "message_processing",
      "status": "active",
      "pending_jobs": 12,
      "active_jobs": 5,
      "completed_jobs_today": 1234,
      "failed_jobs_today": 3,
      "avg_processing_time_ms": 1234,
      "oldest_pending_job_age_seconds": 45
    },
    "llm_requests": {
      "name": "llm_requests",
      "status": "active",
      "pending_jobs": 8,
      "active_jobs": 10,
      "completed_jobs_today": 987,
      "failed_jobs_today": 2,
      "avg_processing_time_ms": 2345,
      "oldest_pending_job_age_seconds": 23
    },
    "analytics_computation": {
      "name": "analytics_computation",
      "status": "active",
      "pending_jobs": 3,
      "active_jobs": 1,
      "completed_jobs_today": 45,
      "failed_jobs_today": 0,
      "avg_processing_time_ms": 5678,
      "oldest_pending_job_age_seconds": 120
    }
  },
  "workers": {
    "total_workers": 15,
    "active_workers": 14,
    "idle_workers": 1,
    "unhealthy_workers": 0,
    "worker_details": [
      {
        "worker_id": "worker_001",
        "status": "active",
        "current_job": "processing_message",
        "jobs_completed_today": 89,
        "uptime_hours": 23.5,
        "memory_usage_mb": 45.6
      }
    ]
  },
  "performance_metrics": {
    "total_throughput_per_minute": 234,
    "error_rate_percentage": 0.24,
    "avg_queue_wait_time_ms": 123,
    "queue_efficiency_score": 0.94
  },
  "alerts": [
    {
      "severity": "warning",
      "message": "Message processing queue approaching capacity",
      "threshold": 100,
      "current_value": 87,
      "suggested_action": "Consider scaling workers"
    }
  ]
}
```

### 3. Limpieza de Datos

Ejecuta tareas de limpieza de mensajes antiguos.

```http
POST /admin/cleanup
```

#### Request Body
```json
{
  "cleanup_type": "archived_messages",
  "criteria": {
    "older_than_days": 180,
    "status": ["archived"],
    "exclude_conversations": [],
    "dry_run": false
  },
  "options": {
    "batch_size": 1000,
    "max_execution_time_minutes": 30,
    "notify_on_completion": true
  }
}
```

#### Ejemplo de Response (202 Accepted)
```json
{
  "cleanup_job_id": "cleanup_20250115_170000",
  "status": "started",
  "estimated_completion": "2025-01-15T17:30:00.000Z",
  "criteria_summary": {
    "cleanup_type": "archived_messages",
    "target_age_days": 180,
    "estimated_messages_affected": 12456,
    "estimated_storage_freed_mb": 234.5
  },
  "progress": {
    "messages_processed": 0,
    "messages_deleted": 0,
    "current_batch": 0,
    "total_batches": 13,
    "percentage_complete": 0
  },
  "monitoring": {
    "progress_url": "/admin/cleanup/cleanup_20250115_170000/status",
    "cancel_url": "/admin/cleanup/cleanup_20250115_170000/cancel"
  }
}
```

## ❌ Códigos de Error

### Errores de Validación (400)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Message content exceeds maximum length",
    "details": {
      "field": "content",
      "max_length": 50000,
      "actual_length": 52345,
      "suggestion": "Consider breaking the message into smaller parts"
    },
    "request_id": "req_error_123"
  }
}
```

### Errores de Rate Limiting (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many messages sent",
    "details": {
      "limit_type": "messages_per_minute",
      "limit": 100,
      "current_count": 101,
      "reset_time": "2025-01-15T17:01:00.000Z",
      "retry_after_seconds": 60
    }
  }
}
```

### Errores de Procesamiento LLM (502)
```json
{
  "error": {
    "code": "LLM_SERVICE_ERROR",
    "message": "LLM provider temporarily unavailable",
    "details": {
      "provider": "lmstudio",
      "error_type": "timeout",
      "retry_possible": true,
      "estimated_retry_delay_seconds": 30,
      "fallback_available": true
    }
  }
}
```

### Errores de Contenido (422)
```json
{
  "error": {
    "code": "CONTENT_SAFETY_VIOLATION",
    "message": "Message content violates safety guidelines",
    "details": {
      "violations": ["inappropriate_language", "personal_information"],
      "safety_score": 0.3,
      "threshold": 0.8,
      "suggestions": [
        "Remove personal information",
        "Use more appropriate language"
      ]
    }
  }
}
```

## 📊 Rate Limiting

### Límites por Endpoint

| Endpoint | Límite | Ventana | Por |
|----------|--------|---------|-----|
| `POST /messages` | 100 req/min | Usuario | Envío de mensajes |
| `GET /messages/*` | 300 req/min | Usuario | Consulta de mensajes |
| `GET /search/*` | 60 req/min | Usuario | Búsquedas |
| `POST /llm/process` | 50 req/min | Usuario | Procesamiento LLM |
| `GET /analytics/*` | 30 req/min | Usuario | Analytics |
| `GET /health` | Sin límite | - | Health checks |

### Headers de Rate Limiting
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642251600
X-RateLimit-Type: messages_per_minute
```

Esta especificación API proporciona una interfaz completa y robusta para todas las operaciones de mensaje en el sistema, con énfasis en la escalabilidad, seguridad y facilidad de uso.