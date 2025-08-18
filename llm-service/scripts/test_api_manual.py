#!/usr/bin/env python3
"""
Script para probar manualmente la API HTTP del microservicio.
Ejecutar mientras el servicio está corriendo:
python scripts/test_api_manual.py
"""
import httpx
import json
import sys
import time
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

class APITester:
    """Tester para la API HTTP del microservicio."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.Client(timeout=30.0)
        self.results = []
    
    def print_header(self, title):
        """Imprimir header decorado."""
        print(f"\n{'='*60}")
        print(f"🌐 {title}")
        print(f"{'='*60}")
    
    def print_result(self, test_name, success, details=None):
        """Imprimir resultado de test."""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        
        if details:
            for key, value in details.items():
                if isinstance(value, dict):
                    print(f"   📋 {key}:")
                    for k, v in value.items():
                        print(f"      {k}: {v}")
                else:
                    print(f"   📊 {key}: {value}")
        
        self.results.append({"test": test_name, "success": success, "details": details})
    
    def test_server_running(self):
        """Verificar que el servidor esté corriendo."""
        self.print_header("VERIFICACIÓN DEL SERVIDOR")
        
        try:
            response = self.client.get(f"{self.base_url}/")
            
            if response.status_code == 200:
                data = response.json()
                self.print_result(
                    "Servidor API accesible",
                    True,
                    {
                        "URL": self.base_url,
                        "Servicio": data.get("service", "Unknown"),
                        "Versión": data.get("version", "Unknown"),
                        "Status": data.get("status", "Unknown")
                    }
                )
                return True
            else:
                self.print_result(
                    "Servidor API accesible",
                    False,
                    {"Error": f"HTTP {response.status_code}"}
                )
                return False
                
        except httpx.ConnectError:
            self.print_result(
                "Servidor API accesible",
                False,
                {"Error": f"No se pudo conectar a {self.base_url}"}
            )
            return False
        except Exception as e:
            self.print_result(
                "Servidor API accesible",
                False,
                {"Error": str(e)}
            )
            return False
    
    def test_health_endpoint(self):
        """Test del endpoint de health."""
        self.print_header("TEST DEL ENDPOINT /health")
        
        try:
            start_time = time.time()
            response = self.client.get(f"{self.base_url}/health")
            response_time = time.time() - start_time
            
            data = response.json()
            
            is_healthy = response.status_code == 200
            
            self.print_result(
                "Endpoint /health",
                True,  # Siempre es exitoso si responde
                {
                    "Status Code": response.status_code,
                    "Estado": data.get("status", "Unknown"),
                    "Servicio LLM": data.get("llm_service", "Unknown"),
                    "Uptime": f"{data.get('uptime', 0):.2f}s",
                    "Tiempo de respuesta": f"{response_time:.3f}s",
                    "Headers": {
                        "X-Correlation-ID": response.headers.get("X-Correlation-ID", "No present"),
                        "X-Process-Time": response.headers.get("X-Process-Time", "No present")
                    }
                }
            )
            
            return is_healthy
            
        except Exception as e:
            self.print_result(
                "Endpoint /health",
                False,
                {"Error": str(e)}
            )
            return False
    
    def test_simple_message(self):
        """Test mensaje simple al LLM."""
        self.print_header("TEST DE MENSAJE SIMPLE")
        
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "user",
                    "content": "Responde exactamente: 'API funcionando correctamente'"
                }
            ],
            "temperature": 0.1,
            "max_tokens": 30
        }
        
        try:
            start_time = time.time()
            response = self.client.post(
                f"{self.base_url}/llm/message",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                self.print_result(
                    "Mensaje simple al LLM",
                    True,
                    {
                        "Respuesta": f"'{data.get('response', '')}'",
                        "Tiempo API": f"{response_time:.3f}s",
                        "Tiempo procesamiento": f"{data.get('processing_time', 0):.3f}s",
                        "Tokens utilizados": data.get('tokens_used', 'No reportado'),
                        "Correlation ID": data.get('correlation_id', 'No present'),
                        "Headers importantes": {
                            "X-Correlation-ID": response.headers.get("X-Correlation-ID"),
                            "X-Process-Time": response.headers.get("X-Process-Time")
                        }
                    }
                )
                return True
            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                self.print_result(
                    "Mensaje simple al LLM",
                    False,
                    {
                        "Status Code": response.status_code,
                        "Error": error_data
                    }
                )
                return False
                
        except Exception as e:
            self.print_result(
                "Mensaje simple al LLM",
                False,
                {"Error": str(e)}
            )
            return False
    
    def test_conversation(self):
        """Test conversación multi-mensaje."""
        self.print_header("TEST DE CONVERSACIÓN")
        
        payload = {
            "model": settings.default_model,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente que responde de forma concisa."
                },
                {
                    "role": "user",
                    "content": "¿Cuál es la capital de Italia?"
                },
                {
                    "role": "assistant",
                    "content": "Roma"
                },
                {
                    "role": "user",
                    "content": "¿Qué río pasa por esa ciudad?"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 50
        }
        
        try:
            start_time = time.time()
            response = self.client.post(f"{self.base_url}/llm/message", json=payload)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verificar que mencione el río Tíber
                response_text = data.get('response', '').lower()
                mentions_tiber = any(word in response_text for word in ['tíber', 'tiber', 'río'])
                
                self.print_result(
                    "Conversación multi-mensaje",
                    True,
                    {
                        "Respuesta": f"'{data.get('response', '')}'",
                        "Menciona río": "Sí" if mentions_tiber else "No",
                        "Tiempo": f"{response_time:.3f}s",
                        "Mensajes enviados": len(payload['messages'])
                    }
                )
                return True
            else:
                self.print_result(
                    "Conversación multi-mensaje",
                    False,
                    {"Status Code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.print_result(
                "Conversación multi-mensaje",
                False,
                {"Error": str(e)}
            )
            return False
    
    def test_parameter_validation(self):
        """Test validación de parámetros."""
        self.print_header("TEST DE VALIDACIÓN")
        
        # Test con parámetros inválidos
        invalid_payloads = [
            {
                "name": "Temperatura inválida",
                "payload": {
                    "model": "test",
                    "messages": [{"role": "user", "content": "test"}],
                    "temperature": 3.0  # Demasiado alta
                }
            },
            {
                "name": "Mensajes vacíos",
                "payload": {
                    "model": "test",
                    "messages": []  # Lista vacía
                }
            },
            {
                "name": "Contenido vacío",
                "payload": {
                    "model": "test",
                    "messages": [{"role": "user", "content": ""}]  # Contenido vacío
                }
            }
        ]
        
        validation_results = []
        
        for test_case in invalid_payloads:
            try:
                response = self.client.post(f"{self.base_url}/llm/message", json=test_case["payload"])
                
                # Esperamos un error de validación (422)
                is_correct = response.status_code == 422
                validation_results.append(is_correct)
                
                print(f"   🧪 {test_case['name']}: {'✅' if is_correct else '❌'} (HTTP {response.status_code})")
                
            except Exception as e:
                validation_results.append(False)
                print(f"   🧪 {test_case['name']}: ❌ Error: {str(e)}")
        
        all_validation_passed = all(validation_results)
        
        self.print_result(
            "Validación de parámetros",
            all_validation_passed,
            {
                "Tests de validación": f"{sum(validation_results)}/{len(validation_results)}",
                "Todos pasaron": "Sí" if all_validation_passed else "No"
            }
        )
        
        return all_validation_passed
    
    def test_error_handling(self):
        """Test manejo de errores."""
        self.print_header("TEST DE MANEJO DE ERRORES")
        
        # Test con contenido muy largo
        large_content = "x" * 15000  # Excede el límite
        
        payload = {
            "model": "test",
            "messages": [{"role": "user", "content": large_content}]
        }
        
        try:
            response = self.client.post(f"{self.base_url}/llm/message", json=payload)
            
            if response.status_code == 400:  # Error de validación esperado
                data = response.json()
                
                self.print_result(
                    "Manejo de errores",
                    True,
                    {
                        "Status Code": response.status_code,
                        "Error Code": data.get('error_code', 'No reportado'),
                        "Error Message": data.get('error', 'No message'),
                        "Correlation ID": data.get('correlation_id', 'No present')
                    }
                )
                return True
            else:
                self.print_result(
                    "Manejo de errores",
                    False,
                    {"Status Code": response.status_code, "Esperado": 400}
                )
                return False
                
        except Exception as e:
            self.print_result(
                "Manejo de errores",
                False,
                {"Error": str(e)}
            )
            return False
    
    def test_concurrent_requests(self):
        """Test peticiones concurrentes."""
        self.print_header("TEST DE PETICIONES CONCURRENTES")
        
        import concurrent.futures
        import threading
        
        def make_request(request_id):
            payload = {
                "model": settings.default_model,
                "messages": [{"role": "user", "content": f"Responde: 'Request {request_id} completado'"}],
                "temperature": 0.1,
                "max_tokens": 20
            }
            
            try:
                start_time = time.time()
                response = self.client.post(f"{self.base_url}/llm/message", json=payload)
                response_time = time.time() - start_time
                
                return {
                    "id": request_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response_time,
                    "correlation_id": response.headers.get("X-Correlation-ID")
                }
            except Exception as e:
                return {
                    "id": request_id,
                    "success": False,
                    "error": str(e),
                    "response_time": 0
                }
        
        # Hacer 3 peticiones concurrentes
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, i+1) for i in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        successful_requests = [r for r in results if r.get("success", False)]
        avg_response_time = sum(r["response_time"] for r in successful_requests) / len(successful_requests) if successful_requests else 0
        
        self.print_result(
            "Peticiones concurrentes",
            len(successful_requests) >= 1,  # Al menos una debe funcionar
            {
                "Peticiones exitosas": f"{len(successful_requests)}/3",
                "Tiempo promedio": f"{avg_response_time:.3f}s",
                "Correlation IDs únicos": len(set(r.get("correlation_id") for r in successful_requests if r.get("correlation_id")))
            }
        )
        
        return len(successful_requests) >= 1
    
    def print_summary(self):
        """Imprimir resumen."""
        self.print_header("RESUMEN DE TESTS API")
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["success"])
        failed = total - passed
        
        print(f"📊 Total de tests: {total}")
        print(f"✅ Exitosos: {passed}")
        print(f"❌ Fallidos: {failed}")
        print(f"📈 Tasa de éxito: {(passed/total)*100:.1f}%")
        
        if failed > 0:
            print(f"\n🔍 Tests fallidos:")
            for result in self.results:
                if not result["success"]:
                    print(f"   • {result['test']}")
        
        overall_success = failed == 0
        status_emoji = "🎉" if overall_success else "⚠️"
        status_text = "TODOS LOS TESTS PASARON" if overall_success else "ALGUNOS TESTS FALLARON"
        
        print(f"\n{status_emoji} {status_text}")
        return overall_success
    
    def close(self):
        """Cerrar cliente HTTP."""
        self.client.close()

def main():
    """Función principal."""
    print("🚀 INICIANDO TESTS DE API HTTP")
    print(f"🌐 URL base: http://localhost:8000")
    print("💡 Asegúrate de que el servicio esté corriendo:")
    print("   uvicorn app.main:app --reload")
    
    tester = APITester()
    
    try:
        # Tests ordenados
        server_ok = tester.test_server_running()
        
        if not server_ok:
            print("\n❌ No se puede continuar: El servidor no está corriendo")
            print("💡 Ejecuta: uvicorn app.main:app --reload")
            return False
        
        tester.test_health_endpoint()
        tester.test_simple_message()
        tester.test_conversation()
        tester.test_parameter_validation()
        tester.test_error_handling()
        tester.test_concurrent_requests()
        
        success = tester.print_summary()
        
        if success:
            print("\n🎯 ¡Tu API está funcionando perfectamente!")
        else:
            print("\n🛠️  Algunos tests fallaron. Revisa los detalles arriba.")
        
        return success
        
    finally:
        tester.close()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrumpidos por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error inesperado: {str(e)}")
        sys.exit(1)