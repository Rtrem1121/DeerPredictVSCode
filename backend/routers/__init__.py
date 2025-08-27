"""
API Routers package for the deer prediction app.

This package contains the API layer routers that use the business logic services.
Following the separation of concerns principle, routers handle HTTP concerns
while services handle business logic.

Routers:
- prediction_router: Main prediction endpoints
- camera_router: Trail camera placement endpoints
- scouting_router: Scouting observation endpoints
- config_router: Configuration management endpoints
"""

from .prediction_router import prediction_router
from .camera_router import camera_router
from .scouting_router import scouting_router
from .config_router import config_router

__all__ = [
    "prediction_router",
    "camera_router", 
    "scouting_router",
    "config_router",
]
