# Message Service - Database Design

Diseño completo de la base de datos MongoDB para el Message Service con enfoque en escalabilidad y performance.

## 📋 Información General

- **Database Engine**: MongoDB 6.0+
- **ODM**: Beanie (Pydantic-based)
- **Database Name**: `message_service`
- **Sharding Strategy**: Horizontal por `conversation_id`
- **Indexing Strategy**: Optimizado para consultas frecuentes

## 🗄️ Colecciones Principales

### 1. messages (Colección Principal)

Almacena todos los mensajes del sistema con metadatos completos.

#### Esquema del Documento

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "message_id": "msg_abc123def456",           // UUID único
  "conversation_id": "conv_789xyz123",        // Clave de sharding
  "user_id": "user_456def789",               
  "character_id": "char_123abc456",          
  
  // Contenido del mensaje
  "content": {
    "text": "Hello Luna! How are you today?",
    "sanitized_text": "Hello Luna! How are you today?",
    "detected_language": "en",
    "content_hash": "sha256:abc123def456...",   // Para deduplicación
    "word_count": 6,
    "character_count": 30,
    "estimated_reading_time_seconds": 2
  },
  
  // Metadatos básicos
  "role": "user",                              // user | assistant | system
  "message_type": "standard",                  // standard | template | system | error
  "status": "active",                          // active | archived | flagged | deleted
  "sequence_number": 245,                      // Orden en la conversación
  
  // Metadatos LLM (solo para mensajes de assistant)
  "llm_metadata": {
    "provider": "lmstudio",                    // lmstudio | openai | anthropic | claude
    "model": "google/gemma-3-12b",
    "model_version": "1.2.3",
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0,
    "stop_sequences": ["\\n\\nHuman:", "\\n\\nAssistant:"],
    "request_id": "req_xyz789abc123",
    "finish_reason": "stop"                    // stop | length | content_filter | error
  },
  
  // Uso de tokens
  "token_usage": {
    "prompt_tokens": 245,
    "completion_tokens": 67,
    "total_tokens": 312,
    "prompt_cost": 0.001835,
    "completion_cost": 0.000503,
    "total_cost": 0.002338,                    // USD
    "cost_currency": "USD",
    "billing_tier": "standard"
  },
  
  // Metadatos de contexto
  "context_metadata": {
    "context_window_size": 20,                 // Configurado
    "messages_in_context": 15,                 // Usado efectivamente
    "context_tokens": 2890,
    "context_hash": "sha256:def456ghi789...",  // Para cache
    "context_compression_ratio": 0.87,
    "effective_context_length": 3456           // Después de compresión
  },
  
  // Metadatos de procesamiento
  "processing_metadata": {
    "processing_time_ms": 1234,
    "queue_time_ms": 45,
    "llm_processing_time_ms": 1100,
    "post_processing_time_ms": 89,
    "total_latency_ms": 1279,
    "retry_count": 0,
    "error_count": 0,
    "worker_id": "worker_003",
    "processing_node": "message-worker-3"
  },
  
  // Metadatos de seguridad
  "safety_metadata": {
    "content_filtered": false,
    "safety_score": 0.95,                      // 0-1 (1 = completamente seguro)
    "detected_issues": [],                     // ["inappropriate_language", "personal_info"]
    "moderation_flags": [],                    // ["spam", "harassment", "hate"]
    "filter_version": "v2.1",
    "manual_review_required": false,
    "approved_by_moderator": null
  },
  
  // Timestamps
  "timestamps": {
    "created_at": ISODate("2025-01-15T10:30:00.123Z"),
    "received_at": ISODate("2025-01-15T10:30:00.098Z"),
    "queued_at": ISODate("2025-01-15T10:30:00.145Z"),
    "processing_started_at": ISODate("2025-01-15T10:30:00.190Z"),
    "processed_at": ISODate("2025-01-15T10:30:01.456Z"),
    "llm_response_at": ISODate("2025-01-15T10:30:02.556Z"),
    "completed_at": ISODate("2025-01-15T10:30:02.789Z"),
    "last_modified_at": ISODate("2025-01-15T10:30:02.789Z")
  },
  
  // Metadatos del cliente
  "client_metadata": {
    "client_msg_id": "client_msg_123",         // Para idempotencia
    "client_version": "1.2.3",
    "user_agent": "CharacterChat/1.0 (Web)",
    "ip_address": "192.168.1.100",             // Para rate limiting
    "platform": "web",                         // web | mobile | api | cli
    "session_id": "session_456def789",
    "request_headers": {
      "x-forwarded-for": "203.0.113.1",
      "user-agent": "Mozilla/5.0..."
    }
  },
  
  // Metadatos personalizados (extensibles)
  "custom_metadata": {
    "intent": "greeting",                      // greeting | question | command | creative
    "sentiment": "positive",                   // positive | neutral | negative
    "confidence": 0.87,                       // 0-1
    "topics": ["greeting", "wellbeing", "casual"],
    "urgency": "low",                         // low | medium | high | urgent
    "complexity_score": 0.23,                // 0-1
    "user_satisfaction": null,                // Will be filled later
    "follow_up_required": false,
    "tagged_by_user": [],
    "bookmarked": false,
    "shared": false
  },
  
  // Metadatos de relaciones
  "relationships": {
    "parent_message_id": null,                // Para hilos futuros
    "reply_to_message_id": null,              // Para respuestas específicas
    "related_message_ids": [],                // Mensajes relacionados
    "thread_id": null,                        // Para organización en hilos
    "conversation_branch": "main"             // main | alternative
  },
  
  // Metadatos de calidad
  "quality_metadata": {
    "coherence_score": 0.92,                 // 0-1
    "relevance_score": 0.88,                 // 0-1
    "helpfulness_score": 0.90,               // 0-1
    "factual_accuracy": null,                // Será completado por evaluadores
    "language_quality": 0.95,                // 0-1
    "creativity_score": 0.67,                // 0-1 (para respuestas creativas)
    "user_feedback": null                    // thumbs up/down, ratings, etc.
  },
  
  // Control de versiones y auditoría
  "version": 1,                              // Para versionado de esquema
  "partition_key": "conv_789xyz123",         // Para sharding (duplica conversation_id)
  "data_classification": "standard",         // standard | sensitive | confidential
  "retention_policy": "standard",            // standard | extended | permanent
  "archived_to_cold_storage": false,
  "backup_status": "backed_up",             // backed_up | pending | failed
  "checksum": "sha256:finalchecksum123"     // Para integridad de datos
}
```

### 2. message_analytics (Colección de Analytics)

Almacena agregaciones y métricas computadas para analytics rápidas.

#### Esquema del Documento

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439012"),
  "analytics_id": "analytics_conv_789xyz123_20250115",
  "conversation_id": "conv_789xyz123",
  "user_id": "user_456def789",
  "aggregation_type": "daily_summary",       // daily_summary | weekly_summary | monthly_summary
  "date": ISODate("2025-01-15T00:00:00.000Z"),
  
  // Métricas de mensajes
  "message_metrics": {
    "total_messages": 45,
    "user_messages": 23,
    "assistant_messages": 22,
    "system_messages": 0,
    "avg_message_length": 125.6,
    "total_words": 2834,
    "total_characters": 14567
  },
  
  // Métricas de tokens
  "token_metrics": {
    "total_tokens": 5678,
    "input_tokens": 2890,
    "output_tokens": 2788,
    "total_cost": 0.04256,
    "avg_tokens_per_message": 126.2,
    "max_tokens_single_message": 456,
    "token_efficiency": 0.87
  },
  
  // Métricas de rendimiento
  "performance_metrics": {
    "avg_response_time_ms": 1234,
    "min_response_time_ms": 456,
    "max_response_time_ms": 3456,
    "median_response_time_ms": 1100,
    "p95_response_time_ms": 2890,
    "total_processing_time_ms": 56789,
    "cache_hit_rate": 0.78
  },
  
  // Métricas de calidad
  "quality_metrics": {
    "avg_coherence_score": 0.89,
    "avg_relevance_score": 0.92,
    "avg_safety_score": 0.97,
    "content_filter_rate": 0.02,
    "user_satisfaction_rate": 0.88,
    "error_rate": 0.01
  },
  
  // Distribuciones
  "distributions": {
    "message_length_distribution": {
      "0-50": 12,
      "51-100": 18,
      "101-200": 10,
      "201+": 5
    },
    "response_time_distribution": {
      "0-500ms": 8,
      "501-1000ms": 15,
      "1001-2000ms": 18,
      "2001ms+": 4
    },
    "topic_distribution": {
      "technology": 0.35,
      "general": 0.25,
      "creative": 0.20,
      "technical": 0.20
    }
  },
  
  "created_at": ISODate("2025-01-16T01:00:00.000Z"),
  "updated_at": ISODate("2025-01-16T01:00:00.000Z"),
  "version": 1
}
```

### 3. message_search_index (Colección para Búsqueda)

Índice optimizado para búsquedas de texto completo.

#### Esquema del Documento

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439013"),
  "message_id": "msg_abc123def456",
  "conversation_id": "conv_789xyz123",
  "user_id": "user_456def789",
  
  // Contenido indexado
  "indexed_content": {
    "full_text": "Hello Luna! How are you today?",
    "normalized_text": "hello luna how are you today",
    "stemmed_text": "hello luna how ar you today",
    "tokens": ["hello", "luna", "how", "are", "you", "today"],
    "bigrams": ["hello luna", "luna how", "how are", "are you", "you today"],
    "trigrams": ["hello luna how", "luna how are", "how are you", "are you today"],
    "entities": [],                           // Entidades nombradas
    "keywords": ["luna", "greeting", "wellbeing"]
  },
  
  // Metadatos de búsqueda
  "search_metadata": {
    "language": "en",
    "sentiment": "positive",
    "topics": ["greeting", "wellbeing"],
    "intent": "greeting",
    "role": "user",
    "message_type": "standard"
  },
  
  // Pesos para ranking
  "search_weights": {
    "importance_score": 0.85,               // Basado en respuesta del usuario
    "recency_score": 0.92,                  // Más reciente = mayor peso
    "engagement_score": 0.78,               // Basado en interacción posterior
    "quality_score": 0.90                   // Basado en métricas de calidad
  },
  
  "created_at": ISODate("2025-01-15T10:30:00.123Z"),
  "last_indexed_at": ISODate("2025-01-15T10:30:05.000Z"),
  "index_version": "v2.1"
}
```

### 4. processing_queue (Colección de Cola)

Gestiona la cola de mensajes para procesamiento asíncrono.

#### Esquema del Documento

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439014"),
  "job_id": "job_abc123def456",
  "message_id": "msg_abc123def456",
  "conversation_id": "conv_789xyz123",
  "user_id": "user_456def789",
  
  // Tipo de trabajo
  "job_type": "message_processing",          // message_processing | llm_generation | analytics_computation
  "priority": "normal",                      // low | normal | high | urgent
  "status": "pending",                       // pending | processing | completed | failed | cancelled
  
  // Configuración del trabajo
  "job_config": {
    "llm_provider": "lmstudio",
    "model": "google/gemma-3-12b",
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_window_size": 20,
    "timeout_seconds": 60
  },
  
  // Progreso y resultados
  "execution": {
    "attempts": 1,
    "max_attempts": 3,
    "worker_id": null,
    "started_at": null,
    "completed_at": null,
    "processing_time_ms": null,
    "error_message": null,
    "result": null
  },
  
  // Metadatos de cola
  "queue_metadata": {
    "queue_name": "message_processing",
    "scheduled_for": ISODate("2025-01-15T10:30:00.123Z"),
    "expires_at": ISODate("2025-01-15T11:30:00.123Z"),
    "retry_after": null,
    "depends_on": []                          // IDs de trabajos prerequisitos
  },
  
  "created_at": ISODate("2025-01-15T10:30:00.123Z"),
  "updated_at": ISODate("2025-01-15T10:30:00.123Z")
}
```

## 🔍 Estrategia de Índices

### Índices de la Colección `messages`

```javascript
// Índice único para message_id
db.messages.createIndex(
  { "message_id": 1 },
  { 
    unique: true,
    name: "idx_message_id_unique"
  }
)

// Índice principal para consultas por conversación
db.messages.createIndex(
  { 
    "conversation_id": 1,
    "sequence_number": 1
  },
  { 
    name: "idx_conversation_sequence",
    background: true
  }
)

// Índice para consultas por usuario
db.messages.createIndex(
  {
    "user_id": 1,
    "timestamps.created_at": -1
  },
  {
    name: "idx_user_chronological",
    background: true
  }
)

// Índice para paginación temporal
db.messages.createIndex(
  {
    "timestamps.created_at": -1,
    "_id": 1
  },
  {
    name: "idx_temporal_pagination",
    background: true
  }
)

// Índice para búsquedas por rol y tipo
db.messages.createIndex(
  {
    "conversation_id": 1,
    "role": 1,
    "message_type": 1,
    "status": 1
  },
  {
    name: "idx_conversation_filtering",
    background: true
  }
)

// Índice para analytics de tokens
db.messages.createIndex(
  {
    "user_id": 1,
    "llm_metadata.provider": 1,
    "llm_metadata.model": 1,
    "timestamps.created_at": -1
  },
  {
    name: "idx_token_analytics",
    background: true,
    partialFilterExpression: {
      "token_usage.total_tokens": { $exists: true }
    }
  }
)

// Índice para búsqueda de texto completo
db.messages.createIndex(
  {
    "content.text": "text",
    "custom_metadata.topics": "text",
    "custom_metadata.intent": "text"
  },
  {
    name: "idx_full_text_search",
    background: true,
    weights: {
      "content.text": 10,
      "custom_metadata.topics": 5,
      "custom_metadata.intent": 3
    }
  }
)

// Índice para limpieza automática (TTL)
db.messages.createIndex(
  { "timestamps.created_at": 1 },
  {
    name: "idx_message_ttl",
    expireAfterSeconds: 63072000,  // 2 años
    partialFilterExpression: {
      "status": "archived",
      "retention_policy": "standard"
    }
  }
)

// Índice para sharding
db.messages.createIndex(
  { "conversation_id": "hashed" },
  {
    name: "idx_shard_key",
    background: true
  }
)

// Índice para deduplicación
db.messages.createIndex(
  {
    "content.content_hash": 1,
    "conversation_id": 1,
    "user_id": 1
  },
  {
    name: "idx_deduplication",
    background: true,
    sparse: true
  }
)

// Índice para consultas de rendimiento
db.messages.createIndex(
  {
    "processing_metadata.worker_id": 1,
    "timestamps.created_at": -1
  },
  {
    name: "idx_worker_performance",
    background: true,
    sparse: true
  }
)

// Índice para auditoría de seguridad
db.messages.createIndex(
  {
    "safety_metadata.content_filtered": 1,
    "safety_metadata.manual_review_required": 1,
    "timestamps.created_at": -1
  },
  {
    name: "idx_safety_audit",
    background: true
  }
)
```

### Índices de la Colección `message_analytics`

```javascript
// Índice para consultas de analytics por conversación
db.message_analytics.createIndex(
  {
    "conversation_id": 1,
    "aggregation_type": 1,
    "date": -1
  },
  {
    name: "idx_conversation_analytics",
    background: true
  }
)

// Índice para analytics por usuario
db.message_analytics.createIndex(
  {
    "user_id": 1,
    "aggregation_type": 1,
    "date": -1
  },
  {
    name: "idx_user_analytics",
    background: true
  }
)

// Índice para analytics globales
db.message_analytics.createIndex(
  {
    "aggregation_type": 1,
    "date": -1
  },
  {
    name: "idx_global_analytics",
    background: true
  }
)

// TTL para analytics antiguos
db.message_analytics.createIndex(
  { "created_at": 1 },
  {
    name: "idx_analytics_ttl",
    expireAfterSeconds: 15768000  // 6 meses
  }
)
```

### Índices de la Colección `message_search_index`

```javascript
// Índice para búsqueda por mensaje
db.message_search_index.createIndex(
  { "message_id": 1 },
  {
    name: "idx_search_message_id",
    unique: true
  }
)

// Índice de texto completo optimizado
db.message_search_index.createIndex(
  {
    "indexed_content.full_text": "text",
    "indexed_content.tokens": "text",
    "search_metadata.topics": "text"
  },
  {
    name: "idx_optimized_text_search",
    weights: {
      "indexed_content.full_text": 10,
      "indexed_content.tokens": 7,
      "search_metadata.topics": 5
    }
  }
)

// Índice para ranking de búsqueda
db.message_search_index.createIndex(
  {
    "search_weights.importance_score": -1,
    "search_weights.recency_score": -1,
    "search_weights.quality_score": -1
  },
  {
    name: "idx_search_ranking",
    background: true
  }
)
```

### Índices de la Colección `processing_queue`

```javascript
// Índice para procesamiento de cola
db.processing_queue.createIndex(
  {
    "status": 1,
    "priority": -1,
    "queue_metadata.scheduled_for": 1
  },
  {
    name: "idx_queue_processing",
    background: true
  }
)

// Índice para trabajos por mensaje
db.processing_queue.createIndex(
  { "message_id": 1 },
  {
    name: "idx_queue_message",
    background: true
  }
)

// TTL para trabajos completados
db.processing_queue.createIndex(
  { "updated_at": 1 },
  {
    name: "idx_queue_ttl",
    expireAfterSeconds: 604800,  // 7 días
    partialFilterExpression: {
      "status": { $in: ["completed", "failed", "cancelled"] }
    }
  }
)
```

## 🔄 Estrategia de Sharding

### Configuración de Sharding

```javascript
// Habilitar sharding en la base de datos
sh.enableSharding("message_service")

// Configurar sharding en la colección principal
sh.shardCollection(
  "message_service.messages",
  { "conversation_id": "hashed" }
)

// Sharding para analytics
sh.shardCollection(
  "message_service.message_analytics",
  { "conversation_id": "hashed", "date": 1 }
)

// Sharding para búsqueda
sh.shardCollection(
  "message_service.message_search_index",
  { "conversation_id": "hashed" }
)
```

### Beneficios del Sharding por `conversation_id`

1. **Localidad de Datos**: Todos los mensajes de una conversación están en el mismo shard
2. **Consultas Eficientes**: Las consultas por conversación son locales a un shard
3. **Escalabilidad Horizontal**: Distribución uniforme con hash
4. **Operaciones Atómicas**: Transacciones por conversación en un solo shard

## 💾 Patrones de Consulta Optimizados

### 1. Obtener Mensajes de Conversación (Más Frecuente)

```javascript
// Query optimizada con projection
db.messages.find(
  {
    "conversation_id": "conv_789xyz123",
    "status": "active"
  },
  {
    "message_id": 1,
    "content.text": 1,
    "role": 1,
    "timestamps.created_at": 1,
    "sequence_number": 1
  }
).sort({
  "sequence_number": 1
}).limit(50)

// Usa índice: idx_conversation_sequence
```

### 2. Paginación Temporal de Mensajes

```javascript
// Cursor-based pagination
db.messages.find(
  {
    "user_id": "user_456def789",
    "timestamps.created_at": { $lt: ISODate("2025-01-15T10:30:00.123Z") }
  }
).sort({
  "timestamps.created_at": -1
}).limit(20)

// Usa índice: idx_user_chronological
```

### 3. Búsqueda de Texto Completo

```javascript
// Búsqueda con scoring
db.messages.find(
  {
    $text: { $search: "quantum computing" },
    "user_id": "user_456def789",
    "timestamps.created_at": {
      $gte: ISODate("2025-01-01T00:00:00.000Z")
    }
  },
  {
    score: { $meta: "textScore" }
  }
).sort({
  score: { $meta: "textScore" }
}).limit(10)

// Usa índice: idx_full_text_search
```

### 4. Analytics de Tokens por Usuario

```javascript
// Aggregation pipeline para analytics
db.messages.aggregate([
  {
    $match: {
      "user_id": "user_456def789",
      "timestamps.created_at": {
        $gte: ISODate("2025-01-01T00:00:00.000Z")
      },
      "token_usage.total_tokens": { $exists: true }
    }
  },
  {
    $group: {
      "_id": {
        "provider": "$llm_metadata.provider",
        "model": "$llm_metadata.model"
      },
      "total_tokens": { $sum: "$token_usage.total_tokens" },
      "total_cost": { $sum: "$token_usage.total_cost" },
      "message_count": { $sum: 1 },
      "avg_tokens": { $avg: "$token_usage.total_tokens" }
    }
  },
  {
    $sort: { "total_tokens": -1 }
  }
])

// Usa índice: idx_token_analytics
```

### 5. Detección de Duplicados

```javascript
// Encontrar mensajes duplicados por hash de contenido
db.messages.find({
  "content.content_hash": "sha256:abc123def456...",
  "conversation_id": "conv_789xyz123"
}).limit(1)

// Usa índice: idx_deduplication
```

## 🗂️ Estrategia de Particionamiento por Tiempo

### Colecciones Particionadas por Mes

```javascript
// Crear colecciones mensuales para datos históricos
// messages_202501, messages_202502, etc.

// Router view para abstracción
db.createView(
  "messages_current",
  "messages_202501",
  []
)

// Script de rotación mensual
function rotateMonthlyCollections() {
  const currentMonth = new Date().toISOString().slice(0, 7).replace('-', '');
  const newCollectionName = `messages_${currentMonth}`;
  
  // Crear nueva colección para el mes actual
  db.createCollection(newCollectionName);
  
  // Aplicar índices a la nueva colección
  applyIndexesToCollection(newCollectionName);
  
  // Actualizar la view
  db.runCommand({
    collMod: "messages_current",
    viewOn: newCollectionName,
    pipeline: []
  });
}
```

## 🔧 Optimizaciones de Rendimiento

### 1. Configuración de Connection Pool

```javascript
// Configuración optimizada de MongoDB
const client = new MongoClient(uri, {
  minPoolSize: 20,                    // Mínimo de conexiones
  maxPoolSize: 100,                   // Máximo de conexiones
  maxIdleTimeMS: 30000,              // Tiempo máximo idle
  serverSelectionTimeoutMS: 5000,     // Timeout de selección de servidor
  socketTimeoutMS: 45000,            // Timeout de socket
  family: 4,                         // Usar IPv4
  keepAlive: true,
  keepAliveInitialDelay: 300000,
  compression: "zstd"                // Compresión de datos
});
```

### 2. Configuración de Índices para Hot Data

```javascript
// Índices con hint para datos frecuentemente accedidos
db.messages.createIndex(
  {
    "conversation_id": 1,
    "timestamps.created_at": -1
  },
  {
    name: "idx_hot_conversation_data",
    background: true,
    // Mantener en memoria para consultas frecuentes
    storageEngine: {
      wiredTiger: {
        configString: "block_compressor=zstd"
      }
    }
  }
)
```

### 3. Agregaciones Precomputadas

```javascript
// Materializar vistas para analytics frecuentes
db.createView(
  "daily_message_stats",
  "messages",
  [
    {
      $match: {
        "timestamps.created_at": {
          $gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000)
        }
      }
    },
    {
      $group: {
        "_id": {
          $dateToString: {
            format: "%Y-%m-%d",
            date: "$timestamps.created_at"
          }
        },
        "total_messages": { $sum: 1 },
        "total_tokens": { $sum: "$token_usage.total_tokens" },
        "total_cost": { $sum: "$token_usage.total_cost" },
        "unique_users": { $addToSet: "$user_id" },
        "unique_conversations": { $addToSet: "$conversation_id" }
      }
    }
  ]
)
```

## 🔒 Configuración de Seguridad

### 1. Validación de Esquema

```javascript
// Validator para colección messages
db.runCommand({
  collMod: "messages",
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["message_id", "conversation_id", "user_id", "content", "role", "timestamps"],
      properties: {
        message_id: {
          bsonType: "string",
          pattern: "^msg_[a-zA-Z0-9]{12,}$"
        },
        conversation_id: {
          bsonType: "string",
          pattern: "^conv_[a-zA-Z0-9]{12,}$"
        },
        user_id: {
          bsonType: "string",
          pattern: "^user_[a-zA-Z0-9]{12,}$"
        },
        content: {
          bsonType: "object",
          required: ["text"],
          properties: {
            text: {
              bsonType: "string",
              maxLength: 50000
            },
            word_count: {
              bsonType: "int",
              minimum: 0
            }
          }
        },
        role: {
          enum: ["user", "assistant", "system"]
        },
        status: {
          enum: ["active", "archived", "flagged", "deleted"]
        },
        token_usage: {
          bsonType: "object",
          properties: {
            total_tokens: {
              bsonType: "int",
              minimum: 0
            },
            total_cost: {
              bsonType: "double",
              minimum: 0
            }
          }
        }
      }
    }
  },
  validationLevel: "strict",
  validationAction: "error"
})
```

### 2. Configuración de Auditoría

```javascript
// Configuración de auditoría para operaciones sensibles
db.adminCommand({
  setFeatureCompatibilityVersion: "6.0"
})

// Habilitar auditoría
db.adminCommand({
  setParameter: 1,
  auditDestination: "file",
  auditPath: "/var/log/mongodb/audit.json",
  auditFilter: {
    atype: {
      $in: [
        "insert", "update", "delete",
        "createCollection", "dropCollection",
        "createIndex", "dropIndex"
      ]
    },
    "param.ns": {
      $regex: "^message_service\\."
    }
  }
})
```

## 📊 Monitoring y Métricas

### 1. Métricas de Performance

```javascript
// Queries lentas (>100ms)
db.setProfilingLevel(2, { slowms: 100 })

// Métricas de colección
db.runCommand({ collStats: "messages" })

// Métricas de índices
db.messages.getIndexes().forEach(function(index) {
  print("Index: " + index.name);
  print("Usage: " + db.runCommand({ 
    indexStats: "messages" 
  }).indexStats[index.name]);
})
```

### 2. Alertas Automatizadas

```javascript
// Script para monitoreo automático
function checkDatabaseHealth() {
  const stats = db.runCommand({ dbStats: 1 });
  const alerts = [];
  
  // Verificar tamaño de base de datos
  if (stats.dataSize > 100 * 1024 * 1024 * 1024) { // 100GB
    alerts.push("Database size exceeds 100GB");
  }
  
  // Verificar performance de índices
  const slowQueries = db.system.profile.find({
    millis: { $gt: 1000 }
  }).count();
  
  if (slowQueries > 10) {
    alerts.push("High number of slow queries detected");
  }
  
  // Verificar espacio en disco
  const diskUsage = db.runCommand({ hostInfo: 1 }).system.memSizeMB;
  if (diskUsage > 80) {
    alerts.push("High memory usage detected");
  }
  
  return alerts;
}
```

## 🔄 Estrategia de Backup y Recuperación

### 1. Backup Incremental

```bash
#!/bin/bash
# Script de backup incremental diario

DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/message_service"

# Backup completo semanal
if [ $(date +%u) -eq 1 ]; then
  mongodump \
    --host="mongodb-cluster" \
    --db="message_service" \
    --out="$BACKUP_DIR/full_$DATE"
else
  # Backup incremental usando oplog
  mongodump \
    --host="mongodb-cluster" \
    --db="message_service" \
    --oplog \
    --out="$BACKUP_DIR/incr_$DATE"
fi

# Comprimir backup
tar -czf "$BACKUP_DIR/backup_$DATE.tar.gz" \
  "$BACKUP_DIR/*_$DATE"

# Limpiar backups antiguos (>30 días)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### 2. Point-in-Time Recovery

```bash
#!/bin/bash
# Script de recuperación point-in-time

RESTORE_TIME="2025-01-15T10:30:00.000Z"
BACKUP_DIR="/backup/message_service"

# Restaurar último backup completo anterior al tiempo objetivo
FULL_BACKUP=$(find "$BACKUP_DIR" -name "full_*.tar.gz" | sort -r | head -1)

# Extraer y restaurar
tar -xzf "$FULL_BACKUP" -C /tmp/restore/
mongorestore \
  --host="mongodb-cluster" \
  --db="message_service_restore" \
  --oplogReplay \
  --oplogLimit="$(date -d "$RESTORE_TIME" +%s):1" \
  /tmp/restore/
```

## 🧹 Estrategia de Limpieza de Datos

### 1. Limpieza Automática por TTL

```javascript
// Los índices TTL se encargan de la limpieza automática
// Ver índices definidos anteriormente con expireAfterSeconds
```

### 2. Limpieza Manual Programada

```javascript
// Script de limpieza mensual
function monthlyCleanup() {
  const cutoffDate = new Date();
  cutoffDate.setFullYear(cutoffDate.getFullYear() - 2);
  
  // Archivar mensajes antiguos
  db.messages.updateMany(
    {
      "timestamps.created_at": { $lt: cutoffDate },
      "status": "active",
      "retention_policy": "standard"
    },
    {
      $set: {
        "status": "archived",
        "archived_to_cold_storage": true,
        "timestamps.archived_at": new Date()
      }
    }
  );
  
  // Limpiar analytics antiguos
  db.message_analytics.deleteMany({
    "date": { $lt: cutoffDate },
    "aggregation_type": "daily_summary"
  });
  
  // Limpiar cola de trabajos antiguos
  db.processing_queue.deleteMany({
    "status": { $in: ["completed", "failed"] },
    "updated_at": { 
      $lt: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000) 
    }
  });
}
```

Este diseño de base de datos proporciona una base sólida, escalable y eficiente para el Message Service, optimizado para high-throughput y consultas complejas mientras mantiene la integridad y seguridad de los datos.