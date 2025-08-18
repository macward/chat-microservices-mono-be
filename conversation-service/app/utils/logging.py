"""
Structured logging configuration for the conversation service.

This module provides security-focused logging with proper sanitization,
audit trails, and monitoring capabilities for security events.
"""

import logging
import logging.config
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from app.config import settings


class SecurityFormatter(logging.Formatter):
    """Custom formatter for security-related logs with sanitization."""
    
    def __init__(self):
        super().__init__()
        self.sensitive_fields = {
            'password', 'secret', 'token', 'key', 'auth', 'session',
            'private_key', 'api_key', 'access_token', 'refresh_token',
            'authorization', 'x-api-key'
        }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with security sanitization."""
        # Create a copy of the record to avoid modifying the original
        record_dict = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields from the record
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in record_dict and not key.startswith('_'):
                    record_dict[key] = self._sanitize_value(key, value)
        
        # Add exception info if present
        if record.exc_info:
            record_dict['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None
            }
        
        return json.dumps(record_dict, default=str, ensure_ascii=False)
    
    def _sanitize_value(self, key: str, value: Any) -> Any:
        """Sanitize sensitive values in log records."""
        if isinstance(key, str) and any(
            sensitive in key.lower() for sensitive in self.sensitive_fields
        ):
            return "[REDACTED]"
        
        if isinstance(value, dict):
            return {k: self._sanitize_value(k, v) for k, v in value.items()}
        
        if isinstance(value, list):
            return [self._sanitize_value(f"item_{i}", item) for i, item in enumerate(value)]
        
        if isinstance(value, str) and len(value) > 1000:
            return value[:997] + "..."
        
        return value


class AuditLogger:
    """Specialized logger for audit trails and security events."""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.security_logger = logging.getLogger("security")
    
    def log_conversation_created(
        self,
        conversation_id: str,
        user_id: str,
        character_id: str,
        ip_address: Optional[str] = None
    ):
        """Log conversation creation for audit trail."""
        self.logger.info(
            "Conversation created",
            extra={
                "event_type": "CONVERSATION_CREATED",
                "conversation_id": conversation_id,
                "user_id": self._safe_id(user_id),
                "character_id": self._safe_id(character_id),
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_conversation_updated(
        self,
        conversation_id: str,
        user_id: str,
        modified_fields: list,
        ip_address: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log conversation updates for audit trail."""
        extra_data = {
            "event_type": "CONVERSATION_UPDATED",
            "conversation_id": conversation_id,
            "user_id": self._safe_id(user_id),
            "modified_fields": modified_fields,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if additional_data:
            extra_data.update(additional_data)
        
        self.logger.info(
            "Conversation updated",
            extra=extra_data
        )
    
    def log_conversation_deleted(
        self,
        conversation_id: str,
        user_id: str,
        ip_address: Optional[str] = None
    ):
        """Log conversation deletion for audit trail."""
        self.logger.warning(
            "Conversation deleted",
            extra={
                "event_type": "CONVERSATION_DELETED",
                "conversation_id": conversation_id,
                "user_id": self._safe_id(user_id),
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_access_attempt(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log resource access attempts for security monitoring."""
        log_level = logging.INFO if success else logging.WARNING
        self.security_logger.log(
            log_level,
            f"Access attempt: {action} {resource_type}",
            extra={
                "event_type": "ACCESS_ATTEMPT",
                "user_id": self._safe_id(user_id),
                "resource_type": resource_type,
                "resource_id": self._safe_id(resource_id),
                "action": action,
                "success": success,
                "ip_address": ip_address,
                "user_agent": user_agent[:100] if user_agent else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_validation_failure(
        self,
        field_name: str,
        field_value: Optional[str],
        error_message: str,
        ip_address: Optional[str] = None
    ):
        """Log validation failures for security analysis."""
        self.security_logger.info(
            f"Validation failure: {field_name}",
            extra={
                "event_type": "VALIDATION_FAILURE",
                "field_name": field_name,
                "field_value": field_value[:50] if field_value else None,
                "error_message": error_message,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = "medium",
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """Log security events for monitoring and alerting."""
        log_level = {
            "low": logging.INFO,
            "medium": logging.WARNING,
            "high": logging.ERROR,
            "critical": logging.CRITICAL
        }.get(severity.lower(), logging.WARNING)
        
        self.security_logger.log(
            log_level,
            f"Security event: {event_type} - {description}",
            extra={
                "event_type": event_type,
                "description": description,
                "severity": severity,
                "user_id": self._safe_id(user_id) if user_id else None,
                "ip_address": ip_address,
                "additional_data": additional_data or {},
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def log_rate_limit_exceeded(
        self,
        identifier: str,
        limit_type: str,
        current_count: int,
        limit_value: int,
        ip_address: Optional[str] = None
    ):
        """Log rate limit violations."""
        self.security_logger.warning(
            f"Rate limit exceeded: {limit_type}",
            extra={
                "event_type": "RATE_LIMIT_EXCEEDED",
                "identifier": self._safe_id(identifier),
                "limit_type": limit_type,
                "current_count": current_count,
                "limit_value": limit_value,
                "ip_address": ip_address,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _safe_id(self, identifier: str) -> str:
        """Safely log identifiers by truncating for privacy."""
        if not identifier:
            return ""
        return identifier[:8] + "..." if len(identifier) > 8 else identifier


def setup_logging():
    """Configure structured logging for the application."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Clear all existing log files on startup
    import glob
    import os
    for log_file in glob.glob(str(log_dir / "*.log*")):
        try:
            os.remove(log_file)
        except OSError:
            pass  # Ignore if file doesn't exist or can't be deleted
    
    # Logging configuration
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            },
            "json": {
                "()": "app.utils.logging.SecurityFormatter"
            }
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "stream": sys.stdout
            },
            "file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": log_dir / "app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "security_file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": log_dir / "security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10  # Keep more security logs
            },
            "audit_file": {
                "level": "INFO",
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "json",
                "filename": log_dir / "audit.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 20  # Keep many audit logs
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False
            },
            "security": {
                "handlers": ["security_file", "console"],
                "level": "INFO",
                "propagate": False
            },
            "audit": {
                "handlers": ["audit_file"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn.access": {
                "handlers": ["file"],
                "level": "INFO",
                "propagate": False
            }
        }
    }
    
    # Adjust log levels based on environment
    if settings.environment == "development":
        config["loggers"][""]["level"] = "DEBUG"
        config["handlers"]["console"]["level"] = "DEBUG"
    elif settings.environment == "production":
        # In production, only log to files (not console)
        config["loggers"][""]["handlers"] = ["file"]
        config["loggers"]["security"]["handlers"] = ["security_file"]
    
    logging.config.dictConfig(config)
    
    # Log the logging setup
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured for environment: {settings.environment}",
        extra={
            "environment": settings.environment,
            "log_directory": str(log_dir.absolute())
        }
    )


# Global audit logger instance
audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    return audit_logger