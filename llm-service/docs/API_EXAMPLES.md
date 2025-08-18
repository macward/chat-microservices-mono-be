# 📋 Ejemplos de API - Casos de Uso Comunes

Esta documentación proporciona ejemplos prácticos para casos de uso específicos del Servicio LLM.

## 🤖 Casos de Uso por Tipo de Aplicación

### 1. Chatbot Simple

```python
# chatbot_simple.py
import requests

class SimpleChatbot:
    def __init__(self, model_name="tu-modelo", system_prompt=None):
        self.base_url = "http://localhost:8000"
        self.model = model_name
        self.conversation = []
        
        if system_prompt:
            self.conversation.append({
                "role": "system", 
                "content": system_prompt
            })
    
    def send_message(self, user_message):
        # Agregar mensaje del usuario
        self.conversation.append({
            "role": "user",
            "content": user_message
        })
        
        payload = {
            "model": self.model,
            "messages": self.conversation,
            "temperature": 0.7,
            "max_tokens": 200
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/llm/message",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                bot_response = data["response"]
                
                # Agregar respuesta del bot al historial
                self.conversation.append({
                    "role": "assistant",
                    "content": bot_response
                })
                
                return {
                    "success": True,
                    "message": bot_response,
                    "tokens_used": data.get("tokens_used"),
                    "processing_time": data.get("processing_time")
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def clear_conversation(self):
        # Mantener solo el prompt del sistema si existe
        if self.conversation and self.conversation[0]["role"] == "system":
            self.conversation = [self.conversation[0]]
        else:
            self.conversation = []

# Ejemplo de uso
if __name__ == "__main__":
    # Crear chatbot con personalidad
    bot = SimpleChatbot(
        system_prompt="Eres un asistente amigable y útil que responde de forma concisa."
    )
    
    print("🤖 Chatbot iniciado. Escribe 'salir' para terminar.")
    
    while True:
        user_input = input("\n👤 Tú: ")
        
        if user_input.lower() in ['salir', 'exit', 'quit']:
            break
        
        result = bot.send_message(user_input)
        
        if result["success"]:
            print(f"🤖 Bot: {result['message']}")
            print(f"   (Tokens: {result['tokens_used']}, Tiempo: {result['processing_time']:.2f}s)")
        else:
            print(f"❌ Error: {result['error']}")
```

### 2. Generador de Contenido

```python
# content_generator.py
import requests
from typing import List, Dict, Any

class ContentGenerator:
    def __init__(self, model_name="tu-modelo"):
        self.base_url = "http://localhost:8000"
        self.model = model_name
    
    def generate_blog_post(self, topic: str, length: str = "medium") -> Dict[str, Any]:
        """Generar un post de blog sobre un tema específico."""
        
        length_tokens = {
            "short": 200,
            "medium": 400,
            "long": 600
        }
        
        system_prompt = """Eres un escritor de contenido experto. 
        Crea posts de blog informativos, bien estructurados y engaging.
        Incluye título, introducción, puntos principales y conclusión."""
        
        user_prompt = f"Escribe un post de blog {length} sobre: {topic}"
        
        return self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=length_tokens.get(length, 400),
            temperature=0.7
        )
    
    def generate_product_description(self, product_name: str, features: List[str]) -> Dict[str, Any]:
        """Generar descripción de producto."""
        
        features_text = "\n- ".join(features)
        
        system_prompt = """Eres un experto en marketing y copywriting. 
        Crea descripciones de productos persuasivas y claras que destaquen beneficios."""
        
        user_prompt = f"""Crea una descripción de producto para:
        Producto: {product_name}
        
        Características:
        - {features_text}
        
        La descripción debe ser persuasiva pero informativa."""
        
        return self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=250,
            temperature=0.6
        )
    
    def generate_email_template(self, purpose: str, tone: str = "professional") -> Dict[str, Any]:
        """Generar template de email."""
        
        system_prompt = f"""Eres un experto en comunicación por email. 
        Crea templates de email con tono {tone} que sean efectivos y apropiados."""
        
        user_prompt = f"Crea un template de email para: {purpose}"
        
        return self._send_request(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=300,
            temperature=0.5
        )
    
    def _send_request(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """Método auxiliar para enviar peticiones al LLM."""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/llm/message",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "content": data["response"],
                    "metadata": {
                        "tokens_used": data.get("tokens_used"),
                        "processing_time": data.get("processing_time"),
                        "model": data.get("model")
                    }
                }
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"error": response.text}
                return {
                    "success": False,
                    "error": error_data.get("error", "Unknown error"),
                    "error_code": error_data.get("error_code")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Ejemplo de uso
if __name__ == "__main__":
    generator = ContentGenerator()
    
    # Generar post de blog
    blog_result = generator.generate_blog_post(
        topic="Beneficios de la inteligencia artificial en las empresas",
        length="medium"
    )
    
    if blog_result["success"]:
        print("📝 Blog Post Generado:")
        print(blog_result["content"])
        print(f"\n📊 Metadata: {blog_result['metadata']}")
    else:
        print(f"❌ Error: {blog_result['error']}")
    
    # Generar descripción de producto
    product_result = generator.generate_product_description(
        product_name="Smartphone XYZ Pro",
        features=[
            "Cámara de 108MP con IA",
            "Batería de 5000mAh",
            "Pantalla OLED de 6.7 pulgadas",
            "Procesador octa-core de última generación",
            "Resistente al agua IP68"
        ]
    )
    
    if product_result["success"]:
        print("\n🛍️ Descripción de Producto:")
        print(product_result["content"])
```

### 3. Asistente de Código

```python
# code_assistant.py
import requests
import json

class CodeAssistant:
    def __init__(self, model_name="tu-modelo"):
        self.base_url = "http://localhost:8000"
        self.model = model_name
    
    def explain_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Explicar qué hace un fragmento de código."""
        
        system_prompt = f"""Eres un experto programador y profesor. 
        Explica código {language} de forma clara y educativa.
        Incluye qué hace el código, cómo funciona y conceptos importantes."""
        
        user_prompt = f"Explica este código {language}:\n\n```{language}\n{code}\n```"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.3)
    
    def generate_code(self, description: str, language: str = "python") -> Dict[str, Any]:
        """Generar código basado en una descripción."""
        
        system_prompt = f"""Eres un experto programador en {language}. 
        Genera código limpio, eficiente y bien comentado.
        Incluye ejemplos de uso cuando sea apropiado."""
        
        user_prompt = f"Genera código {language} para: {description}"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.4)
    
    def review_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Revisar código y sugerir mejoras."""
        
        system_prompt = f"""Eres un revisor de código experto en {language}.
        Analiza el código y proporciona:
        1. Problemas o bugs potenciales
        2. Mejoras de rendimiento
        3. Mejores prácticas
        4. Legibilidad y mantenibilidad"""
        
        user_prompt = f"Revisa este código {language}:\n\n```{language}\n{code}\n```"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.2)
    
    def debug_code(self, code: str, error_message: str, language: str = "python") -> Dict[str, Any]:
        """Ayudar a debuggear código con errores."""
        
        system_prompt = f"""Eres un experto en debugging de {language}.
        Analiza el código y el error para proporcionar:
        1. Explicación del problema
        2. Solución específica
        3. Código corregido si es necesario"""
        
        user_prompt = f"""Ayúdame a debuggear este código {language}:

Código:
```{language}
{code}
```

Error:
{error_message}"""
        
        return self._send_request(system_prompt, user_prompt, temperature=0.3)
    
    def optimize_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Optimizar código para mejor rendimiento."""
        
        system_prompt = f"""Eres un experto en optimización de {language}.
        Analiza el código y proporciona versiones optimizadas considerando:
        1. Complejidad temporal y espacial
        2. Mejores estructuras de datos
        3. Algoritmos más eficientes
        4. Mejores prácticas del lenguaje"""
        
        user_prompt = f"Optimiza este código {language}:\n\n```{language}\n{code}\n```"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.3)
    
    def _send_request(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        """Método auxiliar para enviar peticiones."""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 600
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/llm/message",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data["response"],
                    "tokens_used": data.get("tokens_used"),
                    "processing_time": data.get("processing_time")
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Ejemplo de uso
if __name__ == "__main__":
    assistant = CodeAssistant()
    
    # Ejemplo: Explicar código
    sample_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
    """
    
    explanation = assistant.explain_code(sample_code, "python")
    
    if explanation["success"]:
        print("📖 Explicación del código:")
        print(explanation["response"])
    else:
        print(f"❌ Error: {explanation['error']}")
    
    # Ejemplo: Generar código
    generation = assistant.generate_code(
        "Una función que ordene una lista de diccionarios por una clave específica",
        "python"
    )
    
    if generation["success"]:
        print("\n💻 Código generado:")
        print(generation["response"])
```

### 4. Analizador de Texto

```python
# text_analyzer.py
import requests
from typing import Dict, Any, List

class TextAnalyzer:
    def __init__(self, model_name="tu-modelo"):
        self.base_url = "http://localhost:8000"
        self.model = model_name
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analizar el sentimiento de un texto."""
        
        system_prompt = """Eres un experto en análisis de sentimientos.
        Analiza el texto y proporciona:
        1. Sentimiento general (positivo/negativo/neutro)
        2. Nivel de intensidad (1-10)
        3. Emociones específicas detectadas
        4. Justificación del análisis"""
        
        user_prompt = f"Analiza el sentimiento de este texto:\n\n{text}"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.2)
    
    def summarize_text(self, text: str, length: str = "medium") -> Dict[str, Any]:
        """Resumir un texto."""
        
        length_instructions = {
            "short": "en 2-3 oraciones",
            "medium": "en 1 párrafo",
            "long": "en varios párrafos con puntos clave"
        }
        
        system_prompt = f"""Eres un experto en resúmenes de texto.
        Crea resúmenes precisos que capturen los puntos más importantes."""
        
        user_prompt = f"Resume este texto {length_instructions[length]}:\n\n{text}"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.3)
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """Extraer palabras clave de un texto."""
        
        system_prompt = """Eres un experto en procesamiento de lenguaje natural.
        Extrae las palabras clave más importantes y relevantes del texto."""
        
        user_prompt = f"Extrae las {max_keywords} palabras clave más importantes de este texto:\n\n{text}"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.2)
    
    def translate_text(self, text: str, target_language: str) -> Dict[str, Any]:
        """Traducir texto a otro idioma."""
        
        system_prompt = f"""Eres un traductor experto.
        Traduce el texto al {target_language} manteniendo el tono y contexto original."""
        
        user_prompt = f"Traduce este texto al {target_language}:\n\n{text}"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.3)
    
    def classify_text(self, text: str, categories: List[str]) -> Dict[str, Any]:
        """Clasificar texto en categorías específicas."""
        
        categories_text = ", ".join(categories)
        
        system_prompt = """Eres un experto en clasificación de texto.
        Analiza el contenido y clasifica según las categorías proporcionadas."""
        
        user_prompt = f"""Clasifica este texto en una de estas categorías: {categories_text}
        
        Proporciona:
        1. Categoría más apropiada
        2. Nivel de confianza (1-10)
        3. Justificación
        
        Texto:
        {text}"""
        
        return self._send_request(system_prompt, user_prompt, temperature=0.2)
    
    def improve_writing(self, text: str) -> Dict[str, Any]:
        """Mejorar la escritura de un texto."""
        
        system_prompt = """Eres un editor de texto experto.
        Mejora la escritura considerando:
        1. Claridad y fluidez
        2. Gramática y ortografía
        3. Estilo y tono
        4. Estructura y coherencia"""
        
        user_prompt = f"Mejora este texto:\n\n{text}"
        
        return self._send_request(system_prompt, user_prompt, temperature=0.4)
    
    def _send_request(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Dict[str, Any]:
        """Método auxiliar para enviar peticiones."""
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/llm/message",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "result": data["response"],
                    "metadata": {
                        "tokens_used": data.get("tokens_used"),
                        "processing_time": data.get("processing_time")
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Ejemplo de uso
if __name__ == "__main__":
    analyzer = TextAnalyzer()
    
    sample_text = """
    Me encanta este nuevo producto. La calidad es excepcional y el servicio al cliente
    fue muy atento. Definitivamente lo recomendaría a otros. El precio es justo para
    lo que ofrece y la entrega fue rápida. ¡Muy satisfecho con mi compra!
    """
    
    # Análisis de sentimiento
    sentiment = analyzer.analyze_sentiment(sample_text)
    if sentiment["success"]:
        print("😊 Análisis de Sentimiento:")
        print(sentiment["result"])
    
    # Resumen
    summary = analyzer.summarize_text(sample_text, "short")
    if summary["success"]:
        print("\n📝 Resumen:")
        print(summary["result"])
    
    # Palabras clave
    keywords = analyzer.extract_keywords(sample_text, 5)
    if keywords["success"]:
        print("\n🔍 Palabras Clave:")
        print(keywords["result"])
```

## 🌐 Integración con Frameworks Web

### Flask Integration

```python
# flask_integration.py
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

class LLMService:
    def __init__(self):
        self.base_url = "http://localhost:8000"
    
    def send_message(self, message, **kwargs):
        payload = {
            "model": kwargs.get("model", "tu-modelo"),
            "messages": [{"role": "user", "content": message}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 150)
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/llm/message",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {"success": True, **response.json()}
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"error": response.text}
                return {"success": False, **error_data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

llm_service = LLMService()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    
    if not data or "message" not in data:
        return jsonify({"error": "Mensaje requerido"}), 400
    
    result = llm_service.send_message(
        message=data["message"],
        model=data.get("model"),
        temperature=data.get("temperature"),
        max_tokens=data.get("max_tokens")
    )
    
    if result["success"]:
        return jsonify({
            "response": result["response"],
            "metadata": {
                "tokens_used": result.get("tokens_used"),
                "processing_time": result.get("processing_time")
            }
        })
    else:
        return jsonify({"error": result["error"]}), 500

@app.route('/api/health')
def health():
    try:
        response = requests.get(f"{llm_service.base_url}/health", timeout=5)
        return jsonify(response.json()), response.status_code
    except:
        return jsonify({"status": "unhealthy"}), 503

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

### FastAPI Integration

```python
# fastapi_integration.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from typing import Optional

app = FastAPI(title="Mi App con LLM")

class ChatRequest(BaseModel):
    message: str
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 150

class ChatResponse(BaseModel):
    response: str
    tokens_used: Optional[int] = None
    processing_time: Optional[float] = None

class LLMClient:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(self, message: str, **kwargs):
        payload = {
            "model": kwargs.get("model", "tu-modelo"),
            "messages": [{"role": "user", "content": message}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 150)
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/llm/message",
                json=payload
            )
            
            if response.status_code == 200:
                return {"success": True, **response.json()}
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"error": response.text}
                return {"success": False, **error_data}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

llm_client = LLMClient()

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await llm_client.send_message(
        message=request.message,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    
    if result["success"]:
        return ChatResponse(
            response=result["response"],
            tokens_used=result.get("tokens_used"),
            processing_time=result.get("processing_time")
        )
    else:
        raise HTTPException(status_code=500, detail=result["error"])

@app.get("/api/health")
async def health():
    try:
        response = await llm_client.client.get(f"{llm_client.base_url}/health")
        return response.json()
    except:
        return {"status": "unhealthy"}
```

## 📱 Frontend Examples

### JavaScript (Vanilla)

```html
<!-- index.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Chat con LLM</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        #chat-container { border: 1px solid #ddd; height: 400px; overflow-y: scroll; padding: 10px; margin-bottom: 10px; }
        #input-container { display: flex; gap: 10px; }
        #message-input { flex: 1; padding: 10px; }
        #send-button { padding: 10px 20px; }
        .message { margin-bottom: 10px; padding: 10px; border-radius: 5px; }
        .user-message { background-color: #e3f2fd; text-align: right; }
        .bot-message { background-color: #f5f5f5; }
        .error-message { background-color: #ffebee; color: #c62828; }
    </style>
</head>
<body>
    <h1>🤖 Chat con LLM</h1>
    <div id="chat-container"></div>
    <div id="input-container">
        <input type="text" id="message-input" placeholder="Escribe tu mensaje..." />
        <button id="send-button">Enviar</button>
    </div>

    <script>
        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;

            // Mostrar mensaje del usuario
            addMessage(message, 'user');
            messageInput.value = '';
            sendButton.disabled = true;

            try {
                const response = await fetch('http://localhost:8000/llm/message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: 'tu-modelo',
                        messages: [{ role: 'user', content: message }],
                        temperature: 0.7,
                        max_tokens: 200
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    addMessage(data.response, 'bot');
                    
                    // Mostrar metadata
                    const metadata = `Tokens: ${data.tokens_used || 'N/A'}, Tiempo: ${data.processing_time?.toFixed(2) || 'N/A'}s`;
                    addMessage(metadata, 'metadata');
                } else {
                    const errorData = await response.json();
                    addMessage(`Error: ${errorData.error || 'Error desconocido'}`, 'error');
                }
            } catch (error) {
                addMessage(`Error de conexión: ${error.message}`, 'error');
            } finally {
                sendButton.disabled = false;
                messageInput.focus();
            }
        }

        function addMessage(text, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Auto-focus en el input
        messageInput.focus();
    </script>
</body>
</html>
```

### React Component

```jsx
// ChatComponent.jsx
import React, { useState, useRef, useEffect } from 'react';

const ChatComponent = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    // Agregar mensaje del usuario
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);

    try {
      const response = await fetch('http://localhost:8000/llm/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'tu-modelo',
          messages: [{ role: 'user', content: userMessage }],
          temperature: 0.7,
          max_tokens: 200
        })
      });

      if (response.ok) {
        const data = await response.json();
        
        // Agregar respuesta del bot
        setMessages(prev => [...prev, { 
          type: 'bot', 
          content: data.response,
          metadata: {
            tokens: data.tokens_used,
            processingTime: data.processing_time
          }
        }]);
      } else {
        const errorData = await response.json();
        setMessages(prev => [...prev, { 
          type: 'error', 
          content: `Error: ${errorData.error || 'Error desconocido'}` 
        }]);
      }
    } catch (error) {
      setMessages(prev => [...prev, { 
        type: 'error', 
        content: `Error de conexión: ${error.message}` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <h1>🤖 Chat con LLM</h1>
      
      <div style={{ 
        border: '1px solid #ddd', 
        height: '400px', 
        overflowY: 'scroll', 
        padding: '10px', 
        marginBottom: '10px',
        backgroundColor: '#fafafa'
      }}>
        {messages.map((message, index) => (
          <div key={index} style={{
            marginBottom: '10px',
            padding: '10px',
            borderRadius: '5px',
            backgroundColor: message.type === 'user' ? '#e3f2fd' : 
                            message.type === 'error' ? '#ffebee' : '#f5f5f5',
            textAlign: message.type === 'user' ? 'right' : 'left',
            color: message.type === 'error' ? '#c62828' : 'inherit'
          }}>
            <div>{message.content}</div>
            {message.metadata && (
              <div style={{ fontSize: '0.8em', color: '#666', marginTop: '5px' }}>
                Tokens: {message.metadata.tokens || 'N/A'} | 
                Tiempo: {message.metadata.processingTime?.toFixed(2) || 'N/A'}s
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div style={{ textAlign: 'center', color: '#666' }}>
            🤖 Pensando...
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Escribe tu mensaje..."
          style={{ 
            flex: 1, 
            padding: '10px', 
            resize: 'none',
            minHeight: '40px'
          }}
          disabled={isLoading}
        />
        <button 
          onClick={sendMessage}
          disabled={isLoading || !inputValue.trim()}
          style={{ 
            padding: '10px 20px',
            backgroundColor: '#1976d2',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? '...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
};

export default ChatComponent;
```

## ⚡ Optimización para Producción

### Connection Pooling y Caching

```python
# production_client.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
from functools import lru_cache
import hashlib
import json

class ProductionLLMClient:
    def __init__(self, base_url="http://localhost:8000", cache_size=128):
        self.base_url = base_url
        self.cache_size = cache_size
        
        # Configurar sesión con pool de conexiones
        self.session = requests.Session()
        
        # Estrategia de reintentos
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=20
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Cache simple para respuestas
        self._cache = {}
        self._cache_times = {}
        self._cache_ttl = 300  # 5 minutos
    
    def _get_cache_key(self, payload):
        """Generar clave de cache basada en el payload."""
        # Normalizar payload para caching consistente
        normalized = {
            "model": payload.get("model"),
            "messages": payload.get("messages"),
            "temperature": payload.get("temperature"),
            "max_tokens": payload.get("max_tokens")
        }
        cache_string = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key):
        """Verificar si la entrada de cache es válida."""
        if cache_key not in self._cache_times:
            return False
        
        return time.time() - self._cache_times[cache_key] < self._cache_ttl
    
    def _clean_cache(self):
        """Limpiar entradas de cache expiradas."""
        current_time = time.time()
        expired_keys = [
            key for key, cache_time in self._cache_times.items()
            if current_time - cache_time > self._cache_ttl
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._cache_times.pop(key, None)
    
    def send_message(self, message, use_cache=True, **kwargs):
        """Enviar mensaje con cache y optimizaciones."""
        payload = {
            "model": kwargs.get("model", "tu-modelo"),
            "messages": [{"role": "user", "content": message}],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 150)
        }
        
        # Verificar cache si está habilitado
        if use_cache:
            cache_key = self._get_cache_key(payload)
            
            if self._is_cache_valid(cache_key):
                cached_result = self._cache[cache_key]
                cached_result["cached"] = True
                return cached_result
        
        # Limpiar cache periódicamente
        if len(self._cache) > self.cache_size:
            self._clean_cache()
        
        try:
            start_time = time.time()
            
            response = self.session.post(
                f"{self.base_url}/llm/message",
                json=payload,
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                result = {
                    "success": True,
                    "response": data["response"],
                    "tokens_used": data.get("tokens_used"),
                    "processing_time": data.get("processing_time"),
                    "network_time": response_time,
                    "cached": False
                }
                
                # Guardar en cache
                if use_cache:
                    self._cache[cache_key] = result.copy()
                    self._cache_times[cache_key] = time.time()
                
                return result
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "network_time": response_time
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def batch_send_messages(self, messages_list, **common_kwargs):
        """Enviar múltiples mensajes de forma optimizada."""
        results = []
        
        for message_data in messages_list:
            if isinstance(message_data, str):
                message = message_data
                kwargs = common_kwargs
            else:
                message = message_data.get("message", "")
                kwargs = {**common_kwargs, **message_data.get("kwargs", {})}
            
            result = self.send_message(message, **kwargs)
            results.append(result)
        
        return results
    
    def health_check(self):
        """Health check optimizado."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return {
                "available": response.status_code == 200,
                "data": response.json() if response.status_code == 200 else None
            }
        except:
            return {"available": False, "data": None}
    
    def close(self):
        """Cerrar sesión y limpiar recursos."""
        self.session.close()
        self._cache.clear()
        self._cache_times.clear()

# Uso como singleton
_llm_client = None

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = ProductionLLMClient()
    return _llm_client

# Ejemplo de uso
if __name__ == "__main__":
    client = get_llm_client()
    
    # Mensaje simple
    result1 = client.send_message("¿Qué es Python?")
    print(f"Primera llamada: {result1}")
    
    # Misma pregunta (debería usar cache)
    result2 = client.send_message("¿Qué es Python?")
    print(f"Segunda llamada (cached): {result2}")
    
    # Batch de mensajes
    messages = [
        "¿Qué es JavaScript?",
        "¿Qué es React?",
        "¿Qué es Node.js?"
    ]
    
    batch_results = client.batch_send_messages(messages, temperature=0.5)
    for i, result in enumerate(batch_results):
        print(f"Batch {i+1}: {result['success']}")
    
    # Limpiar al final
    client.close()
```

Esta documentación proporciona ejemplos completos y prácticos para integrar tu Servicio LLM en diferentes tipos de aplicaciones. Cada ejemplo incluye manejo de errores, optimizaciones y mejores prácticas para uso en producción. 🚀