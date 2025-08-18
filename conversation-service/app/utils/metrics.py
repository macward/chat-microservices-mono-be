"""
Prometheus metrics configuration for the conversation service.
"""

from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
from prometheus_client.multiprocess import MultiProcessCollector
from typing import Dict, Any, Optional
import time
from datetime import datetime
import os

from app.config import settings


# Define metrics
REQUEST_COUNT = Counter(
    'conversation_service_requests_total',
    'Total number of requests received',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'conversation_service_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

CONVERSATION_OPERATIONS = Counter(
    'conversation_service_operations_total',
    'Total conversation operations',
    ['operation', 'status']
)

DATABASE_OPERATIONS = Counter(
    'conversation_service_database_operations_total',
    'Total database operations',
    ['operation', 'collection', 'status']
)

DATABASE_DURATION = Histogram(
    'conversation_service_database_duration_seconds',
    'Database operation duration in seconds',
    ['operation', 'collection'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

EXTERNAL_SERVICE_CALLS = Counter(
    'conversation_service_external_calls_total',
    'Total external service calls',
    ['service', 'endpoint', 'status_code']
)

EXTERNAL_SERVICE_DURATION = Histogram(
    'conversation_service_external_calls_duration_seconds',
    'External service call duration in seconds',
    ['service', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_CONVERSATIONS = Gauge(
    'conversation_service_active_conversations',
    'Number of active conversations'
)

TOTAL_CONVERSATIONS = Gauge(
    'conversation_service_total_conversations',
    'Total number of conversations'
)

AUTHENTICATION_ATTEMPTS = Counter(
    'conversation_service_auth_attempts_total',
    'Total authentication attempts',
    ['status']
)

VALIDATION_ERRORS = Counter(
    'conversation_service_validation_errors_total',
    'Total validation errors',
    ['field_type']
)

CIRCUIT_BREAKER_STATE = Gauge(
    'conversation_service_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half-open)',
    ['service']
)

APPLICATION_INFO = Info(
    'conversation_service_application',
    'Application information'
)

# Set application info
APPLICATION_INFO.info({
    'version': '1.0.0',
    'environment': settings.environment,
    'service_name': 'conversation-service'
})


class MetricsCollector:
    """Centralized metrics collection and tracking."""
    
    def __init__(self):
        self.start_time = time.time()
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_conversation_operation(self, operation: str, success: bool):
        """Record conversation operation metrics."""
        status = "success" if success else "error"
        CONVERSATION_OPERATIONS.labels(
            operation=operation,
            status=status
        ).inc()
    
    def record_database_operation(
        self,
        operation: str,
        collection: str,
        duration: float,
        success: bool
    ):
        """Record database operation metrics."""
        status = "success" if success else "error"
        
        DATABASE_OPERATIONS.labels(
            operation=operation,
            collection=collection,
            status=status
        ).inc()
        
        DATABASE_DURATION.labels(
            operation=operation,
            collection=collection
        ).observe(duration)
    
    def record_external_service_call(
        self,
        service: str,
        endpoint: str,
        status_code: int,
        duration: float
    ):
        """Record external service call metrics."""
        EXTERNAL_SERVICE_CALLS.labels(
            service=service,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()
        
        EXTERNAL_SERVICE_DURATION.labels(
            service=service,
            endpoint=endpoint
        ).observe(duration)
    
    def update_conversation_counts(self, active_count: int, total_count: int):
        """Update conversation count gauges."""
        ACTIVE_CONVERSATIONS.set(active_count)
        TOTAL_CONVERSATIONS.set(total_count)
    
    def record_authentication_attempt(self, success: bool):
        """Record authentication attempt metrics."""
        status = "success" if success else "failure"
        AUTHENTICATION_ATTEMPTS.labels(status=status).inc()
    
    def record_validation_error(self, field_type: str):
        """Record validation error metrics."""
        VALIDATION_ERRORS.labels(field_type=field_type).inc()
    
    def update_circuit_breaker_state(self, service: str, state: str):
        """Update circuit breaker state metrics."""
        state_value = {
            "closed": 0,
            "open": 1,
            "half_open": 2
        }.get(state.lower(), 0)
        
        CIRCUIT_BREAKER_STATE.labels(service=service).set(state_value)
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics for health checks."""
        uptime = time.time() - self.start_time
        
        try:
            # Safely access Counter values using _value._value if available
            total_requests = 0
            try:
                for metric in REQUEST_COUNT._value._metrics.values():
                    total_requests += metric._value
            except (AttributeError, TypeError):
                total_requests = 0
            
            # Safely access Gauge values
            try:
                active_conversations = ACTIVE_CONVERSATIONS._value._value
            except (AttributeError, TypeError):
                active_conversations = 0
                
            try:
                total_conversations = TOTAL_CONVERSATIONS._value._value
            except (AttributeError, TypeError):
                total_conversations = 0
            
            # Safely access database operations counter
            database_operations = 0
            try:
                for metric in DATABASE_OPERATIONS._value._metrics.values():
                    database_operations += metric._value
            except (AttributeError, TypeError):
                database_operations = 0
            
            # Safely access external service calls counter
            external_service_calls = 0
            try:
                for metric in EXTERNAL_SERVICE_CALLS._value._metrics.values():
                    external_service_calls += metric._value
            except (AttributeError, TypeError):
                external_service_calls = 0
                
        except Exception:
            # Fallback values if metrics can't be accessed
            total_requests = 0
            active_conversations = 0
            total_conversations = 0
            database_operations = 0
            external_service_calls = 0
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_requests": total_requests,
            "active_conversations": active_conversations,
            "total_conversations": total_conversations,
            "database_operations": database_operations,
            "external_service_calls": external_service_calls
        }


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(self, collector: MetricsCollector, method: str, endpoint: str):
        self.collector = collector
        self.method = method
        self.endpoint = endpoint
        self.start_time = None
        self.status_code = 200
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        # Set status code based on exception
        if exc_type is not None:
            self.status_code = 500
        
        self.collector.record_request(
            self.method,
            self.endpoint,
            self.status_code,
            duration
        )
    
    def set_status_code(self, status_code: int):
        """Set the response status code."""
        self.status_code = status_code


class DatabaseTimer:
    """Context manager for timing database operations."""
    
    def __init__(self, collector: MetricsCollector, operation: str, collection: str):
        self.collector = collector
        self.operation = operation
        self.collection = collection
        self.start_time = None
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.success = False
        
        self.collector.record_database_operation(
            self.operation,
            self.collection,
            duration,
            self.success
        )
    
    def set_success(self, success: bool):
        """Set the operation success status."""
        self.success = success


class ExternalServiceTimer:
    """Context manager for timing external service calls."""
    
    def __init__(self, collector: MetricsCollector, service: str, endpoint: str):
        self.collector = collector
        self.service = service
        self.endpoint = endpoint
        self.start_time = None
        self.status_code = 200
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            self.status_code = 500
        
        self.collector.record_external_service_call(
            self.service,
            self.endpoint,
            self.status_code,
            duration
        )
    
    def set_status_code(self, status_code: int):
        """Set the response status code."""
        self.status_code = status_code


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    return metrics_collector


def generate_metrics() -> tuple[str, str]:
    """Generate Prometheus metrics output."""
    if os.environ.get('PROMETHEUS_MULTIPROC_DIR'):
        # Multi-process mode
        registry = CollectorRegistry()
        MultiProcessCollector(registry)
        return generate_latest(registry), CONTENT_TYPE_LATEST
    else:
        # Single process mode
        return generate_latest(), CONTENT_TYPE_LATEST


def setup_metrics():
    """Initialize metrics collection."""
    # Set initial gauge values
    ACTIVE_CONVERSATIONS.set(0)
    TOTAL_CONVERSATIONS.set(0)
    
    # Initialize circuit breaker states
    CIRCUIT_BREAKER_STATE.labels(service="auth-service").set(0)
    CIRCUIT_BREAKER_STATE.labels(service="characters-service").set(0)