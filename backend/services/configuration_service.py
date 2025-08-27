"""
Configuration Service

Handles all configuration-related operations for the deer prediction app.
This service encapsulates configuration management endpoints and business logic.
"""

from typing import Dict, Any
from fastapi import HTTPException
from backend.config_manager import get_config
import logging

logger = logging.getLogger(__name__)


class ConfigurationService:
    """Service for managing application configuration."""
    
    def __init__(self):
        """Initialize the configuration service."""
        self._config = get_config()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current configuration status and metadata."""
        try:
            config = get_config()
            metadata = config.get_metadata()
            
            return {
                "environment": metadata.environment,
                "version": metadata.version,
                "last_loaded": metadata.last_loaded.isoformat() if metadata.last_loaded else None,
                "source_files": metadata.source_files,
                "validation_errors": metadata.validation_errors,
                "configuration_sections": {
                    "mature_buck_preferences": bool(config.get_mature_buck_preferences()),
                    "scoring_factors": bool(config.get_scoring_factors()),
                    "seasonal_weights": bool(config.get_seasonal_weights()),
                    "weather_modifiers": bool(config.get_weather_modifiers()),
                    "distance_parameters": bool(config.get_distance_parameters()),
                    "api_settings": bool(config.get_api_settings())
                }
            }
        except Exception as e:
            logger.error(f"Error getting configuration status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get configuration status: {str(e)}")
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get all current configuration parameters."""
        try:
            config = get_config()
            
            return {
                "mature_buck_preferences": config.get_mature_buck_preferences(),
                "scoring_factors": config.get_scoring_factors(),
                "seasonal_weights": config.get_seasonal_weights(),
                "weather_modifiers": config.get_weather_modifiers(),
                "distance_parameters": config.get_distance_parameters(),
                "terrain_weights": config.get_terrain_weights(),
                "api_settings": config.get_api_settings(),
                "ml_parameters": config.get_ml_parameters()
            }
        except Exception as e:
            logger.error(f"Error getting configuration parameters: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get configuration parameters: {str(e)}")
    
    def reload_configuration(self) -> Dict[str, Any]:
        """Reload configuration from files (admin only)."""
        try:
            config = get_config()
            config.reload()
            metadata = config.get_metadata()
            
            return {
                "status": "success",
                "message": "Configuration reloaded successfully",
                "version": metadata.version,
                "last_loaded": metadata.last_loaded.isoformat() if metadata.last_loaded else None
            }
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to reload configuration: {str(e)}")
    
    def update_parameter(self, key_path: str, value: Any) -> Dict[str, Any]:
        """Update a specific configuration parameter (admin only)."""
        try:
            config = get_config()
            config.update_config(key_path, value, persist=False)  # Don't persist to file for safety
            
            return {
                "status": "success",
                "message": f"Parameter {key_path} updated successfully",
                "key_path": key_path,
                "new_value": value
            }
        except Exception as e:
            logger.error(f"Error updating configuration parameter {key_path}: {e}")
            raise HTTPException(status_code=400, detail=f"Failed to update parameter: {str(e)}")
    
    def get_config_instance(self):
        """Get the underlying configuration instance for internal use."""
        return get_config()


# Module-level service instance
_configuration_service = None

def get_configuration_service() -> ConfigurationService:
    """Get or create the configuration service instance (singleton pattern)."""
    global _configuration_service
    if _configuration_service is None:
        _configuration_service = ConfigurationService()
    return _configuration_service
