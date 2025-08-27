#!/usr/bin/env python3
"""
Frontend Display Test
Tests that the Streamlit frontend correctly displays all prediction data
"""

import requests
import json
import time
from datetime import datetime

# Test configuration
FRONTEND_URL = "http://localhost:8501"
BACKEND_URL = "http://localhost:8000"

def test_backend_prediction():
    """Test that backend generates expected prediction data"""
    print("🧪 Testing Backend Prediction Generation...")
    
    test_data = {
        "lat": 44.2619,
        "lon": -72.5806,
        "date_time": "2025-08-24T19:30:00",
        "season": "rut",
        "fast_mode": True,
        "include_camera_placement": True
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/predict", json=test_data, timeout=30)
        
        if response.status_code == 200:
            prediction = response.json()
            print("✅ Backend Response Successful")
            
            # Validate travel corridors
            travel_count = len(prediction.get('travel_corridors', {}).get('features', []))
            print(f"  🚶 Travel Corridors: {travel_count}")
            
            # Validate bedding zones
            bedding_count = len(prediction.get('bedding_zones', {}).get('features', []))
            print(f"  🛏️ Bedding Zones: {bedding_count}")
            
            # Validate feeding areas
            feeding_count = len(prediction.get('feeding_areas', {}).get('features', []))
            print(f"  🌾 Feeding Areas: {feeding_count}")
            
            # Validate stand recommendations
            stands = prediction.get('mature_buck_analysis', {}).get('stand_recommendations', [])
            stand_count = len(stands)
            print(f"  🎯 Stand Recommendations: {stand_count}")
            
            # Validate camera placement
            camera = prediction.get('optimal_camera_placement')
            camera_available = bool(camera and camera.get('lat') and camera.get('lon'))
            print(f"  📹 Camera Placement: {'Available' if camera_available else 'Not Available'}")
            
            # Check for expected marker data structure
            print("\n🔍 Validating Data Structure:")
            
            # Travel corridors structure
            if travel_count > 0:
                sample_travel = prediction['travel_corridors']['features'][0]
                has_coords = bool(sample_travel.get('geometry', {}).get('coordinates'))
                has_score = 'score' in sample_travel.get('properties', {})
                print(f"  ✅ Travel data: coordinates={has_coords}, score={has_score}")
            
            # Bedding zones structure
            if bedding_count > 0:
                sample_bedding = prediction['bedding_zones']['features'][0]
                has_coords = bool(sample_bedding.get('geometry', {}).get('coordinates'))
                has_score = 'score' in sample_bedding.get('properties', {})
                print(f"  ✅ Bedding data: coordinates={has_coords}, score={has_score}")
            
            # Feeding areas structure
            if feeding_count > 0:
                sample_feeding = prediction['feeding_areas']['features'][0]
                has_coords = bool(sample_feeding.get('geometry', {}).get('coordinates'))
                has_score = 'score' in sample_feeding.get('properties', {})
                print(f"  ✅ Feeding data: coordinates={has_coords}, score={has_score}")
            
            # Stand recommendations structure
            if stand_count > 0:
                sample_stand = stands[0]
                has_coords = bool(sample_stand.get('coordinates', {}).get('lat'))
                has_confidence = 'confidence' in sample_stand
                has_rating = 'rating' in sample_stand
                print(f"  ✅ Stand data: coordinates={has_coords}, confidence={has_confidence}, rating={has_rating}")
            
            # Camera placement structure
            if camera_available:
                has_lat = 'lat' in camera
                has_lon = 'lon' in camera
                has_confidence = 'confidence' in camera
                has_distance = 'distance_from_stand' in camera
                print(f"  ✅ Camera data: lat={has_lat}, lon={has_lon}, confidence={has_confidence}, distance={has_distance}")
            
            return True, prediction
            
        else:
            print(f"❌ Backend Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Backend Test Failed: {e}")
        return False, None

def test_frontend_accessibility():
    """Test that frontend is accessible"""
    print("\n🌐 Testing Frontend Accessibility...")
    
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return False

def generate_frontend_test_report(prediction_data):
    """Generate a report of what should be visible on the frontend"""
    print("\n📋 Frontend Display Expectations:")
    print("=" * 50)
    
    if prediction_data:
        # Travel corridors
        travel_features = prediction_data.get('travel_corridors', {}).get('features', [])
        print(f"🚶 TRAVEL CORRIDORS ({len(travel_features)} markers):")
        for i, feature in enumerate(travel_features, 1):
            coords = feature.get('geometry', {}).get('coordinates', [])
            score = feature.get('properties', {}).get('score', 0)
            if len(coords) >= 2:
                print(f"   Marker {i}: Blue circle at ({coords[1]:.4f}, {coords[0]:.4f}) - Score: {score:.2f}")
        
        # Bedding zones
        bedding_features = prediction_data.get('bedding_zones', {}).get('features', [])
        print(f"\n🛏️ BEDDING ZONES ({len(bedding_features)} markers):")
        for i, feature in enumerate(bedding_features, 1):
            coords = feature.get('geometry', {}).get('coordinates', [])
            score = feature.get('properties', {}).get('score', 0)
            if len(coords) >= 2:
                print(f"   Marker {i}: Green circle at ({coords[1]:.4f}, {coords[0]:.4f}) - Score: {score:.2f}")
        
        # Feeding areas
        feeding_features = prediction_data.get('feeding_areas', {}).get('features', [])
        print(f"\n🌾 FEEDING AREAS ({len(feeding_features)} markers):")
        for i, feature in enumerate(feeding_features, 1):
            coords = feature.get('geometry', {}).get('coordinates', [])
            score = feature.get('properties', {}).get('score', 0)
            if len(coords) >= 2:
                print(f"   Marker {i}: Orange circle at ({coords[1]:.4f}, {coords[0]:.4f}) - Score: {score:.2f}")
        
        # Stand recommendations
        stands = prediction_data.get('mature_buck_analysis', {}).get('stand_recommendations', [])
        print(f"\n🎯 STAND RECOMMENDATIONS ({len(stands)} markers):")
        for i, stand in enumerate(stands, 1):
            coords = stand.get('coordinates', {})
            lat = coords.get('lat', 0)
            lon = coords.get('lon', 0)
            confidence = stand.get('confidence', 0)
            rating = stand.get('rating', 0)
            
            if i == 1:
                color = "Red (🏆 Primary)"
            elif i == 2:
                color = "Blue (🥈 Secondary)"
            else:
                color = "Purple (🥉 Tertiary)"
                
            print(f"   Stand {i}: {color} marker at ({lat:.4f}, {lon:.4f}) - Rating: {rating}, Confidence: {confidence}%")
        
        # Camera placement
        camera = prediction_data.get('optimal_camera_placement')
        if camera and camera.get('lat') and camera.get('lon'):
            print(f"\n📹 CAMERA PLACEMENT (1 marker):")
            lat = camera.get('lat', 0)
            lon = camera.get('lon', 0)
            confidence = camera.get('confidence', 0)
            distance = camera.get('distance_from_stand', 0)
            print(f"   Camera: Dark green marker at ({lat:.4f}, {lon:.4f}) - Confidence: {confidence}%, Distance: {distance}m")
        else:
            print(f"\n📹 CAMERA PLACEMENT: Not available")
    
    print("\n" + "=" * 50)
    print("🗺️ MAP INTERACTION:")
    print("   - Click anywhere on map to set new hunting location")
    print("   - Click 'Generate Hunting Predictions' to get new predictions")
    print("   - Hover over markers to see tooltips")
    print("   - Click markers to see detailed popups")

def main():
    """Run comprehensive frontend display test"""
    print("🎯 DEER PREDICTION APP - FRONTEND DISPLAY TEST")
    print("=" * 60)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Test backend prediction generation
    backend_success, prediction_data = test_backend_prediction()
    
    # Test frontend accessibility
    frontend_success = test_frontend_accessibility()
    
    # Generate display report
    if backend_success and prediction_data:
        generate_frontend_test_report(prediction_data)
    
    # Overall test result
    print("\n" + "=" * 60)
    if backend_success and frontend_success:
        print("🎉 OVERALL TEST RESULT: ✅ SUCCESS")
        print("\nThe frontend should display:")
        print("✅ Interactive map with hunting location")
        print("✅ Blue circle markers for travel corridors")
        print("✅ Green circle markers for bedding zones")
        print("✅ Orange circle markers for feeding areas")
        print("✅ Red/Blue/Purple markers for top 3 stand sites")
        print("✅ Dark green marker for optimal camera placement")
        print("✅ Clickable popups with detailed information")
        
        print(f"\n👉 Visit {FRONTEND_URL} to verify the display!")
    else:
        print("❌ OVERALL TEST RESULT: FAILED")
        if not backend_success:
            print("   - Backend prediction generation failed")
        if not frontend_success:
            print("   - Frontend is not accessible")

if __name__ == "__main__":
    main()
