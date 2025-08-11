#!/usr/bin/env python3
"""
Enhanced Mature Buck Terrain Analysis

This module provides improved terrain analysis algorithms specifically
optimized for mature buck behavior patterns with better score differentiation.
"""

import numpy as np
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

def enhanced_terrain_analysis(terrain_features: Dict, lat: float, lon: float) -> Dict[str, float]:
    """
    Enhanced terrain analysis for mature bucks with improved accuracy
    
    Args:
        terrain_features: Terrain data
        lat: Latitude
        lon: Longitude
        
    Returns:
        Enhanced terrain scores
    """
    
    # Extract terrain parameters with defaults
    elevation = terrain_features.get('elevation', 800)
    slope = terrain_features.get('slope', 5)
    aspect = terrain_features.get('aspect', 180)
    cover_density = terrain_features.get('cover_density', 0.6)
    water_proximity = terrain_features.get('water_proximity', 300)
    terrain_ruggedness = terrain_features.get('terrain_ruggedness', 0.3)
    
    scores = {}
    
    # 1. ENHANCED BEDDING SUITABILITY (0-100)
    bedding_score = 0
    
    # Elevation preference (mature bucks prefer mid to high elevations)
    if 1000 <= elevation <= 1800:
        bedding_score += 25  # Optimal elevation range
    elif 800 <= elevation < 1000 or 1800 < elevation <= 2200:
        bedding_score += 15  # Good elevation range
    else:
        bedding_score += 5   # Poor elevation range
    
    # Slope preference (moderate slopes for bedding)
    if 8 <= slope <= 20:
        bedding_score += 25  # Optimal slope
    elif 5 <= slope < 8 or 20 < slope <= 30:
        bedding_score += 15  # Moderate slope
    else:
        bedding_score += 5   # Poor slope
    
    # Cover density (mature bucks need thick cover)
    if cover_density >= 0.8:
        bedding_score += 30  # Excellent cover
    elif cover_density >= 0.7:
        bedding_score += 20  # Good cover
    elif cover_density >= 0.5:
        bedding_score += 10  # Fair cover
    else:
        bedding_score += 0   # Poor cover
    
    # Aspect bonus (north/east facing for thermal regulation)
    if 315 <= aspect <= 360 or 0 <= aspect <= 90:
        bedding_score += 20  # North/East facing bonus
    elif 90 < aspect <= 180:
        bedding_score += 10  # South facing - moderate
    else:
        bedding_score += 5   # West facing - less ideal
    
    scores['bedding_suitability'] = min(bedding_score, 100)
    
    # 2. ENHANCED ESCAPE ROUTE QUALITY (0-100)
    escape_score = 0
    
    # Terrain ruggedness (more escape options)
    if terrain_ruggedness >= 0.7:
        escape_score += 35   # Excellent escape terrain
    elif terrain_ruggedness >= 0.5:
        escape_score += 25   # Good escape terrain
    elif terrain_ruggedness >= 0.3:
        escape_score += 15   # Fair escape terrain
    else:
        escape_score += 5    # Poor escape terrain
    
    # Slope contributes to escape routes
    if slope >= 15:
        escape_score += 30   # Steep terrain provides escape options
    elif slope >= 8:
        escape_score += 20   # Moderate slopes
    else:
        escape_score += 10   # Gentle terrain
    
    # Multiple elevation levels nearby (implied by high elevation + slope)
    if elevation > 1200 and slope > 12:
        escape_score += 35   # Mountain terrain with excellent escape options
    elif elevation > 800 and slope > 8:
        escape_score += 20   # Hill terrain with good options
    else:
        escape_score += 10   # Limited escape options
    
    scores['escape_route_quality'] = min(escape_score, 100)
    
    # 3. ENHANCED ISOLATION SCORE (0-100)
    isolation_score = 0
    
    # Remote elevation bonus
    if elevation > 1500:
        isolation_score += 40  # High elevation = more remote
    elif elevation > 1000:
        isolation_score += 25  # Moderate elevation
    else:
        isolation_score += 10  # Lower elevation = more accessible
    
    # Dense cover provides isolation
    if cover_density >= 0.8:
        isolation_score += 30  # Very isolated
    elif cover_density >= 0.6:
        isolation_score += 20  # Moderately isolated
    else:
        isolation_score += 10  # Less isolated
    
    # Difficult terrain reduces human access
    if terrain_ruggedness >= 0.6 and slope >= 15:
        isolation_score += 30  # Very difficult access
    elif terrain_ruggedness >= 0.4 or slope >= 10:
        isolation_score += 20  # Moderate access difficulty
    else:
        isolation_score += 10  # Easy access
    
    scores['isolation_score'] = min(isolation_score, 100)
    
    # 4. ENHANCED PRESSURE RESISTANCE (0-100)
    pressure_score = 0
    
    # Thick cover provides pressure resistance
    if cover_density >= 0.85:
        pressure_score += 35  # Excellent cover
    elif cover_density >= 0.7:
        pressure_score += 25  # Good cover
    else:
        pressure_score += 10  # Poor cover
    
    # Complex terrain helps avoid pressure
    if terrain_ruggedness >= 0.6:
        pressure_score += 25  # Complex terrain
    elif terrain_ruggedness >= 0.4:
        pressure_score += 15  # Moderate complexity
    else:
        pressure_score += 5   # Simple terrain
    
    # Multiple escape routes
    if slope >= 12 and terrain_ruggedness >= 0.5:
        pressure_score += 25  # Excellent escape options
    elif slope >= 8 or terrain_ruggedness >= 0.3:
        pressure_score += 15  # Good escape options
    else:
        pressure_score += 5   # Limited escape options
    
    # Water proximity (too close = pressure, too far = problem)
    if 150 <= water_proximity <= 400:
        pressure_score += 15  # Optimal water distance
    elif 100 <= water_proximity < 150 or 400 < water_proximity <= 600:
        pressure_score += 10  # Moderate water distance
    else:
        pressure_score += 5   # Poor water distance
    
    scores['pressure_resistance'] = min(pressure_score, 100)
    
    # 5. CALCULATE ENHANCED OVERALL SUITABILITY
    weights = {
        'bedding_suitability': 0.35,
        'escape_route_quality': 0.30,
        'isolation_score': 0.20,
        'pressure_resistance': 0.15
    }
    
    overall = sum(scores[key] * weights[key] for key in weights.keys())
    scores['overall_suitability'] = min(overall, 100.0)
    
    # Add enhanced metadata
    scores['enhancement_level'] = 'advanced'
    scores['algorithm_version'] = '2.0'
    
    logger.info(f"Enhanced terrain analysis complete - Overall: {scores['overall_suitability']:.1f}%")
    
    return scores

def enhanced_movement_prediction(season: str, time_of_day: int, terrain_features: Dict, 
                               weather_data: Dict) -> Dict[str, float]:
    """
    Enhanced movement prediction with improved accuracy
    
    Args:
        season: Hunting season
        time_of_day: Hour (0-23)
        terrain_features: Terrain data
        weather_data: Weather conditions
        
    Returns:
        Enhanced movement prediction
    """
    
    base_movement = 30  # Base movement probability
    
    # TIME OF DAY FACTORS (Enhanced)
    if season == "early_season":
        if 5 <= time_of_day <= 8:      # Dawn
            base_movement += 45
        elif 16 <= time_of_day <= 19:  # Dusk
            base_movement += 40
        elif 9 <= time_of_day <= 15:   # Midday
            base_movement += 5
        else:                          # Night
            base_movement += 15
            
    elif season == "rut":
        if 5 <= time_of_day <= 10:     # Morning rut activity
            base_movement += 50
        elif 11 <= time_of_day <= 16:  # Midday rut movement
            base_movement += 35
        elif 17 <= time_of_day <= 20:  # Evening rut
            base_movement += 45
        else:                          # Night rut activity
            base_movement += 25
            
    elif season == "late_season":
        if 6 <= time_of_day <= 9:      # Late dawn
            base_movement += 35
        elif 15 <= time_of_day <= 18:  # Early dusk
            base_movement += 40
        elif 10 <= time_of_day <= 14:  # Midday feeding
            base_movement += 20
        else:                          # Night
            base_movement += 10
    
    # WEATHER FACTORS (Enhanced)
    temp = weather_data.get('temp', 45)
    wind_speed = weather_data.get('wind_speed', 5)
    pressure = weather_data.get('pressure', 30.0)
    
    # Temperature effects
    if season == "early_season":
        if 45 <= temp <= 65:
            base_movement += 15  # Optimal early season temps
        elif temp < 35 or temp > 75:
            base_movement -= 10  # Extreme temperatures
    elif season == "late_season":
        if 25 <= temp <= 45:
            base_movement += 20  # Cold weather movement
        elif temp > 55:
            base_movement -= 15  # Too warm for late season
    
    # Wind effects
    if wind_speed <= 8:
        base_movement += 10  # Calm conditions
    elif wind_speed > 15:
        base_movement -= 15  # High wind reduces movement
    
    # Barometric pressure
    if pressure >= 30.2:
        base_movement += 10  # High pressure
    elif pressure <= 29.8:
        base_movement -= 10  # Low pressure (storm coming)
    
    # TERRAIN EFFECTS
    elevation = terrain_features.get('elevation', 800)
    cover_density = terrain_features.get('cover_density', 0.6)
    
    # Elevation effects on movement
    if 800 <= elevation <= 1500:
        base_movement += 10  # Optimal elevation for movement
    elif elevation > 2000:
        base_movement -= 10  # Very high elevation reduces movement
    
    # Cover density effects
    if 0.6 <= cover_density <= 0.8:
        base_movement += 10  # Good cover encourages movement
    elif cover_density > 0.9:
        base_movement -= 5   # Too thick cover restricts movement
    
    movement_probability = max(0, min(100, base_movement))
    
    # Enhanced confidence calculation
    confidence_factors = {
        'time_certainty': 0.3,
        'weather_certainty': 0.3,
        'terrain_certainty': 0.2,
        'seasonal_certainty': 0.2
    }
    
    # Calculate confidence based on data quality
    base_confidence = 50
    
    # Time certainty (peak times are more certain)
    if ((5 <= time_of_day <= 8) or (16 <= time_of_day <= 19)) and season != "rut":
        base_confidence += 20
    elif season == "rut" and 5 <= time_of_day <= 10:
        base_confidence += 25
    
    # Weather certainty (stable conditions are more predictable)
    if 30.0 <= pressure <= 30.3 and wind_speed <= 10:
        base_confidence += 15
    
    # Terrain certainty (familiar terrain types)
    if 800 <= elevation <= 1800 and 0.5 <= cover_density <= 0.8:
        base_confidence += 15
    
    confidence_score = max(30, min(95, base_confidence))
    
    return {
        'movement_probability': movement_probability,
        'confidence_score': confidence_score,
        'enhancement_level': 'advanced',
        'algorithm_version': '2.0'
    }
