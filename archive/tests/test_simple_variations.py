#!/usr/bin/env python3
"""
Simple test to check if mature buck predictions vary by location
Avoids GUI/matplotlib issues
"""

import requests
import json

def test_location_variations_simple():
    """Test if mature buck data changes with different coordinates"""
    
    print("🧪 TESTING LOCATION-SPECIFIC MATURE BUCK PREDICTIONS")
    print("=" * 60)
    
    # Test different locations
    test_locations = [
        {"lat": 44.26, "lon": -72.58, "name": "Vermont Forest"},
        {"lat": 44.5, "lon": -89.5, "name": "Wisconsin Farmland"},
        {"lat": 40.0, "lon": -75.0, "name": "Pennsylvania Mountains"}
    ]
    
    results = []
    
    for location in test_locations:
        print(f"\n🌍 TESTING: {location['name']} ({location['lat']}, {location['lon']})")
        print("-" * 40)
        
        # Make prediction request to dockerized backend
        url = "http://localhost:8000/predict"
        data = {
            "lat": location["lat"],
            "lon": location["lon"],
            "date_time": "2024-11-15T08:00:00",
            "season": "rut"
        }
        
        try:
            response = requests.post(url, json=data, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ Error: {response.status_code}")
                print(response.text[:200])
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
                "num_stands": len(stand_recommendations)
            }
            
            # Get first stand coordinates if available
            if stand_recommendations:
                first_stand_coords = stand_recommendations[0].get('coordinates', {})
                result["first_stand_lat"] = first_stand_coords.get('lat', 0)
                result["first_stand_lon"] = first_stand_coords.get('lon', 0)
            
            results.append(result)
            
            # Display results
            print(f"📊 Overall Suitability: {result['overall_suitability']:.1f}%")
            print(f"🛡️ Pressure Resistance: {result['pressure_resistance']:.1f}%")
            print(f"🏃 Escape Routes: {result['escape_routes']:.1f}%")
            print(f"🌲 Security Cover: {result['security_cover']:.1f}%")
            print(f"🚶 Movement Probability: {result['movement_probability']:.1f}%")
            print(f"📈 Confidence Score: {result['confidence_score']:.1f}%")
            print(f"🏹 Number of Stands: {result['num_stands']}")
            
            if 'first_stand_lat' in result:
                print(f"📍 First Stand: {result['first_stand_lat']:.6f}, {result['first_stand_lon']:.6f}")
        
        except requests.exceptions.ConnectionError:
            print(f"❌ Could not connect to backend at localhost:8000")
            return
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    # Analysis
    print("\n" + "=" * 60)
    print("🔍 LOCATION VARIATION ANALYSIS:")
    print("=" * 60)
    
    if len(results) >= 2:
        print(f"\nComparing {len(results)} locations:")
        
        # Check if values are different
        variations_found = False
        
        for key in ['overall_suitability', 'pressure_resistance', 'escape_routes', 'movement_probability']:
            values = [r[key] for r in results]
            unique_values = set(round(v, 1) for v in values)  # Round to avoid tiny differences
            
            if len(unique_values) > 1:
                print(f"✅ {key}: VARIES by location")
                for i, r in enumerate(results):
                    print(f"   {r['location']}: {r[key]:.1f}")
                variations_found = True
            else:
                print(f"⚠️ {key}: SAME everywhere ({values[0]:.1f})")
        
        # Check stand coordinates
        if all('first_stand_lat' in r for r in results):
            coords = [(r['first_stand_lat'], r['first_stand_lon']) for r in results]
            unique_coords = set(coords)
            
            if len(unique_coords) > 1:
                print(f"✅ Stand Coordinates: UNIQUE per location")
                for i, r in enumerate(results):
                    print(f"   {r['location']}: {r['first_stand_lat']:.6f}, {r['first_stand_lon']:.6f}")
                variations_found = True
            else:
                print(f"⚠️ Stand Coordinates: SAME everywhere")
        
        print(f"\n🎯 CONCLUSION:")
        if variations_found:
            print("✅ BACKEND IS LOCATION-SPECIFIC: Predictions change with coordinates")
            print("   ➜ Your issue might be frontend caching or session state")
        else:
            print("❌ BACKEND USING STATIC DATA: Same predictions everywhere")
            print("   ➜ This explains why you see identical numbers on the map")
            print("   ➜ Backend needs to use actual coordinates in calculations")
    
    else:
        print("❌ Not enough successful test locations to compare")

if __name__ == "__main__":
    test_location_variations_simple()
