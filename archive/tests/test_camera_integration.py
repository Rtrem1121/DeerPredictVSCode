#!/usr/bin/env python3
"""
Quick test for the integrated camera placement system
Tests both the new endpoint and the main prediction with camera placement option
"""

import requests
import json

def test_camera_integration():
    """Test the integrated camera placement functionality"""
    
    # Test coordinates (Vermont)
    test_lat, test_lon = 44.26, -72.58
    base_url = "http://localhost:8000"
    
    print("🎥 Testing Integrated Camera Placement System")
    print("=" * 60)
    
    # Test 1: New dedicated camera placement endpoint
    print("\n1. Testing /api/camera/optimal-placement endpoint...")
    try:
        response = requests.post(
            f"{base_url}/api/camera/optimal-placement",
            json={"lat": test_lat, "lon": test_lon},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Dedicated camera endpoint working!")
            
            camera = result["optimal_camera"]
            print(f"📍 Camera Position: ({camera['lat']:.6f}, {camera['lon']:.6f})")
            print(f"🎯 Confidence: {camera['confidence_score']:.1f}%")
            print(f"📏 Distance: {camera['distance_meters']:.0f} meters")
            
            insights = result.get("insights", [])
            print(f"💡 Insights: {len(insights)} strategic factors")
            for insight in insights[:2]:
                print(f"   • {insight}")
                
        else:
            print(f"❌ Endpoint failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Endpoint test failed: {e}")
    
    # Test 2: Main prediction with camera placement option
    print("\n2. Testing /predict with include_camera_placement=true...")
    try:
        response = requests.post(
            f"{base_url}/predict",
            json={
                "lat": test_lat,
                "lon": test_lon,
                "date_time": "2025-11-15T06:00:00",
                "season": "rut",
                "include_camera_placement": True
            },
            timeout=45
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Main prediction with camera placement working!")
            
            # Check if camera placement is included
            camera_data = result.get("optimal_camera_placement")
            if camera_data and camera_data.get("enabled"):
                print("✅ Camera placement integrated successfully!")
                
                coords = camera_data["camera_coordinates"]
                print(f"📍 Integrated Camera: ({coords['lat']:.6f}, {coords['lon']:.6f})")
                print(f"🎯 Confidence: {camera_data['confidence_score']:.1f}%")
                print(f"📏 Distance: {camera_data['distance_meters']:.0f} meters")
                print(f"💭 Strategy: {camera_data['placement_reasoning']}")
                
                # Check if it's in the notes
                notes = result.get("notes", "")
                if "Optimal Camera Placement" in notes:
                    print("✅ Camera placement included in prediction notes!")
                else:
                    print("⚠️ Camera placement not found in notes")
                    
            else:
                print("❌ Camera placement not found in main prediction response")
                if camera_data:
                    print(f"   Error: {camera_data.get('error', 'Unknown error')}")
                
        else:
            print(f"❌ Main prediction failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Main prediction test failed: {e}")
    
    # Test 3: Backend health check
    print("\n3. Testing backend health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print("✅ Backend healthy!")
            print(f"   Status: {health.get('status')}")
            if 'features' in health:
                features = health['features']
                if 'camera_placement' in features:
                    print(f"   Camera Placement: {features['camera_placement']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Camera Placement Integration Test Complete!")
    print("Note: Make sure your main backend is running on port 8000")

if __name__ == "__main__":
    test_camera_integration()
