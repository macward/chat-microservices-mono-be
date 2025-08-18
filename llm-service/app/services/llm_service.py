import asyncio
import time
import logging
from typing import Optional, Dict, Any
from lmstudio_client import LMStudioClient

from app.models import LLMRequest, LLMResponse, Message
from app.config import settings
from app.exceptions import (
    LLMServiceError, 
    LLMConnectionError, 
    LLMTimeoutError, 
    LLMModelError
)

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client: Optional[LMStudioClient] = None
        self._start_time = time.time()
        self._initialized = False
    
    async def initialize(self):
        """Inicializar la conexión con el cliente LLM"""
        try:
            base_url = f"http://{settings.lm_studio_host}:{settings.lm_studio_port}"
            self.client = LMStudioClient(base_url=base_url)
            
            # Test de conexión básico
            await self._test_connection()
            
            self._initialized = True
            logger.info(f"Cliente LLM inicializado correctamente: {base_url}")
            
        except Exception as e:
            logger.error(f"Error al inicializar cliente LLM: {str(e)}")
            raise LLMConnectionError(f"No se pudo conectar a LM Studio: {str(e)}")
    
    async def _test_connection(self):
        """Probar la conexión con LM Studio"""
        try:
            # Primero verificar que hay modelos disponibles
            import httpx
            async with httpx.AsyncClient() as client:
                models_response = await client.get(
                    f"http://{settings.lm_studio_host}:{settings.lm_studio_port}/v1/models",
                    timeout=5.0
                )
                
                if models_response.status_code == 200:
                    models_data = models_response.json()
                    available_models = [model["id"] for model in models_data.get("data", [])]
                    
                    if not available_models:
                        raise LLMConnectionError("No hay modelos disponibles en LM Studio")
                    
                    logger.info(f"Modelos disponibles: {available_models}")
                    
                    # Verificar que el modelo por defecto existe
                    if settings.default_model not in available_models:
                        logger.warning(f"Modelo por defecto '{settings.default_model}' no encontrado. Usando '{available_models[0]}'")
                        # Actualizar el modelo por defecto al primer disponible
                        settings.default_model = available_models[0]
                else:
                    raise LLMConnectionError("No se pudo obtener lista de modelos de LM Studio")
            
            # Realizar una petición simple para verificar conectividad
            test_messages = [{"role": "user", "content": "test"}]
            await asyncio.wait_for(
                self._make_request(test_messages, {"max_tokens": 1, "model": settings.default_model}),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            raise LLMConnectionError("Timeout al conectar con LM Studio")
        except Exception as e:
            raise LLMConnectionError(f"Error de conexión: {str(e)}")
    
    async def send_message(self, request: LLMRequest, correlation_id: str = None) -> LLMResponse:
        """Enviar mensaje al LLM y obtener respuesta"""
        if not self._initialized or not self.client:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Convertir mensajes al formato esperado por lmstudio-client
            messages_dict = [{"role": msg.role.value, "content": msg.content} for msg in request.messages]
            
            # Preparar parámetros para la petición
            kwargs = {}
            if request.temperature is not None:
                kwargs["temperature"] = request.temperature
            if request.max_tokens is not None:
                kwargs["max_tokens"] = request.max_tokens
            if request.top_p is not None:
                kwargs["top_p"] = request.top_p
            
            # Asegurar que siempre se especifique un modelo
            model_to_use = request.model if request.model else settings.default_model
            kwargs["model"] = model_to_use
                
            # Enviar petición con reintentos
            response_data = await self._send_with_retry(messages_dict, kwargs)
            
            processing_time = time.time() - start_time
            
            # Extraer el contenido de la respuesta
            response_content = self._extract_response_content(response_data)
            
            return LLMResponse(
                response=response_content,
                model=request.model,
                tokens_used=self._extract_tokens_used(response_data),
                processing_time=round(processing_time, 3),
                correlation_id=correlation_id
            )
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout en petición LLM después de {settings.lm_studio_timeout}s")
            raise LLMTimeoutError("Timeout en la petición al LLM")
        except Exception as e:
            logger.error(f"Error en servicio LLM: {str(e)}")
            raise LLMServiceError(f"Error procesando petición: {str(e)}")
    
    async def _send_with_retry(self, messages: list, kwargs: dict, retry_count: int = 0) -> dict:
        """Enviar petición con lógica de reintentos"""
        try:
            response = await asyncio.wait_for(
                self._make_request(messages, kwargs),
                timeout=settings.lm_studio_timeout
            )
            return response
            
        except Exception as e:
            if retry_count < settings.lm_studio_max_retries:
                retry_delay = 2 ** retry_count  # Backoff exponencial
                logger.warning(f"Reintento {retry_count + 1} para petición LLM en {retry_delay}s: {str(e)}")
                await asyncio.sleep(retry_delay)
                return await self._send_with_retry(messages, kwargs, retry_count + 1)
            raise e
    
    async def _make_request(self, messages: list, kwargs: dict) -> dict:
        """Realizar petición al cliente LLM"""
        try:
            # Extraer el modelo de kwargs si existe
            model = kwargs.pop("model", settings.default_model)
            
            # Realizar petición con el modelo especificado
            response = self.client.generate_with_messages(messages, model=model, **kwargs)
            return response
        except Exception as e:
            logger.error(f"Error en petición a LM Studio: {str(e)}")
            raise LLMModelError(f"Error del modelo LLM: {str(e)}")
    
    def _extract_response_content(self, response_data: Any) -> str:
        """Extraer el contenido de la respuesta del LLM"""
        if isinstance(response_data, dict):
            # Formato OpenAI
            if "choices" in response_data and response_data["choices"]:
                choice = response_data["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
            
            # Formato directo
            if "text" in response_data:
                return response_data["text"]
            if "content" in response_data:
                return response_data["content"]
        
        # Fallback: convertir toda la respuesta a string
        return str(response_data)
    
    def _extract_tokens_used(self, response_data: Any) -> Optional[int]:
        """Extraer el número de tokens utilizados de la respuesta"""
        if isinstance(response_data, dict):
            if "usage" in response_data and "total_tokens" in response_data["usage"]:
                return response_data["usage"]["total_tokens"]
        return None
    
    async def health_check(self) -> bool:
        """Verificar el estado de salud del servicio LLM"""
        try:
            if not self._initialized or not self.client:
                return False
            
            # Test simple de conectividad
            test_messages = [{"role": "user", "content": "ping"}]
            await asyncio.wait_for(
                self._make_request(test_messages, {"max_tokens": 1, "model": settings.default_model}),
                timeout=5.0
            )
            return True
            
        except Exception as e:
            logger.error(f"Health check falló: {str(e)}")
            return False
    
    def get_uptime(self) -> float:
        """Obtener el tiempo activo del servicio en segundos"""
        return time.time() - self._start_time

# Instancia global del servicio
llm_service = LLMService()