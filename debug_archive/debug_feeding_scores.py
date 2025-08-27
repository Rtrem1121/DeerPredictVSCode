#!/usr/bin/env python3
"""
Debug feeding area scores across different locations to check for hardcoded values
"""

import requests
import json

def test_feeding_scores():
    """Test feeding area scores across different locations"""
    
    backend_url = "http://localhost:8000"
    
    # Test different locations
    test_locations = [
        {"name": "Vermont", "lat": 44.2619, "lon": -72.5806},
        {"name": "Maine", "lat": 45.2538, "lon": -69.4455},
        {"name": "New York", "lat": 43.1566, "lon": -74.2478},
        {"name": "Pennsylvania", "lat": 40.2677, "lon": -76.8756},
        {"name": "Wisconsin", "lat": 44.5000, "lon": -89.5000}
    ]
    
    print("🍽️ FEEDING AREA SCORES VERIFICATION TEST")
    print("=" * 60)
    
    for location in test_locations:
        try:
            # Make prediction request
            response = requests.post(f"{backend_url}/predict", json={
                "lat": location["lat"],
                "lon": location["lon"],
                "date_time": "2024-11-15T06:00:00",
                "season": "early_season",
                "moon_phase": "waxing_gibbous"
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract feeding area information
                feeding_areas = data.get('feeding_areas', {})
                features = feeding_areas.get('features', [])
                
                print(f"\n🌲 {location['name'].upper()}:")
                print(f"   📍 Coordinates: {location['lat']}, {location['lon']}")
                print(f"   🍽️ Feeding Areas Found: {len(features)}")
                
                # Look for feeding scores in the features
                for i, feature in enumerate(features[:3]):  # Show first 3
                    properties = feature.get('properties', {})
                    score = properties.get('score', 'N/A')
                    confidence = properties.get('confidence', 'N/A')
                    description = properties.get('description', 'N/A')
                    
                    print(f"   🎯 Area {i+1}: Score={score}, Confidence={confidence}")
                    if description != 'N/A':
                        print(f"      📝 {description}")
                
                # Also check if there's feeding score heatmap data
                feeding_heatmap = data.get('feeding_score_heatmap', '')
                if feeding_heatmap:
                    heatmap_data = json.loads(feeding_heatmap)
                    max_feeding_score = max(max(row) for row in heatmap_data)
                    print(f"   📊 Max Feeding Score in Heatmap: {max_feeding_score:.3f}")
                
            else:
                print(f"❌ {location['name']}: Request failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {location['name']}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("🔍 ANALYSIS:")
    print("=" * 60)
    print("Check if feeding area scores are:")
    print("• Always the same value (0.90) - indicates hardcoded")
    print("• Variable across locations - indicates real calculation")
    print("• Have different coordinates - indicates location-specific")

if __name__ == "__main__":
    test_feeding_scores()
