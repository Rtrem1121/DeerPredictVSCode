#!/usr/bin/env python3
"""
Test script for AM/DAY/PM hunt period logic
Testing the new time-based deer movement patterns before implementing in the main app
"""

import math
from datetime import datetime

# Time periods with your specified ranges
TIME_PERIODS = {
    "AM": {
        "start": "05:30",
        "end": "09:00", 
        "description": "Dawn Hunt (5:30 AM - 9:00 AM)",
        "movement": "Feeding → Bedding",
        "deer_activity": "High (returning from feeding)",
        "wind_strategy": "Block scent from feeding areas"
    },
    "DAY": {
        "start": "09:00",
        "end": "17:00",
        "description": "Day Hunt (9:00 AM - 5:00 PM)", 
        "movement": "Bedding areas (minimal movement)",
        "deer_activity": "Low (bedded down)",
        "wind_strategy": "Block scent from bedding areas"
    },
    "PM": {
        "start": "17:00", 
        "end": "19:00",
        "description": "Evening Hunt (5:00 PM - 7:00 PM)",
        "movement": "Bedding → Feeding",
        "deer_activity": "High (heading to feeding)",
        "wind_strategy": "Block scent from bedding areas"
    }
}

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing between two GPS coordinates"""
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlon_rad = math.radians(lon2 - lon1)
    
    y = math.sin(dlon_rad) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad)
    
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    bearing = (bearing + 360) % 360
    
    return bearing

def bearing_to_compass(bearing):
    """Convert bearing to compass direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return directions[int((bearing + 11.25) / 22.5) % 16]

def calculate_time_based_deer_approach(hunt_period, stand_coords, feeding_coords=None, bedding_coords=None):
    """
    Calculate deer approach direction based on hunt period and movement patterns
    """
    
    period_info = TIME_PERIODS[hunt_period]
    
    if hunt_period == "AM":
        # Dawn: Deer moving FROM feeding areas TO bedding areas
        if feeding_coords:
            # Deer approach stand from feeding area direction
            approach_bearing = calculate_bearing(
                feeding_coords[0], feeding_coords[1],  # Feeding area (source)
                stand_coords[0], stand_coords[1]       # Stand (destination)
            )
            source_type = "feeding area"
        else:
            # Fallback: assume feeding areas are generally south/southeast
            approach_bearing = 135  # SE approach (common feeding direction)
            source_type = "estimated feeding area"
            
    elif hunt_period == "PM":
        # Dusk: Deer moving FROM bedding areas TO feeding areas  
        if bedding_coords:
            # Deer approach stand from bedding area direction
            approach_bearing = calculate_bearing(
                bedding_coords[0], bedding_coords[1],  # Bedding area (source)
                stand_coords[0], stand_coords[1]       # Stand (destination)
            )
            source_type = "bedding area"
        else:
            # Fallback: assume bedding areas are generally north/northeast (cover)
            approach_bearing = 45  # NE approach (common bedding direction)
            source_type = "estimated bedding area"
            
    else:  # DAY period
        # Midday: Deer mostly in bedding, minimal movement
        if bedding_coords:
            approach_bearing = calculate_bearing(
                bedding_coords[0], bedding_coords[1],
                stand_coords[0], stand_coords[1]
            )
            source_type = "bedding area"
        else:
            # Random/minimal movement
            approach_bearing = 180  # Default south
            source_type = "bedding area (estimated)"
    
    compass_dir = bearing_to_compass(approach_bearing)
    
    return {
        "bearing": approach_bearing,
        "compass": compass_dir,
        "source_type": source_type,
        "period_info": period_info,
        "confidence": "High" if hunt_period in ["AM", "PM"] else "Low"
    }

def test_deer_approach_scenarios():
    """Test different hunting scenarios"""
    
    print("🦌 DEER APPROACH PREDICTION TEST\n")
    print("=" * 50)
    
    # Test coordinates (your example)
    hunt_coords = (43.3111, -73.2201)
    stand_coords = (43.309065, -73.225100)
    
    # Mock feeding and bedding areas
    feeding_coords = (43.3050, -73.2180)  # South of stand (common pattern)
    bedding_coords = (43.3150, -73.2280)  # North/northwest of stand (cover areas)
    
    print(f"Hunt Location: {hunt_coords}")
    print(f"Stand Location: {stand_coords}")
    print(f"Feeding Area: {feeding_coords}")
    print(f"Bedding Area: {bedding_coords}\n")
    
    # Test all three periods
    for period in ["AM", "DAY", "PM"]:
        print(f"🕐 {TIME_PERIODS[period]['description']}")
        print("-" * 30)
        
        result = calculate_time_based_deer_approach(
            period, stand_coords, feeding_coords, bedding_coords
        )
        
        print(f"Deer Movement: {result['period_info']['movement']}")
        print(f"Deer Activity: {result['period_info']['deer_activity']}")
        print(f"Approach From: {result['source_type']}")
        print(f"Approach Direction: {result['compass']} ({result['bearing']:.0f}°)")
        print(f"Movement Confidence: {result['confidence']}")
        print(f"Wind Strategy: {result['period_info']['wind_strategy']}")
        print()

def test_with_real_backend_data():
    """Test with actual backend feeding/bedding zone data"""
    
    print("🔬 TESTING WITH BACKEND DATA STRUCTURE\n")
    print("=" * 50)
    
    # Simulate backend response structure
    mock_prediction = {
        "feeding_areas": {
            "features": [
                {
                    "geometry": {"coordinates": [-73.220358, 43.300628]},  # GeoJSON format [lon, lat]
                    "properties": {"score": 0.9}
                },
                {
                    "geometry": {"coordinates": [-73.227025, 43.317295]},
                    "properties": {"score": 0.9}
                }
            ]
        },
        "bedding_zones": {
            "features": [
                # No bedding zones in current backend (empty)
            ]
        }
    }
    
    # Extract feeding areas (convert GeoJSON to lat/lon)
    feeding_areas = []
    for feature in mock_prediction["feeding_areas"]["features"]:
        coords = feature["geometry"]["coordinates"]
        feeding_areas.append((coords[1], coords[0]))  # Convert [lon, lat] to (lat, lon)
    
    # Extract bedding areas
    bedding_areas = []
    for feature in mock_prediction["bedding_zones"]["features"]:
        coords = feature["geometry"]["coordinates"] 
        bedding_areas.append((coords[1], coords[0]))
    
    print(f"Feeding Areas Found: {len(feeding_areas)}")
    print(f"Bedding Areas Found: {len(bedding_areas)}")
    
    if feeding_areas:
        print(f"Nearest Feeding: {feeding_areas[0]}")
    if bedding_areas:
        print(f"Nearest Bedding: {bedding_areas[0]}")
    
    print()
    
    # Test each period with real data
    stand_coords = (43.309065, -73.225100)
    
    for period in ["AM", "DAY", "PM"]:
        feeding_coord = feeding_areas[0] if feeding_areas else None
        bedding_coord = bedding_areas[0] if bedding_areas else None
        
        result = calculate_time_based_deer_approach(
            period, stand_coords, feeding_coord, bedding_coord
        )
        
        print(f"{period} Period: {result['compass']} ({result['bearing']:.0f}°) from {result['source_type']}")

if __name__ == "__main__":
    test_deer_approach_scenarios()
    print("\n" + "=" * 50 + "\n")
    test_with_real_backend_data()
