#!/usr/bin/env python3
"""
Weather Analysis Service

Specialized service for weather data retrieval and analysis, extracted from
the monolithic PredictionService for better separation of concerns.

Author: System Refactoring
Version: 2.0.0
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass

from backend import core
from backend.services.base_service import BaseService, Result, AppError, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Structured weather analysis result"""
    current_weather: Dict[str, Any]
    forecast: Dict[str, Any]
    temperature: float
    conditions: str
    wind_speed: float
    wind_direction: float
    humidity: float
    pressure: float
    moon_phase: str
    hour: int


class WeatherService(BaseService):
    """
    Specialized service for weather analysis operations
    
    Responsibilities:
    - Current weather data retrieval
    - Weather forecast processing
    - Moon phase calculations
    - Weather condition impact analysis
    """
    
    def __init__(self, core_module=None):
        super().__init__()
        self.core = core_module or core
    
    async def get_weather_analysis(self, lat: float, lon: float, 
                                 date_time: datetime) -> Result[WeatherData]:
        """
        Comprehensive weather analysis for hunting predictions
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            date_time: Target datetime for predictions
            
        Returns:
            Result containing WeatherData or error information
        """
        try:
            self.log_operation_start("weather_analysis", lat=lat, lon=lon)
            
            # Validate inputs
            validation_result = self._validate_inputs(lat, lon, date_time)
            if validation_result.is_failure:
                return validation_result
            
            # Get current weather data
            weather_result = await self._get_current_weather(lat, lon)
            if weather_result.is_failure:
                return weather_result
            
            current_weather = weather_result.value
            
            # Calculate moon phase
            moon_phase = self._get_moon_phase(date_time)
            
            # Extract hour for thermal calculations
            hour = date_time.hour
            
            # Create structured weather data
            weather_data = WeatherData(
                current_weather=current_weather,
                forecast={},  # TODO: Implement forecast data
                temperature=current_weather.get('temperature', 0.0),
                conditions=current_weather.get('conditions', 'unknown'),
                wind_speed=current_weather.get('wind_speed', 0.0),
                wind_direction=current_weather.get('wind_direction', 0.0),
                humidity=current_weather.get('humidity', 50.0),
                pressure=current_weather.get('pressure', 1013.25),
                moon_phase=moon_phase,
                hour=hour
            )
            
            self.log_operation_success("weather_analysis", 
                                     temperature=weather_data.temperature,
                                     conditions=weather_data.conditions,
                                     moon_phase=moon_phase)
            
            return Result.success(weather_data)
            
        except Exception as e:
            error = self.handle_unexpected_error("weather_analysis", e, lat=lat, lon=lon)
            return Result.failure(error)
    
    async def _get_current_weather(self, lat: float, lon: float) -> Result[Dict[str, Any]]:
        """Get current weather data from external API"""
        try:
            weather_data = self.core.get_weather_data(lat, lon)
            
            if not weather_data:
                return Result.failure(AppError(
                    ErrorCode.WEATHER_API_UNAVAILABLE,
                    "Weather data unavailable for location",
                    {"lat": lat, "lon": lon}
                ))
            
            # Validate weather data structure
            if not self._is_valid_weather_data(weather_data):
                return Result.failure(AppError(
                    ErrorCode.WEATHER_DATA_INVALID,
                    "Invalid weather data format received",
                    {"lat": lat, "lon": lon, "data_keys": list(weather_data.keys()) if isinstance(weather_data, dict) else "not_dict"}
                ))
            
            return Result.success(weather_data)
            
        except Exception as e:
            return Result.failure(AppError(
                ErrorCode.WEATHER_FORECAST_FAILED,
                f"Failed to fetch weather data: {str(e)}",
                {"lat": lat, "lon": lon, "exception_type": type(e).__name__}
            ))
    
    def _get_moon_phase(self, date_time: datetime) -> str:
        """Calculate moon phase for the given datetime"""
        try:
            return self.core.get_moon_phase(date_time)
        except Exception as e:
            self.logger.warning(f"Moon phase calculation failed: {e}")
            return "unknown"
    
    def _is_valid_weather_data(self, weather_data: Any) -> bool:
        """Validate weather data structure"""
        if not isinstance(weather_data, dict):
            return False
        
        # Check for required fields (with defaults)
        required_fields = ['temperature', 'conditions']
        return any(field in weather_data for field in required_fields)
    
    def _validate_inputs(self, lat: float, lon: float, date_time: datetime) -> Result[None]:
        """Validate input parameters"""
        # Validate coordinates
        if not (-90 <= lat <= 90):
            return Result.failure(AppError(
                ErrorCode.INVALID_COORDINATES,
                f"Invalid latitude: {lat}",
                {"lat": lat, "lon": lon}
            ))
        
        if not (-180 <= lon <= 180):
            return Result.failure(AppError(
                ErrorCode.INVALID_COORDINATES,
                f"Invalid longitude: {lon}",
                {"lat": lat, "lon": lon}
            ))
        
        # Validate datetime
        if not isinstance(date_time, datetime):
            return Result.failure(AppError(
                ErrorCode.INVALID_DATE_TIME,
                f"Invalid datetime type: {type(date_time)}",
                {"date_time": str(date_time)}
            ))
        
        return Result.success(None)
    
    async def get_weather_conditions_for_context(self, lat: float, lon: float) -> Result[Dict[str, Any]]:
        """Get weather conditions formatted for prediction context"""
        try:
            weather_result = await self._get_current_weather(lat, lon)
            if weather_result.is_failure:
                return weather_result
            
            weather_data = weather_result.value
            
            # FIXED: Add cold front detection and weather trigger logic
            temperature = weather_data.get('temperature', 20.0)
            pressure = weather_data.get('pressure', 1013.25)
            wind_speed = weather_data.get('wind_speed', 5.0)
            
            # Convert pressure to inHg if needed (assume it's in hPa/mbar)
            pressure_inhg = pressure * 0.02953 if pressure > 500 else pressure
            
            # Cold front detection (pressure < 29.9 inHg and temperature < 45°F)
            is_cold_front = pressure_inhg < 29.9 and temperature < 45
            
            # Weather triggers that increase deer movement
            weather_triggers = []
            movement_multiplier = 1.0
            
            if is_cold_front:
                weather_triggers.extend([
                    "Cold front conditions detected - increased deer movement expected",
                    "Barometric pressure drop triggering feeding activity",
                    "Temperature drop encouraging deer to feed before weather worsens",
                    "PRIME HUNTING CONDITIONS - deer will be moving"
                ])
                movement_multiplier = 1.5  # 50% increase in movement probability
            
            # High pressure system
            elif pressure_inhg > 30.2:
                weather_triggers.extend([
                    "High pressure system - stable weather patterns",
                    "Normal movement patterns expected"
                ])
                movement_multiplier = 1.0
            
            # Wind conditions
            if wind_speed > 15:
                weather_triggers.extend([
                    "High wind conditions - deer seeking wind protection",
                    "Movement may be reduced in open areas"
                ])
                movement_multiplier *= 0.8  # Reduce movement in high wind
            elif wind_speed < 5:
                weather_triggers.append("Calm wind conditions - good scent management conditions")
            
            # Format for prediction context
            conditions = {
                "temperature": temperature,
                "wind_speed": wind_speed,
                "humidity": weather_data.get('humidity', 60.0),
                "pressure": pressure_inhg,  # Use inHg for consistency
                "conditions": [weather_data.get('conditions', 'clear')],
                "hour": datetime.now().hour,
                # FIXED: Add weather trigger information
                "is_cold_front": is_cold_front,
                "weather_triggers": weather_triggers,
                "movement_multiplier": movement_multiplier,
                "weather_notes": weather_triggers
            }
            
            return Result.success(conditions)
            
        except Exception as e:
            error = self.handle_unexpected_error("weather_conditions_context", e, lat=lat, lon=lon)
            return Result.failure(error)


# Singleton instance
_weather_service = None

def get_weather_service() -> WeatherService:
    """Get the singleton weather service instance"""
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service
