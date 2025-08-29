"""
Backend services package for the deer prediction app.

This package contains the core business logic services extracted from the
monolithic main.py file to create a more maintainable service-based architecture.

Services:
- prediction_service: Core deer prediction logic using EnhancedBeddingZonePredictor exclusively
- camera_service: Trail camera placement algorithms
- scouting_service: Scouting observation management
- configuration_service: Configuration management
- weather_service: Weather analysis and forecasting
- terrain_service: Terrain analysis and scoring
"""

from .prediction_service import PredictionService, get_prediction_service
from .camera_service import CameraService
from .scouting_service import ScoutingService
from .configuration_service import ConfigurationService

__all__ = [
    "PredictionService",
    "get_prediction_service",
    "CameraService", 
    "ScoutingService",
    "ConfigurationService",
]
