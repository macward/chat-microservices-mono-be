"""
Tests de conexión real con LM Studio.
Estos tests requieren que LM Studio esté ejecutándose y tenga un modelo cargado.

Para ejecutar estos tests:
1. Asegúrate de que LM Studio esté ejecutándose en localhost:1234
2. Carga un modelo en LM Studio
3. Ejecuta: pytest tests/test_real_llm_connection.py -v

Para saltar estos tests automáticamente:
pytest -m "not real_llm"
"""
import pytest
import asyncio
import os
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_service import LLMService
from app.models import LLMRequest, Message, MessageRole
from app.config import settings

# Marcador para tests que requieren LM Studio real
pytestmark = pytest.mark.real_llm

def skip_if_no_llm_studio():
    """Skip test if LM Studio is not available."""
    return pytest.mark.skipif(
        os.getenv("SKIP_REAL_LLM_TESTS", "false").lower() == "true",
        reason="Tests de LLM real deshabilitados (SKIP_REAL_LLM_TESTS=true)"
    )

class TestRealLLMConnection:
    """Tests de conexión real con LM Studio."""
    
    @pytest.fixture
    def real_llm_service(self):
        """Crear una instancia real del servicio LLM."""
        service = LLMService()
        return service
    
    @pytest.fixture
    def client(self):
        """Cliente de prueba que usa conexión real."""
        # No mockeamos nada, usamos la aplicación real
        with TestClient(app) as client:
            yield client
    
    @skip_if_no_llm_studio()
    @pytest.mark.asyncio
    async def test_llm_service_initialization(self, real_llm_service):
        """Test que el servicio LLM se puede inicializar con LM Studio real."""
        try:
            await real_llm_service.initialize()
            assert real_llm_service._initialized is True
            assert real_llm_service.client is not None
            print(f"✅ Conexión exitosa con LM Studio en {settings.lm_studio_host}:{settings.lm_studio_port}")
        except Exception as e:
            pytest.fail(f"No se pudo conectar con LM Studio: {str(e)}")
    
    @skip_if_no_llm_studio()
    @pytest.mark.asyncio
    async def test_simple_message_real_llm(self, real_llm_service):
        """Test envío de mensaje simple al LLM real."""
        # Inicializar servicio
        await real_llm_service.initialize()
        
        # Crear petición simple
        request = LLMRequest(
            model=settings.default_model,
            messages=[
                Message(role=MessageRole.USER, content="Hola, responde solo con 'Hola mundo'")
            ],
            temperature=0.1,  # Baja temperatura para respuesta más determinista
            max_tokens=10
        )
        
        # Enviar mensaje
        response = await real_llm_service.send_message(request, "test-real-123")
        
        # Verificar respuesta
        assert response is not None
        assert response.response is not None
        assert len(response.response) > 0
        assert response.correlation_id == "test-real-123"
        assert response.processing_time > 0
        
        print(f"✅ Respuesta del LLM: '{response.response}'")
        print(f"⏱️  Tiempo de procesamiento: {response.processing_time:.2f}s")
        if response.tokens_used:
            print(f"🎫 Tokens utilizados: {response.tokens_used}")
    
    @skip_if_no_llm_studio()
    @pytest.mark.asyncio
    async def test_conversation_real_llm(self, real_llm_service):
        """Test conversación con múltiples mensajes."""
        await real_llm_service.initialize()
        
        request = LLMRequest(
            model=settings.default_model,
            messages=[
                Message(role=MessageRole.SYSTEM, content="Eres un asistente conciso. Responde en español con máximo 20 palabras."),
                Message(role=MessageRole.USER, content="¿Cuál es la capital de Francia?"),
                Message(role=MessageRole.ASSISTANT, content="La capital de Francia es París."),
                Message(role=MessageRole.USER, content="¿Y la de España?")
            ],
            temperature=0.2,
            max_tokens=30
        )
        
        response = await real_llm_service.send_message(request)
        
        assert response is not None
        assert "Madrid" in response.response or "madrid" in response.response.lower()
        
        print(f"✅ Conversación exitosa: '{response.response}'")
    
    @skip_if_no_llm_studio()
    @pytest.mark.asyncio
    async def test_different_parameters_real_llm(self, real_llm_service):
        """Test diferentes parámetros de generación."""
        await real_llm_service.initialize()
        
        # Test con temperatura alta (más creativo)
        creative_request = LLMRequest(
            model=settings.default_model,
            messages=[
                Message(role=MessageRole.USER, content="Inventa una palabra nueva y define su significado.")
            ],
            temperature=0.9,
            max_tokens=50
        )
        
        creative_response = await real_llm_service.send_message(creative_request)
        
        # Test con temperatura baja (más determinista)
        deterministic_request = LLMRequest(
            model=settings.default_model,
            messages=[
                Message(role=MessageRole.USER, content="¿Cuánto es 2 + 2?")
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        deterministic_response = await real_llm_service.send_message(deterministic_request)
        
        assert creative_response is not None
        assert deterministic_response is not None
        assert "4" in deterministic_response.response or "cuatro" in deterministic_response.response.lower()
        
        print(f"🎨 Respuesta creativa: '{creative_response.response}'")
        print(f"🔢 Respuesta determinista: '{deterministic_response.response}'")
    
    @skip_if_no_llm_studio()
    @pytest.mark.asyncio
    async def test_health_check_real_llm(self, real_llm_service):
        """Test health check con LLM real."""
        await real_llm_service.initialize()
        
        is_healthy = await real_llm_service.health_check()
        
        assert is_healthy is True
        
        uptime = real_llm_service.get_uptime()
        assert uptime > 0
        
        print(f"✅ Health check exitoso, uptime: {uptime:.2f}s")

class TestRealAPIEndpoints:
    """Tests de endpoints API con LLM real."""
    
    @skip_if_no_llm_studio()
    def test_health_endpoint_real(self, client):
        """Test endpoint de health con conexión real."""
        response = client.get("/health")
        
        # Puede ser 200 (healthy) o 503 (unhealthy) dependiendo del estado
        assert response.status_code in [200, 503]
        
        data = response.json()
        assert "status" in data
        assert "llm_service" in data
        assert "uptime" in data
        
        print(f"🏥 Health status: {data['status']}")
        print(f"🔗 LLM service: {data['llm_service']}")
    
    @skip_if_no_llm_studio()
    def test_message_endpoint_real(self, client):
        """Test endpoint de mensaje con LLM real."""
        request_payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "user",
                    "content": "Responde exactamente: 'Test exitoso'"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 20
        }
        
        response = client.post("/llm/message", json=request_payload)
        
        # Si LM Studio no está disponible, obtendremos 503
        if response.status_code == 503:
            pytest.skip("LM Studio no disponible")
        
        assert response.status_code == 200
        
        data = response.json()
        assert "response" in data
        assert "processing_time" in data
        
        # Verificar headers
        assert "X-Correlation-ID" in response.headers
        assert "X-Process-Time" in response.headers
        
        print(f"✅ API Response: '{data['response']}'")
        print(f"⏱️  API Processing time: {data['processing_time']:.2f}s")
    
    @skip_if_no_llm_studio()
    def test_large_conversation_real(self, client):
        """Test conversación larga con múltiples intercambios."""
        request_payload = {
            "model": settings.default_model,
            "messages": [
                {"role": "system", "content": "Eres un tutor de matemáticas. Explica paso a paso."},
                {"role": "user", "content": "¿Cómo resuelvo 2x + 5 = 15?"},
                {"role": "assistant", "content": "Para resolver 2x + 5 = 15, primero resta 5 de ambos lados: 2x = 10"},
                {"role": "user", "content": "¿Y ahora qué hago?"},
                {"role": "assistant", "content": "Ahora divide ambos lados entre 2: x = 5"},
                {"role": "user", "content": "¿Puedes verificar la respuesta?"}
            ],
            "temperature": 0.3,
            "max_tokens": 100
        }
        
        response = client.post("/llm/message", json=request_payload)
        
        if response.status_code == 503:
            pytest.skip("LM Studio no disponible")
        
        assert response.status_code == 200
        
        data = response.json()
        # La respuesta debería mencionar verificación o sustitución
        assert any(word in data['response'].lower() for word in ['verific', 'sustituy', 'comprueb', '15'])
        
        print(f"📚 Conversación matemática: '{data['response']}'")

class TestRealLLMPerformance:
    """Tests de rendimiento con LLM real."""
    
    @skip_if_no_llm_studio()
    @pytest.mark.asyncio
    async def test_response_time_real(self, real_llm_service):
        """Test tiempo de respuesta del LLM real."""
        import time
        
        await real_llm_service.initialize()
        
        request = LLMRequest(
            model=settings.default_model,
            messages=[
                Message(role=MessageRole.USER, content="Di 'hola' en 5 idiomas diferentes.")
            ],
            temperature=0.5,
            max_tokens=100
        )
        
        start_time = time.time()
        response = await real_llm_service.send_message(request)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        assert response is not None
        assert total_time < 30.0  # No debería tardar más de 30 segundos
        
        print(f"⚡ Tiempo total de respuesta: {total_time:.2f}s")
        print(f"📊 Tiempo reportado por el servicio: {response.processing_time:.2f}s")
        
        # El tiempo del servicio debería ser menor al tiempo total
        assert response.processing_time <= total_time
    
    @skip_if_no_llm_studio()
    @pytest.mark.asyncio
    async def test_concurrent_requests_real(self, real_llm_service):
        """Test múltiples peticiones concurrentes."""
        await real_llm_service.initialize()
        
        async def send_test_message(message_id):
            request = LLMRequest(
                model=settings.default_model,
                messages=[
                    Message(role=MessageRole.USER, content=f"Responde: 'Mensaje {message_id} procesado'")
                ],
                temperature=0.1,
                max_tokens=20
            )
            return await real_llm_service.send_message(request, f"concurrent-{message_id}")
        
        # Enviar 3 peticiones concurrentes
        tasks = [send_test_message(i) for i in range(1, 4)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verificar que todas las peticiones tuvieron éxito
        successful_responses = [r for r in responses if not isinstance(r, Exception)]
        assert len(successful_responses) >= 1  # Al menos una debería funcionar
        
        for i, response in enumerate(successful_responses):
            print(f"🔄 Respuesta concurrente {i+1}: '{response.response}'")

# Utility function para verificar conectividad antes de tests
def check_lm_studio_availability():
    """Verificar si LM Studio está disponible."""
    import httpx
    try:
        response = httpx.get(f"http://{settings.lm_studio_host}:{settings.lm_studio_port}/v1/models", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

if __name__ == "__main__":
    # Script para verificar conectividad manual
    print("🔍 Verificando conectividad con LM Studio...")
    if check_lm_studio_availability():
        print("✅ LM Studio está disponible")
        print(f"🔗 URL: http://{settings.lm_studio_host}:{settings.lm_studio_port}")
    else:
        print("❌ LM Studio no está disponible")
        print(f"💡 Asegúrate de que LM Studio esté ejecutándose en {settings.lm_studio_host}:{settings.lm_studio_port}")
        print("💡 Y que tengas un modelo cargado")