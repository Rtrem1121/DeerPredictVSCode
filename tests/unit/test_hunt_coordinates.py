#!/usr/bin/env python3
"""
Test script to check the Hunt Coordinates functionality
and verify the #1 stand coordinates are being extracted correctly.
"""

import requests
import json

def test_hunt_coordinates():
    print("🎯 Testing Hunt Coordinates for #1 Predicted Stand")
    print("=" * 60)
    
    # Test location (your example)
    test_lat = 43.3125
    test_lon = -73.2240
    
    print(f"📍 Test Location: {test_lat}, {test_lon}")
    print()
    
    # Make prediction request
    headers = {"Content-Type": "application/json"}
    body = {
        "lat": test_lat,
        "lon": test_lon,
        "date_time": "2025-08-27T06:00:00",
        "season": "early_season"
    }
    
    try:
        print("🔄 Making prediction request...")
        response = requests.post("http://localhost:8000/predict", headers=headers, json=body)
        
        if response.status_code == 200:
            prediction = response.json()
            print("✅ Prediction successful!")
            print()
            
            # Check for mature buck analysis
            if 'mature_buck_analysis' in prediction:
                mature_buck = prediction['mature_buck_analysis']
                print("📊 Mature Buck Analysis found")
                
                if 'stand_recommendations' in mature_buck and mature_buck['stand_recommendations']:
                    stands = mature_buck['stand_recommendations']
                    print(f"🏹 Found {len(stands)} stand recommendations")
                    print()
                    
                    # Show #1 stand details
                    stand_1 = stands[0]
                    print("🥇 #1 PREDICTED STAND COORDINATES:")
                    print(f"   Name: {stand_1.get('name', 'Unnamed')}")
                    print(f"   Quality Score: {stand_1.get('quality_score', 'N/A')}")
                    
                    coords = stand_1.get('coordinates', {})
                    if coords.get('lat') and coords.get('lon'):
                        hunt_lat = coords['lat']
                        hunt_lon = coords['lon']
                        print(f"   📍 GPS Coordinates: {hunt_lat:.6f}, {hunt_lon:.6f}")
                        
                        # Calculate distance from input location
                        import math
                        dlat = hunt_lat - test_lat
                        dlon = hunt_lon - test_lon
                        distance = math.sqrt(dlat*dlat + dlon*dlon) * 111000  # rough meters
                        
                        print(f"   📏 Distance from input: {distance:.1f} meters")
                        
                        print()
                        print("✅ HUNT COORDINATES SHOULD BE:")
                        print(f"   {hunt_lat:.6f}, {hunt_lon:.6f}")
                        print()
                        print("📱 For your GPS device:")
                        print(f"   Latitude:  {hunt_lat:.6f}")
                        print(f"   Longitude: {hunt_lon:.6f}")
                        
                    else:
                        print("❌ No coordinates found in stand #1")
                        print(f"   Coordinates object: {coords}")
                        
                else:
                    print("❌ No stand recommendations found")
                    print(f"   Mature buck keys: {list(mature_buck.keys())}")
                    
            else:
                print("❌ No mature_buck_analysis found")
                print(f"   Response keys: {list(prediction.keys())}")
                
        else:
            print(f"❌ Prediction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_hunt_coordinates()
