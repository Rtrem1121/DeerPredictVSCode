#!/usr/bin/env python3
"""
Wind Analysis and Scent Management System for Mature Buck Hunting

This module provides comprehensive wind analysis capabilities for optimal stand
positioning based on real-time wind data, scent dispersion modeling, and 
terrain-modified wind patterns.

Key Features:
- Real-time wind data integration with OpenWeatherMap
- Advanced scent dispersion modeling
- Terrain-modified wind pattern analysis
- Dynamic stand positioning based on wind direction
- Wind consistency and reliability scoring
- Multi-target downwind positioning optimization

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Union
import logging
import time
import math
from dataclasses import dataclass
from enum import Enum
import requests
from datetime import datetime, timedelta

# Import configuration management
try:
    from .config_manager import get_config
except ImportError:
    from config_manager import get_config

logger = logging.getLogger(__name__)

class WindConsistency(Enum):
    """Wind consistency levels for planning"""
    STEADY = "steady"           # < 15° direction variation
    MODERATE = "moderate"       # 15-45° direction variation  
    VARIABLE = "variable"       # 45-90° direction variation
    CHAOTIC = "chaotic"         # > 90° direction variation

class ScentConeType(Enum):
    """Types of scent dispersion patterns"""
    NARROW = "narrow"           # High wind speed, focused cone
    MODERATE = "moderate"       # Medium wind speed, standard cone
    WIDE = "wide"              # Low wind speed, dispersed cone
    THERMAL = "thermal"         # Thermal-driven dispersion

@dataclass
class WindData:
    """Comprehensive wind data structure"""
    direction_degrees: float    # Wind direction in degrees (0-360)
    speed_mph: float           # Wind speed in mph
    gust_mph: Optional[float]  # Wind gust speed in mph
    consistency: WindConsistency # Wind consistency classification
    reliability_score: float   # 0-100 reliability of wind forecast
    thermal_factor: float      # Thermal wind influence (0-1)
    terrain_modification: float # Terrain effect on wind (-1 to 1)
    forecast_hours: int        # Hours ahead this forecast is valid
    timestamp: datetime        # When this data was collected

@dataclass
class ScentDispersion:
    """Scent dispersion model results"""
    cone_angle_degrees: float     # Total scent cone angle
    effective_distance_yards: float # Maximum effective scent distance
    peak_concentration_distance: float # Distance of peak scent concentration
    dispersion_type: ScentConeType    # Type of scent pattern
    wind_shadow_zones: List[Tuple[float, float]]  # Angles with reduced scent
    terrain_deflection_angles: List[float]        # Angles where terrain affects scent

@dataclass
class WindOptimizedPosition:
    """Optimized stand position based on wind analysis"""
    latitude: float
    longitude: float
    downwind_angle: float          # Angle from target (degrees)
    wind_advantage_score: float    # 0-100 wind positioning score
    scent_safety_margin: float     # Safety margin for wind shifts
    optimal_entry_route: Tuple[float, float]  # Recommended approach coordinates
    fallback_positions: List[Tuple[float, float]]  # Alternative positions
    confidence_modifiers: Dict[str, float]     # Confidence adjustments

class WindAnalyzer:
    """
    Advanced wind analysis system for hunting stand optimization
    
    Provides real-time wind data, scent modeling, and optimal positioning
    calculations for mature buck hunting strategies.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize wind analyzer with configuration"""
        self.config = get_config()
        self.api_key = api_key or self._get_api_key()
        self.wind_cache = {}
        self.terrain_cache = {}
        self._initialize_wind_parameters()
        
        logger.info("🌬️ Wind Analyzer initialized")
    
    def _get_api_key(self) -> str:
        """Get OpenWeatherMap API key from configuration"""
        try:
            # Try to get from config first
            return self.config.get_parameter('weather.api_key', '')
        except:
            # Fallback to environment variable
            import os
            return os.getenv('OPENWEATHERMAP_API_KEY', '')
    
    def _initialize_wind_parameters(self):
        """Initialize wind analysis parameters from configuration"""
        try:
            wind_config = self.config.get_parameter('wind_analysis', {})
        except:
            wind_config = {}
        
        # Default wind analysis parameters
        self.wind_params = {
            'scent_max_distance_yards': wind_config.get('scent_max_distance', 300),
            'scent_peak_distance_yards': wind_config.get('scent_peak_distance', 100),
            'wind_consistency_threshold': wind_config.get('consistency_threshold', 15),
            'thermal_strength_factor': wind_config.get('thermal_strength', 0.3),
            'terrain_modification_factor': wind_config.get('terrain_factor', 0.2),
            'safety_margin_degrees': wind_config.get('safety_margin', 30),
            'cache_duration_minutes': wind_config.get('cache_duration', 15)
        }
    
    def fetch_current_wind_data(self, lat: float, lon: float) -> WindData:
        """
        Fetch current wind data from OpenWeatherMap API
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            WindData object with current wind conditions
        """
        cache_key = f"{lat:.3f}_{lon:.3f}"
        current_time = datetime.now()
        
        # Check cache first
        if cache_key in self.wind_cache:
            cached_data, cache_time = self.wind_cache[cache_key]
            if (current_time - cache_time).seconds < self.wind_params['cache_duration_minutes'] * 60:
                return cached_data
        
        try:
            # Fetch current weather data
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract wind data
            wind_info = data.get('wind', {})
            wind_direction = wind_info.get('deg', 0)
            wind_speed = wind_info.get('speed', 0)
            wind_gust = wind_info.get('gust')
            
            # Calculate wind consistency (simplified - would need historical data for accuracy)
            consistency = self._calculate_wind_consistency(wind_speed, wind_gust)
            
            # Calculate thermal factor based on time of day
            thermal_factor = self._calculate_thermal_factor()
            
            # Calculate terrain modification (simplified - would need detailed terrain analysis)
            terrain_mod = self._calculate_terrain_modification(lat, lon, wind_direction)
            
            wind_data = WindData(
                direction_degrees=wind_direction,
                speed_mph=wind_speed,
                gust_mph=wind_gust,
                consistency=consistency,
                reliability_score=85.0,  # Base reliability for current conditions
                thermal_factor=thermal_factor,
                terrain_modification=terrain_mod,
                forecast_hours=0,
                timestamp=current_time
            )
            
            # Cache the result
            self.wind_cache[cache_key] = (wind_data, current_time)
            
            logger.info(f"🌬️ Wind data fetched: {wind_direction}° at {wind_speed} mph")
            return wind_data
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch wind data: {e}")
            # Return default wind data
            return WindData(
                direction_degrees=270,  # Default west wind
                speed_mph=5.0,
                gust_mph=None,
                consistency=WindConsistency.MODERATE,
                reliability_score=50.0,
                thermal_factor=0.2,
                terrain_modification=0.0,
                forecast_hours=0,
                timestamp=current_time
            )
    
    def _calculate_wind_consistency(self, speed: float, gust: Optional[float]) -> WindConsistency:
        """Calculate wind consistency based on speed and gusts"""
        if gust is None:
            gust = speed
        
        gust_factor = (gust - speed) / max(speed, 1.0)
        
        if gust_factor < 0.3 and speed > 3:
            return WindConsistency.STEADY
        elif gust_factor < 0.7:
            return WindConsistency.MODERATE
        elif gust_factor < 1.5:
            return WindConsistency.VARIABLE
        else:
            return WindConsistency.CHAOTIC
    
    def _calculate_thermal_factor(self) -> float:
        """Calculate thermal wind influence based on time of day"""
        current_hour = datetime.now().hour
        
        # Strong thermal effects during morning and evening transitions
        if 5 <= current_hour <= 8 or 17 <= current_hour <= 20:
            return 0.8
        # Moderate thermal effects during midday
        elif 9 <= current_hour <= 16:
            return 0.4
        # Minimal thermal effects at night
        else:
            return 0.1
    
    def _calculate_terrain_modification(self, lat: float, lon: float, wind_direction: float) -> float:
        """Calculate how terrain modifies wind patterns (simplified)"""
        # This is a simplified calculation - would need detailed terrain analysis
        # for production use
        return 0.1  # Slight terrain modification
    
    def model_scent_dispersion(self, wind_data: WindData, terrain_elevation: Optional[float] = None) -> ScentDispersion:
        """
        Model hunter scent dispersion based on wind conditions
        
        Args:
            wind_data: Current wind conditions
            terrain_elevation: Optional elevation data for terrain effects
            
        Returns:
            ScentDispersion model with scent cone details
        """
        speed = wind_data.speed_mph
        
        # Calculate scent cone angle based on wind speed
        if speed > 10:
            cone_angle = 20  # Narrow cone for high wind
            dispersion_type = ScentConeType.NARROW
        elif speed > 5:
            cone_angle = 35  # Moderate cone for medium wind
            dispersion_type = ScentConeType.MODERATE
        elif speed > 2:
            cone_angle = 60  # Wide cone for low wind
            dispersion_type = ScentConeType.WIDE
        else:
            cone_angle = 90  # Very wide for thermal conditions
            dispersion_type = ScentConeType.THERMAL
        
        # Adjust for thermal effects
        if wind_data.thermal_factor > 0.5:
            cone_angle += 15
            dispersion_type = ScentConeType.THERMAL
        
        # Calculate effective distances
        max_distance = self.wind_params['scent_max_distance_yards'] * min(speed / 5.0, 2.0)
        peak_distance = self.wind_params['scent_peak_distance_yards'] * (speed / 8.0)
        
        # Calculate wind shadow zones (areas with reduced scent)
        wind_shadows = []
        if terrain_elevation and wind_data.terrain_modification > 0.1:
            # Add terrain-based wind shadows
            wind_shadows.append((wind_data.direction_degrees - 45, wind_data.direction_degrees - 15))
            wind_shadows.append((wind_data.direction_degrees + 15, wind_data.direction_degrees + 45))
        
        # Calculate terrain deflection angles
        deflection_angles = []
        if wind_data.terrain_modification != 0:
            deflection_angles.append(wind_data.direction_degrees + wind_data.terrain_modification * 20)
        
        return ScentDispersion(
            cone_angle_degrees=cone_angle,
            effective_distance_yards=max_distance,
            peak_concentration_distance=peak_distance,
            dispersion_type=dispersion_type,
            wind_shadow_zones=wind_shadows,
            terrain_deflection_angles=deflection_angles
        )
    
    def calculate_optimal_downwind_position(self, 
                                          target_lat: float, 
                                          target_lon: float,
                                          wind_data: WindData,
                                          distance_yards: float = 150,
                                          strategy_type: str = "bedding_approach") -> WindOptimizedPosition:
        """
        Calculate optimal downwind stand position relative to target
        
        Args:
            target_lat: Target bedding/corridor latitude
            target_lon: Target bedding/corridor longitude
            wind_data: Current wind conditions
            distance_yards: Desired distance from target
            strategy_type: Type of hunting strategy
            
        Returns:
            WindOptimizedPosition with optimal coordinates and scoring
        """
        # Calculate downwind angle (opposite of wind direction)
        wind_direction = wind_data.direction_degrees
        downwind_angle = (wind_direction + 180) % 360
        
        # Add safety margin for wind shifts
        safety_margin = self.wind_params['safety_margin_degrees']
        
        # Adjust for wind consistency
        if wind_data.consistency == WindConsistency.STEADY:
            angle_adjustment = 0
            confidence_bonus = 0.2
        elif wind_data.consistency == WindConsistency.MODERATE:
            angle_adjustment = 10
            confidence_bonus = 0.1
        elif wind_data.consistency == WindConsistency.VARIABLE:
            angle_adjustment = 20
            confidence_bonus = -0.1
        else:  # CHAOTIC
            angle_adjustment = 30
            confidence_bonus = -0.3
        
        # Calculate optimal position coordinates
        optimal_angle = downwind_angle + angle_adjustment
        distance_degrees = distance_yards / 111000.0  # Rough conversion to degrees
        
        optimal_lat = target_lat + distance_degrees * math.cos(math.radians(optimal_angle))
        optimal_lon = target_lon + distance_degrees * math.sin(math.radians(optimal_angle))
        
        # Calculate wind advantage score
        wind_advantage = self._calculate_wind_advantage_score(wind_data, strategy_type)
        
        # Calculate scent safety margin
        scent_safety = self._calculate_scent_safety_margin(wind_data, distance_yards)
        
        # Calculate optimal entry route (approach from crosswind)
        entry_angle = (optimal_angle + 90) % 360
        entry_distance = distance_yards * 0.3  # 30% of stand distance
        entry_distance_deg = entry_distance / 111000.0
        
        entry_lat = optimal_lat + entry_distance_deg * math.cos(math.radians(entry_angle))
        entry_lon = optimal_lon + entry_distance_deg * math.sin(math.radians(entry_angle))
        
        # Calculate fallback positions for wind shifts
        fallback_positions = []
        for shift in [-45, 45]:
            fallback_angle = (optimal_angle + shift) % 360
            fallback_lat = target_lat + distance_degrees * math.cos(math.radians(fallback_angle))
            fallback_lon = target_lon + distance_degrees * math.sin(math.radians(fallback_angle))
            fallback_positions.append((fallback_lat, fallback_lon))
        
        # Calculate confidence modifiers
        confidence_modifiers = {
            'wind_consistency': confidence_bonus,
            'wind_speed_factor': min(wind_data.speed_mph / 10.0, 1.0) * 0.1,
            'thermal_stability': (1.0 - wind_data.thermal_factor) * 0.05,
            'terrain_alignment': abs(wind_data.terrain_modification) * 0.1
        }
        
        return WindOptimizedPosition(
            latitude=optimal_lat,
            longitude=optimal_lon,
            downwind_angle=optimal_angle,
            wind_advantage_score=wind_advantage,
            scent_safety_margin=scent_safety,
            optimal_entry_route=(entry_lat, entry_lon),
            fallback_positions=fallback_positions,
            confidence_modifiers=confidence_modifiers
        )
    
    def _calculate_wind_advantage_score(self, wind_data: WindData, strategy_type: str) -> float:
        """Calculate wind advantage score based on conditions and strategy"""
        base_score = 50.0
        
        # Wind speed scoring
        if 3 <= wind_data.speed_mph <= 8:
            base_score += 30  # Ideal wind speed
        elif 8 < wind_data.speed_mph <= 12:
            base_score += 20  # Good wind speed
        elif 2 <= wind_data.speed_mph < 3:
            base_score += 10  # Light but usable wind
        else:
            base_score -= 20  # Too light or too strong
        
        # Consistency scoring
        consistency_scores = {
            WindConsistency.STEADY: 20,
            WindConsistency.MODERATE: 10,
            WindConsistency.VARIABLE: -10,
            WindConsistency.CHAOTIC: -25
        }
        base_score += consistency_scores[wind_data.consistency]
        
        # Thermal factor (lower is better for scent control)
        base_score += (1.0 - wind_data.thermal_factor) * 15
        
        # Strategy-specific adjustments
        if strategy_type == "bedding_approach":
            # Bedding approaches need very steady wind
            if wind_data.consistency in [WindConsistency.STEADY, WindConsistency.MODERATE]:
                base_score += 10
        elif strategy_type == "corridor_intercept":
            # Corridor intercepts can handle more variable wind
            if wind_data.speed_mph > 5:
                base_score += 5
        
        return max(0, min(100, base_score))
    
    def _calculate_scent_safety_margin(self, wind_data: WindData, distance_yards: float) -> float:
        """Calculate safety margin for scent detection"""
        # Base safety margin
        base_margin = self.wind_params['safety_margin_degrees']
        
        # Adjust for wind consistency
        if wind_data.consistency == WindConsistency.STEADY:
            margin_multiplier = 1.0
        elif wind_data.consistency == WindConsistency.MODERATE:
            margin_multiplier = 1.2
        elif wind_data.consistency == WindConsistency.VARIABLE:
            margin_multiplier = 1.5
        else:  # CHAOTIC
            margin_multiplier = 2.0
        
        # Adjust for distance (closer requires more margin)
        distance_factor = max(0.5, 200.0 / distance_yards)
        
        # Adjust for thermal effects
        thermal_factor = 1.0 + wind_data.thermal_factor * 0.5
        
        return base_margin * margin_multiplier * distance_factor * thermal_factor
    
    def analyze_multi_target_positioning(self, 
                                       targets: List[Tuple[float, float]], 
                                       wind_data: WindData,
                                       distance_yards: float = 150) -> List[WindOptimizedPosition]:
        """
        Analyze optimal positioning for multiple targets (bedding areas, corridors)
        
        Args:
            targets: List of (lat, lon) tuples for target locations
            wind_data: Current wind conditions
            distance_yards: Desired distance from targets
            
        Returns:
            List of WindOptimizedPosition objects for each target
        """
        positions = []
        
        for target_lat, target_lon in targets:
            position = self.calculate_optimal_downwind_position(
                target_lat, target_lon, wind_data, distance_yards
            )
            positions.append(position)
        
        return positions
    
    def get_wind_forecast(self, lat: float, lon: float, hours_ahead: int = 24) -> List[WindData]:
        """
        Get wind forecast for planning purposes
        
        Args:
            lat: Latitude
            lon: Longitude
            hours_ahead: Number of hours to forecast
            
        Returns:
            List of WindData objects for forecast period
        """
        try:
            url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial',
                'cnt': min(40, hours_ahead // 3)  # API returns 3-hour intervals
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecast_data = []
            for forecast in data['list'][:hours_ahead//3]:
                wind_info = forecast.get('wind', {})
                wind_direction = wind_info.get('deg', 0)
                wind_speed = wind_info.get('speed', 0)
                wind_gust = wind_info.get('gust')
                
                # Calculate forecast reliability (decreases with time)
                hours_out = len(forecast_data) * 3
                reliability = max(50, 90 - hours_out * 2)
                
                consistency = self._calculate_wind_consistency(wind_speed, wind_gust)
                
                wind_data = WindData(
                    direction_degrees=wind_direction,
                    speed_mph=wind_speed,
                    gust_mph=wind_gust,
                    consistency=consistency,
                    reliability_score=reliability,
                    thermal_factor=self._calculate_thermal_factor(),
                    terrain_modification=0.1,
                    forecast_hours=hours_out,
                    timestamp=datetime.now() + timedelta(hours=hours_out)
                )
                
                forecast_data.append(wind_data)
            
            return forecast_data
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch wind forecast: {e}")
            return []

def get_wind_analyzer(api_key: Optional[str] = None) -> WindAnalyzer:
    """Factory function to get wind analyzer instance"""
    return WindAnalyzer(api_key)
