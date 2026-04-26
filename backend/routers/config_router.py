"""
Configuration Router

FastAPI router for configuration management endpoints.
Uses the ConfigurationService for business logic.
"""

from typing import Dict, Any, Optional
import hashlib
import hmac
import os
from fastapi import APIRouter, Header, HTTPException
from backend.services.configuration_service import ConfigurationService

# Create router
config_router = APIRouter(prefix="/config", tags=["configuration"])

# Initialize service
config_service = ConfigurationService()


def _require_admin(x_admin_password: Optional[str] = Header(default=None, alias="X-Admin-Password")) -> None:
    """Require admin password for mutable configuration endpoints."""
    configured_password = os.getenv("APP_PASSWORD")
    if not configured_password:
        raise HTTPException(status_code=503, detail="Admin password is not configured")
    if not x_admin_password:
        raise HTTPException(status_code=401, detail="Missing admin credentials")

    submitted_digest = hashlib.sha256(x_admin_password.encode("utf-8")).digest()
    configured_digest = hashlib.sha256(configured_password.encode("utf-8")).digest()
    if not hmac.compare_digest(submitted_digest, configured_digest):
        raise HTTPException(status_code=403, detail="Invalid admin credentials")


@config_router.get("/status", summary="Get configuration status")
def get_config_status() -> Dict[str, Any]:
    """Get current configuration status and metadata."""
    return config_service.get_status()


@config_router.get("/parameters", summary="Get all configuration parameters") 
def get_config_parameters() -> Dict[str, Any]:
    """Get all current configuration parameters."""
    return config_service.get_parameters()


@config_router.post("/reload", summary="Reload configuration")
def reload_configuration(
    x_admin_password: Optional[str] = Header(default=None, alias="X-Admin-Password")
) -> Dict[str, Any]:
    """Reload configuration from files (admin only)."""
    _require_admin(x_admin_password)
    return config_service.reload_configuration()


@config_router.put("/parameter/{key_path}", summary="Update configuration parameter")
def update_config_parameter(
    key_path: str,
    value: Any,
    x_admin_password: Optional[str] = Header(default=None, alias="X-Admin-Password"),
) -> Dict[str, Any]:
    """Update a specific configuration parameter (admin only)."""
    _require_admin(x_admin_password)
    return config_service.update_parameter(key_path, value)
