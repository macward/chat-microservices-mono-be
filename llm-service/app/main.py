import logging
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.models import LLMRequest, LLMResponse, ErrorResponse, HealthResponse
from app.config import settings
from app.services.llm_service import llm_service
from app.exceptions import (
    LLMServiceError, 
    LLMConnectionError, 
    LLMTimeoutError, 
    LLMValidationError,
    LLMRateLimitError
)
from app.middleware import (
    setup_logging, 
    RequestLoggingMiddleware, 
    SecurityHeadersMiddleware,
    RateLimitMiddleware
)

# Configurar logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Inicio
    logger.info("Iniciando servicio LLM...")
    try:
        await llm_service.initialize()
        logger.info("Servicio LLM iniciado correctamente")
    except Exception as e:
        logger.error(f"Error al iniciar servicio LLM: {str(e)}")
        raise
    
    yield
    
    # Cierre
    logger.info("Cerrando servicio LLM...")

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Microservicio FastAPI para integración con LLM usando LM Studio",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Agregar middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls=settings.rate_limit_requests, period=60)

# Manejadores de excepciones personalizados
@app.exception_handler(LLMConnectionError)
async def llm_connection_error_handler(request: Request, exc: LLMConnectionError):
    correlation_id = getattr(request.state, 'correlation_id', None)
    logger.error(f"Error de conexión LLM: {str(exc)}")
    return JSONResponse(
        status_code=503,
        content=ErrorResponse(
            error="Servicio temporalmente no disponible",
            error_code=exc.error_code,
            detail="No se puede conectar al servicio LLM",
            correlation_id=correlation_id
        ).dict()
    )

@app.exception_handler(LLMTimeoutError)
async def llm_timeout_error_handler(request: Request, exc: LLMTimeoutError):
    correlation_id = getattr(request.state, 'correlation_id', None)
    logger.error(f"Timeout en petición LLM: {str(exc)}")
    return JSONResponse(
        status_code=408,
        content=ErrorResponse(
            error="Timeout en la petición",
            error_code=exc.error_code,
            detail="La petición al LLM tardó demasiado en procesarse",
            correlation_id=correlation_id
        ).dict()
    )

@app.exception_handler(LLMValidationError)
async def llm_validation_error_handler(request: Request, exc: LLMValidationError):
    correlation_id = getattr(request.state, 'correlation_id', None)
    logger.error(f"Error de validación: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Error de validación",
            error_code=exc.error_code,
            detail=str(exc),
            correlation_id=correlation_id
        ).dict()
    )

@app.exception_handler(LLMRateLimitError)
async def llm_rate_limit_error_handler(request: Request, exc: LLMRateLimitError):
    correlation_id = getattr(request.state, 'correlation_id', None)
    logger.error(f"Límite de velocidad excedido: {str(exc)}")
    return JSONResponse(
        status_code=429,
        content=ErrorResponse(
            error="Límite de velocidad excedido",
            error_code=exc.error_code,
            detail="Demasiadas peticiones. Intente más tarde.",
            correlation_id=correlation_id
        ).dict()
    )

@app.exception_handler(LLMServiceError)
async def llm_service_error_handler(request: Request, exc: LLMServiceError):
    correlation_id = getattr(request.state, 'correlation_id', None)
    logger.error(f"Error del servicio LLM: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Error interno del servicio",
            error_code=exc.error_code,
            detail=str(exc),
            correlation_id=correlation_id
        ).dict()
    )

@app.get("/", tags=["General"])
async def read_root():
    """Endpoint raíz del servicio"""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Endpoint de verificación de salud del servicio
    
    Verifica:
    - Estado del servicio principal
    - Conectividad con LM Studio
    - Tiempo activo del servicio
    """
    llm_healthy = await llm_service.health_check()
    uptime = llm_service.get_uptime()
    
    health_status = HealthResponse(
        status="healthy" if llm_healthy else "unhealthy",
        timestamp=time.time(),
        version=settings.app_version,
        llm_service="connected" if llm_healthy else "disconnected",
        uptime=uptime
    )
    
    status_code = 200 if llm_healthy else 503
    return JSONResponse(content=health_status.dict(), status_code=status_code)

@app.post("/llm/message", response_model=LLMResponse, tags=["LLM"])
async def send_llm_message(request: LLMRequest, http_request: Request) -> LLMResponse:
    """
    Enviar un mensaje al LLM y recibir una respuesta
    
    Parámetros:
    - **model**: ID del modelo LLM a utilizar
    - **messages**: Lista de mensajes de la conversación (rol y contenido)
    - **temperature**: Controla la aleatoriedad de la respuesta (0.0 a 2.0)
    - **max_tokens**: Número máximo de tokens en la respuesta
    - **top_p**: Parámetro de muestreo núcleo (0.0 a 1.0)
    - **stream**: Modo streaming (actualmente no implementado)
    
    Retorna:
    - **response**: Respuesta generada por el LLM
    - **model**: Modelo utilizado
    - **tokens_used**: Tokens utilizados (si está disponible)
    - **processing_time**: Tiempo de procesamiento en segundos
    - **correlation_id**: ID de correlación de la petición
    """
    correlation_id = getattr(http_request.state, 'correlation_id', None)
    
    try:
        logger.info(
            f"Procesando petición LLM con {len(request.messages)} mensajes",
            extra={"correlation_id": correlation_id}
        )
        
        # Validar tamaño total de la petición
        total_content_length = sum(len(msg.content) for msg in request.messages)
        if total_content_length > settings.max_request_size:
            raise LLMValidationError(f"Contenido demasiado largo: {total_content_length} caracteres (máximo: {settings.max_request_size})")
        
        # Enviar petición al servicio LLM
        response = await llm_service.send_message(request, correlation_id)
        
        logger.info(
            f"Respuesta LLM generada en {response.processing_time:.2f}s",
            extra={"correlation_id": correlation_id}
        )
        
        return response
        
    except (LLMServiceError, LLMConnectionError, LLMTimeoutError, LLMValidationError):
        # Re-lanzar excepciones conocidas para que las manejen los exception handlers
        raise
    except Exception as e:
        logger.error(
            f"Error inesperado en send_llm_message: {str(e)}",
            extra={"correlation_id": correlation_id}
        )
        raise HTTPException(
            status_code=500,
            detail="Error inesperado al procesar la petición"
        )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
