#!/usr/bin/env python3
"""
Mature Buck Prediction Module for Vermont White-tailed Deer

This module implements specialized prediction algorithms for targeting mature bucks (3.5+ years)
rather than general deer populations. Mature bucks exhibit significantly different behavior
patterns, terrain preferences, and pressure responses compared to younger deer.

Key Differences:
- More secretive and pressure-sensitive
- Prefer thicker, more remote bedding areas
- Different movement patterns and timing
- Enhanced escape route awareness
- Distinct rut behavior patterns

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

# Import unified scoring framework
from .scoring_engine import (
    get_scoring_engine, 
    ScoringContext, 
    TerrainScoreComponents,
    score_terrain_suitability,
    score_with_context
)
from .distance_scorer import (
    get_distance_scorer,
    score_road_proximity,
    score_agricultural_proximity,
    score_escape_routes
)
# Import configuration management
from .config_manager import get_config

logger = logging.getLogger(__name__)

class BuckAgeClass(Enum):
    """Buck age classifications with different behavior patterns"""
    YEARLING = "1.5_years"          # Young, inexperienced
    YOUNG_ADULT = "2.5_years"       # Learning patterns
    MATURE = "3.5_plus_years"       # Fully mature, wary
    DOMINANT = "5.5_plus_years"     # Alpha behavior

class PressureLevel(Enum):
    """Human hunting pressure levels affecting buck behavior"""
    MINIMAL = "minimal"             # <1 hunter per 100 acres
    MODERATE = "moderate"           # 1-3 hunters per 100 acres  
    HIGH = "high"                   # 3-5 hunters per 100 acres
    EXTREME = "extreme"             # >5 hunters per 100 acres

@dataclass
class MatureBuckPreferences:
    """Terrain and habitat preferences specific to mature bucks - now configurable"""
    
    def __init__(self):
        """Initialize preferences from configuration"""
        config = get_config()
        prefs = config.get_mature_buck_preferences()
        
        # Habitat preferences
        habitat = prefs.get('habitat', {})
        self.min_bedding_thickness = habitat.get('min_bedding_thickness', 80.0)
        self.escape_route_count = habitat.get('escape_route_count', 3)
        self.human_avoidance_buffer = habitat.get('human_avoidance_buffer', 800.0)
        
        # Terrain preferences  
        terrain = prefs.get('terrain', {})
        self.elevation_preference_min = terrain.get('elevation_preference_min', 305.0)
        self.slope_preference_max = terrain.get('slope_preference_max', 30.0)
        self.water_proximity_max = terrain.get('water_proximity_max', 400.0)
        
        # Behavioral preferences
        behavioral = prefs.get('behavioral', {})
        self.pressure_sensitivity = behavioral.get('pressure_sensitivity', 0.8)
        self.movement_confidence_threshold = behavioral.get('movement_confidence_threshold', 0.7)
    
class MatureBuckBehaviorModel:
    """
    Comprehensive behavior model for mature buck prediction
    
    This class implements research-based behavior patterns specific to mature
    white-tailed bucks in Vermont's ecosystem. It accounts for seasonal changes,
    pressure responses, and terrain preferences that differ from general deer populations.
    """
    
    def __init__(self):
        self.preferences = MatureBuckPreferences()
        self.confidence_factors = self._initialize_confidence_factors()
        self.config = get_config()
    
    def _safe_float_conversion(self, value, default: float = 0.0) -> float:
        """Safely convert numpy arrays or other values to float"""
        if value is None:
            return default
        
        if hasattr(value, 'size'):
            if value.size > 1:
                return float(np.mean(value))
            elif value.size == 1:
                return float(value.item())
            else:
                return default
        else:
            try:
                return float(value)
            except (ValueError, TypeError):
                return default
        
    def _initialize_confidence_factors(self) -> Dict[str, float]:
        """Initialize confidence scoring factors from configuration"""
        config = get_config()
        scoring_factors = config.get_scoring_factors()
        
        # Get bonuses from configuration
        bonuses = scoring_factors.get('confidence_bonuses', {})
        penalties = scoring_factors.get('confidence_penalties', {})
        
        return {
            'thick_cover_bonus': bonuses.get('thick_cover_bonus', 25.0),
            'escape_route_bonus': bonuses.get('escape_route_bonus', 20.0),
            'elevation_bonus': bonuses.get('elevation_bonus', 15.0),
            'isolation_bonus': bonuses.get('isolation_bonus', 20.0),
            'water_proximity_bonus': bonuses.get('water_proximity_bonus', 10.0),
            'terrain_complexity_bonus': bonuses.get('terrain_complexity_bonus', 15.0),
            'pressure_penalty': penalties.get('pressure_penalty', -30.0),
            'road_proximity_penalty': penalties.get('road_proximity_penalty', -15.0),
            'human_activity_penalty': penalties.get('human_activity_penalty', -25.0)
        }
    
    def analyze_mature_buck_terrain(self, terrain_features: Dict, lat: float, lon: float) -> Dict[str, float]:
        """
        Analyze terrain suitability for mature bucks
        
        Args:
            terrain_features: Terrain analysis results
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Dict containing mature buck terrain scores and factors
        """
        logger.info(f"Analyzing mature buck terrain preferences for {lat}, {lon}")
        
        scores = {
            'bedding_suitability': 0.0,
            'escape_route_quality': 0.0,
            'isolation_score': 0.0,
            'pressure_resistance': 0.0,
            'overall_suitability': 0.0
        }
        
        # Analyze bedding area suitability
        scores['bedding_suitability'] = self._score_bedding_areas(terrain_features)
        
        # Evaluate escape route options
        scores['escape_route_quality'] = self._score_escape_routes(terrain_features)
        
        # Assess isolation from human activity
        scores['isolation_score'] = self._score_isolation(terrain_features, lat, lon)
        
        # Calculate pressure resistance
        scores['pressure_resistance'] = self._score_pressure_resistance(terrain_features)
        
        # Calculate overall suitability
        scores['overall_suitability'] = self._calculate_overall_suitability(scores)
        
        logger.info(f"Mature buck terrain analysis complete. Overall score: {scores['overall_suitability']:.2f}")
        return scores
    
    def _score_bedding_areas(self, terrain_features: Dict) -> float:
        """Score bedding area suitability for mature bucks using unified framework"""
        # Use unified scoring engine for consistent terrain evaluation
        scoring_engine = get_scoring_engine()
        
        # Calculate terrain scores using unified framework
        terrain_scores = scoring_engine.calculate_terrain_scores(terrain_features, "bedding")
        
        # Apply mature buck specific adjustments
        base_score = terrain_scores.total_score()
        
        # Mature buck specific bonuses
        canopy_closure = scoring_engine.safe_float_conversion(terrain_features.get('canopy_closure'), 50.0)
        if canopy_closure >= self.preferences.min_bedding_thickness:
            base_score += 10.0  # Extra bonus for very thick cover
        
        # North-facing aspect bonus for thermal cover
        aspect = scoring_engine.safe_float_conversion(terrain_features.get('aspect'), 180.0)
        if 315 <= aspect <= 360 or 0 <= aspect <= 45:  # North-facing
            base_score += 5.0
        
        return min(base_score, 100.0)
    
    def _score_escape_routes(self, terrain_features: Dict) -> float:
        """Evaluate escape route quality for mature bucks using unified framework"""
        # Use distance scorer for escape route evaluation
        distance_scorer = get_distance_scorer()
        scoring_engine = get_scoring_engine()
        
        # Calculate terrain complexity score
        terrain_scores = scoring_engine.calculate_terrain_scores(terrain_features, "travel")
        
        # Use escape route distance scoring
        escape_distance = scoring_engine.safe_float_conversion(
            terrain_features.get('escape_route_distance'), 200.0
        )
        escape_score = distance_scorer.calculate_escape_route_score(escape_distance)
        
        # Combine terrain travel score with escape route accessibility
        base_score = (terrain_scores.connectivity_score + escape_score) / 2
        
        # Mature buck specific bonuses
        drainage_density = scoring_engine.safe_float_conversion(
            terrain_features.get('drainage_density'), 0.5
        )
        if drainage_density >= 1.5:  # Multiple escape corridors
            base_score += 10.0
        
        return min(base_score, 100.0)
    
    def _score_isolation(self, terrain_features: Dict, lat: float, lon: float) -> float:
        """Score isolation from human activity using unified distance scoring"""
        distance_scorer = get_distance_scorer()
        
        # Use unified distance scoring for road proximity
        road_distance = distance_scorer.safe_distance_conversion(
            terrain_features.get('nearest_road_distance'), 1000.0
        )
        road_score = distance_scorer.calculate_road_impact_score(road_distance)
        
        # Calculate composite isolation score
        distances = {
            'road': road_distance,
            'building': distance_scorer.safe_distance_conversion(
                terrain_features.get('nearest_building_distance'), 1000.0
            )
        }
        
        # Use weighted distance scoring
        weights = {'road': 0.6, 'building': 0.4}
        composite_score = distance_scorer.calculate_composite_distance_score(distances, weights)
        
        # Apply mature buck specific isolation penalties
        trail_density = distance_scorer.safe_distance_conversion(
            terrain_features.get('trail_density'), 0.5
        )
        if trail_density > 2.0:
            composite_score -= 25.0
        elif trail_density > 1.0:
            composite_score -= 15.0
        
        return max(composite_score, 0.0)
    
    def _score_pressure_resistance(self, terrain_features: Dict) -> float:
        """Score area's ability to support mature bucks under hunting pressure"""
        score = 0.0
        
        # Thick escape cover
        escape_cover_thickness = self._safe_float_conversion(terrain_features.get('escape_cover_density'), 50.0)
        if escape_cover_thickness >= 80.0:
            score += 30.0
        elif escape_cover_thickness >= 60.0:
            score += 20.0
        
        # Terrain that's difficult for hunters to access
        hunter_accessibility = self._safe_float_conversion(terrain_features.get('hunter_accessibility'), 0.7)
        if hunter_accessibility <= 0.3:  # Very difficult access
            score += 25.0
        elif hunter_accessibility <= 0.5:
            score += 15.0
        
        # Swampland and wetlands (natural barriers)
        wetland_proximity = self._safe_float_conversion(terrain_features.get('wetland_proximity'), 1000.0)
        if wetland_proximity <= 100:
            score += 20.0
        elif wetland_proximity <= 300:
            score += 10.0
        
        # Cliff faces and steep terrain
        cliff_proximity = self._safe_float_conversion(terrain_features.get('cliff_proximity'), 1000.0)
        if cliff_proximity <= 200:
            score += 15.0
        
        # Dense understory that limits visibility
        visibility_limitation = self._safe_float_conversion(terrain_features.get('visibility_limitation'), 0.5)
        if visibility_limitation >= 0.8:
            score += 10.0
        
        return min(score, 100.0)
    
    def _calculate_overall_suitability(self, scores: Dict[str, float]) -> float:
        """Calculate weighted overall suitability score"""
        weights = {
            'bedding_suitability': 0.35,
            'escape_route_quality': 0.30,
            'isolation_score': 0.20,
            'pressure_resistance': 0.15
        }
        
        overall = sum(scores[key] * weights[key] for key in weights.keys())
        return min(overall, 100.0)
    
    def predict_mature_buck_movement(self, season: str, time_of_day: int, 
                                   terrain_features: Dict, weather_data: Dict, 
                                   lat: float, lon: float) -> Dict[str, any]:
        """
        Predict mature buck movement patterns based on season and conditions
        
        Args:
            season: Hunting season (early_season, rut, late_season)
            time_of_day: Hour of day (0-23)
            terrain_features: Terrain analysis results
            weather_data: Current weather conditions
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Movement prediction data including timing, locations, and confidence
        """
        logger.info(f"Predicting mature buck movement for {season}, hour {time_of_day}")
        
        movement_data = {
            'movement_probability': 0.0,
            'preferred_times': [],
            'movement_corridors': [],
            'bedding_predictions': [],
            'feeding_predictions': [],
            'confidence_score': 0.0,
            'behavioral_notes': []
        }
        
        # Season-specific movement patterns
        if season == "early_season":
            movement_data.update(self._early_season_patterns(time_of_day, terrain_features, weather_data))
        elif season == "rut":
            movement_data.update(self._rut_season_patterns(time_of_day, terrain_features, weather_data))
        elif season == "late_season":
            movement_data.update(self._late_season_patterns(time_of_day, terrain_features, weather_data))
        
        # Populate spatial predictions
        movement_data['movement_corridors'] = self._identify_movement_corridors(terrain_features, lat, lon)
        movement_data['bedding_predictions'] = self._predict_bedding_locations(terrain_features, lat, lon)
        movement_data['feeding_predictions'] = self._predict_feeding_zones(terrain_features, lat, lon, season)
        
        # Apply pressure adjustments
        movement_data = self._apply_pressure_adjustments(movement_data, terrain_features)
        
        # Calculate final confidence
        movement_data['confidence_score'] = self._calculate_movement_confidence(
            movement_data, terrain_features, weather_data
        )
        
        return movement_data
    
    def _early_season_patterns(self, time_of_day: int, terrain_features: Dict, weather_data: Dict) -> Dict:
        """Early season movement patterns for mature bucks"""
        patterns = {
            'movement_probability': 0.0,
            'preferred_times': [],
            'behavioral_notes': []
        }
        
        # Early season: Mature bucks are very cautious, mostly nocturnal
        if 22 <= time_of_day <= 23 or 0 <= time_of_day <= 6:
            patterns['movement_probability'] = 70.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Primary movement window")
        elif 17 <= time_of_day <= 21:
            patterns['movement_probability'] = 40.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Limited movement possible")
        elif 6 <= time_of_day <= 8:
            patterns['movement_probability'] = 30.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Brief morning movement")
        else:
            patterns['movement_probability'] = 5.0
        
        patterns['behavioral_notes'].extend([
            "Mature bucks are establishing fall patterns",
            "Primarily nocturnal movement to avoid pressure",
            "Bachelor groups may still be loosely associated",
            "Focus on food sources with thick cover access"
        ])
        
        return patterns
    
    def _rut_season_patterns(self, time_of_day: int, terrain_features: Dict, weather_data: Dict) -> Dict:
        """Rut season movement patterns for mature bucks"""
        patterns = {
            'movement_probability': 0.0,
            'preferred_times': [],
            'behavioral_notes': []
        }
        
        # Rut: Mature bucks move more during daylight but still cautious
        if 6 <= time_of_day <= 10:
            patterns['movement_probability'] = 80.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Prime morning movement")
        elif 15 <= time_of_day <= 18:
            patterns['movement_probability'] = 75.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Afternoon cruising")
        elif 10 <= time_of_day <= 14:
            patterns['movement_probability'] = 60.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Midday rut activity")
        elif 19 <= time_of_day <= 23 or 0 <= time_of_day <= 5:
            patterns['movement_probability'] = 90.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Peak nocturnal activity")
        
        patterns['behavioral_notes'].extend([
            "Mature bucks increase daytime movement during peak rut",
            "Focus on doe bedding areas and travel corridors",
            "Scrape lines and rub routes become active",
            "Weather fronts trigger increased activity"
        ])
        
        return patterns
    
    def _late_season_patterns(self, time_of_day: int, terrain_features: Dict, weather_data: Dict) -> Dict:
        """Late season movement patterns for mature bucks"""
        patterns = {
            'movement_probability': 0.0,
            'preferred_times': [],
            'behavioral_notes': []
        }
        
        # Late season: Conservative movement, energy conservation
        if 10 <= time_of_day <= 14:
            patterns['movement_probability'] = 50.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Midday thermal movement")
        elif 15 <= time_of_day <= 17:
            patterns['movement_probability'] = 40.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Limited afternoon feeding")
        elif 22 <= time_of_day <= 23 or 0 <= time_of_day <= 6:
            patterns['movement_probability'] = 60.0
            patterns['preferred_times'].append(f"{time_of_day:02d}:00 - Nocturnal feeding")
        else:
            patterns['movement_probability'] = 15.0
        
        patterns['behavioral_notes'].extend([
            "Energy conservation is priority - limited movement",
            "Focus on thermal cover during cold periods",
            "Movement to high-energy food sources only",
            "Extremely pressure sensitive"
        ])
        
        return patterns
    
    def _apply_pressure_adjustments(self, movement_data: Dict, terrain_features: Dict) -> Dict:
        """Apply hunting pressure adjustments to movement predictions"""
        pressure_level = self._assess_hunting_pressure(terrain_features)
        
        if pressure_level == PressureLevel.EXTREME:
            movement_data['movement_probability'] *= 0.3  # 70% reduction
            movement_data['behavioral_notes'].append("EXTREME pressure: Mostly nocturnal movement only")
        elif pressure_level == PressureLevel.HIGH:
            movement_data['movement_probability'] *= 0.5  # 50% reduction
            movement_data['behavioral_notes'].append("HIGH pressure: Reduced daytime movement")
        elif pressure_level == PressureLevel.MODERATE:
            movement_data['movement_probability'] *= 0.7  # 30% reduction
            movement_data['behavioral_notes'].append("MODERATE pressure: Cautious movement patterns")
        
        return movement_data
    
    def _assess_hunting_pressure(self, terrain_features: Dict) -> PressureLevel:
        """Assess current hunting pressure level in the area"""
        # Simplified pressure assessment based on accessibility and human activity
        road_distance = terrain_features.get('nearest_road_distance', 1000)
        trail_density = terrain_features.get('trail_density', 0.5)
        hunter_accessibility = terrain_features.get('hunter_accessibility', 0.7)
        
        pressure_score = 0
        
        if road_distance < 200:
            pressure_score += 3
        elif road_distance < 500:
            pressure_score += 2
        elif road_distance < 1000:
            pressure_score += 1
        
        if trail_density > 2.0:
            pressure_score += 3
        elif trail_density > 1.0:
            pressure_score += 2
        elif trail_density > 0.5:
            pressure_score += 1
        
        if hunter_accessibility > 0.8:
            pressure_score += 3
        elif hunter_accessibility > 0.6:
            pressure_score += 2
        elif hunter_accessibility > 0.4:
            pressure_score += 1
        
        if pressure_score >= 7:
            return PressureLevel.EXTREME
        elif pressure_score >= 5:
            return PressureLevel.HIGH
        elif pressure_score >= 3:
            return PressureLevel.MODERATE
        else:
            return PressureLevel.MINIMAL
    
    def _calculate_movement_confidence(self, movement_data: Dict, terrain_features: Dict, 
                                     weather_data: Dict) -> float:
        """Calculate confidence score for movement predictions using unified framework"""
        # Create scoring context
        context = ScoringContext(
            season=weather_data.get('season', 'early_season'),
            time_of_day=weather_data.get('hour', 12),
            weather_conditions=weather_data.get('conditions', ['clear']),
            pressure_level=weather_data.get('pressure_level', 'moderate')
        )
        
        # Use unified confidence scoring
        scoring_engine = get_scoring_engine()
        confidence_score = scoring_engine.calculate_confidence_score(
            terrain_features, context, "travel"
        )
        
        # Apply movement-specific adjustments
        base_movement_prob = scoring_engine.safe_float_conversion(
            movement_data.get('movement_probability'), 0.0
        )
        
        # Combine terrain confidence with movement probability
        final_confidence = (confidence_score * 0.7) + (base_movement_prob * 0.3)
        
        # Apply mature buck specific pressure penalties
        pressure_level = self._assess_hunting_pressure(terrain_features)
        pressure_penalty = {
            PressureLevel.MINIMAL: 0,
            PressureLevel.MODERATE: -10,
            PressureLevel.HIGH: -20,
            PressureLevel.EXTREME: -30
        }[pressure_level]
        
        return max(0.0, min(100.0, final_confidence + pressure_penalty))
    
    def _calculate_weather_factor(self, weather_data: Dict) -> float:
        """Calculate weather impact on mature buck movement"""
        factor = 0.0
        
        # Barometric pressure (falling pressure increases movement)
        pressure_trend = weather_data.get('pressure_trend', 'stable')
        if pressure_trend == 'falling':
            factor += 15.0
        elif pressure_trend == 'rising':
            factor -= 5.0
        
        # Wind speed (moderate wind preferred, not calm or strong)
        wind_speed = weather_data.get('wind_speed', 5)
        if 3 <= wind_speed <= 12:
            factor += 10.0
        elif wind_speed > 20:
            factor -= 15.0
        
        # Temperature comfort zone
        temperature = weather_data.get('temperature', 15)
        if -5 <= temperature <= 20:  # Celsius
            factor += 5.0
        elif temperature > 25 or temperature < -15:
            factor -= 10.0
        
        # Precipitation (light rain/snow can trigger movement)
        precipitation = weather_data.get('precipitation', 0)
        if 0.1 <= precipitation <= 2.0:  # Light precipitation
            factor += 8.0
        elif precipitation > 5.0:  # Heavy precipitation
            factor -= 12.0
        
        return factor

    def _identify_movement_corridors(self, terrain_features: Dict, lat: float, lon: float) -> List[Dict]:
        """
        Identify specific movement corridors for mature bucks based on terrain features
        
        Args:
            terrain_features: Terrain analysis results
            lat: Base latitude coordinate
            lon: Base longitude coordinate
            
        Returns:
            List of movement corridor predictions with coordinates
        """
        corridors = []
        
        # Get terrain metrics for corridor identification
        drainage_density = self._safe_float_conversion(terrain_features.get('drainage_density'), 0.5)
        ridge_connectivity = self._safe_float_conversion(terrain_features.get('ridge_connectivity'), 0.3)
        terrain_complexity = self._safe_float_conversion(terrain_features.get('terrain_roughness'), 0.5)
        cover_diversity = self._safe_float_conversion(terrain_features.get('cover_type_diversity'), 2.0)
        
        # Calculate coordinate offsets based on terrain features (using meters then converting to degrees)
        # Approximate: 1 degree ≈ 111,000 meters at this latitude
        meters_to_degrees = 1.0 / 111000.0
        
        # Ridge-based corridors (high ridge connectivity)
        if ridge_connectivity >= 0.6:
            for i in range(2):  # Up to 2 ridge corridors
                # Position along ridge systems
                offset_lat = (200 + i * 150) * meters_to_degrees * (1 if i % 2 == 0 else -1)
                offset_lon = (100 + i * 100) * meters_to_degrees * (1 if i % 2 == 0 else -1)
                
                corridor_lat = lat + offset_lat
                corridor_lon = lon + offset_lon
                
                confidence = 75.0 + (ridge_connectivity - 0.6) * 50.0
                
                corridors.append({
                    'lat': corridor_lat,
                    'lon': corridor_lon,
                    'type': 'ridge_corridor',
                    'confidence': min(confidence, 95.0),
                    'description': f'Ridge travel route with {ridge_connectivity:.1f} connectivity',
                    'terrain_feature': 'ridge_system',
                    'suitability_factors': {
                        'ridge_connectivity': ridge_connectivity,
                        'elevation_advantage': True,
                        'escape_options': 'multiple'
                    }
                })
        
        # Drainage-based corridors (high drainage density)
        if drainage_density >= 1.0:
            for i in range(min(3, int(drainage_density))):  # Corridors based on drainage count
                # Position along drainage systems
                angle = (i * 120) * np.pi / 180  # Spread corridors 120 degrees apart
                distance_meters = 180 + i * 80
                
                offset_lat = distance_meters * np.cos(angle) * meters_to_degrees
                offset_lon = distance_meters * np.sin(angle) * meters_to_degrees
                
                corridor_lat = lat + offset_lat
                corridor_lon = lon + offset_lon
                
                confidence = 70.0 + (drainage_density - 1.0) * 25.0
                
                corridors.append({
                    'lat': corridor_lat,
                    'lon': corridor_lon,
                    'type': 'drainage_corridor',
                    'confidence': min(confidence, 90.0),
                    'description': f'Drainage travel route, density {drainage_density:.1f}',
                    'terrain_feature': 'drainage_system',
                    'suitability_factors': {
                        'drainage_density': drainage_density,
                        'concealment': 'excellent',
                        'water_access': True
                    }
                })
        
        # Complex terrain corridors (high terrain complexity)
        if terrain_complexity >= 0.6 and cover_diversity >= 3:
            # Position in complex terrain areas
            offset_lat = 250 * meters_to_degrees * np.cos(45 * np.pi / 180)
            offset_lon = 250 * meters_to_degrees * np.sin(45 * np.pi / 180)
            
            corridor_lat = lat + offset_lat
            corridor_lon = lon + offset_lon
            
            confidence = 65.0 + terrain_complexity * 30.0
            
            corridors.append({
                'lat': corridor_lat,
                'lon': corridor_lon,
                'type': 'complex_terrain_corridor',
                'confidence': min(confidence, 88.0),
                'description': f'Complex terrain route with diverse cover',
                'terrain_feature': 'terrain_complexity',
                'suitability_factors': {
                    'terrain_complexity': terrain_complexity,
                    'cover_diversity': cover_diversity,
                    'hunter_difficulty': 'high'
                }
            })
        
        # Sort by confidence and return top corridors
        corridors.sort(key=lambda x: x['confidence'], reverse=True)
        return corridors[:4]  # Return top 4 corridors
    
    def _predict_bedding_locations(self, terrain_features: Dict, lat: float, lon: float) -> List[Dict]:
        """
        Predict specific bedding locations for mature bucks based on terrain preferences
        
        Args:
            terrain_features: Terrain analysis results
            lat: Base latitude coordinate
            lon: Base longitude coordinate
            
        Returns:
            List of bedding location predictions with coordinates
        """
        bedding_locations = []
        
        # Get terrain metrics for bedding prediction
        canopy_closure = self._safe_float_conversion(terrain_features.get('canopy_closure'), 50.0)
        elevation = self._safe_float_conversion(terrain_features.get('elevation'), 0.0)
        slope = self._safe_float_conversion(terrain_features.get('slope'), 0.0)
        aspect = self._safe_float_conversion(terrain_features.get('aspect'), 180.0)
        understory_density = self._safe_float_conversion(terrain_features.get('understory_density'), 30.0)
        escape_cover_density = self._safe_float_conversion(terrain_features.get('escape_cover_density'), 50.0)
        
        meters_to_degrees = 1.0 / 111000.0
        
        # Primary bedding area (best cover and elevation)
        if canopy_closure >= 70.0 and elevation >= 300.0:
            # Position on north-facing slope with thick cover
            primary_distance = 150  # 150 meters from center point
            if 315 <= aspect <= 360 or 0 <= aspect <= 45:  # North-facing
                # Use aspect to determine position
                angle = (aspect - 315) * np.pi / 180 if aspect >= 315 else (aspect + 45) * np.pi / 180
            else:
                angle = 45 * np.pi / 180  # Default northeast position
            
            offset_lat = primary_distance * np.cos(angle) * meters_to_degrees
            offset_lon = primary_distance * np.sin(angle) * meters_to_degrees
            
            bedding_lat = lat + offset_lat
            bedding_lon = lon + offset_lon
            
            # Calculate confidence based on multiple factors
            confidence = 60.0
            if canopy_closure >= 80.0:
                confidence += 20.0
            if slope >= 5 and slope <= 25:
                confidence += 15.0
            if understory_density >= 70.0:
                confidence += 10.0
            
            bedding_locations.append({
                'lat': bedding_lat,
                'lon': bedding_lon,
                'type': 'primary_bedding',
                'confidence': min(confidence, 95.0),
                'description': f'Primary bedding area with {canopy_closure:.0f}% canopy cover',
                'terrain_characteristics': {
                    'canopy_closure': canopy_closure,
                    'elevation': elevation,
                    'slope': slope,
                    'aspect': aspect,
                    'understory_density': understory_density
                },
                'suitability_factors': {
                    'thermal_cover': canopy_closure >= 80.0,
                    'visibility_advantage': elevation >= 300.0,
                    'concealment': understory_density >= 70.0,
                    'comfort_slope': 5 <= slope <= 25
                }
            })
        
        # Secondary bedding areas (escape cover)
        if escape_cover_density >= 60.0:
            for i in range(2):  # Up to 2 secondary bedding areas
                # Position escape bedding areas
                angle = (120 + i * 120) * np.pi / 180  # 120 degrees apart
                distance = 200 + i * 50  # Varying distances
                
                offset_lat = distance * np.cos(angle) * meters_to_degrees
                offset_lon = distance * np.sin(angle) * meters_to_degrees
                
                bedding_lat = lat + offset_lat
                bedding_lon = lon + offset_lon
                
                confidence = 50.0 + escape_cover_density * 0.5
                
                bedding_locations.append({
                    'lat': bedding_lat,
                    'lon': bedding_lon,
                    'type': 'escape_bedding',
                    'confidence': min(confidence, 85.0),
                    'description': f'Escape bedding area with {escape_cover_density:.0f}% cover density',
                    'terrain_characteristics': {
                        'escape_cover_density': escape_cover_density,
                        'accessibility': 'limited'
                    },
                    'suitability_factors': {
                        'quick_escape': True,
                        'hunter_difficulty': 'high',
                        'pressure_resistance': escape_cover_density >= 70.0
                    }
                })
        
        # Thermal bedding (based on aspect and elevation)
        if elevation >= 280.0:
            # South-facing slopes for winter thermal bedding
            thermal_angle = 180 * np.pi / 180  # South-facing
            thermal_distance = 180
            
            offset_lat = thermal_distance * np.cos(thermal_angle) * meters_to_degrees
            offset_lon = thermal_distance * np.sin(thermal_angle) * meters_to_degrees
            
            bedding_lat = lat + offset_lat
            bedding_lon = lon + offset_lon
            
            confidence = 45.0 + (elevation - 280.0) / 10.0
            
            bedding_locations.append({
                'lat': bedding_lat,
                'lon': bedding_lon,
                'type': 'thermal_bedding',
                'confidence': min(confidence, 80.0),
                'description': f'Thermal bedding area at {elevation:.0f}m elevation',
                'terrain_characteristics': {
                    'elevation': elevation,
                    'aspect': 'south_facing',
                    'thermal_advantage': True
                },
                'suitability_factors': {
                    'winter_comfort': True,
                    'solar_exposure': True,
                    'wind_protection': slope >= 10
                }
            })
        
        # Sort by confidence and return top locations
        bedding_locations.sort(key=lambda x: x['confidence'], reverse=True)
        return bedding_locations[:3]  # Return top 3 bedding areas
    
    def _predict_feeding_zones(self, terrain_features: Dict, lat: float, lon: float, season: str) -> List[Dict]:
        """
        Predict feeding zones for mature bucks based on terrain and seasonal patterns
        
        Args:
            terrain_features: Terrain analysis results
            lat: Base latitude coordinate
            lon: Base longitude coordinate
            season: Current hunting season
            
        Returns:
            List of feeding zone predictions with coordinates
        """
        feeding_zones = []
        
        # Get terrain metrics for feeding prediction
        ag_proximity = self._safe_float_conversion(terrain_features.get('agricultural_proximity'), 1000.0)
        cover_diversity = self._safe_float_conversion(terrain_features.get('cover_type_diversity'), 2.0)
        water_proximity = self._safe_float_conversion(terrain_features.get('water_proximity'), 500.0)
        edge_density = self._safe_float_conversion(terrain_features.get('edge_density'), 0.3)
        canopy_closure = self._safe_float_conversion(terrain_features.get('canopy_closure'), 50.0)
        
        meters_to_degrees = 1.0 / 111000.0
        
        # Agricultural edge feeding (if close to ag land)
        if ag_proximity <= 400.0:
            # Position at ag edge with cover access
            ag_angle = 270 * np.pi / 180  # West side (typical ag placement)
            ag_distance = min(ag_proximity + 50, 300)  # Just outside ag boundary
            
            offset_lat = ag_distance * np.cos(ag_angle) * meters_to_degrees
            offset_lon = ag_distance * np.sin(ag_angle) * meters_to_degrees
            
            feeding_lat = lat + offset_lat
            feeding_lon = lon + offset_lon
            
            # Higher confidence during rut and late season
            base_confidence = 70.0 if season in ['rut', 'late_season'] else 55.0
            confidence = base_confidence + (400 - ag_proximity) / 10.0
            
            feeding_zones.append({
                'lat': feeding_lat,
                'lon': feeding_lon,
                'type': 'agricultural_edge',
                'confidence': min(confidence, 90.0),
                'description': f'Agricultural edge feeding, {ag_proximity:.0f}m from crops',
                'seasonal_preference': season,
                'terrain_characteristics': {
                    'agricultural_proximity': ag_proximity,
                    'edge_access': True,
                    'escape_cover_nearby': canopy_closure >= 60.0
                },
                'feeding_characteristics': {
                    'food_quality': 'high_energy',
                    'seasonal_availability': season != 'early_season',
                    'pressure_risk': 'moderate',
                    'best_times': ['dawn', 'dusk', 'night']
                }
            })
        
        # Forest opening feeding (based on cover diversity and edges)
        if cover_diversity >= 3 and edge_density >= 0.5:
            for i in range(2):  # Up to 2 forest openings
                # Position in diverse cover areas
                angle = (60 + i * 180) * np.pi / 180  # North and south openings
                distance = 220 + i * 80
                
                offset_lat = distance * np.cos(angle) * meters_to_degrees
                offset_lon = distance * np.sin(angle) * meters_to_degrees
                
                feeding_lat = lat + offset_lat
                feeding_lon = lon + offset_lon
                
                confidence = 50.0 + cover_diversity * 10.0 + edge_density * 20.0
                
                feeding_zones.append({
                    'lat': feeding_lat,
                    'lon': feeding_lon,
                    'type': 'forest_opening',
                    'confidence': min(confidence, 85.0),
                    'description': f'Forest opening with {cover_diversity:.0f} cover types',
                    'seasonal_preference': season,
                    'terrain_characteristics': {
                        'cover_diversity': cover_diversity,
                        'edge_density': edge_density,
                        'opening_size': 'moderate'
                    },
                    'feeding_characteristics': {
                        'food_quality': 'browse_and_forbs',
                        'concealment': 'good',
                        'pressure_risk': 'low',
                        'best_times': ['early_morning', 'late_evening']
                    }
                })
        
        # Water-associated feeding (near streams/ponds)
        if water_proximity <= 300.0:
            # Position near water sources
            water_angle = 90 * np.pi / 180  # East side of water
            water_distance = water_proximity + 30  # Slightly away from water edge
            
            offset_lat = water_distance * np.cos(water_angle) * meters_to_degrees
            offset_lon = water_distance * np.sin(water_angle) * meters_to_degrees
            
            feeding_lat = lat + offset_lat
            feeding_lon = lon + offset_lon
            
            confidence = 45.0 + (300 - water_proximity) / 8.0
            
            feeding_zones.append({
                'lat': feeding_lat,
                'lon': feeding_lon,
                'type': 'riparian_feeding',
                'confidence': min(confidence, 75.0),
                'description': f'Riparian feeding area, {water_proximity:.0f}m from water',
                'seasonal_preference': season,
                'terrain_characteristics': {
                    'water_proximity': water_proximity,
                    'moisture_loving_plants': True,
                    'travel_corridor': True
                },
                'feeding_characteristics': {
                    'food_quality': 'succulent_browse',
                    'water_access': True,
                    'pressure_risk': 'variable',
                    'best_times': ['night', 'very_early_morning']
                }
            })
        
        # Late season concentration feeding (high energy sources)
        if season == 'late_season':
            # Oak stands and mast producing areas
            mast_angle = 315 * np.pi / 180  # Northwest (typical hardwood slopes)
            mast_distance = 280
            
            offset_lat = mast_distance * np.cos(mast_angle) * meters_to_degrees
            offset_lon = mast_distance * np.sin(mast_angle) * meters_to_degrees
            
            feeding_lat = lat + offset_lat
            feeding_lon = lon + offset_lon
            
            confidence = 60.0 + (canopy_closure - 40.0) / 2.0  # Better in mature forest
            
            feeding_zones.append({
                'lat': feeding_lat,
                'lon': feeding_lon,
                'type': 'mast_feeding',
                'confidence': min(confidence, 80.0),
                'description': f'Late season mast feeding area',
                'seasonal_preference': 'late_season',
                'terrain_characteristics': {
                    'canopy_closure': canopy_closure,
                    'hardwood_dominance': True,
                    'mast_production': 'likely'
                },
                'feeding_characteristics': {
                    'food_quality': 'high_fat_mast',
                    'energy_content': 'maximum',
                    'seasonal_critical': True,
                    'best_times': ['midday_warmth', 'afternoon']
                }
            })
        
        # Sort by confidence and return top zones
        feeding_zones.sort(key=lambda x: x['confidence'], reverse=True)
        return feeding_zones[:4]  # Return top 4 feeding zones

def _safe_float_conversion_standalone(value, default: float = 0.0) -> float:
    """Safely convert numpy arrays or other values to float - standalone version"""
    if value is None:
        return default
    
    if hasattr(value, 'size'):
        if value.size > 1:
            return float(np.mean(value))
        elif value.size == 1:
            return float(value.item())
        else:
            return default
    else:
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

def _find_optimal_stand_position_for_strategy(strategy: Dict, terrain_analysis: Dict, 
                               mature_buck_scores: Dict, lat: float, lon: float, 
                               strategy_index: int) -> Dict:
    """
    Find optimal stand position based on strategy type and terrain features
    
    Args:
        strategy: Stand strategy configuration
        terrain_analysis: Complete terrain analysis
        mature_buck_scores: Mature buck terrain scores
        lat: Base latitude
        lon: Base longitude
        strategy_index: Index for positioning variation
        
    Returns:
        Dict with lat, lon, and positioning justification
    """
    meters_to_degrees = 1.0 / 111000.0
    strategy_type = strategy['type']
    
    # Get terrain metrics for positioning
    ridge_connectivity = _safe_float_conversion_standalone(terrain_analysis.get('ridge_connectivity'), 0.3)
    drainage_density = _safe_float_conversion_standalone(terrain_analysis.get('drainage_density'), 0.5)
    escape_cover_density = _safe_float_conversion_standalone(terrain_analysis.get('escape_cover_density'), 50.0)
    ag_proximity = _safe_float_conversion_standalone(terrain_analysis.get('agricultural_proximity'), 1000.0)
    elevation = _safe_float_conversion_standalone(terrain_analysis.get('elevation'), 0.0)
    canopy_closure = _safe_float_conversion_standalone(terrain_analysis.get('canopy_closure'), 50.0)
    
    if strategy_type == 'Escape Route Ambush':
        # Position between bedding and escape routes
        if drainage_density >= 1.0:
            # Use drainage systems for escape route positioning
            angle = (45 + strategy_index * 90) * np.pi / 180
            distance = 120 + drainage_density * 30  # Distance based on drainage density
            justification = f"Positioned along drainage corridor with {drainage_density:.1f} density"
            precision_factors = {
                'drainage_density': drainage_density,
                'escape_routes': 'multiple',
                'positioning_method': 'drainage_based'
            }
        else:
            # Fallback to ridge-based positioning
            angle = (30 + strategy_index * 120) * np.pi / 180
            distance = 100 + ridge_connectivity * 50
            justification = f"Ridge-based escape route position"
            precision_factors = {
                'ridge_connectivity': ridge_connectivity,
                'positioning_method': 'ridge_based'
            }
            
    elif strategy_type == 'Secluded Feeding Edge':
        # Position near agricultural or forest edges
        if ag_proximity <= 300.0:
            # Position at agricultural edge
            angle = 225 * np.pi / 180  # Southwest of ag area
            distance = ag_proximity + 60  # Just outside ag boundary
            justification = f"Agricultural edge position, {ag_proximity:.0f}m from crops"
            precision_factors = {
                'agricultural_proximity': ag_proximity,
                'edge_type': 'agricultural',
                'positioning_method': 'ag_edge_based'
            }
        else:
            # Position at forest opening
            angle = (180 + strategy_index * 45) * np.pi / 180
            distance = 150 + canopy_closure * 2  # Distance based on cover density
            justification = f"Forest opening edge with {canopy_closure:.0f}% canopy cover"
            precision_factors = {
                'canopy_closure': canopy_closure,
                'edge_type': 'forest_opening',
                'positioning_method': 'cover_based'
            }
            
    elif strategy_type == 'Pressure Sanctuary':
        # Position in thickest, most remote cover
        if escape_cover_density >= 70.0:
            # Use thick cover areas
            angle = (90 + strategy_index * 180) * np.pi / 180
            distance = 200 + escape_cover_density * 1.5  # Deep in thick cover
            justification = f"Deep sanctuary in {escape_cover_density:.0f}% cover density"
            precision_factors = {
                'escape_cover_density': escape_cover_density,
                'sanctuary_quality': 'premium',
                'positioning_method': 'cover_density_based'
            }
        else:
            # Use elevation for sanctuary
            angle = (135 + strategy_index * 90) * np.pi / 180
            distance = 180 + elevation * 0.3  # Higher elevation for sanctuary
            justification = f"Elevation sanctuary at {elevation:.0f}m"
            precision_factors = {
                'elevation': elevation,
                'sanctuary_quality': 'moderate',
                'positioning_method': 'elevation_based'
            }
            
    elif strategy_type == 'Ridge Saddle Intercept':
        # Position at natural terrain funnels
        if ridge_connectivity >= 0.6:
            # Use actual ridge systems
            angle = (0 + strategy_index * 180) * np.pi / 180  # North/South ridge positions
            distance = 80 + ridge_connectivity * 120  # Close to ridge features
            justification = f"Ridge saddle with {ridge_connectivity:.1f} connectivity"
            precision_factors = {
                'ridge_connectivity': ridge_connectivity,
                'funnel_quality': 'natural',
                'positioning_method': 'ridge_saddle_based'
            }
        else:
            # Use drainage convergence as funnel
            angle = (315 + strategy_index * 45) * np.pi / 180
            distance = 110 + drainage_density * 40
            justification = f"Drainage convergence funnel"
            precision_factors = {
                'drainage_density': drainage_density,
                'funnel_quality': 'drainage_based',
                'positioning_method': 'drainage_convergence'
            }
    else:
        # Default positioning
        angle = (strategy_index * 90) * np.pi / 180
        distance = 150
        justification = "General terrain positioning"
        precision_factors = {'positioning_method': 'default'}
    
    # Calculate coordinates
    offset_lat = distance * np.cos(angle) * meters_to_degrees
    offset_lon = distance * np.sin(angle) * meters_to_degrees
    
    stand_lat = lat + offset_lat
    stand_lon = lon + offset_lon
    
    return {
        'lat': stand_lat,
        'lon': stand_lon,
        'justification': justification,
        'precision_factors': precision_factors,
        'distance_from_center': distance,
        'positioning_angle': angle * 180 / np.pi
    }

def _calculate_terrain_bonus_for_strategy(strategy: Dict, terrain_analysis: Dict) -> float:
    """
    Calculate terrain-specific confidence bonus for stand strategies
    
    Args:
        strategy: Stand strategy configuration
        terrain_analysis: Complete terrain analysis
        
    Returns:
        Confidence bonus based on terrain suitability
    """
    bonus = 0.0
    strategy_type = strategy['type']
    
    # Get relevant terrain metrics
    ridge_connectivity = _safe_float_conversion_standalone(terrain_analysis.get('ridge_connectivity'), 0.3)
    drainage_density = _safe_float_conversion_standalone(terrain_analysis.get('drainage_density'), 0.5)
    escape_cover_density = _safe_float_conversion_standalone(terrain_analysis.get('escape_cover_density'), 50.0)
    ag_proximity = _safe_float_conversion_standalone(terrain_analysis.get('agricultural_proximity'), 1000.0)
    hunter_accessibility = _safe_float_conversion_standalone(terrain_analysis.get('hunter_accessibility'), 0.7)
    cover_diversity = _safe_float_conversion_standalone(terrain_analysis.get('cover_type_diversity'), 2.0)
    
    if strategy_type == 'Escape Route Ambush':
        # Bonus for good escape routes
        if drainage_density >= 1.5:
            bonus += 10.0
        if ridge_connectivity >= 0.7:
            bonus += 8.0
        if escape_cover_density >= 70.0:
            bonus += 6.0
            
    elif strategy_type == 'Secluded Feeding Edge':
        # Bonus for good feeding opportunities
        if ag_proximity <= 200.0:
            bonus += 12.0
        elif ag_proximity <= 400.0:
            bonus += 6.0
        if cover_diversity >= 4:
            bonus += 8.0
            
    elif strategy_type == 'Pressure Sanctuary':
        # Bonus for low pressure areas
        if hunter_accessibility <= 0.3:
            bonus += 15.0
        elif hunter_accessibility <= 0.5:
            bonus += 10.0
        if escape_cover_density >= 80.0:
            bonus += 12.0
            
    elif strategy_type == 'Ridge Saddle Intercept':
        # Bonus for good terrain funnels
        if ridge_connectivity >= 0.8:
            bonus += 15.0
        elif ridge_connectivity >= 0.6:
            bonus += 10.0
        if drainage_density >= 1.0:
            bonus += 5.0
    
    return bonus

def get_mature_buck_predictor() -> MatureBuckBehaviorModel:
    """
    Factory function to get a configured mature buck predictor instance
    
    Returns:
        MatureBuckBehaviorModel: Configured predictor instance
    """
    return MatureBuckBehaviorModel()

# Mature buck specific stand recommendations
def generate_mature_buck_stand_recommendations(terrain_analysis: Dict, mature_buck_scores: Dict, 
                                             lat: float, lon: float) -> List[Dict]:
    """
    Generate stand recommendations specifically optimized for mature bucks
    
    Args:
        terrain_analysis: Terrain analysis results
        mature_buck_scores: Mature buck terrain scores
        lat: Latitude coordinate
        lon: Longitude coordinate
        
    Returns:
        List of mature buck optimized stand recommendations
    """
    recommendations = []
    
    # Mature buck stand strategies
    stand_strategies = [
        {
            'type': 'Escape Route Ambush',
            'description': 'Position between bedding and primary escape corridor',
            'confidence_base': 85.0,
            'setup_requirements': ['Multiple escape routes', 'Thick cover nearby', 'Wind advantage'],
            'best_times': 'Dawn and dusk during high pressure periods'
        },
        {
            'type': 'Secluded Feeding Edge',
            'description': 'Hidden position overlooking isolated food source',
            'confidence_base': 80.0,
            'setup_requirements': ['Remote food source', 'Concealed approach', 'Escape cover'],
            'best_times': 'Night vision or thermal during rut'
        },
        {
            'type': 'Pressure Sanctuary',
            'description': 'Deep cover position in low-pressure sanctuary',
            'confidence_base': 90.0,
            'setup_requirements': ['Difficult hunter access', 'Multiple cover types', 'Water nearby'],
            'best_times': 'All day during peak rut'
        },
        {
            'type': 'Ridge Saddle Intercept',
            'description': 'Strategic position in natural travel funnel',
            'confidence_base': 75.0,
            'setup_requirements': ['Natural funnel', 'Elevation advantage', 'Cross wind setup'],
            'best_times': 'Morning and evening transitions'
        }
    ]
    
    for i, strategy in enumerate(stand_strategies):
        # Calculate position based on terrain features and strategy type
        stand_position = _find_optimal_stand_position_for_strategy(
            strategy, terrain_analysis, mature_buck_scores, lat, lon, i
        )
        
        # Adjust confidence based on terrain suitability
        confidence = strategy['confidence_base']
        confidence += mature_buck_scores.get('overall_suitability', 0) * 0.15
        
        # Add terrain-specific bonuses
        terrain_bonus = _calculate_terrain_bonus_for_strategy(strategy, terrain_analysis)
        confidence += terrain_bonus
        confidence = min(confidence, 95.0)
        
        recommendation = {
            'type': strategy['type'],
            'description': strategy['description'],
            'coordinates': stand_position,
            'confidence': confidence,
            'setup_requirements': strategy['setup_requirements'],
            'best_times': strategy['best_times'],
            'mature_buck_optimized': True,
            'pressure_resistance': mature_buck_scores.get('pressure_resistance', 50.0),
            'escape_route_quality': mature_buck_scores.get('escape_route_quality', 50.0),
            'terrain_justification': stand_position.get('justification', 'General terrain positioning'),
            'precision_factors': stand_position.get('precision_factors', {})
        }
        
        recommendations.append(recommendation)
    
    # Sort by confidence
    recommendations.sort(key=lambda x: x['confidence'], reverse=True)
    
    return recommendations[:4]  # Return top 4 recommendations