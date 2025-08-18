# Fase 3: CRUD Completo (Funcionalidad Detallada)

## Objetivo General
Implementar funcionalidades completas de CRUD para el servicio de conversaciones, agregando endpoints para actualización, archivado y restauración de conversaciones, con soporte para filtros básicos.

## Desglose de Tareas

### 1. Implementar Endpoint PATCH /conversations/{id}
- **Ubicación**: `app/api/conversations.py`
- **Tiempo estimado**: 45 minutos
- **Descripción**: 
  - Crear endpoint para actualización parcial de conversaciones
  - Permitir actualización de campos selectivos
- **Criterios de Aceptación**:
  - Endpoint acepta solicitudes PATCH con JSON parcial
  - Valida campos permitidos para actualización
  - Actualiza solo los campos proporcionados
  - Maneja casos de campos no modificables
- **Consideraciones Técnicas**:
  - Usar Pydantic para validación
  - Implementar lógica de actualización parcial en capa de servicio
  - Manejar casos de conversación no encontrada
- **Dependencias**: 
  - Modelo de conversación existente
  - Servicio de conversaciones implementado

### 2. Desarrollar Endpoint DELETE /conversations/{id}
- **Ubicación**: `app/api/conversations.py`
- **Tiempo estimado**: 40 minutos
- **Descripción**: 
  - Implementar endpoint para "archivado suave" de conversaciones
  - Cambiar estado de conversación a archivado en lugar de eliminación física
- **Criterios de Aceptación**:
  - Marca conversación con estado "archivado"
  - Conserva datos históricos
  - Impide modificaciones posteriores
  - Maneja casos de conversación ya archivada o no existente
- **Consideraciones Técnicas**:
  - Agregar campo `is_archived` o `status` en modelo de conversación
  - Implementar lógica de archivado en capa de repositorio
  - Validar permisos de usuario (si aplica)

### 3. Crear Endpoint POST /conversations/{id}/restore
- **Ubicación**: `app/api/conversations.py`
- **Tiempo estimado**: 40 minutos
- **Descripción**: 
  - Desarrollar funcionalidad para restaurar conversaciones archivadas
  - Revertir estado de archivado
- **Criterios de Aceptación**:
  - Restaura conversaciones previamente archivadas
  - Valida estado previo de la conversación
  - Maneja casos de conversación no archivable
- **Consideraciones Técnicas**:
  - Lógica similar al endpoint de archivado
  - Validaciones de estado de conversación
  - Registro de eventos de restauración

### 4. Implementar Filtros Básicos
- **Ubicación**: `app/repositories/conversation_repository.py`
- **Tiempo estimado**: 45 minutos
- **Descripción**: 
  - Agregar soporte para filtrado de conversaciones
  - Filtros por estado y character_id
- **Criterios de Aceptación**:
  - Filtro por `status` (activo/archivado)
  - Filtro por `character_id`
  - Combinación de filtros
  - Paginación básica
- **Consideraciones Técnicas**:
  - Modificar método de listado en repositorio
  - Usar parámetros de consulta de MongoDB
  - Implementar paginación eficiente

### 5. Manejo de Errores y Validación
- **Ubicación**: `app/api/conversations.py`, `app/services/conversation_service.py`
- **Tiempo estimado**: 30 minutos
- **Descripción**: 
  - Implementar manejo robusto de errores para nuevos endpoints
  - Validaciones de entrada y contexto
- **Criterios de Aceptación**:
  - Mensajes de error descriptivos
  - Códigos de estado HTTP apropiados
  - Validación de permisos y estado de conversación
- **Consideraciones Técnicas**:
  - Usar excepciones personalizadas
  - Middleware de manejo de errores
  - Registro de errores

### 6. Actualización de Documentación API
- **Ubicación**: Endpoints en `app/api/conversations.py`
- **Tiempo estimado**: 20 minutos
- **Descripción**: 
  - Actualizar documentación Swagger/OpenAPI
  - Describir nuevos endpoints y parámetros
- **Criterios de Aceptación**:
  - Documentación clara para cada nuevo endpoint
  - Ejemplos de solicitud y respuesta
  - Descripciones de parámetros
- **Consideraciones Técnicas**:
  - Usar decoradores de OpenAPI de FastAPI
  - Documentar posibles códigos de respuesta
  - Incluir ejemplos de uso

## Resumen de Tiempo
- Tarea 1 (PATCH): 45 minutos
- Tarea 2 (DELETE): 40 minutos
- Tarea 3 (Restore): 40 minutos
- Tarea 4 (Filtros): 45 minutos
- Tarea 5 (Errores): 30 minutos
- Tarea 6 (Documentación): 20 minutos

**Tiempo Total Estimado**: 3.5 horas

## Notas Finales
- Seguir principios de arquitectura de 3 capas
- Mantener código DRY (Don't Repeat Yourself)
- Implementar con enfoque en rendimiento y escalabilidad
- Realizar pruebas unitarias para cada nuevo endpoint

## Dependencias Previas
- Modelo de conversación completado
- Servicio de conversaciones básico implementado
- Configuración de base de datos MongoDB