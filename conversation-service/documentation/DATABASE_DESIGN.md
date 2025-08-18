# Conversation Service - Database Design

Diseño completo de la base de datos MongoDB para el Conversation Service.

## 📋 Información General

- **Database Engine**: MongoDB 5.0+
- **ODM**: Beanie (Pydantic-based)
- **Database Name**: `conversation_service`
- **Connection**: Independiente del monolito original

## 🗄️ Colecciones

### conversations

Colección principal que almacena todas las conversaciones del sistema.

#### Esquema del Documento

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "user_id": "507f1f77bcf86cd799439012",
  "character_id": "507f1f77bcf86cd799439013", 
  "title": "Chat with Luna about philosophy",
  "status": "active",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_window": 4000,
    "stop_sequences": ["\\n\\nHuman:", "\\n\\nAssistant:"],
    "top_p": 0.9,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
  },
  "metadata": {
    "message_count": 15,
    "last_activity": ISODate("2025-01-15T14:30:00.123Z"),
    "total_tokens": 1250,
    "total_input_tokens": 600,
    "total_output_tokens": 650,
    "created_at": ISODate("2025-01-15T10:00:00.000Z"),
    "updated_at": ISODate("2025-01-15T14:30:00.123Z"),
    "first_message_at": ISODate("2025-01-15T10:05:00.000Z"),
    "last_message_at": ISODate("2025-01-15T14:30:00.123Z")
  },
  "tags": ["philosophy", "deep-talk", "personal"],
  "is_archived": false,
  "archived_at": null,
  "version": 1
}
```

#### Campos Detallados

| Campo | Tipo | Descripción | Constraints |
|-------|------|-------------|-------------|
| `_id` | ObjectId | Identificador único de la conversación | Auto-generado |
| `user_id` | String | ID del usuario propietario | Requerido, índice |
| `character_id` | String | ID del personaje asociado | Requerido, validado con Characters Service |
| `title` | String | Título de la conversación | Máximo 200 caracteres |
| `status` | String | Estado de la conversación | Enum: `active`, `archived`, `deleted` |
| `settings` | Object | Configuraciones del LLM | Ver schema settings |
| `metadata` | Object | Metadatos y estadísticas | Ver schema metadata |
| `tags` | Array[String] | Etiquetas para organización | Máximo 10 tags, 50 chars c/u |
| `is_archived` | Boolean | Flag de archivado rápido | Default: false |
| `archived_at` | Date | Timestamp de archivado | Null si no está archivado |
| `version` | Integer | Versión del documento | Control de concurrencia |

#### Schema Settings

```javascript
"settings": {
  "temperature": {
    "type": "number",
    "minimum": 0.0,
    "maximum": 2.0,
    "default": 0.7
  },
  "max_tokens": {
    "type": "integer", 
    "minimum": 1,
    "maximum": 4096,
    "default": 2048
  },
  "context_window": {
    "type": "integer",
    "minimum": 1,
    "maximum": 8192, 
    "default": 4000
  },
  "stop_sequences": {
    "type": "array",
    "items": {"type": "string"},
    "maxItems": 10
  },
  "top_p": {
    "type": "number",
    "minimum": 0.0,
    "maximum": 1.0,
    "default": 0.9
  },
  "frequency_penalty": {
    "type": "number",
    "minimum": -2.0,
    "maximum": 2.0,
    "default": 0.0
  },
  "presence_penalty": {
    "type": "number",
    "minimum": -2.0,
    "maximum": 2.0,
    "default": 0.0
  }
}
```

#### Schema Metadata

```javascript
"metadata": {
  "message_count": {
    "type": "integer",
    "minimum": 0,
    "default": 0
  },
  "last_activity": {
    "type": "date",
    "description": "Última actividad en la conversación"
  },
  "total_tokens": {
    "type": "integer",
    "minimum": 0,
    "default": 0
  },
  "total_input_tokens": {
    "type": "integer", 
    "minimum": 0,
    "default": 0
  },
  "total_output_tokens": {
    "type": "integer",
    "minimum": 0, 
    "default": 0
  },
  "created_at": {
    "type": "date",
    "required": true
  },
  "updated_at": {
    "type": "date",
    "required": true
  },
  "first_message_at": {
    "type": "date",
    "description": "Timestamp del primer mensaje"
  },
  "last_message_at": {
    "type": "date", 
    "description": "Timestamp del último mensaje"
  }
}
```

## 🔍 Índices

### Índices Primarios

```javascript
// Índice único en _id (automático)
db.conversations.createIndex({ "_id": 1 })

// Índice compuesto para consultas del usuario
db.conversations.createIndex({ 
  "user_id": 1, 
  "status": 1, 
  "metadata.last_activity": -1 
})

// Índice para búsquedas por usuario y estado
db.conversations.createIndex({ 
  "user_id": 1, 
  "is_archived": 1 
})
```

### Índices Secundarios

```javascript
// Índice para filtros por personaje
db.conversations.createIndex({ 
  "character_id": 1, 
  "user_id": 1 
})

// Índice para búsquedas de texto en título
db.conversations.createIndex({ 
  "title": "text",
  "tags": "text" 
})

// Índice para ordenamiento temporal
db.conversations.createIndex({ 
  "metadata.created_at": -1 
})

// Índice para estadísticas
db.conversations.createIndex({ 
  "user_id": 1,
  "metadata.last_activity": -1 
})

// Índice TTL para limpieza automática de conversaciones eliminadas
db.conversations.createIndex(
  { "archived_at": 1 },
  { 
    expireAfterSeconds: 7776000, // 90 días
    partialFilterExpression: { "status": "deleted" }
  }
)
```

### Estrategia de Índices

1. **Consultas del Usuario**: Optimizadas para `user_id` + filtros comunes
2. **Paginación**: Soporta cursor-based pagination eficientemente
3. **Búsqueda de Texto**: Índice de texto para búsquedas en título y tags
4. **TTL**: Limpieza automática de conversaciones eliminadas

## 📊 Patrones de Consulta

### 1. Listar Conversaciones del Usuario

```javascript
// Query básica con paginación
db.conversations.find({
  "user_id": "507f1f77bcf86cd799439012",
  "status": "active"
}).sort({
  "metadata.last_activity": -1
}).limit(20)

// Query con cursor pagination
db.conversations.find({
  "user_id": "507f1f77bcf86cd799439012", 
  "status": "active",
  "_id": { "$lt": ObjectId("507f1f77bcf86cd799439011") }
}).sort({
  "_id": -1
}).limit(20)
```

### 2. Búsqueda por Título

```javascript
db.conversations.find({
  "user_id": "507f1f77bcf86cd799439012",
  "$text": { "$search": "philosophy" },
  "status": { "$ne": "deleted" }
}).sort({
  "score": { "$meta": "textScore" }
})
```

### 3. Filtrar por Personaje

```javascript
db.conversations.find({
  "user_id": "507f1f77bcf86cd799439012",
  "character_id": "507f1f77bcf86cd799439013",
  "is_archived": false
}).sort({
  "metadata.last_activity": -1
})
```

### 4. Estadísticas del Usuario

```javascript
// Aggregation pipeline para estadísticas
db.conversations.aggregate([
  {
    "$match": {
      "user_id": "507f1f77bcf86cd799439012"
    }
  },
  {
    "$group": {
      "_id": "$status",
      "count": { "$sum": 1 },
      "total_messages": { "$sum": "$metadata.message_count" },
      "total_tokens": { "$sum": "$metadata.total_tokens" }
    }
  }
])
```

### 5. Conversaciones Recientes

```javascript
db.conversations.find({
  "user_id": "507f1f77bcf86cd799439012",
  "metadata.last_activity": {
    "$gte": ISODate("2025-01-08T00:00:00.000Z")
  }
}).sort({
  "metadata.last_activity": -1
})
```

## 🔄 Operaciones CRUD

### Create (Inserción)

```javascript
db.conversations.insertOne({
  "user_id": "507f1f77bcf86cd799439012",
  "character_id": "507f1f77bcf86cd799439013",
  "title": "Nueva conversación",
  "status": "active",
  "settings": {
    "temperature": 0.7,
    "max_tokens": 2048,
    "context_window": 4000
  },
  "metadata": {
    "message_count": 0,
    "last_activity": new Date(),
    "total_tokens": 0,
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "created_at": new Date(),
    "updated_at": new Date()
  },
  "tags": [],
  "is_archived": false,
  "archived_at": null,
  "version": 1
})
```

### Read (Consulta)

```javascript
db.conversations.findOne({
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "user_id": "507f1f77bcf86cd799439012"
})
```

### Update (Actualización)

```javascript
db.conversations.updateOne(
  {
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "user_id": "507f1f77bcf86cd799439012",
    "version": 1
  },
  {
    "$set": {
      "title": "Título actualizado",
      "metadata.updated_at": new Date(),
      "version": 2
    },
    "$addToSet": {
      "tags": { "$each": ["nuevo-tag"] }
    }
  }
)
```

### Archive (Archivado)

```javascript
db.conversations.updateOne(
  {
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "user_id": "507f1f77bcf86cd799439012"
  },
  {
    "$set": {
      "status": "archived",
      "is_archived": true,
      "archived_at": new Date(),
      "metadata.updated_at": new Date()
    }
  }
)
```

### Restore (Restauración)

```javascript
db.conversations.updateOne(
  {
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "user_id": "507f1f77bcf86cd799439012",
    "status": "archived"
  },
  {
    "$set": {
      "status": "active",
      "is_archived": false,
      "metadata.updated_at": new Date()
    },
    "$unset": {
      "archived_at": ""
    }
  }
)
```

## 🔐 Validación y Constraints

### Document Validation Schema

```javascript
db.createCollection("conversations", {
  validator: {
    "$jsonSchema": {
      "bsonType": "object",
      "required": ["user_id", "character_id", "status", "metadata"],
      "properties": {
        "user_id": {
          "bsonType": "string",
          "pattern": "^[a-f\\d]{24}$"
        },
        "character_id": {
          "bsonType": "string", 
          "pattern": "^[a-f\\d]{24}$"
        },
        "title": {
          "bsonType": "string",
          "maxLength": 200
        },
        "status": {
          "enum": ["active", "archived", "deleted"]
        },
        "settings": {
          "bsonType": "object",
          "properties": {
            "temperature": {
              "bsonType": "number",
              "minimum": 0.0,
              "maximum": 2.0
            },
            "max_tokens": {
              "bsonType": "int",
              "minimum": 1,
              "maximum": 4096
            }
          }
        },
        "tags": {
          "bsonType": "array",
          "maxItems": 10,
          "items": {
            "bsonType": "string",
            "maxLength": 50
          }
        },
        "is_archived": {
          "bsonType": "bool"
        },
        "version": {
          "bsonType": "int",
          "minimum": 1
        }
      }
    }
  }
})
```

## 📈 Optimización y Rendimiento

### Estrategias de Optimización

1. **Compound Indexes**: Índices compuestos para consultas frecuentes
2. **Projection**: Limitar campos retornados en consultas
3. **Pagination**: Cursor-based pagination para eficiencia
4. **Connection Pooling**: Pool de conexiones MongoDB
5. **Read Preference**: Secondary reads para consultas de solo lectura

### Proyecciones Optimizadas

```javascript
// Lista de conversaciones (vista reducida)
db.conversations.find(
  { "user_id": "507f1f77bcf86cd799439012" },
  {
    "title": 1,
    "character_id": 1,
    "status": 1,
    "metadata.last_activity": 1,
    "metadata.message_count": 1,
    "tags": 1,
    "is_archived": 1
  }
)

// Estadísticas solamente
db.conversations.find(
  { "user_id": "507f1f77bcf86cd799439012" },
  {
    "metadata": 1,
    "status": 1
  }
)
```

### Consideraciones de Escala

1. **Sharding**: Por `user_id` para distribución horizontal
2. **Archivado**: TTL automático para datos antiguos
3. **Compresión**: WiredTiger compression para optimizar almacenamiento
4. **Monitoring**: Índices en slow query log

## 🔄 Migración de Datos

### Scripts de Migración

```javascript
// Migración desde monolito
// 1. Extraer conversaciones existentes
db.conversations.find({}).forEach(function(doc) {
  // Transformar estructura si es necesario
  var newDoc = {
    "_id": doc._id,
    "user_id": doc.user_id,
    "character_id": doc.character_id,
    "title": doc.title || "Untitled Conversation",
    "status": doc.is_archived ? "archived" : "active",
    "settings": doc.settings || defaultSettings,
    "metadata": {
      "message_count": doc.message_count || 0,
      "last_activity": doc.updated_at,
      "total_tokens": doc.total_tokens || 0,
      "created_at": doc.created_at,
      "updated_at": doc.updated_at
    },
    "tags": doc.tags || [],
    "is_archived": doc.is_archived || false,
    "version": 1
  };
  
  // Insertar en nueva base de datos
  db.conversations.insertOne(newDoc);
});
```

### Validación Post-Migración

```javascript
// Verificar integridad de datos
var totalOld = db.legacy_conversations.count();
var totalNew = db.conversations.count();
print("Migrated " + totalNew + " of " + totalOld + " conversations");

// Verificar índices
db.conversations.getIndexes().forEach(printjson);
```

## 🛡️ Backup y Recuperación

### Estrategia de Backup

```bash
# Backup completo de la base de datos
mongodump --host localhost:27017 --db conversation_service --out /backup/$(date +%Y%m%d)

# Backup incremental (usando oplog)
mongodump --host localhost:27017 --oplog --out /backup/incremental/$(date +%Y%m%d_%H%M%S)

# Restauración
mongorestore --host localhost:27017 --db conversation_service /backup/20250115
```

### Point-in-Time Recovery

```bash
# Usar replica set para point-in-time recovery
mongorestore --host localhost:27017 --oplogReplay --oplogLimit 1642251600:1 /backup/base
```

## 📊 Monitoreo

### Métricas Importantes

1. **Query Performance**: Tiempo de respuesta de consultas frecuentes
2. **Index Usage**: Utilización de índices
3. **Connection Pool**: Estado del pool de conexiones
4. **Document Growth**: Crecimiento del tamaño de documentos
5. **Lock Contention**: Contención de locks en writes

### Alertas Recomendadas

- Consultas lentas (>100ms)
- Pool de conexiones agotado (>80% utilización)
- Índice no utilizado en consultas frecuentes
- Espacio en disco bajo (<20% libre)