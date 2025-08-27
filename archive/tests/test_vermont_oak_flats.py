#!/usr/bin/env python3
"""
Test Vermont-specific vegetation to verify oak flats instead of soybean
"""

import requests
import json

def test_vermont_vegetation():
    """Test Vermont vegetation to see oak flats instead of soybean"""
    
    backend_url = "http://localhost:8000"
    
    # Test Vermont location specifically
    vermont_location = {"name": "Vermont", "lat": 44.2619, "lon": -72.5806}
    
    print("🍁 VERMONT VEGETATION TEST - Oak Flats vs Soybean")
    print("=" * 60)
    
    try:
        # Make prediction request
        response = requests.post(f"{backend_url}/predict", json={
            "lat": vermont_location["lat"],
            "lon": vermont_location["lon"],
            "date_time": "2024-11-15T06:00:00",
            "season": "early_season",
            "moon_phase": "waxing_gibbous"
        }, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract feeding area information
            feeding_areas = data.get('feeding_areas', {})
            features = feeding_areas.get('features', [])
            
            print(f"\n🌲 {vermont_location['name'].upper()}:")
            print(f"   📍 Coordinates: {vermont_location['lat']}, {vermont_location['lon']}")
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
            
            print(f"\n✅ Vermont should now have oak flats instead of soybean fields!")
            print(f"🍁 Check backend logs for 'Generated oak flats for Vermont area'")
            
        else:
            print(f"❌ {vermont_location['name']}: Request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ {vermont_location['name']}: Error - {e}")
    
    print("\n" + "=" * 60)
    print("🔍 EXPECTED CHANGES:")
    print("=" * 60)
    print("• Vermont should show oak flats (acorn feeding areas)")
    print("• No soybean fields in Vermont coordinates")
    print("• Better reflects Vermont's hardwood forest ecosystem")
    print("• Oak flat feeding rules have confidence 0.8 vs soybean 0.9/0.85")

if __name__ == "__main__":
    test_vermont_vegetation()
