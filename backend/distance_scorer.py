#!/usr/bin/env python3
"""
Distance and Proximity Scoring Module

This module provides specialized scoring functions for distance-based
evaluations including roads, agricultural areas, stands, and escape routes.

Key Features:
- Road proximity impact scoring
- Agricultural area distance evaluation
- Stand placement optimization scoring
- Escape route accessibility scoring
- Stealth and concealment distance factors

Author: Vermont Deer Prediction System  
Version: 1.0.0
"""

import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging

# Import configuration management
try:
    from .config_manager import get_config
except ImportError:
    from config_manager import get_config

logger = logging.getLogger(__name__)

@dataclass
class ProximityFactors:
    """Configuration for proximity-based scoring - now loaded from config"""
    
    def __init__(self):
        """Initialize proximity factors from configuration"""
        config = get_config()
        distance_params = config.get_distance_parameters()
        
        self.road_impact_range = distance_params.get('road_impact_range', 500.0)
        self.agricultural_benefit_range = distance_params.get('agricultural_benefit_range', 800.0)
        self.stand_optimal_min = distance_params.get('stand_optimal_min', 30.0)
        self.stand_optimal_max = distance_params.get('stand_optimal_max', 200.0)
        self.escape_route_max = distance_params.get('escape_route_max', 300.0)
        self.concealment_critical = distance_params.get('concealment_critical', 100.0)

class DistanceScorer:
    """
    Specialized scoring for distance-based evaluations
    """
    
    def __init__(self, proximity_factors: Optional[ProximityFactors] = None):
        """Initialize distance scorer with configuration"""
        self.factors = proximity_factors or ProximityFactors()
        logger.info("📏 Distance Scorer initialized with configuration")
    
    def safe_distance_conversion(self, value: Any, default: float = 0.0) -> float:
        """Safely convert distance value to float"""
        try:
            if isinstance(value, (list, tuple, np.ndarray)):
                if len(value) > 0:
                    return float(value[0])
                return default
            return float(value) if value is not None else default
        except (ValueError, TypeError):
            return default
    
    def calculate_road_impact_score(self, road_distance_yards: float) -> float:
        """
        Calculate road impact score (higher distance = better score)
        
        Args:
            road_distance_yards: Distance to nearest road in yards
            
        Returns:
            Road impact score (0-100)
        """
        distance = self.safe_distance_conversion(road_distance_yards, 0.0)
        
        scoring_ranges = [
            (self.factors.road_impact_range, lambda d: 95.0),
            (self.factors.road_impact_range * 0.7, lambda d: 70.0 + (d / self.factors.road_impact_range * 25.0)),
            (self.factors.road_impact_range * 0.3, lambda d: 40.0 + (d / (self.factors.road_impact_range * 0.7) * 30.0)),
            (0, lambda d: 10.0 + (d / (self.factors.road_impact_range * 0.3) * 30.0)),
        ]

        for threshold, score_func in scoring_ranges:
            if distance >= threshold:
                return score_func(distance)
        return 0.0
    
    def calculate_agricultural_proximity_score(self, ag_distance_yards: float) -> float:
        """
        Calculate agricultural proximity benefit score
        
        Args:
            ag_distance_yards: Distance to nearest agricultural area in yards
            
        Returns:
            Agricultural proximity score (0-100)
        """
        distance = self.safe_distance_conversion(ag_distance_yards, 1000.0)
        
        if distance <= 100.0:
            return 95.0
        elif distance <= 300.0:
            ratio = (300.0 - distance) / 200.0
            return 75.0 + (ratio * 20.0)
        elif distance <= self.factors.agricultural_benefit_range:
            ratio = (self.factors.agricultural_benefit_range - distance) / 500.0
            return 50.0 + (ratio * 25.0)
        else:
            max_penalty_distance = self.factors.agricultural_benefit_range * 2
            if distance <= max_penalty_distance:
                ratio = (max_penalty_distance - distance) / self.factors.agricultural_benefit_range
                return 25.0 + (ratio * 25.0)
            else:
                return 25.0
    
    def calculate_stand_placement_score(self, stand_distance_yards: float) -> float:
        """
        Calculate optimal stand placement distance score
        
        Args:
            stand_distance_yards: Distance to stand in yards
            
        Returns:
            Stand placement score (0-100)
        """
        distance = self.safe_distance_conversion(stand_distance_yards, 100.0)
        
        scoring_ranges = [
            (self.factors.stand_optimal_min, lambda d: 20.0 + (d / self.factors.stand_optimal_min * 65.0) if d > 10.0 else 20.0),
            (self.factors.stand_optimal_max, lambda d: 100.0 - (abs(d - (self.factors.stand_optimal_min + self.factors.stand_optimal_max) / 2) / ((self.factors.stand_optimal_max - self.factors.stand_optimal_min) / 2) * 15.0) if (self.factors.stand_optimal_max - self.factors.stand_optimal_min) > 0 else 100.0),
            (self.factors.stand_optimal_max * 2, lambda d: 40.0 + ((self.factors.stand_optimal_max * 2 - d) / self.factors.stand_optimal_max * 45.0)),
        ]

        for threshold, score_func in scoring_ranges:
            if distance <= threshold:
                return max(25.0, score_func(distance))
        return 25.0
    
    def calculate_escape_route_score(self, escape_distance_yards: float) -> float:
        """
        Calculate escape route accessibility score
        
        Args:
            escape_distance_yards: Distance to nearest escape route in yards
            
        Returns:
            Escape route score (0-100)
        """
        distance = self.safe_distance_conversion(escape_distance_yards, 200.0)
        
        scoring_ranges = [
            (50.0, lambda d: 95.0),
            (150.0, lambda d: 75.0 + ((150.0 - d) / 100.0 * 20.0)),
            (self.factors.escape_route_max, lambda d: 50.0 + ((self.factors.escape_route_max - d) / 150.0 * 25.0)),
            (self.factors.escape_route_max * 2, lambda d: 20.0 + ((self.factors.escape_route_max * 2 - d) / self.factors.escape_route_max * 30.0)),
        ]

        for threshold, score_func in scoring_ranges:
            if distance <= threshold:
                return score_func(distance)
        return 20.0
    
    def calculate_concealment_score(self, visibility_distance_yards: float) -> float:
        """
        Calculate concealment score based on visibility distance
        
        Args:
            visibility_distance_yards: Maximum visibility distance in yards
            
        Returns:
            Concealment score (0-100)
        """
        distance = self.safe_distance_conversion(visibility_distance_yards, 50.0)
        
        scoring_ranges = [
            (30.0, lambda d: 95.0),
            (60.0, lambda d: 80.0 + ((60.0 - d) / 30.0 * 15.0)),
            (self.factors.concealment_critical, lambda d: 60.0 + ((self.factors.concealment_critical - d) / 40.0 * 20.0)),
            (200.0, lambda d: 30.0 + ((200.0 - d) / 100.0 * 30.0)),
        ]

        for threshold, score_func in scoring_ranges:
            if distance <= threshold:
                return score_func(distance)
        return 20.0
    
    def calculate_water_proximity_score(self, water_distance_yards: float) -> float:
        """
        Calculate water source proximity score
        
        Args:
            water_distance_yards: Distance to nearest water source in yards
            
        Returns:
            Water proximity score (0-100)
        """
        distance = self.safe_distance_conversion(water_distance_yards, 500.0)
        
        scoring_ranges = [
            (100.0, lambda d: 90.0),
            (300.0, lambda d: 70.0 + ((300.0 - d) / 200.0 * 20.0)),
            (800.0, lambda d: 45.0 + ((800.0 - d) / 500.0 * 25.0)),
            (1500.0, lambda d: 20.0 + ((1500.0 - d) / 700.0 * 25.0)),
        ]

        for threshold, score_func in scoring_ranges:
            if distance <= threshold:
                return score_func(distance)
        return 20.0
    
    def calculate_terrain_edge_score(self, edge_distance_yards: float, 
                                   edge_type: str = "forest_field") -> float:
        """
        Calculate terrain edge proximity score
        
        Args:
            edge_distance_yards: Distance to terrain edge in yards
            edge_type: Type of edge (forest_field, timber_opening, etc.)
            
        Returns:
            Edge proximity score (0-100)
        """
        distance = self.safe_distance_conversion(edge_distance_yards, 200.0)
        
        edge_quality = {
            "forest_field": 1.0,
            "timber_opening": 0.9,
            "water_edge": 1.1,
            "thick_thin": 0.8,
            "elevation_change": 0.7
        }
        
        quality_modifier = edge_quality.get(edge_type, 1.0)
        
        scoring_ranges = [
            (50.0, lambda d: 90.0),
            (150.0, lambda d: 70.0 + ((150.0 - d) / 100.0 * 20.0)),
            (400.0, lambda d: 45.0 + ((400.0 - d) / 250.0 * 25.0)),
        ]

        for threshold, score_func in scoring_ranges:
            if distance <= threshold:
                return score_func(distance) * quality_modifier
        return 30.0 * quality_modifier
    
    def calculate_thermal_corridor_score(self, thermal_distance_yards: float) -> float:
        """
        Calculate thermal corridor proximity score
        
        Args:
            thermal_distance_yards: Distance to thermal corridor in yards
            
        Returns:
            Thermal corridor score (0-100)
        """
        distance = self.safe_distance_conversion(thermal_distance_yards, 300.0)
        
        if distance <= 75.0:
            # Very close to thermal corridor - excellent
            return 85.0
        elif distance <= 200.0:
            # Close to thermal corridor - good
            ratio = (200.0 - distance) / 125.0
            return 65.0 + (ratio * 20.0)
        elif distance <= 500.0:
            # Moderate thermal access
            ratio = (500.0 - distance) / 300.0
            return 40.0 + (ratio * 25.0)
        else:
            # Poor thermal access
            return 30.0
    
    def calculate_composite_distance_score(self, distances: Dict[str, float],
                                         weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calculate composite score from multiple distance factors
        
        Args:
            distances: Dictionary of distance measurements
            weights: Optional weights for each distance factor
            
        Returns:
            Composite distance score (0-100)
        """
        if weights is None:
            weights = {
                'road': 0.20,
                'agricultural': 0.25,
                'water': 0.15,
                'escape_route': 0.15,
                'concealment': 0.15,
                'edge': 0.10
            }
        
        total_score = 0.0
        total_weight = 0.0
        
        # Calculate individual scores
        score_calculations = {
            'road': lambda d: self.calculate_road_impact_score(d),
            'agricultural': lambda d: self.calculate_agricultural_proximity_score(d),
            'water': lambda d: self.calculate_water_proximity_score(d),
            'escape_route': lambda d: self.calculate_escape_route_score(d),
            'concealment': lambda d: self.calculate_concealment_score(d),
            'edge': lambda d: self.calculate_terrain_edge_score(d),
            'thermal': lambda d: self.calculate_thermal_corridor_score(d)
        }
        
        for factor, distance in distances.items():
            if factor in score_calculations and factor in weights:
                score_func = score_calculations[factor]
                individual_score = score_func(distance)
                weight = weights[factor]
                
                total_score += individual_score * weight
                total_weight += weight
        
        # Normalize by total weight
        if total_weight > 0:
            return total_score / total_weight
        else:
            return 50.0  # Default moderate score


# Global distance scorer instance
_distance_scorer = None

def get_distance_scorer() -> DistanceScorer:
    """Get global distance scorer instance (singleton pattern)"""
    global _distance_scorer
    if _distance_scorer is None:
        _distance_scorer = DistanceScorer()
    return _distance_scorer