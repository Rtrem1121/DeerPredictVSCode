#!/usr/bin/env python3
"""
Test the new frontend interface design for AM/DAY/PM periods
This simulates the new UI before implementing it in the real app
"""

import streamlit as st
import math
from datetime import datetime

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

def calculate_time_based_deer_approach(hunt_period, stand_coords, feeding_areas, bedding_areas):
    """
    NEW: Calculate deer approach based on hunt period and actual movement patterns
    """
    
    if hunt_period == "AM":
        # 5:30-9:00 AM: Deer moving FROM feeding TO bedding
        if feeding_areas:
            source_coords = feeding_areas[0]  # Nearest feeding area
            movement_type = "Returning from feeding areas to bedding"
            confidence = "High"
        else:
            # Fallback: assume feeding south/southeast  
            source_coords = (stand_coords[0] - 0.01, stand_coords[1] - 0.005)
            movement_type = "Estimated: returning from feeding areas"
            confidence = "Medium"
            
    elif hunt_period == "PM":
        # 17:00-19:00: Deer moving FROM bedding TO feeding
        if bedding_areas:
            source_coords = bedding_areas[0]  # Nearest bedding area
            movement_type = "Leaving bedding areas for feeding"
            confidence = "High"
        else:
            # Fallback: assume bedding north/northeast
            source_coords = (stand_coords[0] + 0.01, stand_coords[1] + 0.005)
            movement_type = "Estimated: leaving bedding areas for feeding"
            confidence = "Medium"
            
    else:  # DAY period (9:00-17:00)
        # Midday: Deer in bedding areas, minimal movement
        if bedding_areas:
            source_coords = bedding_areas[0]
            movement_type = "Minimal movement in bedding areas"
            confidence = "Low"
        else:
            # Fallback: assume bedding north/northeast
            source_coords = (stand_coords[0] + 0.008, stand_coords[1] + 0.004)
            movement_type = "Estimated: minimal movement near bedding"
            confidence = "Low"
    
    # Calculate bearing from source to stand
    approach_bearing = calculate_bearing(
        source_coords[0], source_coords[1],
        stand_coords[0], stand_coords[1]
    )
    
    approach_compass = bearing_to_compass(approach_bearing)
    
    return {
        "bearing": approach_bearing,
        "compass": approach_compass,
        "movement_type": movement_type,
        "confidence": confidence,
        "source_coords": source_coords
    }

def simulate_new_ui():
    """Simulate the new UI design for testing"""
    
    print("🎯 NEW UI SIMULATION - AM/DAY/PM HUNT PERIODS")
    print("=" * 60)
    
    # Simulate hunt period selection
    print("Hunt Period Selection:")
    print("🌅 AM Hunt (5:30 AM - 9:00 AM) - Dawn Movement: Feeding → Bedding")
    print("☀️ DAY Hunt (9:00 AM - 5:00 PM) - Bedding Areas: Minimal Movement") 
    print("🌆 PM Hunt (5:00 PM - 7:00 PM) - Dusk Movement: Bedding → Feeding")
    print()
    
    # Test data
    hunt_coords = (43.3111, -73.2201)
    stand_coords = (43.309065, -73.225100)
    
    # Mock backend data (feeding areas from your actual backend)
    feeding_areas = [
        (43.300628, -73.220358),  # From your backend response
        (43.317295, -73.227025)   # Second feeding area
    ]
    
    # Mock bedding areas (empty in current backend, so we estimate)
    bedding_areas = [
        (43.315, -73.228)  # Estimated bedding area
    ]
    
    # Test each period
    for period, emoji, description in [
        ("AM", "🌅", "Dawn Hunt"),
        ("DAY", "☀️", "Day Hunt"), 
        ("PM", "🌆", "Evening Hunt")
    ]:
        print(f"{emoji} {description.upper()} RESULTS:")
        print("-" * 40)
        
        result = calculate_time_based_deer_approach(
            period, stand_coords, feeding_areas, bedding_areas
        )
        
        print(f"📍 Stand Location: {stand_coords[0]:.6f}, {stand_coords[1]:.6f}")
        print(f"🦌 Deer Movement: {result['movement_type']}")
        print(f"🧭 Deer Approach: {result['compass']} ({result['bearing']:.0f}°)")
        print(f"📊 Confidence: {result['confidence']}")
        
        # Wind recommendations based on approach
        optimal_wind_1 = (result['bearing'] + 90) % 360
        optimal_wind_2 = (result['bearing'] - 90) % 360
        wind_dir_1 = bearing_to_compass(optimal_wind_1)
        wind_dir_2 = bearing_to_compass(optimal_wind_2)
        
        print(f"💨 Optimal Winds: {wind_dir_1} or {wind_dir_2}")
        print(f"🚫 Avoid Wind From: {result['compass']} (toward deer)")
        print()

def test_backend_integration():
    """Test how this would integrate with current backend data"""
    
    print("🔧 BACKEND INTEGRATION TEST")
    print("=" * 60)
    
    # Simulate current backend response structure
    mock_backend_response = {
        "feeding_areas": {
            "features": [
                {
                    "geometry": {"coordinates": [-73.220358, 43.300628]},
                    "properties": {"score": 0.9}
                },
                {
                    "geometry": {"coordinates": [-73.227025, 43.317295]},
                    "properties": {"score": 0.9}
                }
            ]
        },
        "bedding_zones": {
            "features": []  # Currently empty in backend
        },
        "mature_buck_analysis": {
            "stand_recommendations": [
                {
                    "coordinates": {"lat": 43.309065, "lon": -73.225100},
                    "confidence": 95,
                    "type": "Travel Corridor Stand"
                }
            ]
        }
    }
    
    # Extract data for new calculation
    feeding_areas = []
    for feature in mock_backend_response["feeding_areas"]["features"]:
        coords = feature["geometry"]["coordinates"]
        feeding_areas.append((coords[1], coords[0]))  # Convert [lon,lat] to (lat,lon)
    
    bedding_areas = []
    for feature in mock_backend_response["bedding_zones"]["features"]:
        coords = feature["geometry"]["coordinates"]
        bedding_areas.append((coords[1], coords[0]))
    
    # Get stand coordinates
    stand_recommendation = mock_backend_response["mature_buck_analysis"]["stand_recommendations"][0]
    stand_coords = (stand_recommendation["coordinates"]["lat"], stand_recommendation["coordinates"]["lon"])
    
    print(f"Backend Data Extracted:")
    print(f"- Feeding Areas: {len(feeding_areas)} found")
    print(f"- Bedding Areas: {len(bedding_areas)} found") 
    print(f"- Stand Location: {stand_coords}")
    print()
    
    # Test with extracted data
    print("Testing AM period with backend data:")
    result = calculate_time_based_deer_approach("AM", stand_coords, feeding_areas, bedding_areas)
    
    print(f"Result: {result['compass']} ({result['bearing']:.0f}°)")
    print(f"Logic: {result['movement_type']}")
    print(f"Confidence: {result['confidence']}")

if __name__ == "__main__":
    simulate_new_ui()
    print()
    test_backend_integration()
