# Servicio LLM con FastAPI y LM Studio Client

Este proyecto implementa un servicio RESTful utilizando FastAPI para interactuar con un modelo de lenguaje grande (LLM) alojado en LM Studio a través de la librería `lmstudio-client`.

## 🚀 Características

- **API REST robusta** con FastAPI
- **Validación de entrada** con Pydantic
- **Manejo de errores** granular y específico
- **Logging estructurado** con correlation IDs
- **Health checks** para monitoreo
- **Rate limiting** y headers de seguridad
- **Reintentos automáticos** con backoff exponencial
- **Tests comprehensivos** (unitarios, integración, y conexión real)

## 📋 Requisitos

### Software Necesario
- Python 3.8+
- [LM Studio](https://lmstudio.ai/) instalado y configurado
- Un modelo de lenguaje cargado en LM Studio

### Dependencias
- FastAPI para la API REST
- Pydantic para validación de datos
- lmstudio-client para conexión con LM Studio
- Uvicorn como servidor ASGI

## 🛠️ Instalación

### 1. Clonar y configurar el proyecto

```bash
git clone <repo-url>
cd llm-service

# Instalar dependencias de producción
pip install -r requirements.txt

# O instalar dependencias de desarrollo (incluye herramientas de testing)
pip install -r requirements-dev.txt
```

### 2. Configurar variables de entorno

```bash
# Copiar template de configuración
cp .env.example .env

# Editar .env con tu configuración
nano .env
```

### 3. Configurar LM Studio

1. Abrir LM Studio
2. Cargar un modelo de lenguaje
3. Iniciar el servidor local (normalmente en `localhost:1234`)
4. Verificar que el modelo esté activo y respondiendo

## 🚀 Uso

### Iniciar el Servicio

```bash
# Modo desarrollo (con auto-reload)
make run-dev
# O: uvicorn app.main:app --reload

# Modo producción
make run
# O: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

El servicio estará disponible en:
- **API**: http://127.0.0.1:8000
- **Documentación**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

### Endpoints Disponibles

#### `GET /`
Información básica del servicio

#### `GET /health`
Estado de salud del servicio y conectividad con LM Studio

#### `POST /llm/message`
Enviar mensaje al LLM

**Ejemplo de petición:**
```json
{
  "model": "tu-modelo-llm",
  "messages": [
    {
      "role": "user",
      "content": "¡Hola! ¿Cómo estás?"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 150,
  "top_p": 0.9
}
```

**Ejemplo de respuesta:**
```json
{
  "response": "¡Hola! Estoy muy bien, gracias por preguntar. ¿En qué puedo ayudarte hoy?",
  "model": "tu-modelo-llm",
  "tokens_used": 25,
  "processing_time": 1.42,
  "correlation_id": "abc-123-def"
}
```

## 🧪 Testing

### Tests Rápidos (Solo Mocks)

```bash
# Todos los tests sin conexión real
make test

# Solo tests unitarios
make test-unit

# Tests de integración (sin LLM real)
make test-integration

# Tests con reporte de cobertura
make test-cov
```

### Tests con Conexión Real a LM Studio

⚠️ **Importante**: Estos tests requieren que LM Studio esté ejecutándose con un modelo cargado.

```bash
# Verificar conectividad con LM Studio
make test-connection

# Tests completos con LLM real
make test-real

# Probar API manualmente (requiere servicio corriendo)
make test-api
```

### Scripts de Validación Manual

#### Verificar Conexión LLM

```bash
# Script interactivo para probar conexión
python scripts/test_llm_connection.py
```

Este script:
- ✅ Verifica que LM Studio esté corriendo
- ✅ Prueba la inicialización del servicio
- ✅ Envía mensajes de prueba
- ✅ Valida diferentes parámetros
- ✅ Realiza health checks

#### Probar API HTTP

```bash
# Primero iniciar el servicio
make run-dev

# En otra terminal, probar la API
python scripts/test_api_manual.py
```

Este script:
- 🌐 Verifica que la API esté respondiendo
- 🏥 Prueba el endpoint de health
- 💬 Envía mensajes simples y conversaciones
- ✅ Valida manejo de errores
- 🔄 Prueba peticiones concurrentes

## 📊 Configuración de Testing

### Variables de Entorno para Tests

```bash
# Saltar tests que requieren LM Studio real
export SKIP_REAL_LLM_TESTS=true

# Ejecutar solo tests de LLM real
export ONLY_REAL_LLM_TESTS=true

# Saltar tests de rendimiento
export SKIP_PERFORMANCE_TESTS=true

# Timeout para tests largos
export TEST_TIMEOUT=30
```

### Marcadores de Tests

- `real_llm`: Tests que requieren LM Studio real
- `mock_llm`: Tests que usan mocks
- `integration`: Tests de integración
- `performance`: Tests de rendimiento
- `slow`: Tests que tardan tiempo

## 🔧 Configuración

### Variables de Entorno

| Variable | Descripción | Valor por Defecto |
|----------|-------------|-------------------|
| `LLM_SERVICE_LM_STUDIO_HOST` | Host de LM Studio | `localhost` |
| `LLM_SERVICE_LM_STUDIO_PORT` | Puerto de LM Studio | `1234` |
| `LLM_SERVICE_LM_STUDIO_TIMEOUT` | Timeout en segundos | `30` |
| `LLM_SERVICE_MAX_REQUEST_SIZE` | Tamaño máximo de petición | `10000` |
| `LLM_SERVICE_RATE_LIMIT_REQUESTS` | Peticiones por minuto | `100` |
| `LLM_SERVICE_LOG_LEVEL` | Nivel de logging | `INFO` |
| `LLM_SERVICE_DEBUG` | Modo debug | `false` |

### Configuración de Producción

Para producción, asegúrate de:

1. **Configurar CORS apropiadamente**:
   ```bash
   LLM_SERVICE_ALLOWED_ORIGINS=["https://tu-dominio.com"]
   ```

2. **Establecer hosts de confianza**:
   ```bash
   LLM_SERVICE_TRUSTED_HOSTS=["tu-dominio.com"]
   ```

3. **Configurar logging JSON**:
   ```bash
   LLM_SERVICE_LOG_FORMAT=json
   LLM_SERVICE_LOG_LEVEL=INFO
   ```

4. **Desactivar debug**:
   ```bash
   LLM_SERVICE_DEBUG=false
   ```

## 🔍 Monitoreo y Logs

### Health Checks

El endpoint `/health` proporciona:
- Estado del servicio
- Conectividad con LM Studio
- Tiempo activo del servicio
- Versión de la aplicación

### Logging Estructurado

Todos los logs incluyen:
- Timestamp ISO
- Nivel de log
- Correlation ID para trackear peticiones
- Información contextual (método, URL, tiempo de procesamiento)

### Headers de Respuesta

Cada respuesta incluye:
- `X-Correlation-ID`: ID único para trackear la petición
- `X-Process-Time`: Tiempo de procesamiento en segundos
- Headers de seguridad estándar

## 🛠️ Desarrollo

### Calidad de Código

```bash
# Verificar estilo de código
make lint

# Formatear código automáticamente
make format

# Limpiar archivos temporales
make clean
```

### Estructura del Proyecto

```
llm-service/
├── app/
│   ├── main.py              # Aplicación FastAPI principal
│   ├── models.py            # Modelos Pydantic
│   ├── config.py            # Configuración
│   ├── exceptions.py        # Excepciones personalizadas
│   ├── middleware.py        # Middleware personalizado
│   └── services/
│       └── llm_service.py   # Lógica de negocio LLM
├── tests/
│   ├── test_*.py           # Tests unitarios e integración
│   └── test_real_llm_connection.py  # Tests con LLM real
├── scripts/
│   ├── test_llm_connection.py      # Validación manual LLM
│   └── test_api_manual.py          # Validación manual API
├── requirements.txt         # Dependencias producción
├── requirements-dev.txt     # Dependencias desarrollo
├── pytest.ini             # Configuración de pytest
├── Makefile               # Comandos útiles
└── .env.example          # Template de configuración
```

## 🚨 Troubleshooting

### Error: "No se pudo conectar con LM Studio"

1. Verificar que LM Studio esté ejecutándose
2. Confirmar que el puerto sea el correcto (por defecto 1234)
3. Asegurarse de que hay un modelo cargado
4. Revisar la configuración en `.env`

### Error: "LLM request timeout"

1. Incrementar `LLM_SERVICE_LM_STUDIO_TIMEOUT`
2. Verificar que el modelo no esté sobrecargado
3. Reducir `max_tokens` en las peticiones

### Tests fallando

1. Para tests mock: `make test-mock`
2. Para verificar LM Studio: `make test-connection`
3. Para debugging: `pytest -v -s`

### Logs no aparecen

1. Configurar `LLM_SERVICE_LOG_LEVEL=DEBUG`
2. Para formato legible: `LLM_SERVICE_LOG_FORMAT=text`

## 📄 Licencia

[Especificar licencia del proyecto]

## 🤝 Contribuir

1. Fork el proyecto
2. Crear branch para feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

---

**¡Tu microservicio LLM está listo para producción!** 🚀