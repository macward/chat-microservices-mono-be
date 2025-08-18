"""Logging configuration for the Message Service."""

import logging
import sys
from typing import Dict, Any
import structlog
from structlog.typing import FilteringBoundLogger

from app.core.config import settings


def setup_logging() -> FilteringBoundLogger:
    """Configure structured logging for the application."""
    
    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Filter out debug messages in production
            structlog.stdlib.filter_by_level,
            # Add log level to output
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Add service information
            structlog.processors.add_log_level,
            # Include stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exception info
            structlog.dev.set_exc_info,
            # JSON formatting for production, console for development
            structlog.dev.ConsoleRenderer() if settings.debug 
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
    
    # Get logger with service context
    logger = structlog.get_logger(
        service=settings.service_name,
        environment=settings.environment,
        version="1.0.0",
    )
    
    return logger


def get_logger(name: str = None, **kwargs) -> FilteringBoundLogger:
    """Get a logger with additional context."""
    if name:
        logger = structlog.get_logger(name)
    else:
        logger = structlog.get_logger()
    
    if kwargs:
        logger = logger.bind(**kwargs)
    
    return logger


# Create default logger
logger = setup_logging()