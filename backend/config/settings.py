#!/usr/bin/env python3
"""
Configuration Management System

Centralized configuration management following the 12-factor app methodology.
Supports environment-based configuration, validation, and hot reloading.

Key Features:
- Environment-based configuration
- Configuration validation
- Type safety with Pydantic
- Hot reloading support
- Secret management
- Configuration versioning

Author: GitHub Copilot
Version: 1.0.0
Date: August 14, 2025
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Deployment environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging level options"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseSettings):
    """Database configuration settings"""
    
    # Database connection
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="deer_prediction", description="Database name")
    username: str = Field(default="app_user", description="Database username")
    password: str = Field(default="", description="Database password")
    
    # Connection pool settings
    min_connections: int = Field(default=1, ge=1, description="Minimum pool connections")
    max_connections: int = Field(default=10, ge=1, description="Maximum pool connections")
    connection_timeout: int = Field(default=30, ge=1, description="Connection timeout seconds")
    
    # Feature flags
    enable_connection_pooling: bool = Field(default=True, description="Enable connection pooling")
    enable_query_logging: bool = Field(default=False, description="Enable SQL query logging")
    
    @field_validator('max_connections')
    @classmethod
    def validate_max_connections(cls, v, info):
        """Ensure max_connections >= min_connections"""
        min_conn = info.data.get('min_connections', 1)
        if v < min_conn:
            raise ValueError(f"max_connections ({v}) must be >= min_connections ({min_conn})")
        return v
    
    @property
    def connection_url(self) -> str:
        """Generate database connection URL"""
        if self.password:
            return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}"
        else:
            return f"postgresql://{self.username}@{self.host}:{self.port}/{self.name}"
    
    model_config = SettingsConfigDict(
        env_prefix="DB_",
        case_sensitive=False
    )


class ExternalAPIConfig(BaseSettings):
    """External API configuration settings"""
    
    # Weather API
    openweathermap_api_key: str = Field(default="", description="OpenWeatherMap API key")
    openweathermap_base_url: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        description="OpenWeatherMap base URL"
    )
    openweathermap_timeout: int = Field(default=10, ge=1, description="API timeout seconds")
    
    # Google Earth Engine
    gee_project_id: str = Field(default="", description="Google Earth Engine project ID")
    gee_service_account_path: str = Field(default="", description="GEE service account file path")
    gee_timeout: int = Field(default=30, ge=1, description="GEE timeout seconds")
    
    # Rate limiting
    api_rate_limit: int = Field(default=100, ge=1, description="API calls per minute")
    api_burst_limit: int = Field(default=10, ge=1, description="Burst API calls")
    
    # Retry configuration
    max_retries: int = Field(default=3, ge=0, description="Maximum API retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, description="Retry delay seconds")
    backoff_factor: float = Field(default=2.0, ge=1.0, description="Exponential backoff factor")
    
    @field_validator('openweathermap_api_key')
    @classmethod
    def validate_weather_api_key(cls, v):
        """Validate OpenWeatherMap API key format"""
        if v and len(v) != 32:
            logger.warning("OpenWeatherMap API key may be invalid (expected 32 characters)")
        return v
    
    model_config = SettingsConfigDict(
        env_prefix="API_",
        case_sensitive=False
    )


class PredictionConfig(BaseSettings):
    """Prediction algorithm configuration"""
    
    # Grid settings
    grid_size: int = Field(default=50, ge=10, le=200, description="Analysis grid size")
    grid_resolution: float = Field(default=0.01, gt=0, description="Grid resolution in degrees")
    
    # Scoring thresholds
    suggestion_threshold: float = Field(default=5.0, ge=0, le=10, description="Suggestion threshold")
    min_suggestion_rating: float = Field(default=8.0, ge=0, le=10, description="Minimum suggestion rating")
    huntable_threshold: float = Field(default=75.0, ge=0, le=100, description="Huntable threshold percentage")
    
    # Time windows
    prediction_window_hours: int = Field(default=48, ge=1, le=168, description="Prediction window hours")
    cache_ttl_minutes: int = Field(default=30, ge=1, description="Prediction cache TTL minutes")
    
    # Algorithm weights
    terrain_weight: float = Field(default=0.4, ge=0, le=1, description="Terrain scoring weight")
    weather_weight: float = Field(default=0.3, ge=0, le=1, description="Weather scoring weight")
    scouting_weight: float = Field(default=0.3, ge=0, le=1, description="Scouting data weight")
    
    # Performance settings
    enable_fast_mode: bool = Field(default=False, description="Enable fast prediction mode")
    max_prediction_time: int = Field(default=60, ge=5, description="Maximum prediction time seconds")
    enable_caching: bool = Field(default=True, description="Enable prediction caching")
    
    # Note: Multi-field validation in Pydantic v2 requires model_validator
    # Simplified for now - weights validation can be added later
    
    model_config = SettingsConfigDict(
        env_prefix="PRED_",
        case_sensitive=False
    )


class SecurityConfig(BaseSettings):
    """Security configuration settings"""
    
    # Authentication
    secret_key: str = Field(default="", description="Application secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, ge=1, description="Access token expiry minutes")
    
    # CORS settings
    allowed_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    allowed_methods: List[str] = Field(default=["*"], description="CORS allowed methods")
    allowed_headers: List[str] = Field(default=["*"], description="CORS allowed headers")
    allow_credentials: bool = Field(default=True, description="CORS allow credentials")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, ge=1, description="API rate limit per minute")
    rate_limit_burst: int = Field(default=10, ge=1, description="Rate limit burst allowance")
    
    # Security headers
    enable_security_headers: bool = Field(default=True, description="Enable security headers")
    enable_csrf_protection: bool = Field(default=False, description="Enable CSRF protection")
    
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        """Validate secret key strength"""
        if not v:
            logger.warning("No secret key configured - using default (INSECURE)")
            return "insecure-default-key-change-in-production"
        if len(v) < 32:
            logger.warning("Secret key may be too short for production use")
        return v
    
    model_config = SettingsConfigDict(
        env_prefix="SEC_",
        case_sensitive=False
    )


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration"""
    
    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Application log level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    enable_structured_logging: bool = Field(default=True, description="Enable structured JSON logging")
    
    # Metrics
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, ge=1000, le=65535, description="Metrics server port")
    metrics_path: str = Field(default="/metrics", description="Metrics endpoint path")
    
    # Health checks
    health_check_interval: int = Field(default=30, ge=5, description="Health check interval seconds")
    enable_detailed_health: bool = Field(default=True, description="Enable detailed health checks")
    
    # Performance monitoring
    enable_profiling: bool = Field(default=False, description="Enable performance profiling")
    slow_query_threshold: float = Field(default=1.0, ge=0.1, description="Slow query threshold seconds")
    
    # Error tracking
    enable_error_tracking: bool = Field(default=True, description="Enable error tracking")
    error_sampling_rate: float = Field(default=1.0, ge=0, le=1, description="Error sampling rate")
    
    model_config = SettingsConfigDict(
        env_prefix="MON_",
        case_sensitive=False
    )


class ApplicationConfig(BaseSettings):
    """Main application configuration"""
    
    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Deployment environment")
    debug: bool = Field(default=False, description="Enable debug mode")
    version: str = Field(default="1.0.0", description="Application version")
    
    # Server settings
    host: str = Field(default="0.0.0.0", description="Server bind host")
    port: int = Field(default=8000, ge=1000, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of worker processes")
    
    # Performance
    max_request_size: int = Field(default=1024*1024, ge=1024, description="Maximum request size bytes")
    request_timeout: int = Field(default=30, ge=1, description="Request timeout seconds")
    
    # Feature flags
    enable_docs: bool = Field(default=True, description="Enable API documentation")
    enable_gee_integration: bool = Field(default=True, description="Enable Google Earth Engine")
    enable_analytics: bool = Field(default=True, description="Enable analytics collection")
    
    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig, description="Database configuration")
    api: ExternalAPIConfig = Field(default_factory=ExternalAPIConfig, description="External API configuration")
    prediction: PredictionConfig = Field(default_factory=PredictionConfig, description="Prediction configuration")
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="Security configuration")
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig, description="Monitoring configuration")
    
    @field_validator('environment')
    @classmethod  
    def validate_environment_settings(cls, v):
        """Validate environment-specific settings"""
        if v == Environment.PRODUCTION:
            # Production-specific validations can be added here
            pass
        return v
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment == Environment.DEVELOPMENT
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        case_sensitive=False
    )


class ConfigurationManager:
    """
    Configuration manager with validation, hot reloading, and environment support.
    
    Features:
    - Environment-based configuration
    - Configuration validation
    - Hot reloading
    - Configuration change notifications
    """
    
    def __init__(self):
        self._config: Optional[ApplicationConfig] = None
        self._config_path: Optional[Path] = None
        self._watchers: List[callable] = []
        
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> ApplicationConfig:
        """
        Load configuration from environment and files.
        
        Args:
            config_path: Optional path to configuration file
            
        Returns:
            ApplicationConfig: Loaded and validated configuration
        """
        try:
            if config_path:
                self._config_path = Path(config_path)
                
            # Load configuration with Pydantic
            self._config = ApplicationConfig()
            
            # Validate configuration
            self._validate_configuration(self._config)
            
            # Log configuration status
            logger.info(
                f"Configuration loaded successfully",
                extra={
                    "environment": self._config.environment.value,
                    "debug": self._config.debug,
                    "version": self._config.version
                }
            )
            
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def get_config(self) -> ApplicationConfig:
        """Get current configuration, loading if necessary"""
        if self._config is None:
            self._config = self.load_config()
        return self._config
    
    def reload_config(self) -> ApplicationConfig:
        """Force reload configuration"""
        logger.info("Reloading configuration")
        old_config = self._config
        self._config = self.load_config(self._config_path)
        
        # Notify watchers of configuration change
        self._notify_watchers(old_config, self._config)
        
        return self._config
    
    def watch_config_changes(self, callback: callable):
        """Register callback for configuration changes"""
        self._watchers.append(callback)
    
    def _validate_configuration(self, config: ApplicationConfig):
        """Perform additional configuration validation"""
        
        # Environment-specific validations
        if config.is_production():
            if not config.security.secret_key or config.security.secret_key == "insecure-default-key-change-in-production":
                raise ValueError("Secure secret key required in production")
            
            if config.debug:
                logger.warning("Debug mode enabled in production")
                
            if "*" in config.security.allowed_origins:
                logger.warning("Wildcard CORS origins in production may be insecure")
        
        # API key validations
        if config.enable_gee_integration and not config.api.gee_project_id:
            logger.warning("GEE integration enabled but no project ID configured")
        
        # Database validation
        if config.database.password == "":
            logger.warning("Database password is empty")
        
        logger.info("Configuration validation completed")
    
    def _notify_watchers(self, old_config: Optional[ApplicationConfig], new_config: ApplicationConfig):
        """Notify registered watchers of configuration changes"""
        for watcher in self._watchers:
            try:
                watcher(old_config, new_config)
            except Exception as e:
                logger.error(f"Configuration watcher failed: {e}")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        if not self._config:
            return {"status": "not_loaded"}
        
        return {
            "status": "loaded",
            "environment": self._config.environment.value,
            "version": self._config.version,
            "debug": self._config.debug,
            "features": {
                "gee_integration": self._config.enable_gee_integration,
                "analytics": self._config.enable_analytics,
                "docs": self._config.enable_docs
            },
            "external_apis": {
                "weather_configured": bool(self._config.api.openweathermap_api_key),
                "gee_configured": bool(self._config.api.gee_project_id)
            }
        }


# Global configuration manager instance
_config_manager = ConfigurationManager()

def get_config() -> ApplicationConfig:
    """Get application configuration (singleton)"""
    return _config_manager.get_config()

def reload_config() -> ApplicationConfig:
    """Reload application configuration"""
    return _config_manager.reload_config()

def get_config_manager() -> ConfigurationManager:
    """Get configuration manager instance"""
    return _config_manager
