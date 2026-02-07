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

__all__ = [
    "PredictionService",
    "get_prediction_service",
    "CameraService",
    "ScoutingService",
    "ConfigurationService",
]


def __getattr__(name):
    if name == "PredictionService":
        from .prediction_service import PredictionService
        return PredictionService
    if name == "get_prediction_service":
        from .prediction_service import get_prediction_service
        return get_prediction_service
    if name == "CameraService":
        from .camera_service import CameraService
        return CameraService
    if name == "ScoutingService":
        from .scouting_service import ScoutingService
        return ScoutingService
    if name == "ConfigurationService":
        from .configuration_service import ConfigurationService
        return ConfigurationService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
