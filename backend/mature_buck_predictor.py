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
try:
    from .scoring_engine import (
        get_scoring_engine, 
        ScoringContext, 
        TerrainScoreComponents,
        score_terrain_suitability,
        score_with_context
    )
except ImportError:
    from scoring_engine import (
        get_scoring_engine, 
        ScoringContext, 
        TerrainScoreComponents,
        score_terrain_suitability,
        score_with_context
    )

try:
    from .distance_scorer import (
        get_distance_scorer,
        score_road_proximity,
        score_agricultural_proximity,
        score_escape_routes
    )
except ImportError:
    from distance_scorer import (
        get_distance_scorer,
        score_road_proximity,
        score_agricultural_proximity,
        score_escape_routes
    )
# Import advanced terrain analysis
try:
    from .terrain_analyzer import (
        get_terrain_analyzer,
        enhance_mature_buck_prediction_with_terrain,
        TerrainFeatureType
    )
except ImportError:
    from terrain_analyzer import (
        get_terrain_analyzer,
        enhance_mature_buck_prediction_with_terrain,
        TerrainFeatureType
    )

# Import wind analysis system
try:
    from .wind_analysis import (
        get_wind_analyzer,
        WindAnalyzer,
        WindData,
        WindOptimizedPosition,
        ScentDispersion
    )
except ImportError:
    from wind_analysis import (
        get_wind_analyzer,
        WindAnalyzer,
        WindData,
        WindOptimizedPosition,
        ScentDispersion
    )

# Import configuration management
try:
    from .config_manager import get_config
except ImportError:
    from config_manager import get_config

logger = logging.getLogger(__name__)

# Proximity scoring configuration
PROXIMITY_THRESHOLDS = {
    'bedding': {
        'min_optimal': 75,      # yards - too close spooks deer
        'max_optimal': 200,     # yards - effective shooting range
        'max_useful': 400       # yards - beyond this, proximity doesn't help
    },
    'feeding': {
        'min_optimal': 25,      # yards - can be closer to feeding areas
        'max_optimal': 150,     # yards - effective range for feeding interception
        'max_useful': 300       # yards - maximum useful proximity
    }
}

PROXIMITY_CONFIG = {
    'bedding_weight': 0.6,      # Bedding proximity importance (60%)
    'feeding_weight': 0.4,      # Feeding proximity importance (40%)
    'confidence_impact': 0.15,  # Max confidence adjustment (15%)
    'enable_multi_zone': True,  # Consider multiple zones
    'distance_penalty_factor': 2.0  # Penalty multiplier for poor proximity
}

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
        self.wind_analyzer = get_wind_analyzer()
        logger.info("🌬️ Wind analysis enabled for mature buck predictions")
    
    def _safe_float_conversion(self, value, default: float = 0.0) -> float:
        """Safely convert numpy arrays or other values to float"""
        # Use unified scoring engine's conversion for consistency
        scoring_engine = get_scoring_engine()
        return scoring_engine.safe_float_conversion(value, default)
        
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
        Analyze terrain suitability for mature bucks using enhanced algorithms and unified scoring
        
        Args:
            terrain_features: Terrain analysis results
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Dict containing mature buck terrain scores and factors
        """
        logger.info(f"Analyzing mature buck terrain preferences for {lat}, {lon}")
        
        # Get enhanced terrain features if available
        enhanced_terrain_features = self._get_enhanced_terrain_features(terrain_features, lat, lon)
        
        # Try enhanced scoring algorithm
        enhanced_scores = self._try_enhanced_scoring(enhanced_terrain_features, lat, lon)
        if enhanced_scores:
            return enhanced_scores
            
        # Use unified scoring framework for standard analysis
        return self._perform_standard_terrain_analysis(enhanced_terrain_features, lat, lon)
    
    def _get_enhanced_terrain_features(self, terrain_features: Dict, lat: float, lon: float) -> Dict:
        """Get enhanced terrain features using mapper if available"""
        try:
            from terrain_feature_mapper import get_terrain_mapper
            terrain_mapper = get_terrain_mapper()
            enhanced_features = terrain_mapper.map_terrain_features(terrain_features, lat, lon)
            logger.info("✅ Using enhanced terrain feature mapping")
            return enhanced_features
        except Exception as e:
            logger.warning(f"Terrain feature mapping unavailable: {e}")
            return terrain_features
    
    def _try_enhanced_scoring(self, terrain_features: Dict, lat: float, lon: float) -> Optional[Dict]:
        """Attempt to use enhanced scoring algorithm"""
        try:
            from enhanced_accuracy import enhanced_terrain_analysis
            scores = enhanced_terrain_analysis(terrain_features, lat, lon)
            logger.info(f"Using enhanced terrain analysis - Overall: {scores['overall_suitability']:.2f}%")
            return scores
        except (ImportError, Exception) as e:
            logger.warning(f"Enhanced scoring unavailable: {e}")
            return None
    
    def _perform_standard_terrain_analysis(self, terrain_features: Dict, 
                                         lat: float, lon: float) -> Dict[str, float]:
        """Perform standard terrain analysis using unified scoring framework"""
        scoring_engine = get_scoring_engine()
        
        # Create scoring context for terrain analysis
        context = ScoringContext(
            season="general",  # Non-seasonal analysis
            time_of_day=12,    # Neutral time
            weather_conditions=["clear"],  # Neutral weather
            pressure_level="moderate",
            behavior_type="mature_buck"  # Specific behavior type
        )
        
        # Calculate terrain scores using unified framework
        scores = {
            'bedding_suitability': self._score_bedding_areas(terrain_features),
            'escape_route_quality': self._score_escape_routes(terrain_features),
            'isolation_score': self._score_isolation(terrain_features, lat, lon),
            'pressure_resistance': self._score_pressure_resistance(terrain_features)
        }
        
        # Apply mature buck specific adjustments
        for score_type, base_score in scores.items():
            adjusted_score = scoring_engine.apply_seasonal_weighting(
                base_score, 
                "general",     # Non-seasonal
                "mature_buck"  # Behavior type
            )
            scores[score_type] = adjusted_score
        
        # Calculate overall suitability
        scores['overall_suitability'] = self._calculate_overall_suitability(scores)
        
        logger.info(f"Mature buck terrain analysis complete - Overall: {scores['overall_suitability']:.2f}%")
        logger.info(
            f"🎯 Scores: Bedding={scores['bedding_suitability']:.1f}%, "
            f"Escape={scores['escape_route_quality']:.1f}%, "
            f"Isolation={scores['isolation_score']:.1f}%, "
            f"Pressure={scores['pressure_resistance']:.1f}%"
        )
        
        return scores
    
    def _score_bedding_areas(self, terrain_features: Dict) -> float:
        """Score bedding area suitability for mature bucks using unified framework"""
        # Use unified scoring engine for consistent terrain evaluation
        scoring_engine = get_scoring_engine()
        
        # Create scoring context for bedding evaluation
        context = ScoringContext(
            season="general",  # Non-seasonal analysis
            time_of_day=12,    # Neutral time
            weather_conditions=["clear"],  # Neutral weather
            pressure_level="moderate"
        )
        
        # Calculate base confidence score for bedding
        base_score = scoring_engine.calculate_confidence_score(
            terrain_features, 
            context,
            "bedding"
        )
        
        # Add mature buck specific bonuses
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
        distance_scorer = get_distance_scorer()
        scoring_engine = get_scoring_engine()
        
        # Create scoring context for escape routes
        context = ScoringContext(
            season="general",
            time_of_day=12,
            weather_conditions=["clear"],
            pressure_level="moderate",
            behavior_type="mature_buck"  # Specific behavior type
        )
        
        # Calculate base terrain and escape scores
        base_terrain_score = scoring_engine.calculate_confidence_score(
            terrain_features,
            context,
            "travel"
        )
        
        # Calculate escape route score based on distance
        escape_distance = scoring_engine.safe_float_conversion(
            terrain_features.get('escape_route_distance'), 200.0
        )
        escape_score = distance_scorer.calculate_escape_route_score(escape_distance)
        
        # Combine terrain and escape accessibility
        base_score = (base_terrain_score + escape_score) / 2
        
        # Mature buck specific bonuses for multiple escape corridors
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
        
        # Initialize prediction data
        movement_data = self._initialize_movement_data()
        
        # Get movement patterns (enhanced or standard)
        movement_data.update(
            self._get_movement_patterns(season, time_of_day, terrain_features, weather_data)
        )
        
        # Add spatial predictions
        self._add_spatial_predictions(movement_data, terrain_features, lat, lon, season)
        
        # Process environmental adjustments
        self._process_environmental_adjustments(movement_data, terrain_features, weather_data)
        
        return movement_data
        
    def _initialize_movement_data(self) -> Dict[str, any]:
        """Initialize the base movement prediction data structure"""
        return {
            'movement_probability': 0.0,
            'preferred_times': [],
            'movement_corridors': [],
            'bedding_predictions': [],
            'feeding_predictions': [],
            'confidence_score': 0.0,
            'behavioral_notes': []
        }
        
    def _get_movement_patterns(self, season: str, time_of_day: int,
                             terrain_features: Dict, weather_data: Dict) -> Dict[str, any]:
        """Get movement patterns using enhanced prediction if available, otherwise standard"""
        try:
            from enhanced_accuracy import enhanced_movement_prediction
            prediction = enhanced_movement_prediction(season, time_of_day, terrain_features, weather_data)
            logger.info(f"Using enhanced movement prediction - Probability: {prediction['movement_probability']:.1f}%")
            return prediction
        except (ImportError, Exception) as e:
            logger.warning(f"Enhanced movement prediction unavailable/failed: {e}, using standard analysis")
            return self._get_standard_movement_patterns(season, time_of_day, terrain_features, weather_data)
            
    def _get_standard_movement_patterns(self, season: str, time_of_day: int,
                                      terrain_features: Dict, weather_data: Dict) -> Dict[str, any]:
        """Get movement patterns using standard seasonal analysis"""
        if season == "early_season":
            return self._early_season_patterns(time_of_day, terrain_features, weather_data)
        elif season == "rut":
            return self._rut_season_patterns(time_of_day, terrain_features, weather_data)
        else:  # late_season
            return self._late_season_patterns(time_of_day, terrain_features, weather_data)
            
    def _add_spatial_predictions(self, movement_data: Dict, terrain_features: Dict,
                               lat: float, lon: float, season: str):
        """Add spatial predictions to movement data"""
        movement_data['movement_corridors'] = self._identify_movement_corridors(
            terrain_features, lat, lon
        )
        movement_data['bedding_predictions'] = self._predict_bedding_locations(
            terrain_features, lat, lon
        )
        movement_data['feeding_predictions'] = self._predict_feeding_zones(
            terrain_features, lat, lon, season
        )
        
    def _process_environmental_adjustments(self, movement_data: Dict,
                                         terrain_features: Dict, weather_data: Dict):
        """Process environmental adjustments to movement data"""
        # Apply pressure adjustments
        movement_data.update(self._apply_pressure_adjustments(movement_data, terrain_features))
        
        # Calculate final confidence
        movement_data['confidence_score'] = self._calculate_movement_confidence(
            movement_data, terrain_features, weather_data
        )
    
    def predict_with_advanced_terrain_analysis(self, season: str, time_of_day: int, 
                                             terrain_features: Dict, weather_data: Dict, 
                                             lat: float, lon: float) -> Dict[str, any]:
        """
        Enhanced mature buck prediction using advanced terrain feature detection
        
        This method combines traditional terrain analysis with sophisticated 5x5 elevation
        grid analysis to detect travel corridors, funnels, and terrain features that
        mature bucks specifically prefer.
        
        Args:
            season: Hunting season (early_season, rut, late_season)
            time_of_day: Hour of day (0-23)
            terrain_features: Basic terrain analysis results
            weather_data: Current weather conditions
            lat: Latitude coordinate
            lon: Longitude coordinate
            
        Returns:
            Enhanced movement prediction with terrain feature analysis
        """
        logger.info(f"🎯 Starting enhanced mature buck prediction with advanced terrain analysis")
        
        # Start with basic movement prediction
        basic_prediction = self.predict_mature_buck_movement(
            season, time_of_day, terrain_features, weather_data, lat, lon
        )
        
        # Enhance with advanced terrain analysis
        enhanced_prediction = enhance_mature_buck_prediction_with_terrain(
            basic_prediction, lat, lon
        )
        
        # Extract terrain analysis for additional insights
        terrain_analysis = enhanced_prediction['advanced_terrain_analysis']
        
        # Enhance movement corridors with detected terrain features
        enhanced_corridors = self._enhance_corridors_with_terrain_features(
            enhanced_prediction['movement_corridors'], 
            terrain_analysis['travel_corridors'],
            terrain_analysis['detected_features']
        )
        enhanced_prediction['movement_corridors'] = enhanced_corridors
        
        # Enhance bedding predictions with terrain benches and slope breaks
        enhanced_bedding = self._enhance_bedding_with_terrain_features(
            enhanced_prediction['bedding_predictions'],
            terrain_analysis['detected_features']
        )
        enhanced_prediction['bedding_predictions'] = enhanced_bedding
        
        # Add specific terrain-based stand recommendations
        enhanced_prediction['terrain_stand_recommendations'] = self._generate_terrain_based_stands(
            terrain_analysis, lat, lon
        )
        
        # Add natural funnel analysis
        enhanced_prediction['natural_funnels'] = terrain_analysis['natural_funnels']
        
        # Enhanced behavioral insights based on terrain
        enhanced_prediction['terrain_behavioral_insights'] = self._generate_terrain_behavioral_insights(
            terrain_analysis, season, weather_data
        )
        
        logger.info(f"✅ Enhanced prediction complete with {len(terrain_analysis['detected_features'])} terrain features")
        
        return enhanced_prediction
    
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
        """
        Apply hunting pressure adjustments to movement predictions using configured factors
        
        Args:
            movement_data: Current movement prediction data
            terrain_features: Terrain analysis results
            
        Returns:
            Updated movement data with pressure adjustments
        
        Raises:
            ValueError: If movement_data lacks required fields
        """
        if 'movement_probability' not in movement_data:
            raise ValueError("Movement data missing required 'movement_probability' field")
            
        try:
            pressure_level = self._assess_hunting_pressure(terrain_features)
            original_probability = movement_data['movement_probability']
            
            # Get adjustment factors from configuration
            config = get_config()
            pressure_factors = config.get('mature_buck_preferences', {}).get('pressure_factors', {
                'extreme': 0.3,  # 70% reduction
                'high': 0.5,     # 50% reduction
                'moderate': 0.7,  # 30% reduction
                'minimal': 1.0    # No reduction
            })
            
            # Apply configured pressure adjustment
            adjustment = pressure_factors.get(pressure_level.value, 1.0)
            movement_data['movement_probability'] *= adjustment
            
            # Add behavioral notes
            if pressure_level == PressureLevel.EXTREME:
                movement_data['behavioral_notes'].extend([
                    "⚠️ EXTREME pressure: Mostly nocturnal movement only",
                    "🌙 Primary movement period: 10 PM - 4 AM",
                    "🏃‍♂️ Uses maximum cover for all movement"
                ])
            elif pressure_level == PressureLevel.HIGH:
                movement_data['behavioral_notes'].extend([
                    "⚠️ HIGH pressure: Reduced daytime movement",
                    "🌅 Brief movement possible at dawn/dusk",
                    "🌲 Prefers thick cover travel routes"
                ])
            elif pressure_level == PressureLevel.MODERATE:
                movement_data['behavioral_notes'].extend([
                    "⚠️ MODERATE pressure: Cautious movement patterns",
                    "⏰ Movement possible throughout day",
                    "👣 Uses established escape routes"
                ])
            else:
                movement_data['behavioral_notes'].extend([
                    "✅ MINIMAL pressure: Normal movement patterns",
                    "🎯 Most predictable movement behavior",
                    "🌞 Regular daytime activity possible"
                ])
            
            # Log the adjustment
            logger.info(
                f"Applied pressure adjustment: {pressure_level.value} "
                f"({original_probability:.1f}% → {movement_data['movement_probability']:.1f}%)"
            )
            
        except Exception as e:
            logger.error(f"Error applying pressure adjustments: {e}")
            # Preserve original movement data on error
            return movement_data
            
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
        """
        Calculate weather impact on mature buck movement using the scoring engine
        
        Args:
            weather_data: Weather condition data
            
        Returns:
            Weather impact factor (-100 to 100)
        """
        scoring_engine = get_scoring_engine()
        
        # Create weather conditions list for scoring engine
        conditions = []
        
        # Check precipitation
        precipitation = self._safe_float_conversion(weather_data.get('precipitation'), 0)
        if precipitation > 5.0:
            conditions.append('heavy_rain')
        elif precipitation >= 0.1:
            conditions.append('light_rain')
            
        # Check temperature and wind
        temperature = self._safe_float_conversion(weather_data.get('temperature'), 15)
        wind_speed = self._safe_float_conversion(weather_data.get('wind_speed'), 5)
        
        if temperature > 25:
            conditions.append('hot')
        elif temperature < -5:
            conditions.append('cold_front')
            
        if wind_speed > 15:
            conditions.append('windy')
        
        # Get base movement score
        base_score = 70.0  # Default moderate activity level
        adjusted_score = scoring_engine.apply_weather_modifiers(
            base_score, 
            'movement',
            conditions or ['clear']  # Use 'clear' if no specific conditions
        )
        
        # Additional pressure trend adjustment
        pressure_trend = weather_data.get('pressure_trend', 'stable')
        if pressure_trend == 'falling':
            adjusted_score *= 1.2  # 20% increase for falling pressure
        elif pressure_trend == 'rising':
            adjusted_score *= 0.9  # 10% decrease for rising pressure
        
        # Convert to factor range (-100 to 100)
        return (adjusted_score - base_score) * 2  # Scale difference to factor range

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
    
    def _enhance_corridors_with_terrain_features(self, basic_corridors: List[Dict], 
                                               terrain_corridors: List[Dict],
                                               detected_features: List[Dict]) -> List[Dict]:
        """
        Enhance movement corridors with detected terrain features
        
        Args:
            basic_corridors: Basic corridor predictions
            terrain_corridors: Detected terrain corridors
            detected_features: All detected terrain features
            
        Returns:
            Enhanced corridor predictions with terrain feature integration
        """
        enhanced_corridors = basic_corridors.copy()
        
        # Add terrain-detected corridors
        for terrain_corridor in terrain_corridors:
            # Create enhanced corridor entry
            enhanced_corridor = {
                'lat': terrain_corridor['corridor_lat'],
                'lon': terrain_corridor['corridor_lon'],
                'type': f"terrain_{terrain_corridor['type']}",
                'confidence': terrain_corridor['confidence'],
                'description': f"Terrain-detected {terrain_corridor['type'].replace('_', ' ')}",
                'terrain_analysis': True,
                'mature_buck_suitability': terrain_corridor['mature_buck_suitability'],
                'terrain_features': terrain_corridor.get('primary_feature', {}),
                'suitability_factors': {
                    'feature_based': True,
                    'terrain_confidence': terrain_corridor['confidence'],
                    'corridor_type': terrain_corridor['type'],
                    **terrain_corridor.get('properties', {})
                }
            }
            enhanced_corridors.append(enhanced_corridor)
        
        # Enhance existing corridors with nearby terrain features
        for corridor in enhanced_corridors:
            if not corridor.get('terrain_analysis', False):
                # Find nearby terrain features
                corridor_lat = corridor['lat']
                corridor_lon = corridor['lon']
                
                nearby_features = []
                for feature in detected_features:
                    # Calculate approximate distance (simple lat/lon difference)
                    lat_diff = abs(feature['lat'] - corridor_lat)
                    lon_diff = abs(feature['lon'] - corridor_lon)
                    distance_approx = (lat_diff + lon_diff) * 111000  # Rough meters
                    
                    if distance_approx <= 100:  # Within 100m
                        nearby_features.append(feature)
                
                if nearby_features:
                    # Enhance corridor with nearby feature data
                    best_feature = max(nearby_features, key=lambda x: x['mature_buck_score'])
                    corridor['terrain_enhancement'] = {
                        'nearby_features': len(nearby_features),
                        'best_feature_type': best_feature['type'],
                        'best_feature_score': best_feature['mature_buck_score'],
                        'terrain_confidence_boost': min(10.0, best_feature['mature_buck_score'] / 10.0)
                    }
                    corridor['confidence'] = min(100.0, corridor['confidence'] + corridor['terrain_enhancement']['terrain_confidence_boost'])
        
        # Sort by confidence and return top corridors
        enhanced_corridors.sort(key=lambda x: x['confidence'], reverse=True)
        return enhanced_corridors[:6]  # Return top 6 enhanced corridors
    
    def _enhance_bedding_with_terrain_features(self, basic_bedding: List[Dict], 
                                             detected_features: List[Dict]) -> List[Dict]:
        """
        Enhance bedding predictions with terrain benches and slope breaks
        
        Args:
            basic_bedding: Basic bedding area predictions
            detected_features: All detected terrain features
            
        Returns:
            Enhanced bedding predictions with terrain feature integration
        """
        enhanced_bedding = basic_bedding.copy()
        
        # Find terrain features suitable for bedding
        bedding_features = [f for f in detected_features 
                           if f['type'] in ['bench', 'slope_break'] and f['mature_buck_score'] >= 60.0]
        
        for feature in bedding_features:
            # Create bedding area from terrain feature
            terrain_bedding = {
                'lat': feature['lat'],
                'lon': feature['lon'],
                'type': f"terrain_{feature['type']}_bedding",
                'confidence': feature['confidence'],
                'description': f"Terrain-detected {feature['type'].replace('_', ' ')} bedding area",
                'terrain_characteristics': feature.get('properties', {}),
                'suitability_factors': {
                    'terrain_based': True,
                    'feature_type': feature['type'],
                    'mature_buck_score': feature['mature_buck_score'],
                    'detection_confidence': feature['confidence']
                }
            }
            
            # Add specific terrain-based factors
            if feature['type'] == 'bench':
                terrain_bedding['suitability_factors'].update({
                    'flatness': True,
                    'size_adequate': feature['properties'].get('size_estimate_sqm', 0) >= 50,
                    'bedding_comfort': feature['properties'].get('bedding_suitability', 0.5)
                })
            elif feature['type'] == 'slope_break':
                terrain_bedding['suitability_factors'].update({
                    'transition_zone': True,
                    'accessibility': feature['properties'].get('accessibility', 0.5),
                    'bedding_potential': feature['properties'].get('bedding_potential', False)
                })
            
            enhanced_bedding.append(terrain_bedding)
        
        # Enhance existing bedding areas with nearby features
        for bedding in enhanced_bedding:
            if not bedding.get('terrain_characteristics'):
                bedding_lat = bedding['lat']
                bedding_lon = bedding['lon']
                
                # Find nearby terrain features that support bedding
                nearby_support_features = []
                for feature in detected_features:
                    lat_diff = abs(feature['lat'] - bedding_lat)
                    lon_diff = abs(feature['lon'] - bedding_lon)
                    distance_approx = (lat_diff + lon_diff) * 111000
                    
                    if distance_approx <= 75:  # Within 75m
                        if feature['type'] in ['saddle', 'slope_break', 'bench', 'drainage']:
                            nearby_support_features.append(feature)
                
                if nearby_support_features:
                    bedding['terrain_support'] = {
                        'supporting_features': len(nearby_support_features),
                        'best_support_type': max(nearby_support_features, 
                                               key=lambda x: x['mature_buck_score'])['type'],
                        'terrain_confidence_boost': min(8.0, len(nearby_support_features) * 2.0)
                    }
                    bedding['confidence'] = min(100.0, bedding['confidence'] + bedding['terrain_support']['terrain_confidence_boost'])
        
        # Sort by confidence and return top bedding areas
        enhanced_bedding.sort(key=lambda x: x['confidence'], reverse=True)
        return enhanced_bedding[:4]  # Return top 4 enhanced bedding areas
    
    def _generate_terrain_based_stands(self, terrain_analysis: Dict, lat: float, lon: float) -> List[Dict]:
        """
        Generate stand recommendations based on detected terrain features
        
        Args:
            terrain_analysis: Complete terrain analysis results
            lat: Base latitude
            lon: Base longitude
            
        Returns:
            List of terrain-based stand recommendations
        """
        stand_recommendations = []
        
        detected_features = terrain_analysis['detected_features']
        natural_funnels = terrain_analysis['natural_funnels']
        travel_corridors = terrain_analysis['travel_corridors']
        
        # Funnel-based stands (highest priority)
        for funnel in natural_funnels:
            if funnel['mature_buck_suitability'] >= 70.0:
                stand = {
                    'type': 'Natural Terrain Funnel Stand',
                    'lat': funnel['center_lat'],
                    'lon': funnel['center_lon'],
                    'confidence': funnel['confidence'],
                    'mature_buck_score': funnel['mature_buck_suitability'],
                    'setup_requirements': [
                        f"Position for {len(funnel['contributing_features'])} converging features",
                        "Multiple approach angle coverage",
                        "Wind consideration for funnel direction"
                    ],
                    'best_conditions': [
                        "High pressure periods when bucks use secure routes",
                        "Weather fronts that trigger movement",
                        "Rut season for increased daylight activity"
                    ],
                    'terrain_advantages': {
                        'natural_constraint': True,
                        'multiple_features': funnel['properties']['feature_count'],
                        'funnel_strength': funnel['properties']['funnel_strength'],
                        'ambush_potential': funnel['properties']['ambush_potential']
                    }
                }
                stand_recommendations.append(stand)
        
        # Saddle-based stands
        saddle_features = [f for f in detected_features 
                          if f['type'] == 'saddle' and f['mature_buck_score'] >= 65.0]
        for saddle in saddle_features[:2]:  # Top 2 saddles
            stand = {
                'type': 'Saddle Ambush Stand',
                'lat': saddle['lat'],
                'lon': saddle['lon'],
                'confidence': saddle['confidence'],
                'mature_buck_score': saddle['mature_buck_score'],
                'setup_requirements': [
                    f"Position in saddle with {saddle['properties']['depth_meters']:.1f}m depth",
                    "Cover approach routes on both sides",
                    "Wind advantage from higher ground"
                ],
                'best_conditions': [
                    "Any movement period - natural travel route",
                    "Pressure situations when bucks seek easy passage",
                    "Early morning and late evening transitions"
                ],
                'terrain_advantages': {
                    'natural_funnel': True,
                    'easy_passage': True,
                    'saddle_depth': saddle['properties']['depth_meters'],
                    'concealment_rating': saddle['properties']['concealment_rating']
                }
            }
            stand_recommendations.append(stand)
        
        # Ridge corridor stands
        ridge_corridors = [c for c in travel_corridors 
                          if c['type'] == 'ridge_corridor' and c['mature_buck_suitability'] >= 60.0]
        for ridge in ridge_corridors[:2]:  # Top 2 ridge corridors
            stand = {
                'type': 'Ridge Travel Corridor Stand',
                'lat': ridge['corridor_lat'],
                'lon': ridge['corridor_lon'],
                'confidence': ridge['confidence'],
                'mature_buck_score': ridge['mature_buck_suitability'],
                'setup_requirements': [
                    "Position along ridge spine travel route",
                    "Multiple escape route coverage",
                    "Elevation advantage for detection"
                ],
                'best_conditions': [
                    "Dry conditions when ridges are preferred",
                    "Clear weather for long-distance spotting",
                    "Rut season travel between doe groups"
                ],
                'terrain_advantages': {
                    'elevation_advantage': True,
                    'travel_corridor': True,
                    'escape_routes': ridge['properties']['escape_routes'],
                    'seasonal_preference': ridge['properties']['seasonal_preference']
                }
            }
            stand_recommendations.append(stand)
        
        # Drainage corridor stands
        drainage_corridors = [c for c in travel_corridors 
                             if c['type'] == 'drainage_corridor' and c['mature_buck_suitability'] >= 55.0]
        for drainage in drainage_corridors[:1]:  # Top drainage corridor
            stand = {
                'type': 'Concealed Drainage Stand',
                'lat': drainage['corridor_lat'],
                'lon': drainage['corridor_lon'],
                'confidence': drainage['confidence'],
                'mature_buck_score': drainage['mature_buck_suitability'],
                'setup_requirements': [
                    "Position overlooking drainage corridor",
                    "Concealed approach to avoid detection",
                    "Cover multiple drainage access points"
                ],
                'best_conditions': [
                    "High pressure periods - maximum concealment value",
                    "Wet conditions when drainages are active",
                    "Dawn and dusk for water access"
                ],
                'terrain_advantages': {
                    'maximum_concealment': True,
                    'water_access': True,
                    'pressure_resistance': True,
                    'year_round_viability': True
                }
            }
            stand_recommendations.append(stand)
        
        # Sort by mature buck score
        stand_recommendations.sort(key=lambda x: x['mature_buck_score'], reverse=True)
        
        return stand_recommendations[:4]  # Return top 4 terrain-based stands
    
    def _generate_terrain_behavioral_insights(self, terrain_analysis: Dict, season: str, weather_data: Dict) -> List[str]:
        """
        Generate behavioral insights based on terrain analysis
        
        Args:
            terrain_analysis: Complete terrain analysis results
            season: Current hunting season
            weather_data: Weather conditions
            
        Returns:
            List of terrain-based behavioral insights
        """
        insights = []
        
        mature_buck_analysis = terrain_analysis['mature_buck_analysis']
        detected_features = terrain_analysis['detected_features']
        natural_funnels = terrain_analysis['natural_funnels']
        
        # Overall terrain assessment
        overall_score = mature_buck_analysis['overall_suitability']
        if overall_score >= 80.0:
            insights.append("🎯 PREMIUM mature buck terrain - expect regular use during appropriate conditions")
        elif overall_score >= 60.0:
            insights.append("✅ GOOD mature buck habitat - selective use based on pressure and weather")
        elif overall_score >= 40.0:
            insights.append("⚠️ MODERATE terrain - expect limited mature buck activity")
        else:
            insights.append("❌ CHALLENGING terrain for mature buck activity")
        
        # Feature-specific insights
        feature_analysis = mature_buck_analysis['feature_analysis']
        
        if 'saddle' in feature_analysis:
            saddle_data = feature_analysis['saddle']
            if saddle_data['avg_score'] >= 70.0:
                insights.append(f"🏔️ {saddle_data['count']} premium saddle(s) detected - expect consistent travel routes")
        
        if 'drainage' in feature_analysis:
            drainage_data = feature_analysis['drainage']
            if drainage_data['count'] >= 2:
                insights.append(f"💧 Multiple drainage systems provide excellent concealed movement options")
        
        if 'bench' in feature_analysis:
            bench_data = feature_analysis['bench']
            if bench_data['avg_score'] >= 65.0:
                insights.append(f"🛏️ High-quality bedding sites detected - expect daytime presence")
        
        # Seasonal behavioral insights
        if season == "rut":
            if len(natural_funnels) >= 2:
                insights.append("💘 RUT ADVANTAGE: Multiple funnels increase doe monitoring opportunities")
            if feature_analysis.get('ridge_spine', {}).get('count', 0) >= 1:
                insights.append("🦌 RUT TRAVEL: Ridge systems ideal for covering territory during rut")
        
        elif season == "early_season":
            if feature_analysis.get('drainage', {}).get('avg_score', 0) >= 60.0:
                insights.append("🌅 EARLY SEASON: Drainage corridors provide security during high pressure")
        
        elif season == "late_season":
            if overall_score >= 70.0:
                insights.append("❄️ LATE SEASON: High-quality terrain becomes critical for energy conservation")
        
        # Weather-based insights
        pressure_trend = weather_data.get('pressure_trend', 'stable')
        if pressure_trend == 'falling' and len(natural_funnels) >= 1:
            insights.append("📉 PRESSURE DROP: Funnel activity likely to increase - prime opportunity")
        
        wind_speed = weather_data.get('wind_speed', 5)
        if wind_speed >= 15 and feature_analysis.get('drainage', {}).get('count', 0) >= 1:
            insights.append("💨 WINDY CONDITIONS: Drainage corridors provide wind protection and noise cover")
        
        # Strategic insights
        corridor_analysis = mature_buck_analysis['corridor_analysis']
        if corridor_analysis['corridor_diversity'] >= 3:
            insights.append("🎯 TACTICAL ADVANTAGE: Multiple corridor types allow pressure adaptation")
        
        if corridor_analysis['total_corridors'] >= 4:
            insights.append("🗺️ COMPLEX MOVEMENT: Multiple travel options suggest established mature buck territory")
        
        return insights
    
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
    
    def _calculate_proximity_score(self, distance_yards: float, 
                                  min_optimal: float, 
                                  max_optimal: float, 
                                  max_useful: float) -> float:
        """
        Calculate proximity score based on distance and optimal ranges
        
        Args:
            distance_yards: Distance to zone in yards
            min_optimal: Minimum optimal distance
            max_optimal: Maximum optimal distance  
            max_useful: Maximum useful distance
            
        Returns:
            Proximity score (0-100)
            
        Scoring Logic:
        - 0 to min_optimal: Linear increase from 60 to 100
        - min_optimal to max_optimal: 100 (optimal range)  
        - max_optimal to max_useful: Linear decrease from 100 to 20
        - Beyond max_useful: 10 (minimal benefit)
        """
        if distance_yards <= min_optimal:
            # Too close - linear increase from 60 to 100
            if distance_yards <= 0:
                return 60.0
            return 60.0 + (40.0 * (distance_yards / min_optimal))
        
        elif distance_yards <= max_optimal:
            # Optimal range - maximum score
            return 100.0
        
        elif distance_yards <= max_useful:
            # Useful but declining - linear decrease from 100 to 20
            range_size = max_useful - max_optimal
            distance_beyond_optimal = distance_yards - max_optimal
            decline_factor = distance_beyond_optimal / range_size
            return 100.0 - (80.0 * decline_factor)
        
        else:
            # Beyond useful range - minimal benefit
            return 10.0
    
    def _calculate_multi_zone_distances(self, stand_lat: float, stand_lon: float, 
                                       zone_locations: List[Dict]) -> Dict:
        """
        Calculate distances to multiple zones and return analysis
        
        Args:
            stand_lat: Stand latitude
            stand_lon: Stand longitude
            zone_locations: List of zone dictionaries with lat/lon
            
        Returns:
            {
                'distances': [list of distances in yards],
                'closest': {'distance': float, 'zone': dict},
                'average_distance': float,
                'within_optimal_count': int
            }
        """
        if not zone_locations:
            return {
                'distances': [],
                'closest': {'distance': float('inf'), 'zone': None},
                'average_distance': float('inf'),
                'within_optimal_count': 0
            }
        
        distances = []
        closest_zone = None
        closest_distance = float('inf')
        
        for zone in zone_locations:
            zone_lat = zone.get('lat')
            zone_lon = zone.get('lon')
            
            if zone_lat is None or zone_lon is None:
                continue
                
            # Calculate distance in miles, convert to yards
            distance_miles = self._calculate_haversine_distance(
                stand_lat, stand_lon, zone_lat, zone_lon
            )
            distance_yards = distance_miles * 1760
            
            distances.append(distance_yards)
            
            if distance_yards < closest_distance:
                closest_distance = distance_yards
                closest_zone = zone
        
        if not distances:
            return {
                'distances': [],
                'closest': {'distance': float('inf'), 'zone': None},
                'average_distance': float('inf'),
                'within_optimal_count': 0
            }
        
        return {
            'distances': distances,
            'closest': {'distance': closest_distance, 'zone': closest_zone},
            'average_distance': sum(distances) / len(distances),
            'within_optimal_count': len([d for d in distances if d <= 200])  # Within 200 yards
        }
    
    def calculate_zone_proximity_scores(self, stand_lat: float, stand_lon: float, 
                                       bedding_locations: List[Dict], 
                                       feeding_locations: List[Dict]) -> Dict:
        """
        Calculate proximity scores for stand relative to deer activity zones
        
        Args:
            stand_lat: Stand latitude
            stand_lon: Stand longitude
            bedding_locations: List of predicted bedding locations
            feeding_locations: List of predicted feeding locations
            
        Returns:
            {
                'bedding_proximity': {
                    'closest_distance_yards': float,
                    'average_distance_yards': float,
                    'proximity_score': float (0-100),
                    'optimal_range': bool
                },
                'feeding_proximity': {
                    'closest_distance_yards': float,
                    'average_distance_yards': float, 
                    'proximity_score': float (0-100),
                    'optimal_range': bool
                },
                'combined_proximity_score': float (0-100)
            }
        """
        # Calculate bedding proximity
        bedding_analysis = self._calculate_multi_zone_distances(
            stand_lat, stand_lon, bedding_locations
        )
        
        bedding_thresholds = PROXIMITY_THRESHOLDS['bedding']
        bedding_closest = bedding_analysis['closest']['distance']
        bedding_score = self._calculate_proximity_score(
            bedding_closest,
            bedding_thresholds['min_optimal'],
            bedding_thresholds['max_optimal'],
            bedding_thresholds['max_useful']
        )
        
        bedding_optimal = (bedding_thresholds['min_optimal'] <= 
                          bedding_closest <= bedding_thresholds['max_optimal'])
        
        # Calculate feeding proximity
        feeding_analysis = self._calculate_multi_zone_distances(
            stand_lat, stand_lon, feeding_locations
        )
        
        feeding_thresholds = PROXIMITY_THRESHOLDS['feeding']
        feeding_closest = feeding_analysis['closest']['distance']
        feeding_score = self._calculate_proximity_score(
            feeding_closest,
            feeding_thresholds['min_optimal'],
            feeding_thresholds['max_optimal'],
            feeding_thresholds['max_useful']
        )
        
        feeding_optimal = (feeding_thresholds['min_optimal'] <= 
                          feeding_closest <= feeding_thresholds['max_optimal'])
        
        # Calculate combined score using configured weights
        combined_score = (
            bedding_score * PROXIMITY_CONFIG['bedding_weight'] +
            feeding_score * PROXIMITY_CONFIG['feeding_weight']
        )
        
        return {
            'bedding_proximity': {
                'closest_distance_yards': bedding_closest,
                'average_distance_yards': bedding_analysis['average_distance'],
                'proximity_score': bedding_score,
                'optimal_range': bedding_optimal
            },
            'feeding_proximity': {
                'closest_distance_yards': feeding_closest,
                'average_distance_yards': feeding_analysis['average_distance'],
                'proximity_score': feeding_score,
                'optimal_range': feeding_optimal
            },
            'combined_proximity_score': combined_score
        }
    
    def _calculate_haversine_distance(self, lat1: float, lon1: float, 
                                     lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        
        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates
            
        Returns:
            Distance in miles
        """
        import math
        
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat_rad = math.radians(lat2 - lat1)
        dlon_rad = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = (math.sin(dlat_rad/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon_rad/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return 3959 * c  # Earth radius in miles

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
                               strategy_index: int, wind_data: Optional[WindData] = None) -> Dict:
    """
    Find optimal stand position based on strategy type, terrain features, and wind conditions
    
    Args:
        strategy: Stand strategy configuration
        terrain_analysis: Complete terrain analysis
        mature_buck_scores: Mature buck terrain scores
        lat: Base latitude
        lon: Base longitude
        strategy_index: Index for positioning variation
        wind_data: Optional wind data for positioning optimization
        
    Returns:
        Dict with lat, lon, positioning justification, and wind analysis
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
    
    # Base positioning logic - realistic hunting distances (100-400 yards)
    if strategy_type == 'Escape Route Ambush':
        # Position between bedding and escape routes
        if drainage_density >= 1.0:
            # Use drainage systems for escape route positioning
            base_angle = (45 + strategy_index * 90)
            base_distance = 200 + drainage_density * 80  # 200-280 meters (220-300 yards)
            justification = f"Positioned along drainage corridor with {drainage_density:.1f} density"
            precision_factors = {
                'drainage_density': drainage_density,
                'escape_routes': 'multiple',
                'positioning_method': 'drainage_based'
            }
        else:
            # Fallback to ridge-based positioning
            base_angle = (30 + strategy_index * 120)
            base_distance = 180 + ridge_connectivity * 120  # 180-300 meters (200-330 yards)
            justification = f"Ridge-based escape route position"
            precision_factors = {
                'ridge_connectivity': ridge_connectivity,
                'positioning_method': 'ridge_based'
            }
            
    elif strategy_type == 'Secluded Feeding Edge':
        # Position near agricultural or forest edges
        if ag_proximity <= 300.0:
            # Position at agricultural edge
            base_angle = 225  # Southwest of ag area
            base_distance = ag_proximity + 120  # 120-420 meters from ag (130-460 yards)
            justification = f"Agricultural edge position, {ag_proximity:.0f}m from crops"
            precision_factors = {
                'agricultural_proximity': ag_proximity,
                'edge_type': 'agricultural',
                'positioning_method': 'ag_edge_based'
            }
        else:
            # Position at forest opening
            base_angle = (180 + strategy_index * 45)
            base_distance = 250 + canopy_closure * 2  # 250-350 meters (270-380 yards)
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
            base_angle = (90 + strategy_index * 180)
            base_distance = 300 + escape_cover_density * 2  # 300-440 meters (330-480 yards)
            justification = f"Deep sanctuary in {escape_cover_density:.0f}% cover density"
            precision_factors = {
                'escape_cover_density': escape_cover_density,
                'sanctuary_quality': 'premium',
                'positioning_method': 'cover_density_based'
            }
        else:
            # Use elevation for sanctuary
            base_angle = (135 + strategy_index * 90)
            base_distance = 280 + elevation * 0.5  # 280+ meters based on elevation (300+ yards)
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
            base_angle = (0 + strategy_index * 180)  # North/South ridge positions
            base_distance = 160 + ridge_connectivity * 200  # 160-360 meters (175-390 yards)
            justification = f"Ridge saddle with {ridge_connectivity:.1f} connectivity"
            precision_factors = {
                'ridge_connectivity': ridge_connectivity,
                'funnel_quality': 'natural',
                'positioning_method': 'ridge_saddle_based'
            }
        else:
            # Use drainage convergence as funnel
            base_angle = (315 + strategy_index * 45)
            base_distance = 200 + drainage_density * 80  # 200-280 meters (220-300 yards)
            justification = f"Drainage convergence funnel"
            precision_factors = {
                'drainage_density': drainage_density,
                'funnel_quality': 'drainage_based',
                'positioning_method': 'drainage_convergence'
            }
    else:
        # Default positioning
        base_angle = (strategy_index * 90)
        base_distance = 220  # 220 meters (240 yards)
        justification = "General terrain positioning"
        precision_factors = {'positioning_method': 'default'}
    
    # Wind-aware positioning optimization
    wind_optimized_data = None
    final_angle = base_angle
    wind_adjustment_info = {}
    
    if wind_data:
        try:
            # Create a wind analyzer instance for this calculation
            from wind_analysis import WindAnalyzer
            wind_analyzer = WindAnalyzer()
            
            # Calculate wind-optimized position relative to predicted bedding area
            # Use the base coordinates as the "target" bedding area
            wind_position = wind_analyzer.calculate_optimal_downwind_position(
                target_lat=lat,
                target_lon=lon,
                wind_data=wind_data,
                distance_yards=base_distance * 1.09361,  # Convert meters to yards
                strategy_type=strategy_type.lower().replace(' ', '_')
            )
            
            # Extract wind-optimized angle
            wind_angle = wind_position.downwind_angle
            
            # Blend terrain-based angle with wind-optimized angle
            # Weight wind more heavily for certain strategies
            if strategy_type in ['Escape Route Ambush', 'Secluded Feeding Edge']:
                wind_weight = 0.7  # Prioritize wind for ambush strategies
            elif strategy_type == 'Pressure Sanctuary':
                wind_weight = 0.4  # Less wind dependence for sanctuaries
            else:
                wind_weight = 0.6  # Moderate wind consideration
            
            # Calculate blended angle
            angle_diff = abs(wind_angle - base_angle)
            if angle_diff > 180:
                angle_diff = 360 - angle_diff
            
            # If wind and terrain angles are too far apart, find a compromise
            if angle_diff <= 90:
                # Blend the angles
                final_angle = (wind_weight * wind_angle + (1 - wind_weight) * base_angle)
            else:
                # Use terrain angle but add wind safety margin
                final_angle = base_angle
                wind_weight = 0.2  # Reduce wind influence when conflict is high
            
            # Store wind optimization data
            wind_optimized_data = wind_position
            wind_adjustment_info = {
                'wind_direction': wind_data.direction_degrees,
                'wind_speed': wind_data.speed_mph,
                'wind_consistency': wind_data.consistency.value,
                'optimal_wind_angle': wind_angle,
                'terrain_angle': base_angle,
                'final_angle': final_angle,
                'wind_weight_used': wind_weight,
                'wind_advantage_score': wind_position.wind_advantage_score,
                'scent_safety_margin': wind_position.scent_safety_margin,
                'entry_route': wind_position.optimal_entry_route,
                'fallback_positions': wind_position.fallback_positions
            }
            
            # Update justification with wind information
            wind_status = "favorable" if wind_position.wind_advantage_score > 60 else "acceptable" if wind_position.wind_advantage_score > 40 else "challenging"
            justification += f" | Wind: {wind_data.direction_degrees:.0f}° at {wind_data.speed_mph:.1f}mph ({wind_status})"
            
        except Exception as e:
            logger.warning(f"⚠️ Wind optimization failed: {e}")
            # Fall back to terrain-only positioning
            final_angle = base_angle
    
    # Calculate final coordinates using wind-adjusted angle
    angle_rad = final_angle * np.pi / 180
    offset_lat = base_distance * np.cos(angle_rad) * meters_to_degrees
    offset_lon = base_distance * np.sin(angle_rad) * meters_to_degrees
    
    stand_lat = lat + offset_lat
    stand_lon = lon + offset_lon
    
    # Debug logging for positioning
    logger.info(f"🎯 {strategy_type}: base_distance={base_distance}m, angle={final_angle:.1f}°, offset_lat={offset_lat:.6f}, offset_lon={offset_lon:.6f}")
    
    # Prepare return data
    result = {
        'lat': stand_lat,
        'lon': stand_lon,
        'justification': justification,
        'precision_factors': precision_factors,
        'distance_from_center': base_distance,
        'positioning_angle': final_angle,
        'wind_optimized': wind_data is not None,
        'wind_data': wind_adjustment_info
    }
    
    # Add wind optimization details if available
    if wind_optimized_data:
        result['wind_optimization'] = {
            'downwind_position': (wind_optimized_data.latitude, wind_optimized_data.longitude),
            'wind_advantage_score': wind_optimized_data.wind_advantage_score,
            'scent_safety_margin': wind_optimized_data.scent_safety_margin,
            'confidence_modifiers': wind_optimized_data.confidence_modifiers,
            'entry_route': wind_optimized_data.optimal_entry_route,
            'fallback_positions': wind_optimized_data.fallback_positions
        }
    
    return result

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
                                             lat: float, lon: float, 
                                             weather_data: Optional[Dict] = None) -> List[Dict]:
    """
    Generate stand recommendations specifically optimized for mature bucks with wind analysis
    
    Args:
        terrain_analysis: Terrain analysis results
        mature_buck_scores: Mature buck terrain scores
        lat: Latitude coordinate
        lon: Longitude coordinate
        weather_data: Optional weather data including wind information
        
    Returns:
        List of mature buck optimized stand recommendations with wind optimization
    """
    recommendations = []
    
    # Fetch current wind data if weather_data is available
    wind_data = None
    if weather_data:
        try:
            from wind_analysis import get_wind_analyzer
            wind_analyzer = get_wind_analyzer()
            wind_data = wind_analyzer.fetch_current_wind_data(lat, lon)
            logger.info(f"🌬️ Wind data integrated: {wind_data.direction_degrees:.0f}° at {wind_data.speed_mph:.1f}mph")
        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch wind data: {e}")
    
    # Generate bedding and feeding predictions for proximity analysis
    try:
        buck_predictor = get_mature_buck_predictor()
        bedding_locations = buck_predictor._predict_bedding_locations(terrain_analysis, lat, lon)
        feeding_locations = buck_predictor._predict_feeding_zones(terrain_analysis, lat, lon, 'rut')  # Default to rut season
        logger.info(f"🎯 Proximity analysis: {len(bedding_locations)} bedding zones, {len(feeding_locations)} feeding zones")
    except Exception as e:
        logger.warning(f"⚠️ Failed to generate proximity zones: {e}")
        bedding_locations = []
        feeding_locations = []

    # Mature buck stand strategies
    stand_strategies = [
        {
            'type': 'Escape Route Ambush',
            'description': 'Position between bedding and primary escape corridor',
            'confidence_base': 85.0,
            'setup_requirements': ['Multiple escape routes', 'Thick cover nearby', 'Wind advantage'],
            'best_times': 'Dawn and dusk during high pressure periods',
            'wind_critical': True  # Wind is critical for ambush strategies
        },
        {
            'type': 'Secluded Feeding Edge',
            'description': 'Hidden position overlooking isolated food source',
            'confidence_base': 80.0,
            'setup_requirements': ['Remote food source', 'Concealed approach', 'Escape cover'],
            'best_times': 'Night vision or thermal during rut',
            'wind_critical': True  # Wind is critical for feeding areas
        },
        {
            'type': 'Pressure Sanctuary',
            'description': 'Deep cover position in low-pressure sanctuary',
            'confidence_base': 90.0,
            'setup_requirements': ['Difficult hunter access', 'Multiple cover types', 'Water nearby'],
            'best_times': 'All day during peak rut',
            'wind_critical': False  # Sanctuary less dependent on wind
        },
        {
            'type': 'Ridge Saddle Intercept',
            'description': 'Strategic position in natural travel funnel',
            'confidence_base': 75.0,
            'setup_requirements': ['Natural funnel', 'Elevation advantage', 'Cross wind setup'],
            'best_times': 'Morning and evening transitions',
            'wind_critical': True  # Funnel intercepts need good wind
        }
    ]
    
    for i, strategy in enumerate(stand_strategies):
        # Calculate position based on terrain features, strategy type, and wind
        stand_position = _find_optimal_stand_position_for_strategy(
            strategy, terrain_analysis, mature_buck_scores, lat, lon, i, wind_data
        )
        
        # Adjust confidence based on terrain suitability
        confidence = strategy['confidence_base']
        confidence += mature_buck_scores.get('overall_suitability', 0) * 0.15
        
        # Add terrain-specific bonuses
        terrain_bonus = _calculate_terrain_bonus_for_strategy(strategy, terrain_analysis)
        confidence += terrain_bonus
        
        # Add wind-specific confidence adjustments
        wind_confidence_adjustment = 0.0
        wind_notes = []
        
        if wind_data and stand_position.get('wind_optimized'):
            wind_info = stand_position.get('wind_data', {})
            wind_advantage_score = wind_info.get('wind_advantage_score', 50.0)
            
            # Calculate wind confidence adjustment
            if strategy['wind_critical']:
                # Wind-critical strategies get larger adjustments
                if wind_advantage_score >= 80:
                    wind_confidence_adjustment = 15.0
                    wind_notes.append("🌬️ Excellent wind conditions")
                elif wind_advantage_score >= 60:
                    wind_confidence_adjustment = 8.0
                    wind_notes.append("🌬️ Good wind conditions")
                elif wind_advantage_score >= 40:
                    wind_confidence_adjustment = 2.0
                    wind_notes.append("🌬️ Acceptable wind conditions")
                else:
                    wind_confidence_adjustment = -10.0
                    wind_notes.append("⚠️ Challenging wind conditions")
            else:
                # Non-critical strategies get smaller adjustments
                if wind_advantage_score >= 60:
                    wind_confidence_adjustment = 5.0
                    wind_notes.append("🌬️ Wind advantage present")
                elif wind_advantage_score < 40:
                    wind_confidence_adjustment = -3.0
                    wind_notes.append("⚠️ Wind conditions suboptimal")
            
            # Add wind consistency bonus/penalty
            wind_consistency = wind_info.get('wind_consistency', 'moderate')
            if wind_consistency == 'steady':
                wind_confidence_adjustment += 3.0
                wind_notes.append("✅ Steady wind pattern")
            elif wind_consistency == 'variable':
                wind_confidence_adjustment -= 2.0
                wind_notes.append("⚠️ Variable wind pattern")
            elif wind_consistency == 'chaotic':
                wind_confidence_adjustment -= 5.0
                wind_notes.append("❌ Chaotic wind pattern")
        
        # Apply wind adjustment to confidence
        confidence += wind_confidence_adjustment
        
        # Calculate proximity scores for this stand position
        proximity_analysis = {}
        proximity_confidence_adjustment = 0.0
        proximity_notes = []
        
        if bedding_locations or feeding_locations:
            try:
                stand_lat = stand_position.get('lat', lat)
                stand_lon = stand_position.get('lon', lon)
                
                proximity_analysis = buck_predictor.calculate_zone_proximity_scores(
                    stand_lat, stand_lon, bedding_locations, feeding_locations
                )
                
                # Calculate confidence adjustment based on proximity (up to 15% impact)
                combined_proximity = proximity_analysis['combined_proximity_score']
                proximity_confidence_adjustment = (combined_proximity - 50.0) * PROXIMITY_CONFIG['confidence_impact']
                
                # Add proximity insights
                bedding_prox = proximity_analysis['bedding_proximity']
                feeding_prox = proximity_analysis['feeding_proximity']
                
                if bedding_prox['optimal_range']:
                    proximity_notes.append(f"🛏️ Optimal bedding distance ({bedding_prox['closest_distance_yards']:.0f} yds)")
                else:
                    proximity_notes.append(f"🛏️ Bedding distance: {bedding_prox['closest_distance_yards']:.0f} yds")
                
                if feeding_prox['optimal_range']:
                    proximity_notes.append(f"🌿 Optimal feeding distance ({feeding_prox['closest_distance_yards']:.0f} yds)")
                else:
                    proximity_notes.append(f"🌿 Feeding distance: {feeding_prox['closest_distance_yards']:.0f} yds")
                
                if combined_proximity >= 80:
                    proximity_notes.append("🎯 Excellent zone proximity - high intercept probability")
                elif combined_proximity >= 60:
                    proximity_notes.append("✅ Good zone proximity - solid positioning")
                elif combined_proximity < 40:
                    proximity_notes.append("⚠️ Suboptimal zone proximity - consider repositioning")
                    
            except Exception as e:
                logger.warning(f"⚠️ Failed to calculate proximity for stand {i+1}: {e}")
        
        # Apply proximity adjustment to confidence
        confidence += proximity_confidence_adjustment
        confidence = min(confidence, 95.0)
        
        # Prepare setup requirements with wind information
        setup_requirements = strategy['setup_requirements'].copy()
        if wind_data:
            wind_speed = wind_data.speed_mph
            wind_direction = wind_data.direction_degrees
            setup_requirements.append(f"Wind: {wind_direction:.0f}° at {wind_speed:.1f}mph")
        
        recommendation = {
            'type': strategy['type'],
            'description': strategy['description'],
            'coordinates': stand_position,
            'confidence': confidence,
            'setup_requirements': setup_requirements,
            'best_times': strategy['best_times'],
            'mature_buck_optimized': True,
            'pressure_resistance': mature_buck_scores.get('pressure_resistance', 50.0),
            'escape_route_quality': mature_buck_scores.get('escape_route_quality', 50.0),
            'terrain_justification': stand_position.get('justification', 'General terrain positioning'),
            'precision_factors': stand_position.get('precision_factors', {}),
            'wind_optimized': stand_position.get('wind_optimized', False),
            'wind_analysis': stand_position.get('wind_data', {}),
            'wind_confidence_adjustment': wind_confidence_adjustment,
            'wind_notes': wind_notes,
            'proximity_analysis': proximity_analysis,
            'proximity_confidence_adjustment': proximity_confidence_adjustment,
            'proximity_notes': proximity_notes
        }
        
        # Add wind optimization details if available
        if stand_position.get('wind_optimization'):
            recommendation['wind_optimization'] = stand_position['wind_optimization']
        
        recommendations.append(recommendation)
    
    # Sort by confidence (now includes wind factors)
    recommendations.sort(key=lambda x: x['confidence'], reverse=True)
    
    return recommendations[:4]  # Return top 4 recommendations