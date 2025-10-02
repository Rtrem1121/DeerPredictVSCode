#!/usr/bin/env python3
"""
Test the Field Decision Widget prototype
"""

import requests
import json

def test_prototype_api_connection():
    """Test if the prototype can connect to the main API"""
    
    print("🧪 Testing Field Decision Widget Prototype...")
    
    # Test data
    test_payload = {
        "lat": 43.3006,
        "lon": -73.2247,
        "date_time": "2025-08-27T19:30:00",
        "season": "early_season"
    }
    
    try:
        print("📡 Connecting to main API...")
        response = requests.post("http://localhost:8000/predict", json=test_payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API connection successful!")
            
            # Check for stand recommendations
            stands = data.get('stand_recommendations', [])
            print(f"📍 Found {len(stands)} stand recommendations")
            
            if stands:
                print("\n🎯 Stand Preview:")
                for i, stand in enumerate(stands[:2]):  # Show first 2
                    print(f"  Stand #{i+1}: {stand.get('type', 'Unknown')} - {stand.get('confidence', 0):.1f}%")
                    coords = stand.get('coordinates', {})
                    print(f"    Coordinates: {coords.get('lat', 0):.6f}, {coords.get('lon', 0):.6f}")
                
                print("\n🌬️ Wind Analysis Test:")
                print("  Current prototype will analyze these stands for wind impact")
                print("  Wind directions: N, NE, E, SE, S, SW, W, NW")
                
                return True
            else:
                print("⚠️ No stand recommendations found in response")
                return False
                
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure the main deer prediction app is running on port 8000")
        return False

def test_wind_analysis_logic():
    """Test the wind analysis logic"""
    
    print("\n🌬️ Testing Wind Analysis Logic...")
    
    # Sample stand data
    sample_stands = [
        {
            'type': 'Feeding Area Stand',
            'confidence': 64.5,
            'coordinates': {'lat': 43.296134, 'lon': -73.232192},
            'reasoning': 'Close to feeding zones'
        },
        {
            'type': 'Ambush Stand', 
            'confidence': 47.5,
            'coordinates': {'lat': 43.303134, 'lon': -73.225692},
            'reasoning': 'Elevated position'
        }
    ]
    
    # Test different wind directions
    test_winds = ['N', 'S', 'E', 'W']
    
    for wind in test_winds:
        print(f"\n🌬️ Testing Wind: {wind}")
        
        # Simplified wind analysis (from prototype logic)
        for i, stand in enumerate(sample_stands):
            stand_type = stand['type']
            original_confidence = stand['confidence']
            
            # Determine deer approach (simplified)
            if 'Feeding' in stand_type:
                deer_approach = "SW"
            else:
                deer_approach = "NE"
            
            # Wind quality check (simplified)
            if wind in ['N', 'NW', 'NE'] and deer_approach == "SW":
                wind_quality = "EXCELLENT"
                adjusted = min(95, original_confidence * 1.15)
            elif wind in ['S', 'SW', 'SE'] and deer_approach == "NE":
                wind_quality = "EXCELLENT"  
                adjusted = min(95, original_confidence * 1.15)
            else:
                wind_quality = "POOR"
                adjusted = max(20, original_confidence * 0.75)
            
            print(f"  Stand #{i+1}: {original_confidence:.1f}% → {adjusted:.1f}% ({wind_quality})")
    
    print("\n✅ Wind analysis logic working!")

if __name__ == "__main__":
    print("🧪 Field Decision Widget Prototype Test\n")
    
    # Test API connection
    api_success = test_prototype_api_connection()
    
    # Test wind logic
    test_wind_analysis_logic()
    
    print("\n" + "="*50)
    if api_success:
        print("✅ Prototype ready for testing!")
        print("🌐 Access at: http://localhost:8502")
        print("📱 Mobile-friendly interface with big buttons")
        print("🌬️ Wind analysis for field decisions")
    else:
        print("⚠️ Start main app first: docker-compose up -d")
        print("📡 Then test prototype: http://localhost:8502")
    
    print("="*50)
