#!/usr/bin/env python3

import requests
import time

def test_multiple_locations():
    """Test multiple locations to confirm feeding markers show real oak positions"""
    
    locations = [
        {"name": "Vermont 1", "lat": 44.2619, "lon": -72.5806},
        {"name": "Vermont 2", "lat": 44.5619, "lon": -72.2806},
    ]
    
    print("🗺️ TESTING FEEDING MARKER POSITIONS")
    print("=" * 60)
    
    for location in locations:
        print(f"\n📍 {location['name']}: {location['lat']}, {location['lon']}")
        
        response = requests.post(
            "http://localhost:8000/predict",
            json={
                "latitude": location['lat'],
                "longitude": location['lon'],
                "season": "early_season",
                "time_of_day": "morning"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            feeding_areas = data.get('feeding_areas', [])
            
            print(f"   🍽️ Feeding Areas: {len(feeding_areas)}")
            for i, area in enumerate(feeding_areas, 1):
                lat = area.get('lat', 'N/A')
                lon = area.get('lon', 'N/A')
                score = area.get('score', 'N/A')
                print(f"      Area {i}: Lat={lat:.6f}, Lon={lon:.6f}, Score={score}")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
        
        time.sleep(1)  # Brief pause between requests
    
    print(f"\n✅ If positions are different between locations, markers show real oak tree locations!")
    print(f"📍 If positions are identical, there might still be an issue.")

if __name__ == "__main__":
    test_multiple_locations()
