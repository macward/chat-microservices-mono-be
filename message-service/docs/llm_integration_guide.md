# 🚀 Guía de Integración - Servicio LLM

Esta guía está dirigida a **desarrolladores que quieren integrar el Servicio LLM** en sus proyectos. Proporciona ejemplos claros y prácticos para comenzar rápidamente.

## 📋 Información General

### ¿Qué es el Servicio LLM?
Un microservicio REST que proporciona acceso fácil y confiable a modelos de lenguaje grandes (LLMs) a través de una API HTTP simple. Maneja la comunicación con LM Studio y proporciona funcionalidades adicionales como:

- ✅ Validación automática de entrada
- ✅ Manejo robusto de errores
- ✅ Reintentos automáticos
- ✅ Logging estructurado
- ✅ Rate limiting
- ✅ Health checks

### Información del Servicio
- **URL Base**: `http://localhost:8023` (configurable)
- **Formato**: JSON REST API
- **Autenticación**: Ninguna (configurable)
- **Rate Limit**: 100 requests/minuto por IP (configurable)

---

## 🔗 Endpoints Disponibles

### 1. Health Check
**Verificar estado del servicio**

```http
GET /health
```

**Respuesta Exitosa (200):**
```json
{
  "status": "healthy",
  "timestamp": 1640995200.0,
  "version": "1.0.0",
  "llm_service": "connected",
  "uptime": 3600.5
}
```

### 2. Información del Servicio
**Obtener información básica**

```http
GET /
```

**Respuesta (200):**
```json
{
  "service": "LLM Service",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

### 3. Enviar Mensaje al LLM
**Endpoint principal para interactuar con el LLM**

```http
POST /llm/message
Content-Type: application/json
```

---

## 💬 Cómo Enviar Mensajes

### Estructura de la Petición

```json
{
  "model": "nombre-del-modelo",
  "messages": [
    {
      "role": "user|assistant|system",
      "content": "texto del mensaje"
    }
  ],
  "temperature": 0.7,     // Opcional: 0.0-2.0
  "max_tokens": 150,      // Opcional: 1-4000
  "top_p": 0.9,          // Opcional: 0.0-1.0
  "stream": false        // Opcional: no implementado aún
}
```

### Estructura de la Respuesta

```json
{
  "response": "Respuesta generada por el LLM",
  "model": "nombre-del-modelo-usado",
  "tokens_used": 25,
  "processing_time": 1.42,
  "correlation_id": "abc-123-def-456"
}
```

---

## 📚 Ejemplos Prácticos

### Ejemplo 1: Mensaje Simple

**Petición:**
```bash
curl -X POST "http://localhost:8000/llm/message" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tu-modelo",
    "messages": [
      {
        "role": "user",
        "content": "¿Cuál es la capital de Francia?"
      }
    ],
    "temperature": 0.3,
    "max_tokens": 50
  }'
```

**Respuesta:**
```json
{
  "response": "La capital de Francia es París.",
  "model": "tu-modelo",
  "tokens_used": 8,
  "processing_time": 0.85,
  "correlation_id": "req-abc123"
}
```

### Ejemplo 2: Conversación con Contexto

**Petición:**
```bash
curl -X POST "http://localhost:8000/llm/message" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tu-modelo",
    "messages": [
      {
        "role": "system",
        "content": "Eres un tutor de matemáticas que explica paso a paso."
      },
      {
        "role": "user",
        "content": "¿Cómo resuelvo 2x + 5 = 15?"
      }
    ],
    "temperature": 0.2,
    "max_tokens": 200
  }'
```

**Respuesta:**
```json
{
  "response": "Para resolver la ecuación 2x + 5 = 15, sigue estos pasos:\n\n1. Resta 5 de ambos lados: 2x = 10\n2. Divide ambos lados entre 2: x = 5\n\nPor lo tanto, x = 5.",
  "model": "tu-modelo",
  "tokens_used": 45,
  "processing_time": 1.23,
  "correlation_id": "req-def456"
}
```

### Ejemplo 3: Conversación Continua

**Petición:**
```bash
curl -X POST "http://localhost:8000/llm/message" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tu-modelo",
    "messages": [
      {
        "role": "user",
        "content": "¿Cuál es la capital de España?"
      },
      {
        "role": "assistant", 
        "content": "La capital de España es Madrid."
      },
      {
        "role": "user",
        "content": "¿Cuántos habitantes tiene?"
      }
    ],
    "temperature": 0.5,
    "max_tokens": 100
  }'
```

---

## 🛠️ Ejemplos de Código

### Python con requests

```python
import requests
import json

def send_llm_message(message, model="tu-modelo", temperature=0.7):
    url = "http://localhost:8000/llm/message"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": message}
        ],
        "temperature": temperature,
        "max_tokens": 150
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "response": data["response"],
            "tokens_used": data.get("tokens_used"),
            "processing_time": data.get("processing_time"),
            "correlation_id": data.get("correlation_id")
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e)
        }

# Ejemplo de uso
result = send_llm_message("¿Cómo está el clima hoy?")
if result["success"]:
    print(f"Respuesta: {result['response']}")
    print(f"Tokens usados: {result['tokens_used']}")
else:
    print(f"Error: {result['error']}")
```

### Python con httpx (async)

```python
import httpx
import asyncio

async def send_llm_message_async(message, model="tu-modelo"):
    url = "http://localhost:8000/llm/message"
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {"error": f"Request error: {str(e)}"}

# Ejemplo de uso
async def main():
    result = await send_llm_message_async("Explica qué es la inteligencia artificial")
    if "error" not in result:
        print(f"Respuesta: {result['response']}")
    else:
        print(f"Error: {result['error']}")

# Ejecutar
asyncio.run(main())
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

async function sendLLMMessage(message, model = 'tu-modelo', temperature = 0.7) {
  const url = 'http://localhost:8000/llm/message';
  
  const payload = {
    model: model,
    messages: [
      { role: 'user', content: message }
    ],
    temperature: temperature,
    max_tokens: 150
  };
  
  try {
    const response = await axios.post(url, payload, {
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' }
    });
    
    return {
      success: true,
      response: response.data.response,
      tokensUsed: response.data.tokens_used,
      processingTime: response.data.processing_time,
      correlationId: response.data.correlation_id
    };
    
  } catch (error) {
    return {
      success: false,
      error: error.response?.data?.detail || error.message
    };
  }
}

// Ejemplo de uso
(async () => {
  const result = await sendLLMMessage('¿Qué es JavaScript?');
  
  if (result.success) {
    console.log(`Respuesta: ${result.response}`);
    console.log(`Tokens: ${result.tokensUsed}`);
  } else {
    console.log(`Error: ${result.error}`);
  }
})();
```

### JavaScript (Frontend)

```javascript
async function sendLLMMessage(message, model = 'tu-modelo') {
  const url = 'http://localhost:8000/llm/message';
  
  const payload = {
    model: model,
    messages: [{ role: 'user', content: message }],
    temperature: 0.7,
    max_tokens: 150
  };
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return {
      success: true,
      response: data.response,
      tokensUsed: data.tokens_used,
      processingTime: data.processing_time
    };
    
  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}

// Ejemplo de uso en una función
async function handleUserMessage() {
  const userInput = document.getElementById('user-input').value;
  const result = await sendLLMMessage(userInput);
  
  if (result.success) {
    document.getElementById('response').textContent = result.response;
  } else {
    document.getElementById('error').textContent = result.error;
  }
}
```

---

## ❌ Manejo de Errores

### Códigos de Error HTTP

| Código | Descripción | Acción Recomendada |
|--------|-------------|-------------------|
| `200` | Éxito | Procesar respuesta |
| `400` | Error de validación | Revisar formato de datos |
| `408` | Timeout | Reintentar con parámetros más pequeños |
| `422` | Error de validación Pydantic | Revisar esquema de datos |
| `429` | Rate limit excedido | Esperar y reintentar |
| `503` | Servicio no disponible | Verificar conexión LLM |
| `500` | Error interno | Contactar soporte |

### Ejemplos de Respuestas de Error

**Error de Validación (400):**
```json
{
  "error": "Error de validación",
  "error_code": "LLM_VALIDATION_ERROR",
  "detail": "Contenido demasiado largo: 15000 caracteres (máximo: 10000)",
  "correlation_id": "req-error-123"
}
```

**Timeout (408):**
```json
{
  "error": "Timeout en la petición",
  "error_code": "LLM_TIMEOUT",
  "detail": "La petición al LLM tardó demasiado en procesarse",
  "correlation_id": "req-timeout-456"
}
```

**Rate Limit (429):**
```json
{
  "error": "Límite de velocidad excedido",
  "error_code": "LLM_RATE_LIMIT_ERROR", 
  "detail": "Demasiadas peticiones. Intente más tarde.",
  "correlation_id": "req-rate-789"
}
```

### Manejo Robusto de Errores

```python
import requests
import time
from typing import Dict, Any

def send_llm_message_with_retry(
    message: str, 
    model: str = "tu-modelo",
    max_retries: int = 3,
    base_delay: float = 1.0
) -> Dict[str, Any]:
    """
    Envía mensaje al LLM con reintentos automáticos.
    """
    url = "http://localhost:8000/llm/message"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": message}],
        "temperature": 0.7,
        "max_tokens": 150
    }
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                return {
                    "success": True,
                    **response.json()
                }
            elif response.status_code == 429:  # Rate limit
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # Backoff exponencial
                    print(f"Rate limit alcanzado. Esperando {delay}s...")
                    time.sleep(delay)
                    continue
            elif response.status_code == 408:  # Timeout
                if attempt < max_retries:
                    print(f"Timeout en intento {attempt + 1}. Reintentando...")
                    continue
            
            # Para otros errores, devolver inmediatamente
            error_data = response.json()
            return {
                "success": False,
                "error": error_data.get("error", "Error desconocido"),
                "error_code": error_data.get("error_code"),
                "status_code": response.status_code
            }
            
        except requests.exceptions.Timeout:
            if attempt < max_retries:
                print(f"Timeout de conexión en intento {attempt + 1}. Reintentando...")
                time.sleep(base_delay * (2 ** attempt))
                continue
            return {
                "success": False,
                "error": "Timeout de conexión después de varios intentos"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "No se pudo conectar al servicio LLM"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}"
            }
    
    return {
        "success": False,
        "error": f"Falló después de {max_retries} intentos"
    }

# Ejemplo de uso
result = send_llm_message_with_retry("¿Qué es machine learning?")
if result["success"]:
    print(f"Respuesta: {result['response']}")
else:
    print(f"Error: {result['error']}")
```

---

## ⚡ Optimización y Mejores Prácticas

### 1. Gestión de Parámetros

```python
# Configuración recomendada para diferentes casos de uso

# Para respuestas precisas y deterministas
precise_config = {
    "temperature": 0.1,
    "max_tokens": 100,
    "top_p": 0.9
}

# Para respuestas creativas
creative_config = {
    "temperature": 0.8,
    "max_tokens": 300,
    "top_p": 0.9
}

# Para resúmenes o análisis
analytical_config = {
    "temperature": 0.3,
    "max_tokens": 200,
    "top_p": 0.95
}
```

### 2. Gestión de Contexto en Conversaciones

```python
class LLMConversation:
    def __init__(self, model: str, system_prompt: str = None):
        self.model = model
        self.messages = []
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
    
    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
    
    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})
    
    def send_message(self, user_message: str, **kwargs) -> Dict[str, Any]:
        # Agregar mensaje del usuario
        self.add_user_message(user_message)
        
        # Enviar toda la conversación
        payload = {
            "model": self.model,
            "messages": self.messages,
            **kwargs
        }
        
        response = requests.post(
            "http://localhost:8000/llm/message",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # Agregar respuesta del asistente al historial
            self.add_assistant_message(data["response"])
            return {"success": True, **data}
        else:
            return {"success": False, "error": response.text}
    
    def clear_history(self, keep_system_prompt: bool = True):
        if keep_system_prompt and self.messages and self.messages[0]["role"] == "system":
            self.messages = [self.messages[0]]
        else:
            self.messages = []

# Ejemplo de uso
conversation = LLMConversation(
    model="tu-modelo",
    system_prompt="Eres un asistente técnico especializado en programación."
)

result1 = conversation.send_message("¿Qué es Python?")
result2 = conversation.send_message("¿Cuáles son sus ventajas?")
result3 = conversation.send_message("Dame un ejemplo de código")
```

### 3. Pool de Conexiones (Para Alto Volumen)

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class LLMClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Configurar reintentos automáticos
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def send_message(self, message: str, **kwargs) -> Dict[str, Any]:
        payload = {
            "model": kwargs.get("model", "tu-modelo"),
            "messages": [{"role": "user", "content": message}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 150)
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/llm/message",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return {"success": True, **response.json()}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": str(e)}
    
    def health_check(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def close(self):
        self.session.close()

# Uso como singleton o en un contexto manager
llm_client = LLMClient()

# Al final de la aplicación
llm_client.close()
```

---

## 🔧 Configuración y Deployment

### Variables de Entorno para Integración

Si despliegas tu propio servicio, puedes configurar:

```bash
# URL del servicio LLM
LLM_SERVICE_URL=http://localhost:8000

# Configuración de tu aplicación
LLM_SERVICE_TIMEOUT=30
LLM_SERVICE_MAX_RETRIES=3
LLM_SERVICE_DEFAULT_MODEL=tu-modelo-preferido
```

### Verificación de Conectividad

```python
def verify_llm_service(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Verificar que el servicio LLM esté funcionando correctamente."""
    try:
        # Health check
        health_response = requests.get(f"{base_url}/health", timeout=5)
        if health_response.status_code != 200:
            return {
                "available": False,
                "error": f"Health check falló: HTTP {health_response.status_code}"
            }
        
        health_data = health_response.json()
        
        # Test simple
        test_response = requests.post(
            f"{base_url}/llm/message",
            json={
                "model": "test",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5
            },
            timeout=10
        )
        
        return {
            "available": True,
            "health_status": health_data.get("status"),
            "llm_connected": health_data.get("llm_service") == "connected",
            "test_successful": test_response.status_code in [200, 503]  # 503 es OK si LLM no está disponible
        }
        
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }

# Verificar antes de usar
status = verify_llm_service()
if status["available"]:
    print("✅ Servicio LLM disponible")
    if status["llm_connected"]:
        print("✅ LLM conectado y funcionando")
    else:
        print("⚠️ Servicio disponible pero LLM desconectado")
else:
    print(f"❌ Servicio no disponible: {status['error']}")
```

---

## 📊 Monitoreo e Integración

### Headers Útiles en las Respuestas

Cada respuesta incluye headers útiles para debugging y monitoreo:

```python
response = requests.post(url, json=payload)

# Headers disponibles
correlation_id = response.headers.get("X-Correlation-ID")
process_time = response.headers.get("X-Process-Time")

print(f"Correlation ID: {correlation_id}")
print(f"Tiempo de procesamiento: {process_time}s")
```

### Logging Recomendado

```python
import logging

# Configurar logging para tu integración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_llm_message_with_logging(message: str, **kwargs) -> Dict[str, Any]:
    start_time = time.time()
    
    try:
        logger.info(f"Enviando mensaje al LLM: {message[:50]}...")
        
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            correlation_id = data.get("correlation_id", "unknown")
            process_time = data.get("processing_time", 0)
            tokens_used = data.get("tokens_used", 0)
            
            logger.info(
                f"Respuesta LLM exitosa - "
                f"ID: {correlation_id}, "
                f"Tokens: {tokens_used}, "
                f"Tiempo: {process_time:.2f}s"
            )
            
            return {"success": True, **data}
        else:
            logger.error(f"Error LLM: HTTP {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        logger.error(f"Excepción en LLM: {str(e)}")
        return {"success": False, "error": str(e)}
    finally:
        total_time = time.time() - start_time
        logger.info(f"Tiempo total de operación: {total_time:.2f}s")
```

---

## 🚨 Troubleshooting Común

### Problema: "Connection refused"
```bash
# Verificar que el servicio esté corriendo
curl http://localhost:8000/health

# Si no responde, iniciar el servicio
cd /path/to/llm-service
uvicorn app.main:app --reload
```

### Problema: "Service unavailable (503)"
```bash
# El servicio está corriendo pero LM Studio no
# 1. Abrir LM Studio
# 2. Cargar un modelo
# 3. Verificar que esté en localhost:1234
```

### Problema: "Request timeout"
```python
# Aumentar timeout o reducir max_tokens
payload = {
    "messages": [...],
    "max_tokens": 50,  # Reducir para respuestas más rápidas
    "temperature": 0.1  # Menor temperatura = más rápido
}

requests.post(url, json=payload, timeout=60)  # Más tiempo
```

### Problema: "Rate limit exceeded"
```python
# Implementar backoff exponencial
import time

def send_with_backoff(payload, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json=payload)
        if response.status_code != 429:
            return response
        
        wait_time = 2 ** attempt
        time.sleep(wait_time)
    
    return response
```

---

## 📞 Soporte

- **Documentación API**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Logs**: Revisar logs del servicio para correlation IDs
- **Configuración**: Verificar variables de entorno en `.env`

---

¡Tu integración con el Servicio LLM está lista! 🚀
