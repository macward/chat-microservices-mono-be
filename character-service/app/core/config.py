"""
Centralized Configuration Management for Character Chat API

This module implements a comprehensive, security-focused configuration management system
using Pydantic Settings for type-safe environment variable handling. Follows OWASP ASVS 
Level 2 requirements and implements defense-in-depth configuration security.

Security Features:
- Secure secret generation and validation
- Environment-specific security requirements
- Configuration validation with type safety
- No hardcoded secrets in source code
- Audit logging of configuration access
- Environment isolation and validation

Architecture:
- Hierarchical configuration with logical groupings
- Environment-based configuration profiles
- Centralized validation and error handling
- Support for multiple deployment environments
- Integration with dependency injection container

Configuration Categories:
- Database: MongoDB connection and performance settings
- Security: JWT, encryption, authentication, and authorization
- API: FastAPI application configuration and CORS
- LM Studio: Client settings and model configuration
- Logging: Audit trails and security event logging
- Application: Environment, debug, and feature flags
"""

import os
import secrets
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Supported application environments with specific security requirements."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class SecurityConfig(BaseSettings):
    """
    Security configuration implementing OWASP ASVS Level 2 requirements.
    
    Manages JWT tokens, encryption, password hashing, and authentication
    with environment-specific security validation and secure defaults.
    """
    
    # JWT Configuration
    secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(64),
        description="JWT signing secret key (auto-generated if not provided)",
        env="JWT_SECRET_KEY"
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm",
        env="JWT_ALGORITHM"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=480,  # Max 8 hours
        description="JWT access token expiration in minutes",
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        ge=1,
        le=30,
        description="JWT refresh token expiration in days",
        env="REFRESH_TOKEN_EXPIRE_DAYS"
    )
    
    # Password Security
    password_bcrypt_rounds: int = Field(
        default=12,
        ge=10,
        le=15,
        description="Bcrypt rounds for password hashing",
        env="PASSWORD_BCRYPT_ROUNDS"
    )
    password_min_length: int = Field(
        default=8,
        ge=8,
        le=128,
        description="Minimum password length requirement",
        env="PASSWORD_MIN_LENGTH"
    )
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60,
        ge=10,
        le=1000,
        description="API requests per minute per user",
        env="RATE_LIMIT_PER_MINUTE"
    )
    login_rate_limit_per_minute: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Login attempts per minute per IP",
        env="LOGIN_RATE_LIMIT_PER_MINUTE"
    )
    
    # Security Headers and CORS
    allowed_hosts: List[str] = Field(
        default=["*"],
        description="Allowed hosts for CORS",
        env="ALLOWED_HOSTS"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
        env="CORS_ALLOW_CREDENTIALS"
    )
    
    # Security Features
    enforce_https: bool = Field(
        default=False,
        description="Enforce HTTPS in production",
        env="ENFORCE_HTTPS"
    )
    secure_cookies: bool = Field(
        default=False,
        description="Use secure flag for cookies",
        env="SECURE_COOKIES"
    )
    session_timeout_minutes: int = Field(
        default=60,
        ge=15,
        le=480,
        description="Session timeout in minutes",
        env="SESSION_TIMEOUT_MINUTES"
    )
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate JWT secret key strength."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        
        # In production, ensure it's not a default or weak value
        weak_keys = [
            "development-secret-key",
            "your-secret-key-here",
            "changeme",
            "secret",
            "password"
        ]
        if v.lower() in weak_keys:
            raise ValueError("JWT secret key cannot be a default or weak value")
        
        return v
    
    @field_validator('algorithm')
    @classmethod
    def validate_jwt_algorithm(cls, v: str) -> str:
        """Validate JWT algorithm is secure."""
        allowed_algorithms = ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]
        if v not in allowed_algorithms:
            raise ValueError(f"JWT algorithm must be one of {allowed_algorithms}")
        return v
    
    @field_validator('allowed_hosts')
    @classmethod
    def validate_cors_hosts(cls, v: List[str]) -> List[str]:
        """Validate CORS configuration for security."""
        # Note: Environment-specific validation will be handled at the Settings level
        if "*" in v:
            logger.warning("Wildcard CORS origin (*) detected - review for production use")
        
        return v
    
    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


class APIConfig(BaseSettings):
    """
    API configuration for FastAPI application settings.
    
    Manages application metadata, documentation, and API behavior
    with environment-specific defaults and feature flags.
    """
    
    # Application metadata
    title: str = Field(
        default="Character Chat API",
        description="API title",
        env="API_TITLE"
    )
    version: str = Field(
        default="2.0.0",
        description="API version",
        env="API_VERSION"
    )
    description: str = Field(
        default="Advanced character-based chat API with conversation management",
        description="API description",
        env="API_DESCRIPTION"
    )
    
    # Server configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host",
        env="API_HOST"
    )
    port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Server port",
        env="API_PORT"
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload for development",
        env="API_RELOAD"
    )
    
    # Documentation settings
    docs_url: Optional[str] = Field(
        default="/docs",
        description="Swagger documentation URL (None to disable)",
        env="API_DOCS_URL"
    )
    redoc_url: Optional[str] = Field(
        default="/redoc",
        description="ReDoc documentation URL (None to disable)",
        env="API_REDOC_URL"
    )
    openapi_url: Optional[str] = Field(
        default="/openapi.json",
        description="OpenAPI schema URL (None to disable)",
        env="API_OPENAPI_URL"
    )
    
    # Performance settings
    request_timeout_seconds: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds",
        env="API_REQUEST_TIMEOUT"
    )
    max_request_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum request size in MB",
        env="API_MAX_REQUEST_SIZE"
    )
    
    # Feature flags
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection",
        env="API_ENABLE_METRICS"
    )
    enable_health_checks: bool = Field(
        default=True,
        description="Enable health check endpoints",
        env="API_ENABLE_HEALTH_CHECKS"
    )
    
    @field_validator('port')
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number is not privileged."""
        if v < 1024:
            logger.warning(f"Using privileged port {v}, ensure proper permissions")
        return v
    
    class Config:
        env_prefix = "API_"
        case_sensitive = False


class LMStudioConfig(BaseSettings):
    """
    LM Studio client configuration for LLM interactions.
    
    Manages connection settings, model configuration, and performance
    optimization for LM Studio client integration.
    """
    
    # Connection settings
    base_url: str = Field(
        default="http://localhost:1234/v1",
        description="LM Studio server base URL",
        env="LMSTUDIO_BASE_URL"
    )
    timeout_seconds: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Request timeout in seconds",
        env="LMSTUDIO_TIMEOUT"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts",
        env="LMSTUDIO_MAX_RETRIES"
    )
    
    # Model configuration
    default_model: str = Field(
        default="google/gemma-3-12b",
        description="Default model to use",
        env="LMSTUDIO_DEFAULT_MODEL"
    )
    max_tokens: int = Field(
        default=2048,
        ge=100,
        le=8192,
        description="Maximum tokens per response",
        env="LMSTUDIO_MAX_TOKENS"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature for responses",
        env="LMSTUDIO_TEMPERATURE"
    )
    
    # Performance settings
    enable_streaming: bool = Field(
        default=True,
        description="Enable streaming responses",
        env="LMSTUDIO_ENABLE_STREAMING"
    )
    context_window_size: int = Field(
        default=4096,
        ge=1024,
        le=32768,
        description="Context window size for conversations",
        env="LMSTUDIO_CONTEXT_WINDOW"
    )
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Validate LM Studio base URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("LM Studio base URL must start with http:// or https://")
        return v.rstrip('/')
    
    class Config:
        env_prefix = "LMSTUDIO_"
        case_sensitive = False


class LoggingConfig(BaseSettings):
    """
    Logging configuration for audit trails and security events.
    
    Manages log levels, security event logging, and audit trail
    configuration with environment-specific settings.
    """
    
    # Log levels
    log_level: str = Field(
        default="INFO",
        description="Application log level",
        env="LOG_LEVEL"
    )
    security_log_level: str = Field(
        default="INFO",
        description="Security events log level",
        env="SECURITY_LOG_LEVEL"
    )
    
    # File logging
    enable_file_logging: bool = Field(
        default=True,
        description="Enable logging to files",
        env="LOG_ENABLE_FILE"
    )
    log_file_path: str = Field(
        default="logs/app.log",
        description="Application log file path",
        env="LOG_FILE_PATH"
    )
    security_log_file_path: str = Field(
        default="logs/security.log",
        description="Security log file path",
        env="SECURITY_LOG_FILE_PATH"
    )
    audit_log_file_path: str = Field(
        default="logs/audit.log",
        description="Audit log file path",
        env="AUDIT_LOG_FILE_PATH"
    )
    
    # Log rotation
    max_log_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum log file size in MB before rotation",
        env="LOG_MAX_SIZE_MB"
    )
    backup_count: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of backup log files to keep",
        env="LOG_BACKUP_COUNT"
    )
    
    # Security logging
    enable_audit_logging: bool = Field(
        default=True,
        description="Enable audit event logging",
        env="LOG_ENABLE_AUDIT"
    )
    enable_security_logging: bool = Field(
        default=True,
        description="Enable security event logging",
        env="LOG_ENABLE_SECURITY"
    )
    log_sensitive_data: bool = Field(
        default=False,
        description="Allow logging of sensitive data (development only)",
        env="LOG_SENSITIVE_DATA"
    )
    
    @field_validator('log_level', 'security_log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is supported."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator('log_sensitive_data')
    @classmethod
    def validate_sensitive_logging(cls, v: bool) -> bool:
        """Warn about sensitive data logging in production."""
        if v:
            logger.warning("Sensitive data logging is enabled - use only in development")
        return v
    
    class Config:
        env_prefix = "LOG_"
        case_sensitive = False


class ApplicationConfig(BaseSettings):
    """
    Application-level configuration and feature flags.
    
    Manages environment-specific settings, debug flags, and
    application behavior configuration.
    """
    
    # Environment settings
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment",
        env="ENVIRONMENT"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
        env="DEBUG"
    )
    testing: bool = Field(
        default=False,
        description="Enable testing mode",
        env="TESTING"
    )
    
    # Application info
    app_name: str = Field(
        default="Character Chat API",
        description="Application name",
        env="APP_NAME"
    )
    app_description: str = Field(
        default="Advanced character-based chat API",
        description="Application description",
        env="APP_DESCRIPTION"
    )
    
    # Feature flags
    enable_admin_interface: bool = Field(
        default=True,
        description="Enable admin interface",
        env="ENABLE_ADMIN_INTERFACE"
    )
    enable_legacy_endpoints: bool = Field(
        default=True,
        description="Enable legacy API endpoints",
        env="ENABLE_LEGACY_ENDPOINTS"
    )
    enable_rate_limiting: bool = Field(
        default=True,
        description="Enable API rate limiting",
        env="ENABLE_RATE_LIMITING"
    )
    
    # Performance settings
    worker_processes: int = Field(
        default=1,
        ge=1,
        le=16,
        description="Number of worker processes",
        env="WORKER_PROCESSES"
    )
    enable_caching: bool = Field(
        default=True,
        description="Enable application caching",
        env="ENABLE_CACHING"
    )
    cache_ttl_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        description="Default cache TTL in minutes",
        env="CACHE_TTL_MINUTES"
    )
    
    @field_validator('debug')
    @classmethod
    def validate_debug_mode(cls, v: bool, info) -> bool:
        """Ensure debug mode is disabled in production."""
        # Note: Environment-specific validation will be handled at the Settings level
        # This is a basic validation that will be enhanced by model validators
        return v
    
    class Config:
        env_prefix = "APP_"
        case_sensitive = False


class Settings(BaseSettings):
    """
    Main configuration class that aggregates all configuration sections.
    
    Provides centralized access to all application configuration with
    environment-specific validation and secure defaults. Implements
    comprehensive validation and security checks for production deployment.
    """
    
    # Environment detection
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Application environment",
        env="ENVIRONMENT"
    )
    
    # Configuration sections
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    lmstudio: LMStudioConfig = Field(default_factory=LMStudioConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    application: ApplicationConfig = Field(default_factory=ApplicationConfig)
    
    @model_validator(mode='after')
    def validate_environment_consistency(self):
        """Ensure all configuration sections use consistent environment."""
        # Update application config environment to match main environment
        if self.application:
            self.application.environment = self.environment
        
        return self
    
    @model_validator(mode='after')
    def validate_production_security(self):
        """Apply additional security validations for production environment."""
        if self.environment == Environment.PRODUCTION:
            # Production security requirements
            if self.security:
                if not self.security.enforce_https:
                    logger.warning("HTTPS enforcement should be enabled in production")
                
                if not self.security.secure_cookies:
                    logger.warning("Secure cookies should be enabled in production")
                
                if self.security.cors_allow_credentials and "*" in self.security.allowed_hosts:
                    raise ValueError("CORS credentials with wildcard origin is insecure in production")
            
            # Production API requirements
            if self.api:
                if self.api.docs_url or self.api.redoc_url:
                    logger.warning("API documentation should be disabled in production")
                
                if self.api.reload:
                    raise ValueError("Auto-reload must be disabled in production")
            
            # Production debug validation
            if self.application and self.application.debug:
                raise ValueError("Debug mode must be disabled in production")
        
        return self
    
    def get_jwt_secret(self) -> str:
        """Get JWT secret key."""
        return self.security.secret_key
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING
    
    def get_log_level(self) -> str:
        """Get appropriate log level for environment."""
        if self.is_development():
            return "DEBUG"
        elif self.is_production():
            return "WARNING"
        else:
            return "INFO"
    
    def create_directories(self) -> None:
        """Create necessary directories for logs and data."""
        try:
            # Create log directories
            log_paths = [
                self.logging.log_file_path,
                self.logging.security_log_file_path,
                self.logging.audit_log_file_path
            ]
            
            for log_path in log_paths:
                log_dir = Path(log_path).parent
                log_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info("Configuration directories created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create configuration directories: {e}")
            raise
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True


class ConfigManager:
    """
    Configuration manager for secure loading and validation.
    
    Provides centralized configuration management with security validation,
    environment-specific loading, and audit logging of configuration access.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or ".env"
        self._settings: Optional[Settings] = None
        self._loaded = False
    
    def load_settings(self, validate_security: bool = True) -> Settings:
        """
        Load and validate application settings.
        
        Args:
            validate_security: Whether to perform security validation
            
        Returns:
            Settings: Validated configuration settings
            
        Raises:
            ValueError: If configuration validation fails
            RuntimeError: If configuration loading fails
        """
        try:
            logger.info(f"Loading configuration from environment and {self.env_file}")
            
            # Load settings with environment file
            self._settings = Settings(_env_file=self.env_file)
            
            # Create necessary directories
            self._settings.create_directories()
            
            # Perform security validation if requested
            if validate_security:
                self._validate_security_requirements()
            
            self._loaded = True
            
            logger.info(f"Configuration loaded successfully for {self._settings.environment} environment")
            
            # Log configuration summary (without sensitive data)
            self._log_configuration_summary()
            
            return self._settings
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise RuntimeError(f"Configuration loading failed: {str(e)}")
    
    def get_settings(self) -> Settings:
        """
        Get loaded settings instance.
        
        Returns:
            Settings: Current configuration settings
            
        Raises:
            RuntimeError: If settings not loaded
        """
        if not self._loaded or self._settings is None:
            raise RuntimeError("Settings must be loaded before access")
        
        return self._settings
    
    def reload_settings(self) -> Settings:
        """Reload configuration settings."""
        self._loaded = False
        self._settings = None
        return self.load_settings()
    
    def _validate_security_requirements(self) -> None:
        """Perform comprehensive security validation."""
        if not self._settings:
            return
        
        logger.info("Performing security validation on configuration")
        
        # Environment-specific security checks
        if self._settings.is_production():
            self._validate_production_security()
        elif self._settings.environment == Environment.STAGING:
            self._validate_staging_security()
        
        # General security validations
        self._validate_secret_strength()
        self._validate_network_security()
        
        logger.info("Security validation completed successfully")
    
    def _validate_production_security(self) -> None:
        """Validate production-specific security requirements."""
        if not self._settings:
            return
        
        security = self._settings.security
        api = self._settings.api
        
        # Critical production security requirements
        security_issues = []
        
        if len(security.secret_key) < 64:
            security_issues.append("JWT secret key should be at least 64 characters in production")
        
        if not security.enforce_https:
            security_issues.append("HTTPS enforcement must be enabled in production")
        
        if api.docs_url or api.redoc_url:
            security_issues.append("API documentation should be disabled in production")
        
        if self._settings.application.debug:
            security_issues.append("Debug mode must be disabled in production")
        
        if security.password_bcrypt_rounds < 12:
            security_issues.append("Password hashing rounds should be at least 12 in production")
        
        if security_issues:
            raise ValueError(f"Production security validation failed: {'; '.join(security_issues)}")
    
    def _validate_staging_security(self) -> None:
        """Validate staging-specific security requirements."""
        if not self._settings:
            return
        
        # Staging should have production-like security but may allow documentation
        logger.info("Applying staging security validation")
        
        security = self._settings.security
        if len(security.secret_key) < 32:
            raise ValueError("JWT secret key must be at least 32 characters in staging")
    
    def _validate_secret_strength(self) -> None:
        """Validate strength of secret keys and sensitive configuration."""
        if not self._settings:
            return
        
        security = self._settings.security
        
        # Check for weak or default secrets
        weak_indicators = [
            "password", "secret", "key", "changeme", "default",
            "development", "test", "demo", "example"
        ]
        
        secret_lower = security.secret_key.lower()
        for indicator in weak_indicators:
            if indicator in secret_lower:
                logger.warning(f"JWT secret may be weak (contains '{indicator}')")
    
    def _validate_network_security(self) -> None:
        """Validate network and connection security settings."""
        if not self._settings:
            return
        
        security = self._settings.security
        
        # CORS validation
        if "*" in security.allowed_hosts and security.cors_allow_credentials:
            logger.warning("CORS wildcard with credentials is potentially insecure")
    
    def _log_configuration_summary(self) -> None:
        """Log configuration summary without sensitive information."""
        if not self._settings:
            return
        
        try:
            summary = {
                "environment": self._settings.environment.value,
                "debug_mode": self._settings.application.debug,
                "api_host": self._settings.api.host,
                "api_port": self._settings.api.port,
                "documentation_enabled": bool(self._settings.api.docs_url),
                "security_features": {
                    "https_enforced": self._settings.security.enforce_https,
                    "secure_cookies": self._settings.security.secure_cookies,
                    "rate_limiting": self._settings.application.enable_rate_limiting,
                    "audit_logging": self._settings.logging.enable_audit_logging
                },
                "lmstudio_configured": bool(self._settings.lmstudio.base_url)
            }
            
            logger.info(f"Configuration summary: {summary}")
            
        except Exception as e:
            logger.error(f"Failed to log configuration summary: {e}")


# Global configuration manager instance
config_manager = ConfigManager()


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns:
        Settings: Current application settings
    """
    return config_manager.get_settings()


def load_configuration(env_file: Optional[str] = None, validate_security: bool = True) -> Settings:
    """
    Load application configuration from environment and file.
    
    Args:
        env_file: Optional path to environment file
        validate_security: Whether to perform security validation
        
    Returns:
        Settings: Loaded and validated configuration settings
    """
    if env_file:
        global config_manager
        config_manager = ConfigManager(env_file)
    
    return config_manager.load_settings(validate_security)


def get_environment() -> Environment:
    """Get current application environment."""
    return get_settings().environment


def is_development() -> bool:
    """Check if running in development environment."""
    return get_settings().is_development()


def is_production() -> bool:
    """Check if running in production environment.""" 
    return get_settings().is_production()


def is_testing() -> bool:
    """Check if running in testing environment."""
    return get_settings().is_testing()


# Configuration validation utilities
def validate_configuration() -> Dict[str, Any]:
    """
    Validate current configuration and return status report.
    
    Returns:
        Dict containing validation results and recommendations
    """
    try:
        settings = get_settings()
        
        validation_result = {
            "valid": True,
            "environment": settings.environment.value,
            "warnings": [],
            "errors": [],
            "security_score": 100,
            "recommendations": []
        }
        
        # Security scoring and validation
        security_deductions = 0
        
        # Check secret strength
        if len(settings.security.secret_key) < 64:
            validation_result["warnings"].append("JWT secret key should be at least 64 characters")
            security_deductions += 10
        
        # Check production security
        if settings.is_production():
            if not settings.security.enforce_https:
                validation_result["errors"].append("HTTPS must be enforced in production")
                security_deductions += 20
                validation_result["valid"] = False
            
            if settings.application.debug:
                validation_result["errors"].append("Debug mode must be disabled in production")
                security_deductions += 15
                validation_result["valid"] = False
        
        # Check CORS configuration
        if "*" in settings.security.allowed_hosts and settings.security.cors_allow_credentials:
            validation_result["warnings"].append("CORS wildcard with credentials is insecure")
            security_deductions += 15
        
        # Calculate final security score
        validation_result["security_score"] = max(0, 100 - security_deductions)
        
        # Add recommendations
        if validation_result["security_score"] < 80:
            validation_result["recommendations"].append("Review and strengthen security configuration")
        
        if settings.is_development() and not settings.logging.enable_audit_logging:
            validation_result["recommendations"].append("Enable audit logging for better debugging")
        
        return validation_result
        
    except Exception as e:
        return {
            "valid": False,
            "environment": "unknown",
            "errors": [f"Configuration validation failed: {str(e)}"],
            "warnings": [],
            "security_score": 0,
            "recommendations": ["Fix configuration errors before proceeding"]
        }