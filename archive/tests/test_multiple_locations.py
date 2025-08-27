#!/usr/bin/env python3
"""
Test multiple coordinates to verify terrain score variation
"""
import requests
import json

# Test coordinates - different locations that should give different scores
test_coordinates = [
    (44.074565, -72.647567, "User's Location"),
    (44.1, -72.7, "Slightly North"),
    (44.0, -72.6, "Slightly South"),
    (43.9, -72.5, "Further South"),
    (44.2, -72.8, "Further North")
]

def test_multiple_locations():
    """Test terrain scores across multiple coordinates"""
    print("MULTIPLE LOCATION TERRAIN SCORE TEST")
    print("=" * 60)
    
    results = []
    
    for lat, lon, name in test_coordinates:
        print(f"\nTesting {name}: ({lat}, {lon})")
        
        try:
            # Make API call using /predict endpoint
            test_request = {
                "name": f"Test Location: {name}",
                "lat": lat,
                "lon": lon,
                "date_time": "2024-10-15T06:00:00",
                "season": "early_season",
                "weather": {"temperature": 45, "wind_speed": 8, "wind_direction": 190}
            }
            
            response = requests.post('http://localhost:8000/predict', 
                                   json=test_request,
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                mature_buck_data = data.get('mature_buck_analysis', {})
                terrain_scores = mature_buck_data.get('terrain_scores', {})
                
                isolation = terrain_scores.get('isolation_score', 0)
                pressure = terrain_scores.get('pressure_resistance', 0)
                
                print(f"  Isolation Score: {isolation:.1f}%")
                print(f"  Pressure Resistance: {pressure:.1f}%")
                
                results.append({
                    'name': name,
                    'lat': lat,
                    'lon': lon,
                    'isolation': isolation,
                    'pressure': pressure
                })
            else:
                print(f"  API Error: {response.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    # Check for variation
    print("\n" + "=" * 60)
    print("VARIATION ANALYSIS:")
    print("=" * 60)
    
    if results:
        isolations = [r['isolation'] for r in results]
        pressures = [r['pressure'] for r in results]
        
        iso_unique = len(set(isolations))
        pressure_unique = len(set(pressures))
        
        print(f"Isolation scores: {isolations}")
        print(f"Unique isolation values: {iso_unique}/{len(isolations)}")
        print(f"Pressure scores: {pressures}")
        print(f"Unique pressure values: {pressure_unique}/{len(pressures)}")
        
        if iso_unique == 1 and pressure_unique == 1:
            print("❌ SCORES ARE STILL HARDCODED - NO VARIATION!")
        else:
            print("✅ SCORES ARE VARYING BY LOCATION!")
    
    return results

if __name__ == "__main__":
    test_multiple_locations()
