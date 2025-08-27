#!/usr/bin/env python3
"""
Test Fix for Deer Approach Direction Bug

This module tests the fix for the hardcoded SE (135°) deer approach direction
that should be calculated dynamically based on terrain and bedding zones.
"""

import math
from typing import Dict, List, Tuple, Optional

def calculate_terrain_based_deer_approach(terrain_features: Dict, stand_coords: Dict, 
                                        stand_type: str) -> Tuple[float, str]:
    """
    Calculate deer approach direction based on terrain features when bedding zones aren't available
    
    Args:
        terrain_features: Terrain analysis results
        stand_coords: Stand coordinates {'lat': float, 'lon': float}
        stand_type: Type of stand (bedding, feeding, travel corridor, etc.)
    
    Returns:
        Tuple of (bearing_degrees, compass_direction)
    """
    
    # Get terrain characteristics
    aspect = terrain_features.get('aspect', 0)
    slope = terrain_features.get('slope', 0) 
    elevation = terrain_features.get('elevation', 1000)
    terrain_type = terrain_features.get('terrain_type', 'mixed')
    
    # Default approach bearing - will be modified based on terrain
    approach_bearing = 180.0  # Default to south approach
    
    # Stand type specific logic
    if stand_type == "Travel Corridor":
        # Travel corridors: deer approach from bedding (typically higher/north) to feeding (lower/south)
        if 'ridge' in terrain_type.lower() or 'saddle' in terrain_type.lower():
            # On ridges/saddles, deer typically approach from N/NE (bedding areas)
            approach_bearing = 45.0  # NE approach
        elif 'valley' in terrain_type.lower() or 'creek' in terrain_type.lower():
            # In valleys, deer approach from sides (E/W) or uphill
            approach_bearing = 270.0 if aspect < 180 else 90.0  # W or E approach
        else:
            # Default corridor - approach from higher elevation
            approach_bearing = 0.0 if slope > 10 else 180.0  # N or S
            
    elif stand_type == "Bedding Area":
        # Bedding areas: deer approach from feeding areas (typically lower/agricultural)
        if slope > 15:
            # Steep terrain - deer approach from below
            approach_bearing = 180.0  # South approach (from valleys)
        else:
            # Gentle terrain - approach from feeding areas
            approach_bearing = 135.0 if 'agricultural' in terrain_type else 225.0
            
    elif stand_type == "Feeding Area":
        # Feeding areas: deer approach from bedding (typically higher/thicker cover)
        if terrain_features.get('forest_edge', False):
            # Field edge - deer come from forest (typically north in Vermont)
            approach_bearing = 0.0  # North approach from forest
        elif slope > 10:
            # Sloped feeding area - deer approach from uphill bedding
            approach_bearing = aspect + 180  # Opposite of slope aspect
        else:
            # Flat feeding area - approach from nearest cover
            approach_bearing = 315.0  # NW approach (typical forest direction)
    
    else:  # General stand
        # Use terrain features to determine most likely approach
        if 'ridge' in terrain_type.lower():
            approach_bearing = 90.0  # E approach along ridge
        elif 'valley' in terrain_type.lower():
            approach_bearing = 0.0   # N approach down valley
        elif slope > 15:
            # Steep terrain - approach from downhill
            approach_bearing = aspect  # Same direction as slope faces
        else:
            # Gentle terrain - use aspect-based approach
            if 90 <= aspect <= 270:  # East to west facing slopes
                approach_bearing = aspect + 180  # Approach from behind slope
            else:  # North/south facing slopes
                approach_bearing = 135.0  # Default SE approach
    
    # Normalize bearing to 0-360 range
    approach_bearing = approach_bearing % 360
    
    # Convert to compass direction
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    compass_dir = directions[int((approach_bearing + 11.25) / 22.5) % 16]
    
    return approach_bearing, compass_dir

def enhanced_deer_approach_calculation(prediction_data: Dict) -> Tuple[float, str]:
    """
    Enhanced deer approach calculation that tries multiple methods
    
    Args:
        prediction_data: Full prediction response from backend
        
    Returns:
        Tuple of (bearing_degrees, compass_direction)
    """
    
    # Method 1: Try bedding zone calculation (existing logic)
    bedding_zones = prediction_data.get('bedding_zones', {}).get('zones', [])
    stand_coords = prediction_data.get('coordinates', {})
    
    if bedding_zones and stand_coords.get('lat') and stand_coords.get('lon'):
        try:
            first_bedding = bedding_zones[0]
            bedding_lat = first_bedding.get('lat', 0)
            bedding_lon = first_bedding.get('lon', 0)
            
            if bedding_lat and bedding_lon:
                bearing = calculate_bearing(
                    bedding_lat, bedding_lon, 
                    stand_coords['lat'], stand_coords['lon']
                )
                directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                            "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                compass_dir = directions[int((bearing + 11.25) / 22.5) % 16]
                return bearing, compass_dir
        except:
            pass  # Fall through to terrain-based calculation
    
    # Method 2: Travel corridor calculation
    travel_zones = prediction_data.get('travel_zones', {}).get('zones', [])
    if travel_zones and len(travel_zones) >= 2:
        try:
            # Use direction between travel zones
            zone1 = travel_zones[0]
            zone2 = travel_zones[1] 
            bearing = calculate_bearing(
                zone1.get('lat', 0), zone1.get('lon', 0),
                zone2.get('lat', 0), zone2.get('lon', 0)
            )
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            compass_dir = directions[int((bearing + 11.25) / 22.5) % 16]
            return bearing, compass_dir
        except:
            pass
    
    # Method 3: Terrain-based calculation (fallback)
    terrain_features = prediction_data.get('terrain_features', {})
    stand_type = prediction_data.get('stand_type', 'General')
    
    return calculate_terrain_based_deer_approach(terrain_features, stand_coords, stand_type)

def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate bearing between two points"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

# Test cases to verify the fix works
def test_deer_approach_calculations():
    """Test the new deer approach calculation logic"""
    
    print("🧪 Testing Deer Approach Direction Calculations\n")
    
    # Test Case 1: Ridge travel corridor
    test_case_1 = {
        'terrain_features': {
            'terrain_type': 'ridge_top',
            'aspect': 180,  # South-facing
            'slope': 20,
            'elevation': 1500
        },
        'coordinates': {'lat': 44.0, 'lon': -72.0},
        'stand_type': 'Travel Corridor',
        'bedding_zones': {'zones': []}  # No bedding zones
    }
    
    bearing, direction = enhanced_deer_approach_calculation(test_case_1)
    print(f"Ridge Travel Corridor: {direction} ({bearing:.0f}°)")
    print(f"Expected: NE approach (deer coming from bedding areas uphill)\n")
    
    # Test Case 2: Valley feeding area
    test_case_2 = {
        'terrain_features': {
            'terrain_type': 'valley_agricultural',
            'aspect': 90,   # East-facing
            'slope': 5,
            'elevation': 800,
            'forest_edge': True
        },
        'coordinates': {'lat': 44.0, 'lon': -72.0},
        'stand_type': 'Feeding Area',
        'bedding_zones': {'zones': []}
    }
    
    bearing, direction = enhanced_deer_approach_calculation(test_case_2)
    print(f"Valley Feeding Area: {direction} ({bearing:.0f}°)")
    print(f"Expected: N approach (deer coming from forest cover)\n")
    
    # Test Case 3: Bedding area on steep slope
    test_case_3 = {
        'terrain_features': {
            'terrain_type': 'north_slope',
            'aspect': 360,  # North-facing
            'slope': 25,
            'elevation': 1200
        },
        'coordinates': {'lat': 44.0, 'lon': -72.0},
        'stand_type': 'Bedding Area',
        'bedding_zones': {'zones': []}
    }
    
    bearing, direction = enhanced_deer_approach_calculation(test_case_3)
    print(f"Steep Bedding Area: {direction} ({bearing:.0f}°)")
    print(f"Expected: S approach (deer coming from feeding areas below)\n")
    
    # Test Case 4: With actual bedding zone data
    test_case_4 = {
        'terrain_features': {'terrain_type': 'mixed'},
        'coordinates': {'lat': 44.26, 'lon': -72.58},
        'stand_type': 'Travel Corridor',
        'bedding_zones': {
            'zones': [
                {'lat': 44.27, 'lon': -72.57, 'confidence': 85}
            ]
        }
    }
    
    bearing, direction = enhanced_deer_approach_calculation(test_case_4)
    print(f"With Bedding Zone Data: {direction} ({bearing:.0f}°)")
    print(f"Expected: Dynamic based on bedding zone location\n")
    
    print("✅ All test cases completed!")
    print("🔧 Ready to implement in frontend code")

if __name__ == "__main__":
    test_deer_approach_calculations()
