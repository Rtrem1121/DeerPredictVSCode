"""
Application settings and configuration management.
Implements secure configuration loading with validation.
"""
import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class APISettings:
    """External API configuration settings"""
    openweathermap_api_key: str
    overpass_api_url: str = "https://overpass-api.de/api/interpreter"
    elevation_api_url: str = "https://api.open-meteo.com/v1/elevation"
    forecast_api_url: str = "https://api.open-meteo.com/v1/forecast"
    timeout_seconds: int = 30
    rate_limit_delay: float = 2.0
    max_retries: int = 3


@dataclass
class AnalysisSettings:
    """Deer behavior analysis configuration"""
    grid_size: int = 10
    grid_span_degrees: float = 0.04
    high_score_percentile: int = 85
    travel_corridor_percentile: int = 90
    max_stands_to_return: int = 5
    min_confidence_threshold: float = 50.0


@dataclass
class SecuritySettings:
    """Security and validation settings"""
    max_request_rate_per_minute: int = 60
    input_validation_enabled: bool = True
    cors_origins: list = field(default_factory=lambda: ["*"])
    rate_limiting_enabled: bool = True


@dataclass
class CacheSettings:
    """Caching configuration for performance optimization"""
    enabled: bool = False
    ttl_hours: int = 24
    redis_url: Optional[str] = None
    memory_cache_size: int = 1000


@dataclass
class LoggingSettings:
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5


@dataclass
class AppSettings:
    """Main application settings container"""
    api: APISettings
    analysis: AnalysisSettings
    security: SecuritySettings
    cache: CacheSettings
    logging: LoggingSettings
    debug: bool = False
    testing: bool = False
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return not (self.debug or self.testing)


class SettingsError(Exception):
    """Raised when there's an error in configuration"""
    pass


def _get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
    """
    Safely retrieve environment variable with validation.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value or default
        
    Raises:
        SettingsError: If required variable is missing
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise SettingsError(f"Required environment variable '{key}' is not set")
    
    return value


def _convert_to_bool(value: str) -> bool:
    """Convert string to boolean safely"""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes', 'on')


def _convert_to_list(value: str, separator: str = ",") -> list:
    """Convert comma-separated string to list"""
    if not value:
        return []
    return [item.strip() for item in value.split(separator) if item.strip()]


def load_settings() -> AppSettings:
    """
    Load application settings from environment variables.
    
    Returns:
        AppSettings: Configured application settings
        
    Raises:
        SettingsError: If configuration is invalid
    """
    try:
        # API Settings
        api_settings = APISettings(
            openweathermap_api_key=_get_env_var(
                "OPENWEATHERMAP_API_KEY", 
                required=True
            ),
            overpass_api_url=_get_env_var(
                "OVERPASS_API_URL", 
                "https://overpass-api.de/api/interpreter"
            ),
            elevation_api_url=_get_env_var(
                "ELEVATION_API_URL",
                "https://api.open-meteo.com/v1/elevation"
            ),
            forecast_api_url=_get_env_var(
                "FORECAST_API_URL",
                "https://api.open-meteo.com/v1/forecast"
            ),
            timeout_seconds=int(_get_env_var("API_TIMEOUT", 30)),
            rate_limit_delay=float(_get_env_var("API_RATE_LIMIT_DELAY", 2.0)),
            max_retries=int(_get_env_var("API_MAX_RETRIES", 3))
        )
        
        # Analysis Settings
        analysis_settings = AnalysisSettings(
            grid_size=int(_get_env_var("GRID_SIZE", 10)),
            grid_span_degrees=float(_get_env_var("GRID_SPAN_DEGREES", 0.04)),
            high_score_percentile=int(_get_env_var("HIGH_SCORE_PERCENTILE", 85)),
            travel_corridor_percentile=int(_get_env_var("TRAVEL_CORRIDOR_PERCENTILE", 90)),
            max_stands_to_return=int(_get_env_var("MAX_STANDS_TO_RETURN", 5)),
            min_confidence_threshold=float(_get_env_var("MIN_CONFIDENCE_THRESHOLD", 50.0))
        )
        
        # Security Settings
        security_settings = SecuritySettings(
            max_request_rate_per_minute=int(_get_env_var("MAX_REQUEST_RATE_PER_MINUTE", 60)),
            input_validation_enabled=_convert_to_bool(_get_env_var("INPUT_VALIDATION_ENABLED", True)),
            cors_origins=_convert_to_list(_get_env_var("CORS_ORIGINS", "*")),
            rate_limiting_enabled=_convert_to_bool(_get_env_var("RATE_LIMITING_ENABLED", True))
        )
        
        # Cache Settings
        cache_settings = CacheSettings(
            enabled=_convert_to_bool(_get_env_var("CACHE_ENABLED", False)),
            ttl_hours=int(_get_env_var("CACHE_TTL_HOURS", 24)),
            redis_url=_get_env_var("REDIS_URL"),
            memory_cache_size=int(_get_env_var("MEMORY_CACHE_SIZE", 1000))
        )
        
        # Logging Settings
        log_file_path = _get_env_var("LOG_FILE_PATH")
        if log_file_path:
            # Ensure log directory exists
            Path(log_file_path).parent.mkdir(parents=True, exist_ok=True)
            
        logging_settings = LoggingSettings(
            level=_get_env_var("LOG_LEVEL", "INFO").upper(),
            format=_get_env_var(
                "LOG_FORMAT",
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            file_path=log_file_path,
            max_file_size_mb=int(_get_env_var("LOG_MAX_FILE_SIZE_MB", 10)),
            backup_count=int(_get_env_var("LOG_BACKUP_COUNT", 5))
        )
        
        # Main Settings
        settings = AppSettings(
            api=api_settings,
            analysis=analysis_settings,
            security=security_settings,
            cache=cache_settings,
            logging=logging_settings,
            debug=_convert_to_bool(_get_env_var("DEBUG", False)),
            testing=_convert_to_bool(_get_env_var("TESTING", False))
        )
        
        logger.info("Application settings loaded successfully")
        return settings
        
    except (ValueError, TypeError) as e:
        raise SettingsError(f"Invalid configuration value: {e}")
    except Exception as e:
        raise SettingsError(f"Failed to load settings: {e}")


# Global settings instance
_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """
    Get application settings singleton.
    
    Returns:
        AppSettings: Configured application settings
    """
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def reload_settings() -> AppSettings:
    """
    Force reload of application settings.
    
    Returns:
        AppSettings: Newly loaded settings
    """
    global _settings
    _settings = None
    return get_settings()
