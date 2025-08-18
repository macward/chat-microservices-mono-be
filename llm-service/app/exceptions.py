"""
Excepciones personalizadas para el servicio LLM
"""

class LLMServiceError(Exception):
    """Excepción base para errores del servicio LLM"""
    def __init__(self, message: str, error_code: str = "LLM_SERVICE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class LLMConnectionError(LLMServiceError):
    """Excepción para errores de conexión con LM Studio"""
    def __init__(self, message: str = "No se pudo conectar con LM Studio"):
        super().__init__(message, "LLM_CONNECTION_ERROR")

class LLMTimeoutError(LLMServiceError):
    """Excepción para timeouts en peticiones al LLM"""
    def __init__(self, message: str = "Timeout en la petición al LLM"):
        super().__init__(message, "LLM_TIMEOUT")

class LLMValidationError(LLMServiceError):
    """Excepción para errores de validación de entrada"""
    def __init__(self, message: str = "Error de validación en los datos de entrada"):
        super().__init__(message, "LLM_VALIDATION_ERROR")

class LLMModelError(LLMServiceError):
    """Excepción para errores relacionados con el modelo LLM"""
    def __init__(self, message: str = "Error en el modelo LLM"):
        super().__init__(message, "LLM_MODEL_ERROR")

class LLMRateLimitError(LLMServiceError):
    """Excepción para errores de límite de velocidad"""
    def __init__(self, message: str = "Límite de velocidad excedido"):
        super().__init__(message, "LLM_RATE_LIMIT_ERROR")