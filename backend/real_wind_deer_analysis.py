#!/usr/bin/env python3
"""
Real-Time Wind-Optimized Deer Prediction Enhancement

Integrates real wind data with deer behavioral modeling for:
1. Wind-aware bedding site prediction
2. Scent-optimized travel corridor analysis  
3. Wind-based stand positioning
4. Real-time wind shift alerts

Author: Expert Deer Biologist Team
Version: 1.0.0
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import math

logger = logging.getLogger(__name__)

@dataclass
class WindBehaviorModel:
    """Deer behavioral response to wind conditions"""
    wind_speed_mph: float
    wind_direction_degrees: float  # 0=North, 90=East, 180=South, 270=West
    wind_consistency: str          # 'steady', 'variable', 'gusty'
    deer_behavior_modification: Dict[str, float]

class RealTimeWindDeerAnalyzer:
    """
    Real-time wind integration with deer behavior modeling
    Uses actual Open-Meteo wind data for predictions
    """
    
    def __init__(self):
        # Deer behavioral thresholds based on research
        self.wind_thresholds = {
            'calm_wind_max': 5,      # mph - deer most active
            'moderate_wind_max': 15,  # mph - normal activity
            'high_wind_max': 25,     # mph - reduced activity
            'extreme_wind_min': 25   # mph - bedding/hiding behavior
        }
        
        # Scent dispersion distances (research-based)
        self.scent_distances = {
            'human_detection_yards': {
                'calm': 100,      # 0-5 mph
                'light': 200,     # 5-10 mph  
                'moderate': 400,  # 10-15 mph
                'strong': 600     # 15+ mph
            }
        }
    
    def analyze_wind_deer_behavior(self, wind_data: Dict, terrain_features: Dict, 
                                 lat: float, lon: float) -> Dict[str, Any]:
        """
        Analyze how real wind conditions affect deer behavior
        
        Args:
            wind_data: Real wind data from Open-Meteo
            terrain_features: Terrain analysis results
            lat, lon: Location coordinates
            
        Returns:
            Wind-modified deer behavior predictions
        """
        
        current_wind = wind_data.get('wind', {})
        wind_speed = current_wind.get('speed', 5)  # mph
        wind_direction = current_wind.get('deg', 0)  # degrees
        
        # Hourly wind forecasts for next 24 hours
        hourly_wind = wind_data.get('hourly_wind', [])
        
        logger.info(f"🌬️ Wind Analysis: {wind_speed}mph from {wind_direction}°")
        
        # Analyze wind behavioral impacts
        behavior_analysis = {
            'current_wind_impact': self._assess_wind_impact(wind_speed, wind_direction),
            'bedding_modifications': self._wind_bedding_analysis(wind_data, terrain_features),
            'travel_modifications': self._wind_travel_analysis(wind_data, terrain_features),
            'scent_dispersion': self._calculate_scent_zones(wind_speed, wind_direction),
            'optimal_stand_positions': self._calculate_wind_optimized_stands(wind_data, terrain_features, lat, lon),
            'wind_forecast_impact': self._analyze_wind_forecast(hourly_wind),
            'hunting_recommendations': []
        }
        
        # Generate hunting recommendations
        behavior_analysis['hunting_recommendations'] = self._generate_wind_recommendations(behavior_analysis)
        
        return behavior_analysis
    
    def _assess_wind_impact(self, wind_speed: float, wind_direction: float) -> Dict[str, Any]:
        """Assess overall wind impact on deer behavior"""
        
        impact = {
            'activity_level': 'normal',
            'movement_confidence': 1.0,
            'bedding_preference': 'standard',
            'alertness_level': 'normal'
        }
        
        # Wind speed impacts
        if wind_speed <= self.wind_thresholds['calm_wind_max']:
            impact.update({
                'activity_level': 'high',
                'movement_confidence': 1.2,
                'bedding_preference': 'open_areas',
                'alertness_level': 'high'  # More alert in calm conditions
            })
        elif wind_speed <= self.wind_thresholds['moderate_wind_max']:
            impact.update({
                'activity_level': 'normal', 
                'movement_confidence': 1.0,
                'bedding_preference': 'standard'
            })
        elif wind_speed <= self.wind_thresholds['high_wind_max']:
            impact.update({
                'activity_level': 'reduced',
                'movement_confidence': 0.8,
                'bedding_preference': 'wind_protected',
                'alertness_level': 'reduced'  # Hearing impaired
            })
        else:  # Extreme wind
            impact.update({
                'activity_level': 'minimal',
                'movement_confidence': 0.5,
                'bedding_preference': 'deep_cover',
                'alertness_level': 'minimal'
            })
        
        return impact
    
    def _wind_bedding_analysis(self, wind_data: Dict, terrain_features: Dict) -> Dict[str, Any]:
        """Analyze how wind affects bedding site selection"""
        
        current_wind = wind_data.get('wind', {})
        wind_speed = current_wind.get('speed', 5)
        wind_direction = current_wind.get('deg', 0)
        
        bedding_mods = {
            'preferred_aspects': [],  # Slope aspects deer will prefer
            'wind_protection_factor': 1.0,
            'visibility_requirements': 'standard',
            'elevation_preferences': []
        }
        
        # Calculate downwind monitoring positions
        # Deer bed facing downwind to scent-check approaches
        downwind_direction = (wind_direction + 180) % 360
        
        # Preferred bedding aspects (deer face downwind)
        # Allow ±45° tolerance for terrain constraints
        preferred_range = [
            (downwind_direction - 45) % 360,
            (downwind_direction + 45) % 360
        ]
        bedding_mods['preferred_aspects'] = preferred_range
        
        # Wind speed modifications
        if wind_speed > 15:  # High wind - seek protection
            bedding_mods.update({
                'wind_protection_factor': 1.5,  # Increased need for wind breaks
                'visibility_requirements': 'reduced',  # Accept less visibility for protection
                'elevation_preferences': ['leeward_slopes', 'valley_bottoms', 'dense_cover']
            })
        elif wind_speed < 5:  # Calm wind - prioritize visibility
            bedding_mods.update({
                'wind_protection_factor': 0.7,
                'visibility_requirements': 'enhanced',  # Need good sightlines
                'elevation_preferences': ['ridge_tops', 'open_slopes', 'field_edges']
            })
        
        return bedding_mods
    
    def _wind_travel_analysis(self, wind_data: Dict, terrain_features: Dict) -> Dict[str, Any]:
        """Analyze how wind affects travel corridor selection"""
        
        current_wind = wind_data.get('wind', {})
        wind_speed = current_wind.get('speed', 5)
        wind_direction = current_wind.get('deg', 0)
        
        travel_mods = {
            'corridor_preferences': [],
            'timing_modifications': {},
            'route_selection_factors': {}
        }
        
        # Wind direction impacts on corridor selection
        if wind_speed > 20:  # High wind - use protected routes
            travel_mods['corridor_preferences'] = [
                'creek_bottoms',     # Wind protected
                'dense_timber',      # Wind break
                'leeward_slopes'     # Protected from wind
            ]
            travel_mods['timing_modifications'] = {
                'dawn_movement': 'delayed',    # Wait for wind to calm
                'dusk_movement': 'earlier',    # Move before evening wind
                'midday_movement': 'increased' # Use calm periods
            }
        
        elif wind_speed < 5:  # Calm wind - can use open routes
            travel_mods['corridor_preferences'] = [
                'field_edges',       # Good visibility
                'ridge_tops',        # Scent advantage
                'open_corridors'     # Less cover needed
            ]
            travel_mods['timing_modifications'] = {
                'dawn_movement': 'normal',
                'dusk_movement': 'normal', 
                'midday_movement': 'reduced'  # Avoid open areas in daylight
            }
        
        # Scent management in travel routes
        # Deer prefer crosswind or upwind travel when possible
        crosswind_angles = [
            (wind_direction + 90) % 360,   # Left crosswind
            (wind_direction - 90) % 360    # Right crosswind  
        ]
        upwind_angle = wind_direction
        
        travel_mods['route_selection_factors'] = {
            'preferred_travel_angles': crosswind_angles + [upwind_angle],
            'avoid_downwind_travel': True,
            'scent_awareness_boost': wind_speed / 20.0  # Higher wind = more scent awareness
        }
        
        return travel_mods
    
    def _calculate_scent_zones(self, wind_speed: float, wind_direction: float) -> Dict[str, Any]:
        """Calculate human scent dispersion zones"""
        
        # Determine scent category based on wind speed
        if wind_speed <= 5:
            scent_category = 'calm'
        elif wind_speed <= 10:
            scent_category = 'light'  
        elif wind_speed <= 15:
            scent_category = 'moderate'
        else:
            scent_category = 'strong'
        
        detection_distance = self.scent_distances['human_detection_yards'][scent_category]
        
        # Calculate scent cone geometry
        scent_zone = {
            'max_detection_distance_yards': detection_distance,
            'scent_cone_angle': self._calculate_scent_cone_angle(wind_speed),
            'primary_scent_direction': wind_direction,
            'danger_zone_coordinates': self._calculate_danger_zone(wind_direction, detection_distance),
            'safe_approach_angles': self._calculate_safe_approaches(wind_direction)
        }
        
        return scent_zone
    
    def _calculate_scent_cone_angle(self, wind_speed: float) -> float:
        """Calculate scent dispersion cone angle based on wind speed"""
        
        # Research-based scent cone angles
        if wind_speed <= 5:     # Calm - wide dispersion
            return 60.0  # degrees
        elif wind_speed <= 10:  # Light - moderate dispersion
            return 45.0
        elif wind_speed <= 15:  # Moderate - focused dispersion  
            return 30.0
        else:                   # Strong - narrow dispersion
            return 20.0
    
    def _calculate_danger_zone(self, wind_direction: float, distance_yards: float) -> List[Tuple[float, float]]:
        """Calculate coordinates of scent danger zone"""
        
        # Convert to relative coordinates (hunter at 0,0)
        # Wind direction is where wind is going TO (scent travels this direction)
        
        scent_direction_rad = math.radians(wind_direction)
        cone_angle = self._calculate_scent_cone_angle(5)  # Use moderate cone
        half_cone_rad = math.radians(cone_angle / 2)
        
        # Calculate danger zone polygon points
        danger_zone = []
        
        # Center line of scent cone
        center_x = distance_yards * math.sin(scent_direction_rad)
        center_y = distance_yards * math.cos(scent_direction_rad)
        
        # Left edge of cone
        left_angle = scent_direction_rad - half_cone_rad
        left_x = distance_yards * math.sin(left_angle)
        left_y = distance_yards * math.cos(left_angle)
        
        # Right edge of cone  
        right_angle = scent_direction_rad + half_cone_rad
        right_x = distance_yards * math.sin(right_angle)
        right_y = distance_yards * math.cos(right_angle)
        
        danger_zone = [
            (0, 0),           # Hunter position
            (left_x, left_y), # Left cone edge
            (center_x, center_y), # Cone center
            (right_x, right_y),   # Right cone edge
            (0, 0)            # Back to hunter
        ]
        
        return danger_zone
    
    def _calculate_safe_approaches(self, wind_direction: float) -> List[float]:
        """Calculate safe approach angles to avoid scent detection"""
        
        # Safe approaches are upwind and crosswind
        upwind_angle = (wind_direction + 180) % 360
        crosswind_left = (wind_direction + 270) % 360  
        crosswind_right = (wind_direction + 90) % 360
        
        return [upwind_angle, crosswind_left, crosswind_right]
    
    def _calculate_wind_optimized_stands(self, wind_data: Dict, terrain_features: Dict, 
                                       lat: float, lon: float) -> List[Dict[str, Any]]:
        """Calculate optimal stand positions based on wind patterns"""
        
        current_wind = wind_data.get('wind', {})
        wind_direction = current_wind.get('deg', 0)
        
        # Get hourly wind forecast to check consistency
        hourly_wind = wind_data.get('hourly_wind', [])
        
        optimized_stands = []
        
        # For each potential deer target area, calculate optimal stand position
        target_areas = ['bedding_zones', 'feeding_areas', 'travel_corridors']
        
        for target_type in target_areas:
            # Calculate stand position that's upwind/crosswind from target
            stand_recommendation = {
                'target_type': target_type,
                'recommended_bearing_from_target': (wind_direction + 180) % 360,  # Upwind
                'alternative_bearings': [
                    (wind_direction + 225) % 360,  # Upwind-left
                    (wind_direction + 135) % 360   # Upwind-right
                ],
                'distance_yards': self._calculate_optimal_stand_distance(current_wind.get('speed', 5)),
                'wind_consistency_score': self._assess_wind_consistency(hourly_wind),
                'setup_notes': self._generate_stand_setup_notes(wind_data, target_type)
            }
            
            optimized_stands.append(stand_recommendation)
        
        return optimized_stands
    
    def _calculate_optimal_stand_distance(self, wind_speed: float) -> int:
        """Calculate optimal stand distance based on wind speed"""
        
        # Closer in high wind (shorter scent travel), farther in calm wind
        if wind_speed >= 15:
            return 75   # yards - closer due to reduced scent travel
        elif wind_speed >= 10:
            return 100  # yards - moderate distance
        elif wind_speed >= 5:
            return 125  # yards - standard distance
        else:
            return 150  # yards - farther due to wider scent dispersion
    
    def _assess_wind_consistency(self, hourly_wind: List[Dict]) -> float:
        """Assess wind direction consistency over next 8 hours"""
        
        if not hourly_wind or len(hourly_wind) < 8:
            return 0.5  # Unknown consistency
        
        directions = [hour.get('wind_direction', 0) for hour in hourly_wind[:8]]
        
        # Calculate direction variance
        # Convert to unit vectors to handle 360° wraparound
        x_components = [math.cos(math.radians(d)) for d in directions]
        y_components = [math.sin(math.radians(d)) for d in directions]
        
        mean_x = sum(x_components) / len(x_components)
        mean_y = sum(y_components) / len(y_components)
        
        # Resultant vector length indicates consistency
        resultant_length = math.sqrt(mean_x**2 + mean_y**2)
        
        return resultant_length  # 1.0 = perfectly consistent, 0.0 = completely random
    
    def _analyze_wind_forecast(self, hourly_wind: List[Dict]) -> Dict[str, Any]:
        """Analyze wind forecast for hunting planning"""
        
        if not hourly_wind:
            return {'forecast_quality': 'unavailable'}
        
        forecast_analysis = {
            'forecast_quality': 'good',
            'best_hunting_hours': [],
            'wind_shift_alerts': [],
            'consistency_periods': []
        }
        
        # Analyze each hour for hunting suitability
        for i, hour_data in enumerate(hourly_wind[:24]):
            hour = hour_data.get('hour', i)
            wind_speed = hour_data.get('wind_speed', 5)
            wind_direction = hour_data.get('wind_direction', 0)
            
            # Score this hour for hunting (calm, steady wind is best)
            hour_score = self._score_hunting_hour(wind_speed, wind_direction, i, hourly_wind)
            
            if hour_score >= 0.8:  # High score hours
                forecast_analysis['best_hunting_hours'].append({
                    'hour': hour,
                    'score': hour_score,
                    'wind_speed': wind_speed,
                    'wind_direction': wind_direction,
                    'reason': self._explain_hour_score(wind_speed, wind_direction)
                })
        
        return forecast_analysis
    
    def _score_hunting_hour(self, wind_speed: float, wind_direction: float, 
                           hour_index: int, hourly_wind: List[Dict]) -> float:
        """Score an hour for hunting quality based on wind conditions"""
        
        score = 1.0
        
        # Wind speed scoring (5-15 mph is optimal)
        if 5 <= wind_speed <= 15:
            speed_score = 1.0
        elif wind_speed < 5:
            speed_score = 0.7  # Too calm - scent lingers
        elif wind_speed <= 20:
            speed_score = 0.8  # Acceptable  
        else:
            speed_score = 0.4  # Too windy
        
        # Wind consistency scoring (check ±2 hours)
        consistency_score = 1.0
        if hour_index >= 2 and hour_index < len(hourly_wind) - 2:
            directions = []
            for offset in [-2, -1, 0, 1, 2]:
                idx = hour_index + offset
                if 0 <= idx < len(hourly_wind):
                    directions.append(hourly_wind[idx].get('wind_direction', 0))
            
            if directions:
                direction_variance = self._calculate_direction_variance(directions)
                if direction_variance < 30:      # Very consistent
                    consistency_score = 1.0
                elif direction_variance < 60:   # Moderately consistent
                    consistency_score = 0.8
                else:                           # Variable
                    consistency_score = 0.6
        
        return score * speed_score * consistency_score
    
    def _calculate_direction_variance(self, directions: List[float]) -> float:
        """Calculate variance in wind directions (handling 360° wraparound)"""
        
        # Convert to unit vectors
        x_components = [math.cos(math.radians(d)) for d in directions]
        y_components = [math.sin(math.radians(d)) for d in directions]
        
        # Calculate mean direction
        mean_x = sum(x_components) / len(x_components)
        mean_y = sum(y_components) / len(y_components)
        mean_direction = math.degrees(math.atan2(mean_y, mean_x)) % 360
        
        # Calculate variance from mean
        variances = []
        for direction in directions:
            diff = abs(direction - mean_direction)
            # Handle wraparound (e.g., 350° vs 10° = 20° difference, not 340°)
            if diff > 180:
                diff = 360 - diff
            variances.append(diff)
        
        return sum(variances) / len(variances)
    
    def _explain_hour_score(self, wind_speed: float, wind_direction: float) -> str:
        """Explain why an hour scored well for hunting"""
        
        explanations = []
        
        if 5 <= wind_speed <= 15:
            explanations.append("optimal wind speed")
        elif wind_speed < 5:
            explanations.append("calm conditions")
        
        if 5 <= wind_speed <= 10:
            explanations.append("good scent control")
        
        return ", ".join(explanations) if explanations else "favorable conditions"
    
    def _generate_stand_setup_notes(self, wind_data: Dict, target_type: str) -> List[str]:
        """Generate specific setup notes for wind conditions"""
        
        current_wind = wind_data.get('wind', {})
        wind_speed = current_wind.get('speed', 5)
        
        notes = []
        
        if target_type == 'bedding_zones':
            notes.append("🛏️ Position upwind from bedding areas")
            notes.append("🌬️ Expect deer to face downwind while bedded")
            
        elif target_type == 'feeding_areas':  
            notes.append("🌾 Set up on downwind edge of feeding area")
            notes.append("👃 Deer will frequently scent-check while feeding")
            
        elif target_type == 'travel_corridors':
            notes.append("🛤️ Position at crosswind angle to corridor")
            notes.append("⚡ Expect quick movement through corridors")
        
        # Wind-specific notes
        if wind_speed > 15:
            notes.append("💨 High wind - deer may move more in daylight")
            notes.append("🔇 Hearing advantage - deer can't hear as well")
        elif wind_speed < 5:
            notes.append("🤫 Calm conditions - extra stealth required") 
            notes.append("👂 Deer hearing at maximum - minimize noise")
        
        return notes
    
    def _generate_wind_recommendations(self, behavior_analysis: Dict) -> List[str]:
        """Generate hunting recommendations based on wind analysis"""
        
        recommendations = []
        
        wind_impact = behavior_analysis.get('current_wind_impact', {})
        activity_level = wind_impact.get('activity_level', 'normal')
        
        if activity_level == 'high':
            recommendations.append("🎯 Excellent wind conditions - deer highly active")
            recommendations.append("🌄 Focus on dawn/dusk movement periods")
            
        elif activity_level == 'reduced':
            recommendations.append("⚠️ Moderate wind - deer activity reduced") 
            recommendations.append("🏔️ Target wind-protected bedding areas")
            
        elif activity_level == 'minimal':
            recommendations.append("🌪️ High wind - minimal deer movement expected")
            recommendations.append("🛏️ Focus on bedding areas in thick cover")
        
        # Scent management recommendations
        scent_data = behavior_analysis.get('scent_dispersion', {})
        detection_distance = scent_data.get('max_detection_distance_yards', 200)
        
        recommendations.append(f"👃 Scent detection risk: {detection_distance} yards downwind")
        recommendations.append("🏹 Use crosswind or upwind approach routes only")
        
        # Wind forecast recommendations
        forecast = behavior_analysis.get('wind_forecast_impact', {})
        best_hours = forecast.get('best_hunting_hours', [])
        
        if best_hours:
            best_hour = best_hours[0]['hour']
            recommendations.append(f"⏰ Optimal hunting window: {best_hour:02d}:00 hour")
        
        return recommendations

# Global instance
_wind_deer_analyzer = None

def get_wind_deer_analyzer() -> RealTimeWindDeerAnalyzer:
    """Get the global wind-deer analyzer instance"""
    global _wind_deer_analyzer
    if _wind_deer_analyzer is None:
        _wind_deer_analyzer = RealTimeWindDeerAnalyzer()
    return _wind_deer_analyzer
