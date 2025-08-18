#!/usr/bin/env python3
"""
Script para probar manualmente la conexión con LM Studio.
Ejecutar: python scripts/test_llm_connection.py
"""
import asyncio
import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path para importar app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.llm_service import LLMService
from app.models import LLMRequest, Message, MessageRole
from app.config import settings
import httpx

class LLMConnectionTester:
    """Tester para validar conexión con LM Studio."""
    
    def __init__(self):
        self.service = LLMService()
        self.results = []
    
    def print_header(self, title):
        """Imprimir header decorado."""
        print(f"\n{'='*60}")
        print(f"🔧 {title}")
        print(f"{'='*60}")
    
    def print_result(self, test_name, success, message="", details=None):
        """Imprimir resultado de test."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if message:
            print(f"   💡 {message}")
        if details:
            for key, value in details.items():
                print(f"   📊 {key}: {value}")
        
        self.results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "details": details or {}
        })
    
    def check_lm_studio_server(self):
        """Verificar si el servidor LM Studio está corriendo."""
        self.print_header("VERIFICACIÓN DEL SERVIDOR LM STUDIO")
        
        try:
            url = f"http://{settings.lm_studio_host}:{settings.lm_studio_port}"
            response = httpx.get(f"{url}/v1/models", timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                model_count = len(models.get('data', []))
                self.print_result(
                    "Servidor LM Studio accesible",
                    True,
                    f"Respondiendo en {url}",
                    {"Modelos disponibles": model_count}
                )
                
                if model_count > 0:
                    for i, model in enumerate(models.get('data', [])[:3]):  # Mostrar máximo 3
                        print(f"   🤖 Modelo {i+1}: {model.get('id', 'Unknown')}")
                else:
                    self.print_result(
                        "Modelos cargados",
                        False,
                        "No hay modelos cargados en LM Studio"
                    )
                    
                return True
            else:
                self.print_result(
                    "Servidor LM Studio accesible",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except httpx.ConnectError:
            self.print_result(
                "Servidor LM Studio accesible",
                False,
                f"No se pudo conectar a {settings.lm_studio_host}:{settings.lm_studio_port}"
            )
            return False
        except Exception as e:
            self.print_result(
                "Servidor LM Studio accesible",
                False,
                f"Error inesperado: {str(e)}"
            )
            return False
    
    async def test_service_initialization(self):
        """Test inicialización del servicio."""
        self.print_header("INICIALIZACIÓN DEL SERVICIO LLM")
        
        try:
            await self.service.initialize()
            self.print_result(
                "Inicialización del servicio",
                True,
                "Servicio LLM inicializado correctamente"
            )
            return True
        except Exception as e:
            self.print_result(
                "Inicialización del servicio",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_simple_message(self):
        """Test mensaje simple."""
        self.print_header("TEST DE MENSAJE SIMPLE")
        
        try:
            request = LLMRequest(
                model=settings.default_model,
                messages=[
                    Message(role=MessageRole.USER, content="Di exactamente: 'Conexión exitosa'")
                ],
                temperature=0.1,
                max_tokens=20
            )
            
            response = await self.service.send_message(request, "manual-test-1")
            
            self.print_result(
                "Envío de mensaje simple",
                True,
                "Mensaje enviado y respuesta recibida",
                {
                    "Respuesta": f"'{response.response}'",
                    "Tiempo de procesamiento": f"{response.processing_time:.2f}s",
                    "Tokens utilizados": response.tokens_used or "No reportado",
                    "Correlation ID": response.correlation_id
                }
            )
            return True
            
        except Exception as e:
            self.print_result(
                "Envío de mensaje simple",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_conversation(self):
        """Test conversación multi-mensaje."""
        self.print_header("TEST DE CONVERSACIÓN")
        
        try:
            request = LLMRequest(
                model=settings.default_model,
                messages=[
                    Message(role=MessageRole.SYSTEM, content="Responde de forma concisa en español."),
                    Message(role=MessageRole.USER, content="¿Cuál es la capital de Francia?"),
                    Message(role=MessageRole.ASSISTANT, content="París"),
                    Message(role=MessageRole.USER, content="¿Cuántos habitantes tiene aproximadamente?")
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            response = await self.service.send_message(request, "manual-test-2")
            
            # Verificar que la respuesta sea sobre población
            population_keywords = ["millón", "habitantes", "población", "personas"]
            has_population_info = any(keyword in response.response.lower() for keyword in population_keywords)
            
            self.print_result(
                "Conversación multi-mensaje",
                True,
                "Conversación completada",
                {
                    "Respuesta": f"'{response.response}'",
                    "Contiene info de población": "Sí" if has_population_info else "No",
                    "Tiempo": f"{response.processing_time:.2f}s"
                }
            )
            return True
            
        except Exception as e:
            self.print_result(
                "Conversación multi-mensaje",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_different_parameters(self):
        """Test diferentes parámetros."""
        self.print_header("TEST DE PARÁMETROS")
        
        try:
            # Test temperatura alta
            creative_request = LLMRequest(
                model=settings.default_model,
                messages=[
                    Message(role=MessageRole.USER, content="Inventa una palabra nueva")
                ],
                temperature=0.9,
                max_tokens=30
            )
            
            creative_response = await self.service.send_message(creative_request)
            
            # Test temperatura baja
            precise_request = LLMRequest(
                model=settings.default_model,
                messages=[
                    Message(role=MessageRole.USER, content="¿Cuánto es 2 + 2?")
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            precise_response = await self.service.send_message(precise_request)
            
            self.print_result(
                "Parámetros de temperatura",
                True,
                "Tests con diferentes temperaturas completados",
                {
                    "Respuesta creativa (T=0.9)": f"'{creative_response.response}'",
                    "Respuesta precisa (T=0.1)": f"'{precise_response.response}'",
                    "Tiempo creativa": f"{creative_response.processing_time:.2f}s",
                    "Tiempo precisa": f"{precise_response.processing_time:.2f}s"
                }
            )
            return True
            
        except Exception as e:
            self.print_result(
                "Parámetros de temperatura",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    async def test_health_check(self):
        """Test health check."""
        self.print_header("TEST DE HEALTH CHECK")
        
        try:
            is_healthy = await self.service.health_check()
            uptime = self.service.get_uptime()
            
            self.print_result(
                "Health check",
                is_healthy,
                "Servicio saludable" if is_healthy else "Servicio no saludable",
                {
                    "Estado": "Healthy" if is_healthy else "Unhealthy",
                    "Uptime": f"{uptime:.2f}s"
                }
            )
            return is_healthy
            
        except Exception as e:
            self.print_result(
                "Health check",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def print_summary(self):
        """Imprimir resumen de resultados."""
        self.print_header("RESUMEN DE RESULTADOS")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total de tests: {total_tests}")
        print(f"✅ Exitosos: {passed_tests}")
        print(f"❌ Fallidos: {failed_tests}")
        print(f"📈 Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n🔍 Tests fallidos:")
            for result in self.results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        overall_success = failed_tests == 0
        status_emoji = "🎉" if overall_success else "⚠️"
        status_text = "TODOS LOS TESTS PASARON" if overall_success else "ALGUNOS TESTS FALLARON"
        
        print(f"\n{status_emoji} {status_text}")
        
        return overall_success

async def main():
    """Función principal del tester."""
    print("🚀 INICIANDO TESTS DE CONEXIÓN LLM")
    print(f"🔗 Configuración: {settings.lm_studio_host}:{settings.lm_studio_port}")
    print(f"🤖 Modelo por defecto: {settings.default_model}")
    
    tester = LLMConnectionTester()
    
    # 1. Verificar servidor
    server_ok = tester.check_lm_studio_server()
    
    if not server_ok:
        print("\n❌ No se puede continuar: LM Studio no está disponible")
        print("💡 Asegúrate de que:")
        print("   • LM Studio esté ejecutándose")
        print("   • Esté escuchando en el puerto correcto")
        print("   • Tengas al menos un modelo cargado")
        return False
    
    # 2. Tests del servicio
    await tester.test_service_initialization()
    await tester.test_simple_message()
    await tester.test_conversation()
    await tester.test_different_parameters()
    await tester.test_health_check()
    
    # 3. Resumen
    success = tester.print_summary()
    
    if success:
        print("\n🎯 ¡Tu microservicio está funcionando correctamente con LM Studio!")
    else:
        print("\n🛠️  Hay algunos problemas que necesitan atención.")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
        sys.exit(1)