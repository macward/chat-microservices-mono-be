# 🤖 Configuración de Modelos - Servicio LLM

Esta guía explica cómo se asignan y configuran los modelos en el Servicio LLM.

## 📍 Dónde se Asigna el Modelo

El modelo se asigna en **3 lugares principales** del código:

### 1. **Configuración por Defecto** (`app/config.py`)

```python
# Líneas 32-35
default_model: str = Field(
    "dirty-muse-writer-v01-uncensored-erotica-nsfw",
    description="Modelo LLM por defecto"
)
```

**Propósito**: Define qué modelo usar cuando no se especifica uno en la petición.

### 2. **En cada Petición HTTP** (especificado por el cliente)

```json
{
    "model": "dirty-muse-writer-v01-uncensored-erotica-nsfw",
    "messages": [
        {"role": "user", "content": "¡Hola!"}
    ]
}
```

**Propósito**: Permite al cliente especificar qué modelo usar para esa petición específica.

### 3. **Lógica de Selección** (`app/services/llm_service.py`)

```python
# Línea 100
model_to_use = request.model if request.model else settings.default_model
kwargs["model"] = model_to_use
```

**Propósito**: Si el cliente no especifica modelo, usa el configurado por defecto.

---

## 🔧 Cómo Cambiar el Modelo

### Opción 1: Variable de Entorno (Recomendado)

```bash
# En .env
LLM_SERVICE_DEFAULT_MODEL=google/gemma-3-12b
```

### Opción 2: Modificar config.py

```python
default_model: str = Field(
    "google/gemma-3-12b",  # Cambiar aquí
    description="Modelo LLM por defecto"
)
```

### Opción 3: Especificar en cada Petición

```python
import requests

response = requests.post("http://localhost:8000/llm/message", json={
    "model": "google/gemma-3-12b",  # Modelo específico
    "messages": [{"role": "user", "content": "¡Hola!"}]
})
```

---

## 📋 Modelos Disponibles Actualmente

Según LM Studio, tienes estos modelos cargados:

```json
{
    "data": [
        {
            "id": "dirty-muse-writer-v01-uncensored-erotica-nsfw",
            "object": "model",
            "owned_by": "organization_owner"
        },
        {
            "id": "dirty-muse-writer-v01-uncensored-erotica-nsfw:2",
            "object": "model", 
            "owned_by": "organization_owner"
        },
        {
            "id": "text-embedding-nomic-embed-text-v1.5",
            "object": "model",
            "owned_by": "organization_owner"
        },
        {
            "id": "google/gemma-3-12b",
            "object": "model",
            "owned_by": "organization_owner"
        }
    ]
}
```

### ✅ **Modelo Configurado Actualmente**
- `dirty-muse-writer-v01-uncensored-erotica-nsfw` (por defecto)

### 🔄 **Modelos Alternativos Disponibles**
- `dirty-muse-writer-v01-uncensored-erotica-nsfw:2`
- `google/gemma-3-12b`
- `text-embedding-nomic-embed-text-v1.5` (para embeddings)

---

## 🚀 Verificar Modelos Disponibles

### Desde la Terminal

```bash
# Ver modelos disponibles en LM Studio
curl -s http://localhost:1234/v1/models | python -m json.tool
```

### Desde el Código

```python
import requests

def get_available_models():
    response = requests.get("http://localhost:1234/v1/models")
    if response.status_code == 200:
        models = response.json()
        return [model["id"] for model in models["data"]]
    return []

models = get_available_models()
print("Modelos disponibles:", models)
```

### Desde el Servicio LLM

El servicio automáticamente verifica modelos disponibles al inicializar y ajusta el modelo por defecto si es necesario:

```python
# En llm_service.py líneas 51-64
if settings.default_model not in available_models:
    logger.warning(f"Modelo por defecto '{settings.default_model}' no encontrado. Usando '{available_models[0]}'")
    settings.default_model = available_models[0]
```

---

## ⚙️ Configuración Avanzada

### Usar Diferentes Modelos según el Caso de Uso

```python
# Cliente Python con múltiples modelos
class LLMClient:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.models = {
            "chat": "dirty-muse-writer-v01-uncensored-erotica-nsfw",
            "reasoning": "google/gemma-3-12b",
            "embeddings": "text-embedding-nomic-embed-text-v1.5"
        }
    
    def chat(self, message):
        return self._send_message(message, self.models["chat"])
    
    def reason(self, question):
        return self._send_message(question, self.models["reasoning"])
    
    def _send_message(self, message, model):
        response = requests.post(f"{self.base_url}/llm/message", json={
            "model": model,
            "messages": [{"role": "user", "content": message}]
        })
        return response.json()["response"]
```

### Validación de Modelos

El servicio incluye validación automática:

1. **Al iniciar**: Verifica que hay modelos disponibles
2. **En cada petición**: Valida que el modelo solicitado existe
3. **Fallback automático**: Si el modelo por defecto no existe, usa el primero disponible

---

## 🚨 Troubleshooting

### Error: "Multiple models are loaded. Please specify a model"

**Causa**: LM Studio tiene múltiples modelos y no sabe cuál usar.

**Solución**:
1. Especificar modelo en cada petición
2. Configurar modelo por defecto válido
3. El servicio ahora maneja esto automáticamente

### Error: "Model not found"

**Causa**: El modelo especificado no está cargado en LM Studio.

**Solución**:
1. Verificar modelos disponibles: `curl http://localhost:1234/v1/models`
2. Usar uno de los modelos listados
3. Cargar el modelo deseado en LM Studio

### Error: "No models available"

**Causa**: LM Studio no tiene ningún modelo cargado.

**Solución**:
1. Abrir LM Studio
2. Cargar al menos un modelo
3. Reiniciar el servicio

---

## 📝 Ejemplos Prácticos

### Cambiar Modelo por Variable de Entorno

```bash
# Crear .env
echo "LLM_SERVICE_DEFAULT_MODEL=google/gemma-3-12b" > .env

# Reiniciar servicio
uvicorn app.main:app --reload
```

### Usar Modelo Específico en Petición

```bash
curl -X POST "http://localhost:8000/llm/message" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-3-12b",
    "messages": [{"role": "user", "content": "¡Hola!"}],
    "temperature": 0.7
  }'
```

### Cliente que Maneja Múltiples Modelos

```python
models_config = {
    "creative_writing": "dirty-muse-writer-v01-uncensored-erotica-nsfw",
    "analytical": "google/gemma-3-12b",
    "conversational": "dirty-muse-writer-v01-uncensored-erotica-nsfw:2"
}

def ask_llm(question, task_type="conversational"):
    model = models_config.get(task_type, models_config["conversational"])
    
    response = requests.post("http://localhost:8000/llm/message", json={
        "model": model,
        "messages": [{"role": "user", "content": question}]
    })
    
    return response.json()["response"]

# Uso
creative_response = ask_llm("Escribe un poema", "creative_writing")
analytical_response = ask_llm("Analiza estos datos", "analytical")
```

---

**✅ Configuración actual**: `dirty-muse-writer-v01-uncensored-erotica-nsfw`

**🔧 Para cambiar**: Modifica la variable de entorno `LLM_SERVICE_DEFAULT_MODEL` o especifica el modelo en cada petición.