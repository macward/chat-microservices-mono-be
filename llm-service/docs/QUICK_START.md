# ⚡ Quick Start - Servicio LLM

**¿Quieres integrar el Servicio LLM en 5 minutos?** Esta guía te llevará de cero a tu primera integración funcionando.

## 🎯 Objetivo

Al final de esta guía tendrás:
- ✅ El servicio LLM corriendo
- ✅ Tu primera petición exitosa
- ✅ Un ejemplo funcional para tu proyecto

---

## 📋 Pre-requisitos

```bash
# Verificar que LM Studio esté corriendo
curl http://localhost:1234/v1/models

# Si responde con una lista de modelos, ¡estás listo!
```

---

## 🚀 Paso 1: Arrancar el Servicio

```bash
# Clonar el repositorio
git clone <repo-url>
cd llm-service

# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servicio
uvicorn app.main:app --reload
```

**✅ Verificar que funciona:**
```bash
curl http://localhost:8000/health
```

Deberías ver algo como:
```json
{
  "status": "healthy",
  "llm_service": "connected",
  "version": "1.0.0"
}
```

---

## 💬 Paso 2: Tu Primera Petición

### Con curl:

```bash
curl -X POST "http://localhost:8000/llm/message" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tu-modelo",
    "messages": [
      {
        "role": "user", 
        "content": "¡Hola! ¿Funciona correctamente?"
      }
    ],
    "temperature": 0.7,
    "max_tokens": 50
  }'
```

### Con Python:

```python
import requests

response = requests.post("http://localhost:8000/llm/message", json={
    "model": "tu-modelo",
    "messages": [{"role": "user", "content": "¡Hola! ¿Funciona correctamente?"}],
    "temperature": 0.7,
    "max_tokens": 50
})

print(response.json())
```

### Con JavaScript:

```javascript
fetch('http://localhost:8000/llm/message', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'tu-modelo',
    messages: [{ role: 'user', content: '¡Hola! ¿Funciona correctamente?' }],
    temperature: 0.7,
    max_tokens: 50
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

**✅ Respuesta esperada:**
```json
{
  "response": "¡Hola! Sí, estoy funcionando correctamente...",
  "tokens_used": 12,
  "processing_time": 1.23,
  "correlation_id": "abc-123"
}
```

---

## 🛠️ Paso 3: Integrar en Tu Proyecto

### Opción A: Cliente Python Simple

```python
# llm_client.py
import requests

class LLMClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def ask(self, question, model="tu-modelo"):
        response = requests.post(f"{self.base_url}/llm/message", json={
            "model": model,
            "messages": [{"role": "user", "content": question}],
            "temperature": 0.7,
            "max_tokens": 200
        })
        
        if response.status_code == 200:
            return response.json()["response"]
        else:
            return f"Error: {response.text}"

# Usar en tu código
llm = LLMClient()
answer = llm.ask("¿Qué es Python?")
print(answer)
```

### Opción B: Cliente JavaScript

```javascript
// llm-client.js
class LLMClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }
  
  async ask(question, model = 'tu-modelo') {
    try {
      const response = await fetch(`${this.baseUrl}/llm/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: model,
          messages: [{ role: 'user', content: question }],
          temperature: 0.7,
          max_tokens: 200
        })
      });
      
      const data = await response.json();
      return response.ok ? data.response : `Error: ${data.error}`;
    } catch (error) {
      return `Error: ${error.message}`;
    }
  }
}

// Usar en tu código
const llm = new LLMClient();
llm.ask('¿Qué es JavaScript?').then(answer => console.log(answer));
```

---

## 🎯 Casos de Uso Rápidos

### 1. Chatbot Básico

```python
# chatbot.py
from llm_client import LLMClient

llm = LLMClient()
conversation = []

print("🤖 Chatbot iniciado. Escribe 'salir' para terminar.")

while True:
    user_input = input("\n👤 Tú: ")
    if user_input.lower() == 'salir':
        break
    
    # Mantener historial de conversación
    conversation.append({"role": "user", "content": user_input})
    
    response = requests.post("http://localhost:8000/llm/message", json={
        "model": "tu-modelo",
        "messages": conversation,
        "temperature": 0.7,
        "max_tokens": 150
    })
    
    if response.status_code == 200:
        bot_response = response.json()["response"]
        print(f"🤖 Bot: {bot_response}")
        
        # Agregar respuesta del bot al historial
        conversation.append({"role": "assistant", "content": bot_response})
    else:
        print(f"❌ Error: {response.text}")
```

### 2. Generador de Contenido

```python
# content_generator.py
from llm_client import LLMClient

llm = LLMClient()

def generate_blog_post(topic):
    prompt = f"Escribe un post de blog sobre: {topic}. Incluye título, introducción y 3 puntos principales."
    return llm.ask(prompt)

def generate_email(purpose):
    prompt = f"Escribe un email profesional para: {purpose}"
    return llm.ask(prompt)

# Ejemplos
blog = generate_blog_post("Beneficios del trabajo remoto")
email = generate_email("solicitar una reunión con el equipo")

print("📝 Blog post:", blog)
print("📧 Email:", email)
```

### 3. Analizador de Texto

```python
# text_analyzer.py
from llm_client import LLMClient

llm = LLMClient()

def analyze_sentiment(text):
    prompt = f"Analiza el sentimiento de este texto (positivo/negativo/neutro): {text}"
    return llm.ask(prompt)

def summarize_text(text):
    prompt = f"Resume este texto en 2-3 oraciones: {text}"
    return llm.ask(prompt)

# Ejemplo
text = "Me encanta este producto. La calidad es excelente y el servicio fue increíble."
sentiment = analyze_sentiment(text)
summary = summarize_text(text)

print("😊 Sentimiento:", sentiment)
print("📄 Resumen:", summary)
```

---

## 🌐 Integración Web Rápida

### HTML + JavaScript (Copy & Paste)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat LLM</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 50px auto; }
        #chat { border: 1px solid #ddd; height: 300px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
        #input { width: 80%; padding: 10px; }
        #send { padding: 10px; }
        .message { margin: 5px 0; padding: 5px; border-radius: 3px; }
        .user { background: #e3f2fd; text-align: right; }
        .bot { background: #f5f5f5; }
    </style>
</head>
<body>
    <h1>🤖 Chat con LLM</h1>
    <div id="chat"></div>
    <input type="text" id="input" placeholder="Escribe tu mensaje...">
    <button id="send">Enviar</button>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const send = document.getElementById('send');

        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;

            // Mostrar mensaje del usuario
            chat.innerHTML += `<div class="message user">👤 ${message}</div>`;
            input.value = '';

            try {
                const response = await fetch('http://localhost:8000/llm/message', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        model: 'tu-modelo',
                        messages: [{ role: 'user', content: message }],
                        temperature: 0.7,
                        max_tokens: 150
                    })
                });

                const data = await response.json();
                chat.innerHTML += `<div class="message bot">🤖 ${data.response}</div>`;
                chat.scrollTop = chat.scrollHeight;
            } catch (error) {
                chat.innerHTML += `<div class="message bot">❌ Error: ${error.message}</div>`;
            }
        }

        send.onclick = sendMessage;
        input.onkeypress = (e) => { if (e.key === 'Enter') sendMessage(); };
    </script>
</body>
</html>
```

---

## 🔧 Configuración Básica

### Archivo .env (Opcional)

```bash
# .env
LLM_SERVICE_LM_STUDIO_HOST=localhost
LLM_SERVICE_LM_STUDIO_PORT=1234
LLM_SERVICE_DEBUG=true
LLM_SERVICE_LOG_LEVEL=INFO
```

### Dockerfile (Para Deploy)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🚨 Solución de Problemas

### Error: "Connection refused"
```bash
# El servicio no está corriendo
uvicorn app.main:app --reload
```

### Error: "Service unavailable (503)"
```bash
# LM Studio no está corriendo o sin modelo cargado
# 1. Abrir LM Studio
# 2. Cargar un modelo
# 3. Verificar puerto 1234
```

### Error: "Request timeout"
```python
# Reducir max_tokens para respuestas más rápidas
"max_tokens": 50  # En lugar de 200
```

### Error: "Rate limit exceeded"
```python
# Esperar un momento entre peticiones
import time
time.sleep(1)  # Esperar 1 segundo
```

---

## 🎉 ¡Listo!

**En 5 minutos has:**
- ✅ Configurado el servicio LLM
- ✅ Hecho tu primera petición exitosa  
- ✅ Creado ejemplos funcionales
- ✅ Integrado en tu proyecto

### 📚 Próximos Pasos

1. **Ver más ejemplos**: `docs/API_EXAMPLES.md`
2. **Guía completa**: `docs/INTEGRATION_GUIDE.md`
3. **Documentación API**: `http://localhost:8000/docs`

### 🚀 ¿Necesitas Ayuda?

- **Health Check**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs`
- **Tests**: `python scripts/test_llm_connection.py`

---

¡Tu integración con LLM está lista para usar! 🚀