#!/usr/bin/env python3
"""
Test if mature buck predictions change with different locations
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from main import app
from fastapi.testclient import TestClient
import json

def test_location_specific_predictions():
    """Test if mature buck data changes with different coordinates"""
    
    print("🧪 TESTING LOCATION-SPECIFIC MATURE BUCK PREDICTIONS")
    print("=" * 60)
    
    # Create test client
    client = TestClient(app)
    
    # Test different locations
    test_locations = [
        {"lat": 44.26, "lon": -72.58, "name": "Vermont Forest"},
        {"lat": 44.5, "lon": -89.5, "name": "Wisconsin Farmland"},
        {"lat": 40.0, "lon": -75.0, "name": "Pennsylvania Mountains"},
        {"lat": 39.0, "lon": -94.0, "name": "Missouri Plains"}
    ]
    
    results = []
    
    for location in test_locations:
        print(f"\n🌍 TESTING: {location['name']} ({location['lat']}, {location['lon']})")
        print("-" * 50)
        
        # Make prediction request
        data = {
            "lat": location["lat"],
            "lon": location["lon"],
            "date_time": "2024-11-15T08:00:00",
            "season": "rut"
        }
        
        response = client.post("/predict", json=data)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            continue
            
        prediction = response.json()
        mature_buck_data = prediction.get('mature_buck_analysis', {})
        
        if not mature_buck_data:
            print("❌ No mature buck analysis data")
            continue
            
        # Extract key metrics
        terrain_scores = mature_buck_data.get('terrain_scores', {})
        movement_data = mature_buck_data.get('movement_prediction', {})
        stand_recommendations = mature_buck_data.get('stand_recommendations', [])
        
        result = {
            "location": location['name'],
            "coordinates": f"{location['lat']}, {location['lon']}",
            "overall_suitability": terrain_scores.get('overall_suitability', 0),
            "pressure_resistance": terrain_scores.get('pressure_resistance', 0),
            "escape_routes": terrain_scores.get('escape_route_quality', 0),
            "security_cover": terrain_scores.get('security_cover', 0),
            "movement_probability": movement_data.get('movement_probability', 0),
            "confidence_score": movement_data.get('confidence_score', 0),
            "num_stands": len(stand_recommendations),
            "stand_coords": [s.get('coordinates', {}) for s in stand_recommendations[:2]]  # First 2 stands
        }
        
        results.append(result)
        
        # Display results
        print(f"📊 Overall Suitability: {result['overall_suitability']:.1f}%")
        print(f"🛡️ Pressure Resistance: {result['pressure_resistance']:.1f}%")
        print(f"🏃 Escape Routes: {result['escape_routes']:.1f}%")
        print(f"🌲 Security Cover: {result['security_cover']:.1f}%")
        print(f"🚶 Movement Probability: {result['movement_probability']:.1f}%")
        print(f"📈 Confidence Score: {result['confidence_score']:.1f}%")
        print(f"🏹 Number of Stands: {result['num_stands']}")
        
        if result['num_stands'] > 0:
            for i, coords in enumerate(result['stand_coords'], 1):
                if coords:
                    print(f"   Stand {i}: {coords.get('lat', 0):.6f}, {coords.get('lon', 0):.6f}")
    
    # Analysis
    print("\n" + "=" * 60)
    print("🔍 LOCATION VARIATION ANALYSIS:")
    print("=" * 60)
    
    if len(results) >= 2:
        # Check if values are different
        first_result = results[0]
        variations_found = False
        
        for key in ['overall_suitability', 'pressure_resistance', 'escape_routes', 'movement_probability']:
            values = [r[key] for r in results]
            unique_values = set(values)
            
            if len(unique_values) > 1:
                print(f"✅ {key}: VARIES by location - {unique_values}")
                variations_found = True
            else:
                print(f"⚠️ {key}: SAME everywhere - {values[0]}")
        
        # Check coordinate variations
        all_coords = []
        for r in results:
            for coord in r['stand_coords']:
                if coord and 'lat' in coord:
                    all_coords.append((coord['lat'], coord['lon']))
        
        unique_coords = set(all_coords)
        if len(unique_coords) > 1:
            print(f"✅ Stand Coordinates: UNIQUE per location ({len(unique_coords)} different)")
            variations_found = True
        else:
            print(f"⚠️ Stand Coordinates: SAME everywhere")
        
        print("\n🎯 CONCLUSION:")
        if variations_found:
            print("✅ BACKEND IS LOCATION-SPECIFIC: Predictions change with different coordinates")
        else:
            print("❌ BACKEND MAY BE USING STATIC DATA: Same predictions everywhere")
            print("   This could explain why you see identical numbers on the map")
    
    else:
        print("❌ Not enough test locations to compare")

if __name__ == "__main__":
    test_location_specific_predictions()
