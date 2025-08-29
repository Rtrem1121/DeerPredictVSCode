#!/usr/bin/env python3
"""
Enhanced Mature Buck Terrain Analysis

This module provides improved terrain analysis algorithms specifically
optimized for mature buck behavior patterns with better score differentiation.
NOW INCLUDES REAL OSM SECURITY DATA INTEGRATION.
"""

import numpy as np
import logging
from typing import Dict, List, Tuple

# Initialize logger at module level to prevent assignment issues
logger = logging.getLogger(__name__)

def enhanced_terrain_analysis(terrain_features: Dict, lat: float, lon: float) -> Dict[str, float]:
    """
    Enhanced terrain analysis for mature bucks with REAL OSM security integration
    
    Args:
        terrain_features: Terrain data
        lat: Latitude
        lon: Longitude
        
    Returns:
        Enhanced terrain scores with REAL security analysis
    """
    
    # **INTEGRATE REAL OSM SECURITY ANALYSIS**
    logger.info(f"🔍 Enhanced analysis: Starting REAL OSM security integration for {lat:.6f}, {lon:.6f}")
    
    try:
        from .real_osm_security import get_real_osm_security
        osm_security = get_real_osm_security()
        security_analysis = osm_security.get_comprehensive_security_data(lat, lon, radius=2000)
        logger.info(f"✅ Real OSM security data obtained: {len(security_analysis.get('parking_areas', []))}P "
                   f"{len(security_analysis.get('trail_networks', []))}T "
                   f"{len(security_analysis.get('road_network', []))}R "
                   f"{len(security_analysis.get('buildings', []))}B")
    except Exception as e:
        logger.warning(f"⚠️ OSM security integration failed: {e}")
        security_analysis = {'overall_security_score': 50.0, 'data_source': 'osm_failed'}
    
    # Extract terrain parameters with defaults and safe conversion
    def safe_float(value, default):
        """Safely convert value to float, handling arrays"""
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) > 0:
                return float(value[0]) if hasattr(value[0], '__float__') else default
            return default
        return float(value) if value is not None else default
    
    elevation = safe_float(terrain_features.get('elevation'), 800)
    slope = safe_float(terrain_features.get('slope'), 5)
    aspect = safe_float(terrain_features.get('aspect'), 180)
    cover_density = safe_float(terrain_features.get('cover_density'), 0.6)
    water_proximity = safe_float(terrain_features.get('water_proximity'), 300)
    terrain_ruggedness = safe_float(terrain_features.get('terrain_ruggedness'), 0.3)
    
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
    
    # 3. ENHANCED ISOLATION SCORE (0-100) - Use road distance calculation
    isolation_score = 0
    
    # Use road distance calculation (primary factor for isolation)
    road_distance = terrain_features.get('nearest_road_distance', 1000.0)  # meters
    road_distance_yards = road_distance * 1.094  # Convert to yards
    
    # Road distance impact (same logic as distance_scorer.py)
    road_impact_range = 500.0  # yards
    if road_distance_yards >= road_impact_range:
        isolation_score = 95.0  # Very isolated (far from roads)
    elif road_distance_yards >= road_impact_range * 0.7:  # >= 350 yards
        isolation_score = 70.0 + (road_distance_yards / road_impact_range * 25.0)
    elif road_distance_yards >= road_impact_range * 0.3:  # >= 150 yards
        isolation_score = 40.0 + (road_distance_yards / (road_impact_range * 0.7) * 30.0)
    else:
        isolation_score = 10.0 + (road_distance_yards / (road_impact_range * 0.3) * 30.0)
    
    scores['isolation_score'] = min(isolation_score, 100)
    
    # 4. ENHANCED PRESSURE RESISTANCE (0-100) - Use enhanced terrain features
    pressure_score = 0.0
    
    # Use enhanced terrain features if available
    escape_cover_density = terrain_features.get('escape_cover_density', cover_density * 100)
    hunter_accessibility = terrain_features.get('hunter_accessibility', 0.7)
    wetland_proximity = terrain_features.get('wetland_proximity', 1000.0)
    cliff_proximity = terrain_features.get('cliff_proximity', 1000.0)
    visibility_limitation = terrain_features.get('visibility_limitation', 0.5)
    
    # Thick escape cover
    if escape_cover_density >= 80.0:
        pressure_score += 30.0
    elif escape_cover_density >= 60.0:
        pressure_score += 20.0
    
    # Terrain that's difficult for hunters to access
    if hunter_accessibility <= 0.3:  # Very difficult access
        pressure_score += 25.0
    elif hunter_accessibility <= 0.5:
        pressure_score += 15.0
    
    # Swampland and wetlands (natural barriers)
    if wetland_proximity <= 100:
        pressure_score += 20.0
    elif wetland_proximity <= 300:
        pressure_score += 10.0
    
    # Cliff faces and steep terrain
    if cliff_proximity <= 200:
        pressure_score += 15.0
    
    # Dense understory that limits visibility
    if visibility_limitation >= 0.8:
        pressure_score += 10.0
    
    scores['pressure_resistance'] = min(pressure_score, 100)
    
    # DEBUG: Log the calculated pressure resistance for debugging
    logger.info(f"🔍 Enhanced accuracy pressure resistance calculation: {pressure_score:.1f} for coordinates {lat:.6f}, {lon:.6f}")
    logger.info(f"🔍 Enhanced accuracy final scores: isolation={scores.get('isolation_score', 0):.1f}, pressure={scores.get('pressure_resistance', 0):.1f}")
    
    # 5. CALCULATE ENHANCED OVERALL SUITABILITY
    # **INTEGRATE REAL OSM SECURITY SCORES**
    # Get OSM security score (0-100 scale, higher = more secure)
    osm_security_score = security_analysis.get('overall_security_score', 50.0)
    
    # Enhanced weights that include REAL security data (critical for mature bucks)
    weights = {
        'bedding_suitability': 0.25,    # Reduced to make room for security
        'escape_route_quality': 0.25,   # Reduced to make room for security  
        'isolation_score': 0.15,        # Reduced to make room for security
        'pressure_resistance': 0.10,    # Reduced to make room for security
        'osm_security_score': 0.25      # NEW: Real OSM security data (CRITICAL for mature bucks)
    }
    
    # Add OSM security score to the scores dict
    scores['osm_security_score'] = osm_security_score
    scores['security_analysis'] = security_analysis  # Include full security analysis
    
    # Calculate overall with REAL security integration
    overall = sum(scores.get(key, 50.0) * weights[key] for key in weights.keys())
    
    # Apply REAL security threat penalties (mature bucks are extremely security conscious)
    threat_categories = security_analysis.get('threat_categories', {})
    
    security_penalties = {
        'extreme': -20.0,  # Extreme threat = major penalty
        'high': -12.0,     # High threat = significant penalty
        'moderate': -4.0,  # Moderate threat = minor penalty
        'low': 0.0         # Low threat = no penalty
    }
    
    # Access threats are CRITICAL for mature bucks (parking areas are the worst)
    access_threat = threat_categories.get('access_threats', {}).get('threat_level', 'unknown')
    if access_threat in security_penalties:
        penalty = security_penalties[access_threat] * 1.5  # 1.5x penalty for access threats
        overall += penalty
        if penalty < 0:
            logger.info(f"🚗 OSM Access threat penalty: {penalty:.1f} points ({access_threat})")
    
    # Road threats are also very important
    road_threat = threat_categories.get('road_threats', {}).get('threat_level', 'unknown')  
    if road_threat in security_penalties:
        penalty = security_penalties[road_threat] * 1.2  # 1.2x penalty for road threats
        overall += penalty
        if penalty < 0:
            logger.info(f"🛣️ OSM Road threat penalty: {penalty:.1f} points ({road_threat})")
    
    # Trail and structure threats
    for threat_type, category_key in [('trail', 'trail_threats'), ('structure', 'structure_threats')]:
        threat_level = threat_categories.get(category_key, {}).get('threat_level', 'unknown')
        if threat_level in security_penalties:
            penalty = security_penalties[threat_level]
            overall += penalty
            if penalty < 0:
                logger.info(f"🏠 OSM {threat_type.title()} threat penalty: {penalty:.1f} points ({threat_level})")
    
    # Bonus for truly remote areas (no infrastructure detected)
    osm_data = security_analysis.get('real_osm_data', {})
    if osm_data and security_analysis.get('data_source') != 'osm_failed':
        total_features = (len(osm_data.get('parking_areas', [])) + 
                        len(osm_data.get('trail_networks', [])) + 
                        len(osm_data.get('road_network', [])) + 
                        len(osm_data.get('buildings', [])))
        
        if total_features == 0:
            overall += 8.0  # Bonus for truly remote areas
            logger.info("✅ OSM Remote area bonus: +8.0 points (no infrastructure)")
        elif total_features < 3:
            overall += 4.0   # Bonus for very low infrastructure
            logger.info(f"✅ OSM Low infrastructure bonus: +4.0 points ({total_features} features)")
    
    scores['overall_suitability'] = min(max(overall, 0.0), 100.0)
    
    # Add enhanced metadata
    scores['enhancement_level'] = 'advanced_with_real_osm_security'
    scores['algorithm_version'] = '3.0_real_data'
    
    logger.info(f"Enhanced terrain analysis complete - Overall: {scores['overall_suitability']:.1f}%")
    logger.info(f"🔒 OSM Security Score: {scores.get('osm_security_score', 'N/A'):.1f}%, "
               f"Data Source: {security_analysis.get('data_source', 'unknown')}")
    
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
    
    # Safe float conversion helper
    def safe_float(value, default):
        """Safely convert value to float, handling arrays"""
        if isinstance(value, (list, tuple, np.ndarray)):
            if len(value) > 0:
                return float(value[0]) if hasattr(value[0], '__float__') else default
            return default
        return float(value) if value is not None else default
    
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
    temp = safe_float(weather_data.get('temp'), 45)
    wind_speed = safe_float(weather_data.get('wind_speed'), 5)
    pressure = safe_float(weather_data.get('pressure'), 30.0)
    
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
    elevation = safe_float(terrain_features.get('elevation'), 800)
    cover_density = safe_float(terrain_features.get('cover_density'), 0.6)
    
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
