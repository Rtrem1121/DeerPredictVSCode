"""
Configuration Router

FastAPI router for configuration management endpoints.
Uses the ConfigurationService for business logic.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from backend.services.configuration_service import ConfigurationService

# Create router
config_router = APIRouter(prefix="/config", tags=["configuration"])

# Initialize service
config_service = ConfigurationService()


@config_router.get("/status", summary="Get configuration status")
def get_config_status() -> Dict[str, Any]:
    """Get current configuration status and metadata."""
    return config_service.get_status()


@config_router.get("/parameters", summary="Get all configuration parameters") 
def get_config_parameters() -> Dict[str, Any]:
    """Get all current configuration parameters."""
    return config_service.get_parameters()


@config_router.post("/reload", summary="Reload configuration")
def reload_configuration() -> Dict[str, Any]:
    """Reload configuration from files (admin only)."""
    return config_service.reload_configuration()


@config_router.put("/parameter/{key_path}", summary="Update configuration parameter")
def update_config_parameter(key_path: str, value: Any) -> Dict[str, Any]:
    """Update a specific configuration parameter (admin only)."""
    return config_service.update_parameter(key_path, value)
