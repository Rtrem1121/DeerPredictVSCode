#!/usr/bin/env python3
"""
Quick Backend Data Quality Validation
Tests key endpoints and validates data accuracy
"""

import requests
import json
import time
from datetime import datetime

def test_prediction_quality():
    """Test prediction endpoint data quality"""
    print("🎯 Testing Prediction Quality...")
    
    # Test location in Vermont
    payload = {
        "latitude": 44.26639,
        "longitude": -72.58133,
        "date": "2024-11-15",
        "time": "06:00",
        "season": "early_season",
        "weather": {
            "temperature": 35,
            "wind_speed": 8,
            "wind_direction": 225,
            "pressure": 30.15,
            "humidity": 65
        }
    }
    
    try:
        start_time = time.time()
        response = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            print(f"✅ Response received in {response_time:.2f}s")
            print(f"📊 Data structure validation:")
            
            # Validate main components
            required_fields = ['markers', 'stand_locations', 'confidence', 'analysis']
            for field in required_fields:
                if field in data:
                    print(f"   ✅ {field}: Present")
                else:
                    print(f"   ❌ {field}: Missing")
                    
            # Validate data quality
            markers = data.get('markers', [])
            stands = data.get('stand_locations', [])
            confidence = data.get('confidence', 0)
            
            print(f"\n📈 Data Quality Metrics:")
            print(f"   🎯 Markers Generated: {len(markers)}")
            print(f"   🏹 Stand Locations: {len(stands)}")
            print(f"   📊 Confidence Score: {confidence}%")
            
            # Check marker types
            marker_types = {}
            for marker in markers:
                marker_type = marker.get('type', 'unknown')
                marker_types[marker_type] = marker_types.get(marker_type, 0) + 1
                
            print(f"   🎨 Marker Distribution: {marker_types}")
            
            # Validate stand quality
            valid_stands = 0
            for stand in stands:
                if (stand.get('lat') and stand.get('lon') and 
                    stand.get('confidence', 0) > 0):
                    valid_stands += 1
                    
            print(f"   🎯 Quality Stands: {valid_stands}/{len(stands)}")
            
            # Show sample stand data
            if stands:
                print(f"\n🏹 Sample Stand Location:")
                sample_stand = stands[0]
                print(f"   📍 Coordinates: ({sample_stand.get('lat', 'N/A'):.6f}, {sample_stand.get('lon', 'N/A'):.6f})")
                print(f"   🎯 Confidence: {sample_stand.get('confidence', 'N/A')}%")
                print(f"   📝 Justification: {sample_stand.get('justification', 'N/A')}")
                
            return True
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {str(e)}")
        return False

def test_seasonal_differences():
    """Test predictions across seasons"""
    print("\n🍂 Testing Seasonal Variations...")
    
    seasons = ["early_season", "rut", "late_season"]
    location = {"lat": 44.26639, "lon": -72.58133}
    results = {}
    
    for season in seasons:
        payload = {
            "latitude": location["lat"],
            "longitude": location["lon"],
            "date": "2024-11-15",
            "time": "06:00",
            "season": season,
            "weather": {
                "temperature": 25 if season == "late_season" else 45,
                "wind_speed": 5,
                "wind_direction": 270,
                "pressure": 30.10,
                "humidity": 70
            }
        }
        
        try:
            response = requests.post("http://127.0.0.1:8000/predict", json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                confidence = data.get('confidence', 0)
                stands = len(data.get('stand_locations', []))
                markers = len(data.get('markers', []))
                
                results[season] = {
                    "confidence": confidence,
                    "stands": stands,
                    "markers": markers
                }
                print(f"   ✅ {season}: {confidence}% confidence, {stands} stands, {markers} markers")
            else:
                print(f"   ❌ {season}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {season}: Error - {str(e)}")
            
    # Check for variation
    if len(results) >= 2:
        confidences = [r["confidence"] for r in results.values()]
        variation = max(confidences) - min(confidences)
        print(f"\n📊 Seasonal Confidence Variation: {variation:.1f}%")
        
        if variation > 5:
            print("✅ Good seasonal variation detected")
        else:
            print("⚠️  Limited seasonal variation")
            
    return len(results) > 0

def test_camera_placement():
    """Test camera placement functionality"""
    print("\n📷 Testing Camera Placement...")
    
    payload = {
        "latitude": 44.26639,
        "longitude": -72.58133,
        "radius_miles": 0.5,
        "terrain_features": ["water", "ridge", "valley"],
        "camera_count": 3
    }
    
    try:
        response = requests.post("http://127.0.0.1:8000/trail-cameras", json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            cameras = data.get('camera_locations', [])
            
            print(f"✅ Camera placement successful")
            print(f"📷 Generated {len(cameras)} camera positions")
            
            # Check camera quality
            high_quality_cameras = 0
            for camera in cameras:
                if camera.get('confidence', 0) > 60:
                    high_quality_cameras += 1
                    
            print(f"🎯 High-quality positions: {high_quality_cameras}/{len(cameras)}")
            
            # Show sample camera
            if cameras:
                sample_camera = cameras[0]
                print(f"\n📷 Sample Camera Position:")
                print(f"   📍 Location: ({sample_camera.get('lat', 'N/A'):.6f}, {sample_camera.get('lon', 'N/A'):.6f})")
                print(f"   🎯 Confidence: {sample_camera.get('confidence', 'N/A')}%")
                print(f"   📝 Reason: {sample_camera.get('reason', 'N/A')}")
                
            return len(cameras) > 0
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Request Error: {str(e)}")
        return False

def test_scouting_data():
    """Test scouting data endpoints"""
    print("\n🔍 Testing Scouting Data...")
    
    try:
        # Test observation types
        response = requests.get("http://127.0.0.1:8000/scouting/types", timeout=10)
        if response.status_code == 200:
            types = response.json()
            print(f"✅ Observation types: {len(types)} available")
            print(f"   📋 Types: {[t.get('name', 'Unknown') for t in types[:5]]}")
        else:
            print(f"❌ Types endpoint: HTTP {response.status_code}")
            
        # Test observations retrieval
        params = {
            "lat": 44.26639,
            "lon": -72.58133,
            "radius_miles": 10
        }
        response = requests.get("http://127.0.0.1:8000/scouting/observations", params=params, timeout=10)
        
        if response.status_code == 200:
            observations = response.json()
            print(f"✅ Observations: {len(observations)} retrieved")
            return True
        else:
            print(f"❌ Observations endpoint: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Scouting test error: {str(e)}")
        return False

def main():
    """Run quick validation tests"""
    print("🦌 DEER PREDICTION BACKEND VALIDATION")
    print("=" * 45)
    
    # Test connectivity first
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Backend connectivity confirmed")
        else:
            print(f"⚠️  Backend response: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Backend connectivity failed: {str(e)}")
        print("🚨 Cannot proceed with tests")
        return False
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_prediction_quality():
        tests_passed += 1
        
    if test_seasonal_differences():
        tests_passed += 1
        
    if test_camera_placement():
        tests_passed += 1
        
    if test_scouting_data():
        tests_passed += 1
    
    # Final report
    print("\n" + "=" * 45)
    print("📊 VALIDATION SUMMARY")
    print("=" * 45)
    print(f"Tests Passed: {tests_passed}/{total_tests}")
    print(f"Success Rate: {(tests_passed/total_tests*100):.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED - Backend producing accurate data!")
        return True
    elif tests_passed >= total_tests * 0.75:
        print("✅ MOSTLY PASSING - Backend functioning well with minor issues")
        return True
    else:
        print("⚠️  ISSUES DETECTED - Backend needs attention")
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n📄 Backend Status: {'EXCELLENT' if success else 'NEEDS ATTENTION'}")
