#!/usr/bin/env python3
"""
Unified Scoring Engine for Deer Prediction System

This module provides a centralized scoring framework to eliminate repeated
scoring logic throughout the application. It handles terrain, weather, 
seasonal, and behavioral scoring with consistent methodologies.

Key Features:
- Unified confidence calculation framework
- Standardized terrain feature evaluation
- Consistent seasonal weighting system
- Centralized weather impact assessment
- Modular scoring components for reuse

Author: Vermont Deer Prediction System
Version: 1.0.0
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import math

# Import configuration management
from .config_manager import get_config

# Set up logging
logger = logging.getLogger(__name__)

class ScoreType(Enum):
    """Types of scores used in the system"""
    CONFIDENCE = "confidence"       # 0-100 confidence scores
    SUITABILITY = "suitability"    # 0-100 suitability scores
    PROBABILITY = "probability"     # 0-1 probability scores
    RATING = "rating"              # 0-10 rating scores
    NORMALIZED = "normalized"       # 0-1 normalized scores

class SeasonalWeight(Enum):
    """Seasonal weighting factors"""
    EARLY_SEASON = "early_season"
    RUT = "rut"
    LATE_SEASON = "late_season"

@dataclass
class ScoringContext:
    """Context information for scoring calculations"""
    season: str
    time_of_day: int
    weather_conditions: List[str]
    pressure_level: str = "moderate"
    terrain_type: str = "mixed"
    behavior_type: str = "general"

@dataclass
class TerrainScoreComponents:
    """Components of terrain-based scoring"""
    elevation_score: float = 0.0
    slope_score: float = 0.0
    aspect_score: float = 0.0
    cover_score: float = 0.0
    drainage_score: float = 0.0
    connectivity_score: float = 0.0
    isolation_score: float = 0.0
    
    def total_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted total terrain score using configuration"""
        if weights is None:
            # Get weights from configuration
            config = get_config()
            weights = config.get_terrain_weights()
            
            # Fallback defaults if configuration missing
            if not weights:
                weights = {
                    'elevation': 0.15, 'slope': 0.15, 'aspect': 0.10,
                    'cover': 0.25, 'drainage': 0.15, 'connectivity': 0.10,
                    'isolation': 0.10
                }
        
        return (
            self.elevation_score * weights.get('elevation', 0.15) +
            self.slope_score * weights.get('slope', 0.15) +
            self.aspect_score * weights.get('aspect', 0.10) +
            self.cover_score * weights.get('cover', 0.25) +
            self.drainage_score * weights.get('drainage', 0.15) +
            self.connectivity_score * weights.get('connectivity', 0.10) +
            self.isolation_score * weights.get('isolation', 0.10)
        )

class ScoringEngine:
    """
    Unified scoring engine for all deer prediction calculations
    """
    
    def __init__(self):
        """Initialize the scoring engine with configuration-based parameters"""
        self.config = get_config()
        self.seasonal_weights = self._initialize_seasonal_weights()
        self.weather_modifiers = self._initialize_weather_modifiers()
        self.terrain_preferences = self._initialize_terrain_preferences()
        
        logger.info("🎯 Scoring Engine initialized with configuration")
    
    def _initialize_seasonal_weights(self) -> Dict[str, Dict[str, float]]:
        """Initialize seasonal weighting factors from configuration"""
        config_weights = self.config.get_seasonal_weights()
        
        # Provide fallback defaults if configuration is missing
        defaults = {
            "early_season": {"travel": 1.0, "bedding": 1.0, "feeding": 1.2, "movement": 0.9},
            "rut": {"travel": 1.3, "bedding": 0.9, "feeding": 1.0, "movement": 1.4},
            "late_season": {"travel": 0.8, "bedding": 1.5, "feeding": 1.1, "movement": 0.7}
        }
        
        # Merge configuration with defaults
        for season in defaults:
            if season in config_weights:
                defaults[season].update(config_weights[season])
        
        return defaults
    
    def _initialize_weather_modifiers(self) -> Dict[str, Dict[str, float]]:
        """Initialize weather impact modifiers from configuration"""
        config_modifiers = self.config.get_weather_modifiers()
        
        # Provide fallback defaults
        defaults = {
            "clear": {"travel": 1.0, "bedding": 1.0, "feeding": 1.0},
            "cloudy": {"travel": 1.1, "bedding": 1.0, "feeding": 1.0},
            "light_rain": {"travel": 0.8, "bedding": 1.2, "feeding": 0.9},
            "heavy_rain": {"travel": 0.5, "bedding": 1.5, "feeding": 0.6},
            "snow": {"travel": 0.7, "bedding": 1.3, "feeding": 0.8},
            "cold_front": {"travel": 1.3, "bedding": 0.9, "feeding": 1.2},
            "hot": {"travel": 0.6, "bedding": 1.4, "feeding": 0.7},
            "windy": {"travel": 0.8, "bedding": 1.2, "feeding": 0.9}
        }
        
        # Update with configuration values
        defaults.update(config_modifiers)
        return defaults
    
    def _initialize_terrain_preferences(self) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """Initialize terrain preference ranges (min, max) for different behaviors"""
        return {
            "bedding": {
                "elevation": (300.0, 1000.0),
                "slope": (5.0, 25.0),
                "canopy_closure": (70.0, 100.0),
                "understory_density": (60.0, 100.0)
            },
            "feeding": {
                "elevation": (200.0, 800.0),
                "slope": (0.0, 15.0),
                "agricultural_proximity": (0.0, 500.0),
                "edge_density": (0.5, 2.0)
            },
            "travel": {
                "elevation": (250.0, 900.0),
                "slope": (0.0, 20.0),
                "ridge_connectivity": (0.4, 1.0),
                "drainage_density": (0.5, 2.0)
            }
        }
    
    def safe_float_conversion(self, value: Any, default: float = 0.0) -> float:
        """Safely convert value to float with default fallback"""
        try:
            if isinstance(value, (list, tuple, np.ndarray)):
                if len(value) > 0:
                    return float(value[0])
                return default
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def normalize_score(self, value: float, min_val: float, max_val: float, 
                       invert: bool = False) -> float:
        """
        Normalize a value to 0-1 range with optional inversion
        
        Args:
            value: Value to normalize
            min_val: Minimum expected value
            max_val: Maximum expected value
            invert: If True, higher input values result in lower normalized scores
            
        Returns:
            Normalized score (0-1)
        """
        if max_val <= min_val:
            return 0.5  # Default middle value for invalid range
        
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0.0, min(1.0, normalized))
        
        return 1.0 - normalized if invert else normalized
    
    def score_terrain_feature(self, value: float, feature_name: str, 
                             behavior_type: str) -> float:
        """
        Score a terrain feature based on behavior preferences
        
        Args:
            value: Feature value
            feature_name: Name of terrain feature
            behavior_type: Type of behavior (bedding, feeding, travel)
            
        Returns:
            Score (0-100)
        """
        preferences = self.terrain_preferences.get(behavior_type, {})
        feature_range = preferences.get(feature_name)
        
        if not feature_range:
            # No specific preference - use moderate scoring
            return 50.0
        
        min_pref, max_pref = feature_range
        
        if min_pref <= value <= max_pref:
            # Value is in preferred range
            range_center = (min_pref + max_pref) / 2
            distance_from_center = abs(value - range_center)
            range_width = (max_pref - min_pref) / 2
            
            if range_width > 0:
                score = 100.0 - (distance_from_center / range_width) * 30.0
            else:
                score = 100.0
            
            return max(70.0, score)  # Minimum 70 for preferred range
        
        else:
            # Value is outside preferred range - calculate penalty
            if value < min_pref:
                distance = min_pref - value
                penalty_range = min_pref * 0.5  # Penalty range
            else:
                distance = value - max_pref
                penalty_range = max_pref * 0.5  # Penalty range
            
            if penalty_range > 0:
                penalty = (distance / penalty_range) * 70.0
                score = 70.0 - min(penalty, 60.0)  # Max penalty of 60 points
            else:
                score = 10.0  # Minimum score
            
            return max(10.0, score)
    
    def calculate_terrain_scores(self, terrain_features: Dict, 
                                behavior_type: str) -> TerrainScoreComponents:
        """
        Calculate comprehensive terrain scores for a behavior type
        
        Args:
            terrain_features: Dictionary of terrain feature values
            behavior_type: Type of behavior to score for
            
        Returns:
            TerrainScoreComponents with individual scores
        """
        # Extract and convert terrain values
        elevation = self.safe_float_conversion(terrain_features.get('elevation'), 0.0)
        slope = self.safe_float_conversion(terrain_features.get('slope'), 0.0)
        aspect = self.safe_float_conversion(terrain_features.get('aspect'), 180.0)
        canopy_closure = self.safe_float_conversion(terrain_features.get('canopy_closure'), 50.0)
        drainage_density = self.safe_float_conversion(terrain_features.get('drainage_density'), 0.5)
        ridge_connectivity = self.safe_float_conversion(terrain_features.get('ridge_connectivity'), 0.3)
        road_distance = self.safe_float_conversion(terrain_features.get('nearest_road_distance'), 500.0)
        
        # Calculate individual terrain scores
        elevation_score = self.score_terrain_feature(elevation, 'elevation', behavior_type)
        slope_score = self.score_terrain_feature(slope, 'slope', behavior_type)
        
        # Aspect scoring (behavior-specific)
        if behavior_type == 'bedding':
            # Prefer north-facing slopes for bedding
            aspect_score = 100.0 if (315 <= aspect <= 360 or 0 <= aspect <= 45) else 50.0
        elif behavior_type == 'feeding':
            # Prefer south-facing slopes for feeding
            aspect_score = 100.0 if (135 <= aspect <= 225) else 60.0
        else:
            # Neutral for travel
            aspect_score = 70.0
        
        # Cover scoring
        if behavior_type == 'bedding':
            cover_score = self.score_terrain_feature(canopy_closure, 'canopy_closure', behavior_type)
        elif behavior_type == 'feeding':
            # For feeding, prefer edge habitats (moderate cover)
            if 30 <= canopy_closure <= 70:
                cover_score = 90.0
            else:
                cover_score = 50.0
        else:
            # Travel prefers moderate cover
            cover_score = 80.0 if 40 <= canopy_closure <= 80 else 60.0
        
        # Drainage scoring
        drainage_score = self.score_terrain_feature(drainage_density, 'drainage_density', behavior_type)
        
        # Connectivity scoring
        connectivity_score = ridge_connectivity * 100.0
        
        # Isolation scoring (higher road distance = better isolation)
        isolation_score = self.normalize_score(road_distance, 0.0, 2000.0) * 100.0
        
        return TerrainScoreComponents(
            elevation_score=elevation_score,
            slope_score=slope_score,
            aspect_score=aspect_score,
            cover_score=cover_score,
            drainage_score=drainage_score,
            connectivity_score=connectivity_score,
            isolation_score=isolation_score
        )
    
    def apply_seasonal_weighting(self, base_score: float, behavior_type: str, 
                                season: str) -> float:
        """
        Apply seasonal weighting to base score
        
        Args:
            base_score: Base score to modify
            behavior_type: Type of behavior
            season: Current season
            
        Returns:
            Seasonally adjusted score
        """
        weights = self.seasonal_weights.get(season, {})
        multiplier = weights.get(behavior_type, 1.0)
        
        return base_score * multiplier
    
    def apply_weather_modifiers(self, base_score: float, behavior_type: str,
                               weather_conditions: List[str]) -> float:
        """
        Apply weather condition modifiers to base score
        
        Args:
            base_score: Base score to modify
            behavior_type: Type of behavior
            weather_conditions: List of current weather conditions
            
        Returns:
            Weather-adjusted score
        """
        total_modifier = 1.0
        
        for condition in weather_conditions:
            modifier = self.weather_modifiers.get(condition, {})
            condition_modifier = modifier.get(behavior_type, 1.0)
            total_modifier *= condition_modifier
        
        return base_score * total_modifier
    
    def calculate_confidence_score(self, terrain_features: Dict, 
                                  context: ScoringContext,
                                  behavior_type: str = "general") -> float:
        """
        Calculate unified confidence score using all factors
        
        Args:
            terrain_features: Terrain analysis results
            context: Scoring context information
            behavior_type: Specific behavior to score for
            
        Returns:
            Confidence score (0-100)
        """
        # Get terrain scores
        terrain_scores = self.calculate_terrain_scores(terrain_features, behavior_type)
        base_terrain_score = terrain_scores.total_score()
        
        # Apply seasonal weighting
        seasonal_score = self.apply_seasonal_weighting(
            base_terrain_score, behavior_type, context.season
        )
        
        # Apply weather modifiers
        weather_adjusted_score = self.apply_weather_modifiers(
            seasonal_score, behavior_type, context.weather_conditions
        )
        
        # Apply pressure penalty
        pressure_penalties = {
            "minimal": 0.0,
            "moderate": -5.0,
            "high": -15.0,
            "extreme": -25.0
        }
        pressure_penalty = pressure_penalties.get(context.pressure_level, -5.0)
        
        # Calculate final confidence
        final_confidence = weather_adjusted_score + pressure_penalty
        
        # Ensure score is within valid range
        return max(0.0, min(100.0, final_confidence))
    
    def calculate_distance_score(self, distance_yards: float, 
                                optimal_range: Tuple[float, float] = (30, 200)) -> float:
        """
        Calculate score based on distance from optimal range
        
        Args:
            distance_yards: Distance in yards
            optimal_range: Tuple of (min_optimal, max_optimal) distances
            
        Returns:
            Distance score (0-100)
        """
        min_optimal, max_optimal = optimal_range
        
        if min_optimal <= distance_yards <= max_optimal:
            # Within optimal range - score based on position in range
            range_center = (min_optimal + max_optimal) / 2
            distance_from_center = abs(distance_yards - range_center)
            range_width = (max_optimal - min_optimal) / 2
            
            if range_width > 0:
                score = 100.0 - (distance_from_center / range_width) * 20.0
            else:
                score = 100.0
            
            return max(80.0, score)
        
        else:
            # Outside optimal range - apply penalty
            if distance_yards < min_optimal:
                # Too close
                penalty = (min_optimal - distance_yards) / min_optimal * 60.0
            else:
                # Too far
                penalty = (distance_yards - max_optimal) / max_optimal * 60.0
            
            score = 80.0 - min(penalty, 70.0)
            return max(10.0, score)
    
    def calculate_wind_favorability(self, stand_direction: float, 
                                   wind_direction: float) -> float:
        """
        Calculate wind favorability score
        
        Args:
            stand_direction: Direction from center to stand (degrees)
            wind_direction: Wind direction (degrees)
            
        Returns:
            Wind favorability score (0-100)
        """
        # Calculate angle difference
        angle_diff = abs(stand_direction - wind_direction)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        
        # Score based on wind angle
        if angle_diff <= 30:  # Excellent wind
            return 90.0
        elif angle_diff <= 60:  # Good wind
            return 75.0
        elif angle_diff <= 90:  # Acceptable wind
            return 60.0
        elif angle_diff <= 120:  # Marginal wind
            return 40.0
        else:  # Poor wind
            return 25.0
    
    def convert_score_type(self, score: float, from_type: ScoreType, 
                          to_type: ScoreType) -> float:
        """
        Convert between different score types
        
        Args:
            score: Score to convert
            from_type: Original score type
            to_type: Target score type
            
        Returns:
            Converted score
        """
        # Normalize to 0-1 first
        if from_type == ScoreType.CONFIDENCE:
            normalized = score / 100.0
        elif from_type == ScoreType.RATING:
            normalized = score / 10.0
        elif from_type == ScoreType.PROBABILITY:
            normalized = score
        elif from_type == ScoreType.NORMALIZED:
            normalized = score
        else:
            normalized = score / 100.0  # Default to confidence
        
        # Convert to target type
        if to_type == ScoreType.CONFIDENCE:
            return normalized * 100.0
        elif to_type == ScoreType.RATING:
            return normalized * 10.0
        elif to_type == ScoreType.PROBABILITY:
            return normalized
        elif to_type == ScoreType.NORMALIZED:
            return normalized
        else:
            return normalized * 100.0  # Default to confidence


# Global scoring engine instance
_scoring_engine = None

def get_scoring_engine() -> ScoringEngine:
    """Get global scoring engine instance (singleton pattern)"""
    global _scoring_engine
    if _scoring_engine is None:
        _scoring_engine = ScoringEngine()
    return _scoring_engine


# Convenience functions for common scoring operations
def score_terrain_suitability(terrain_features: Dict, behavior_type: str) -> float:
    """Quick terrain suitability scoring"""
    engine = get_scoring_engine()
    scores = engine.calculate_terrain_scores(terrain_features, behavior_type)
    return scores.total_score()

def score_with_context(terrain_features: Dict, context: ScoringContext, 
                      behavior_type: str = "general") -> float:
    """Quick contextual confidence scoring"""
    engine = get_scoring_engine()
    return engine.calculate_confidence_score(terrain_features, context, behavior_type)

def normalize_value(value: float, min_val: float, max_val: float, 
                   invert: bool = False) -> float:
    """Quick value normalization"""
    engine = get_scoring_engine()
    return engine.normalize_score(value, min_val, max_val, invert)
