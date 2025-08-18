import logging
import time
import uuid
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.config import settings

def setup_logging():
    """Configurar el sistema de logging estructurado"""
    
    # Configurar formateador
    if settings.log_format == "json":
        # Formateador JSON personalizado
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_obj = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                
                # Agregar información extra si existe
                if hasattr(record, 'correlation_id'):
                    log_obj["correlation_id"] = record.correlation_id
                if hasattr(record, 'method'):
                    log_obj["method"] = record.method
                if hasattr(record, 'url'):
                    log_obj["url"] = record.url
                if hasattr(record, 'status_code'):
                    log_obj["status_code"] = record.status_code
                if hasattr(record, 'process_time'):
                    log_obj["process_time"] = record.process_time
                if hasattr(record, 'client_ip'):
                    log_obj["client_ip"] = record.client_ip
                    
                return json.dumps(log_obj, ensure_ascii=False)
        
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Configurar handler
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    # Configurar logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Limpiar handlers existentes
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)
    
    root_logger.addHandler(handler)
    
    # Configurar loggers específicos
    logging.getLogger("uvicorn.access").disabled = True  # Desactivar logs de acceso de uvicorn

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging de peticiones con IDs de correlación"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generar ID de correlación
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id
        
        start_time = time.time()
        
        # Obtener información del cliente
        client_ip = None
        if request.client:
            client_ip = request.client.host
        
        # Log de inicio de petición
        logger = logging.getLogger(__name__)
        logger.info(
            "Petición iniciada",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # Procesar petición
        try:
            response = await call_next(request)
        except Exception as e:
            # Log de error
            process_time = time.time() - start_time
            logger.error(
                f"Error procesando petición: {str(e)}",
                extra={
                    "correlation_id": correlation_id,
                    "process_time": round(process_time, 4),
                    "error": str(e)
                }
            )
            raise
        
        process_time = time.time() - start_time
        
        # Log de finalización de petición
        logger.info(
            "Petición completada",
            extra={
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "process_time": round(process_time, 4)
            }
        )
        
        # Agregar headers de respuesta
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para agregar headers de seguridad"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Headers de seguridad básicos
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware básico para rate limiting (implementación simple)"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"
        
        current_time = time.time()
        
        # Limpiar entradas antiguas
        if client_ip in self.clients:
            self.clients[client_ip] = [
                timestamp for timestamp in self.clients[client_ip]
                if current_time - timestamp < self.period
            ]
        else:
            self.clients[client_ip] = []
        
        # Verificar límite
        if len(self.clients[client_ip]) >= self.calls:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=429,
                detail="Límite de velocidad excedido. Intente más tarde."
            )
        
        # Registrar petición
        self.clients[client_ip].append(current_time)
        
        return await call_next(request)