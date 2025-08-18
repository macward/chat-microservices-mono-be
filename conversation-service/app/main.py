import uvicorn
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from app.api.v1 import conversations
from app.api.handlers import register_exception_handlers
from app.middleware.auth import AuthenticationMiddleware
from app.utils.logging import setup_logging
from app.utils.metrics import setup_metrics, get_metrics_collector, generate_metrics
from app.config import settings
from app.database import init_mongodb, get_database

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Conversation Service...")
    await init_mongodb()
    setup_metrics()
    logger.info("Conversation Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Conversation Service...")

app = FastAPI(
    title="Conversation Service",
    description="Manages conversations in the Character Chat API ecosystem",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(
    AuthenticationMiddleware,
    exclude_paths=["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]
)

# Register exception handlers
register_exception_handlers(app)

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Enhanced health check endpoint with service dependencies."""
    metrics_collector = get_metrics_collector()
    health_status = {
        "status": "healthy",
        "service": "conversation-service",
        "version": "1.0.0",
        "environment": settings.environment,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": metrics_collector.get_system_metrics()["uptime_seconds"],
        "dependencies": {
            "database": "unknown",
            "auth_service": "unknown",
            "characters_service": "unknown"
        }
    }
    
    # Check database connectivity
    try:
        db = get_database()
        await db.command("ping")
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
        logger.warning(f"Database health check failed: {e}")
    
    # Check external services (simplified)
    try:
        from app.services.external_clients import get_auth_client, get_characters_client
        
        # Auth service check
        auth_client = get_auth_client()
        if auth_client.circuit_breaker.state == "closed":
            health_status["dependencies"]["auth_service"] = "healthy"
        else:
            health_status["dependencies"]["auth_service"] = "degraded"
        
        # Characters service check  
        characters_client = get_characters_client()
        if characters_client.circuit_breaker.state == "closed":
            health_status["dependencies"]["characters_service"] = "healthy"
        else:
            health_status["dependencies"]["characters_service"] = "degraded"
            
    except Exception as e:
        logger.warning(f"External service health check failed: {e}")
        health_status["dependencies"]["auth_service"] = "unknown"
        health_status["dependencies"]["characters_service"] = "unknown"
    
    return health_status


# Prometheus metrics endpoint
@app.get("/metrics", tags=["metrics"])
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    content, content_type = generate_metrics()
    return Response(content=content, media_type=content_type)

# Include routers
app.include_router(
    conversations.router, 
    prefix="/v1/conversations", 
    tags=["conversations"]
)

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "app.main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.environment == "development",
        log_config=None  # Use our custom logging configuration
    )