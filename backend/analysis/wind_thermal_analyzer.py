#!/usr/bin/env python3
"""
Wind Direction and Thermal Analysis Integration

Comprehensive analysis of wind patterns and thermal effects for hunting location optimization.
Integrates prevailing winds, thermal winds, and terrain interactions for bedding, stand, and feeding locations.

Author: GitHub Copilot
Version: 1.0.0
Date: September 1, 2025
"""

import numpy as np
import math
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
@dataclass
class WindAnalysisResult:
    """Comprehensive wind analysis for a hunting location"""
    prevailing_wind_direction: float      # degrees (0-360)
    prevailing_wind_speed: float         # mph
    thermal_wind_active: bool            # whether thermal winds are significant
    thermal_wind_direction: str          # 'upslope', 'downslope', 'neutral'
    thermal_strength: float              # 0-10 scale
    effective_wind_direction: float      # combined wind direction (degrees)
    effective_wind_speed: float          # combined wind speed (mph)
    scent_cone_direction: float          # primary scent travel direction
    optimal_approach_bearing: float      # best approach direction for hunters
    wind_advantage_rating: float         # 0-10 rating for wind conditions
    recommendations: List[str]           # specific recommendations

@dataclass 
class LocationWindAnalysis:
    """Wind analysis specific to bedding, stand, or feeding locations"""
    location_type: str                   # 'bedding', 'stand', 'feeding'
    coordinates: Tuple[float, float]     # (lat, lon)
    wind_analysis: WindAnalysisResult    # overall wind analysis
    position_advantages: List[str]       # location-specific wind advantages
    position_disadvantages: List[str]    # location-specific wind issues
    optimal_entry_routes: List[str]      # recommended approach routes
    scent_management_tips: List[str]     # scent control recommendations
    timing_recommendations: str          # best times for this location
    confidence_score: float              # 0-1 confidence in analysis

class WindThermalAnalyzer:
    """
    Comprehensive wind and thermal analysis for hunting locations
    
    Combines:
    - Real-time weather data (prevailing winds)
    - Thermal wind calculations (terrain-based)
    - Location-specific analysis (bedding/stand/feeding)
    - Scent management recommendations
    """
    
    def __init__(self):
        # Wind analysis configuration
        self.config = {
            'thermal_significance_threshold': 3.0,  # mph - when thermal winds matter
            'light_wind_threshold': 5.0,           # mph - when wind is considered light
            'strong_wind_threshold': 15.0,         # mph - when wind is strong
            'optimal_wind_speed_range': (3, 12),   # mph - ideal wind speeds for hunting
            'scent_cone_spread_degrees': 30,       # typical scent cone spread
            'thermal_lag_hours': 1.0,              # hours between solar heating and thermal effect
        }
        
        # Vermont-specific wind patterns
        self.vermont_wind_patterns = {
            'common_directions': [180, 225, 270, 315],  # S, SW, W, NW most common
            'seasonal_tendencies': {
                'spring': 225,   # SW
                'summer': 270,   # W  
                'fall': 315,     # NW
                'winter': 360    # N
            }
        }
    
    def analyze_location_winds(self, location_type: str, lat: float, lon: float,
                              weather_data: Dict, terrain_features: Dict, 
                              thermal_data: Optional[Dict] = None,
                              time_of_day: int = 12) -> LocationWindAnalysis:
        """
        Comprehensive wind analysis for a specific hunting location
        
        Args:
            location_type: 'bedding', 'stand', or 'feeding'
            lat, lon: Location coordinates
            weather_data: Real weather data with wind information
            terrain_features: Terrain data (slope, aspect, elevation)
            thermal_data: Optional thermal analysis data
            time_of_day: Hour of day (0-23)
            
        Returns:
            Complete wind analysis for the location
        """
        
        logger.info(f"🌬️ Analyzing winds for {location_type} at {lat:.4f}, {lon:.4f}")
        
        # Analyze overall wind conditions
        wind_analysis = self._analyze_wind_conditions(weather_data, terrain_features, thermal_data, time_of_day)
        
        # Location-specific analysis
        position_analysis = self._analyze_position_specific_winds(
            location_type, wind_analysis, terrain_features
        )
        
        # Generate recommendations
        recommendations = self._generate_wind_recommendations(
            location_type, wind_analysis, position_analysis, terrain_features
        )
        
        result = LocationWindAnalysis(
            location_type=location_type,
            coordinates=(lat, lon),
            wind_analysis=wind_analysis,
            position_advantages=position_analysis['advantages'],
            position_disadvantages=position_analysis['disadvantages'],
            optimal_entry_routes=recommendations['entry_routes'],
            scent_management_tips=recommendations['scent_tips'],
            timing_recommendations=recommendations['timing'],
            confidence_score=wind_analysis.wind_advantage_rating / 10.0
        )
        
        logger.info(f"🎯 Wind analysis complete: {wind_analysis.effective_wind_direction:.0f}° at {wind_analysis.effective_wind_speed:.1f}mph, "
                   f"rating {wind_analysis.wind_advantage_rating:.1f}/10")
        
        return result
    
    def _analyze_wind_conditions(self, weather_data: Dict, terrain_features: Dict,
                                thermal_data: Optional[Dict], time_of_day: int) -> WindAnalysisResult:
        """Analyze overall wind conditions combining prevailing and thermal winds"""
        
        # Extract prevailing wind data
        prevailing_direction = weather_data.get('wind_direction', 270)  # degrees
        prevailing_speed = weather_data.get('wind_speed', 5)           # mph
        
        # Analyze thermal contribution
        thermal_active = False
        thermal_direction = 'neutral'
        thermal_strength = 0.0
        
        if thermal_data:
            thermal_active = thermal_data.get('is_active', False)
            thermal_direction = thermal_data.get('direction', 'neutral')
            thermal_strength = thermal_data.get('strength_scale', 0)
        
        # Calculate effective wind (combination of prevailing + thermal)
        effective_direction, effective_speed = self._combine_wind_sources(
            prevailing_direction, prevailing_speed, 
            thermal_direction, thermal_strength, terrain_features
        )
        
        # Calculate scent cone direction (where scent travels)
        scent_direction = (effective_direction + 180) % 360  # Downwind direction
        
        # Calculate optimal approach bearing (upwind approach)
        optimal_approach = effective_direction  # Upwind approach
        
        # Rate wind advantage for hunting
        wind_rating = self._rate_wind_conditions(effective_speed, prevailing_speed, thermal_strength)
        
        # Generate wind-specific recommendations
        recommendations = self._generate_general_wind_recommendations(
            effective_direction, effective_speed, thermal_active, thermal_strength
        )
        
        return WindAnalysisResult(
            prevailing_wind_direction=prevailing_direction,
            prevailing_wind_speed=prevailing_speed,
            thermal_wind_active=thermal_active,
            thermal_wind_direction=thermal_direction,
            thermal_strength=thermal_strength,
            effective_wind_direction=effective_direction,
            effective_wind_speed=effective_speed,
            scent_cone_direction=scent_direction,
            optimal_approach_bearing=optimal_approach,
            wind_advantage_rating=wind_rating,
            recommendations=recommendations
        )
    
    def _combine_wind_sources(self, prevailing_dir: float, prevailing_speed: float,
                             thermal_dir: str, thermal_strength: float,
                             terrain: Dict) -> Tuple[float, float]:
        """Combine prevailing wind and thermal wind effects"""
        
        # If thermal wind is not significant, use prevailing wind
        if thermal_strength < self.config['thermal_significance_threshold']:
            return prevailing_dir, prevailing_speed
        
        # Convert thermal direction to degrees
        thermal_dir_degrees = self._thermal_to_degrees(thermal_dir, terrain)
        
        # Calculate thermal wind speed (proportional to strength)
        thermal_speed = thermal_strength * 0.8  # Max ~8 mph for strength 10
        
        # Vector combination of winds
        # Prevailing wind vector
        prev_x = prevailing_speed * math.sin(math.radians(prevailing_dir))
        prev_y = prevailing_speed * math.cos(math.radians(prevailing_dir))
        
        # Thermal wind vector  
        thermal_x = thermal_speed * math.sin(math.radians(thermal_dir_degrees))
        thermal_y = thermal_speed * math.cos(math.radians(thermal_dir_degrees))
        
        # Combined vector
        combined_x = prev_x + thermal_x
        combined_y = prev_y + thermal_y
        
        # Convert back to direction and speed
        combined_speed = math.sqrt(combined_x**2 + combined_y**2)
        combined_direction = math.degrees(math.atan2(combined_x, combined_y)) % 360
        
        return combined_direction, combined_speed
    
    def _thermal_to_degrees(self, thermal_dir: str, terrain: Dict) -> float:
        """Convert thermal direction to compass degrees based on terrain"""
        
        slope_aspect = terrain.get('aspect', 180)  # degrees
        
        if thermal_dir == 'upslope':
            return slope_aspect  # Up the slope
        elif thermal_dir == 'downslope':
            return (slope_aspect + 180) % 360  # Down the slope
        else:  # neutral
            return slope_aspect  # Default to slope aspect
    
    def _rate_wind_conditions(self, effective_speed: float, prevailing_speed: float, 
                             thermal_strength: float) -> float:
        """Rate wind conditions for hunting (0-10 scale)"""
        
        rating = 5.0  # Base rating
        
        # Speed rating
        if self.config['optimal_wind_speed_range'][0] <= effective_speed <= self.config['optimal_wind_speed_range'][1]:
            rating += 2.0  # Optimal speed range
        elif effective_speed < self.config['light_wind_threshold']:
            rating -= 1.0  # Too light, unpredictable
        elif effective_speed > self.config['strong_wind_threshold']:
            rating -= 2.0  # Too strong, difficult hunting
        
        # Thermal advantage
        if thermal_strength > 5:
            rating += 1.5  # Strong thermal patterns are predictable
        elif thermal_strength > 3:
            rating += 0.5  # Moderate thermal help
        
        # Consistency rating
        speed_difference = abs(effective_speed - prevailing_speed)
        if speed_difference < 2:
            rating += 0.5  # Consistent winds
        
        return max(0.0, min(10.0, rating))
    
    def _analyze_position_specific_winds(self, location_type: str, wind_analysis: WindAnalysisResult,
                                        terrain: Dict) -> Dict:
        """Analyze wind advantages/disadvantages for specific location types"""
        
        advantages = []
        disadvantages = []
        
        wind_dir = wind_analysis.effective_wind_direction
        wind_speed = wind_analysis.effective_wind_speed
        slope_aspect = terrain.get('aspect', 180)
        
        if location_type == 'bedding':
            # Bedding locations need wind protection and scent security
            if self._is_leeward_position(wind_dir, slope_aspect):
                advantages.append("Leeward slope provides wind protection")
                advantages.append("Reduced scent dispersal for bedded deer")
            else:
                disadvantages.append("Windward exposure may disturb bedded deer")
            
            if wind_speed > 10:
                disadvantages.append("Strong winds may prevent bedding use")
            elif 3 <= wind_speed <= 8:
                advantages.append("Moderate winds mask approach sounds")
        
        elif location_type == 'stand':
            # Stand locations need scent management and approach advantages
            if wind_analysis.thermal_wind_active:
                advantages.append("Thermal winds provide predictable scent control")
            
            approach_angle = abs(wind_dir - slope_aspect)
            if approach_angle < 45 or approach_angle > 315:
                advantages.append("Upwind approach route available")
            else:
                disadvantages.append("Limited upwind approach options")
            
            if 5 <= wind_speed <= 12:
                advantages.append("Optimal wind speed for scent management")
            elif wind_speed < 3:
                disadvantages.append("Light winds create unpredictable scent patterns")
        
        elif location_type == 'feeding':
            # Feeding locations need security and approach/exit routes
            if wind_analysis.thermal_wind_active and wind_analysis.thermal_strength > 4:
                advantages.append("Strong thermal patterns aid deer security")
            
            if self._provides_multiple_wind_options(wind_dir, terrain):
                advantages.append("Multiple approach angles with wind advantage")
            
            if wind_speed > 12:
                disadvantages.append("Strong winds may prevent feeding activity")
        
        return {
            'advantages': advantages,
            'disadvantages': disadvantages
        }
    
    def _is_leeward_position(self, wind_direction: float, slope_aspect: float) -> bool:
        """Check if position is on leeward (protected) side of slope"""
        # Leeward side is opposite to wind direction
        leeward_aspect = (wind_direction + 180) % 360
        aspect_difference = abs(leeward_aspect - slope_aspect)
        return aspect_difference < 90 or aspect_difference > 270
    
    def _provides_multiple_wind_options(self, wind_direction: float, terrain: Dict) -> bool:
        """Check if terrain provides multiple approach options"""
        # Complex terrain with varied aspects provides more options
        slope = terrain.get('slope', 0)
        return slope > 15  # Steeper terrain typically has more varied aspects
    
    def _generate_wind_recommendations(self, location_type: str, wind_analysis: WindAnalysisResult,
                                      position_analysis: Dict, terrain: Dict) -> Dict:
        """Generate specific recommendations for the location and wind conditions"""
        
        entry_routes = []
        scent_tips = []
        timing = "Standard timing"
        
        wind_dir = wind_analysis.effective_wind_direction
        wind_speed = wind_analysis.effective_wind_speed
        
        # Entry route recommendations
        if wind_analysis.thermal_wind_active:
            if wind_analysis.thermal_wind_direction == 'downslope':
                entry_routes.append("Morning approach from upper elevations")
                timing = "Best during morning thermal period (5:30-8:00 AM)"
            elif wind_analysis.thermal_wind_direction == 'upslope':
                entry_routes.append("Evening approach from lower elevations")
                timing = "Best during evening thermal period (4:00-7:00 PM)"
        
        # Add primary upwind route
        upwind_direction = self._direction_to_compass(wind_analysis.optimal_approach_bearing)
        entry_routes.append(f"Primary approach from {upwind_direction}")
        
        # Scent management tips
        if wind_speed < 5:
            scent_tips.append("Use scent elimination products - light winds disperse scent slowly")
            scent_tips.append("Check wind direction frequently - light winds can shift")
        
        if wind_analysis.thermal_wind_active:
            scent_tips.append("Use thermal patterns to your advantage")
            scent_tips.append("Plan approach timing with thermal wind shifts")
        
        scent_tips.append(f"Primary scent cone travels toward {self._direction_to_compass(wind_analysis.scent_cone_direction)}")
        
        return {
            'entry_routes': entry_routes,
            'scent_tips': scent_tips,
            'timing': timing
        }
    
    def _generate_general_wind_recommendations(self, wind_dir: float, wind_speed: float,
                                              thermal_active: bool, thermal_strength: float) -> List[str]:
        """Generate general wind recommendations"""
        
        recommendations = []
        
        # Wind speed recommendations
        if wind_speed < 3:
            recommendations.append("Light winds - use extra scent control measures")
        elif wind_speed > 15:
            recommendations.append("Strong winds - deer movement may be reduced")
        else:
            recommendations.append("Good wind conditions for hunting")
        
        # Thermal recommendations
        if thermal_active and thermal_strength > 5:
            recommendations.append("Strong thermal patterns - plan timing around thermal shifts")
        elif thermal_active:
            recommendations.append("Moderate thermal activity - useful for scent management")
        
        # Direction consistency
        recommendations.append(f"Primary wind from {self._direction_to_compass(wind_dir)}")
        
        return recommendations
    
    def _direction_to_compass(self, degrees: float) -> str:
        """Convert degrees to compass direction"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
    
    def create_wind_analysis_summary(self, analyses: List[LocationWindAnalysis]) -> Dict:
        """Create a comprehensive summary of wind analysis for all locations"""
        
        summary = {
            'overall_wind_conditions': {},
            'location_summaries': {},
            'tactical_recommendations': [],
            'timing_optimization': {},
            'confidence_assessment': 0.0
        }
        
        if not analyses:
            return summary
        
        # Overall conditions (use first analysis as representative)
        first_analysis = analyses[0]
        wind = first_analysis.wind_analysis
        
        summary['overall_wind_conditions'] = {
            'prevailing_wind': f"{self._direction_to_compass(wind.prevailing_wind_direction)} at {wind.prevailing_wind_speed:.1f} mph",
            'thermal_activity': wind.thermal_wind_active,
            'effective_wind': f"{self._direction_to_compass(wind.effective_wind_direction)} at {wind.effective_wind_speed:.1f} mph",
            'hunting_rating': f"{wind.wind_advantage_rating:.1f}/10"
        }
        
        # Individual location summaries
        for analysis in analyses:
            loc_type = analysis.location_type
            summary['location_summaries'][loc_type] = {
                'advantages': analysis.position_advantages,
                'entry_routes': analysis.optimal_entry_routes,
                'timing': analysis.timing_recommendations,
                'confidence': analysis.confidence_score
            }
        
        # Overall tactical recommendations
        thermal_analyses = [a for a in analyses if a.wind_analysis.thermal_wind_active]
        if thermal_analyses:
            summary['tactical_recommendations'].append("Use thermal wind patterns for enhanced scent management")
        
        high_confidence = [a for a in analyses if a.confidence_score > 0.7]
        if len(high_confidence) == len(analyses):
            summary['tactical_recommendations'].append("High confidence in wind predictions - execute planned approaches")
        
        # Average confidence
        summary['confidence_assessment'] = sum(a.confidence_score for a in analyses) / len(analyses)
        
        return summary

# Global analyzer instance
_wind_thermal_analyzer = None

def get_wind_thermal_analyzer() -> WindThermalAnalyzer:
    """Get the singleton wind thermal analyzer instance"""
    global _wind_thermal_analyzer
    if _wind_thermal_analyzer is None:
        _wind_thermal_analyzer = WindThermalAnalyzer()
    return _wind_thermal_analyzer
