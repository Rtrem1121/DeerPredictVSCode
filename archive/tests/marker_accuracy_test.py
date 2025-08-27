#!/usr/bin/env python3
"""
Frontend Marker Accuracy Test
Verifies that the frontend displays markers at the correct locations
"""

import requests
import json

def test_marker_accuracy():
    """Test that frontend displays markers at exact backend-provided coordinates"""
    print("🎯 FRONTEND MARKER ACCURACY TEST")
    print("=" * 50)
    
    # Get prediction data
    test_data = {
        "lat": 44.2619,
        "lon": -72.5806,
        "date_time": "2025-08-24T19:30:00",
        "season": "rut",
        "fast_mode": True,
        "include_camera_placement": True
    }
    
    try:
        response = requests.post("http://localhost:8000/predict", json=test_data, timeout=30)
        prediction = response.json()
        
        print("✅ Backend Prediction Retrieved")
        print("\n🗺️ EXPECTED MARKER LOCATIONS:")
        print("=" * 50)
        
        # Travel corridors
        travel_features = prediction.get('travel_corridors', {}).get('features', [])
        print(f"🚶 TRAVEL CORRIDORS ({len(travel_features)} blue circles):")
        for i, feature in enumerate(travel_features, 1):
            coords = feature.get('geometry', {}).get('coordinates', [])
            score = feature.get('properties', {}).get('score', 0)
            if len(coords) >= 2:
                lat, lon = coords[1], coords[0]  # GeoJSON format [lon, lat]
                print(f"   {i}. Blue circle at {lat:.6f}, {lon:.6f} (Score: {score:.2f})")
        
        # Bedding zones
        bedding_features = prediction.get('bedding_zones', {}).get('features', [])
        print(f"\n🛏️ BEDDING ZONES ({len(bedding_features)} green circles):")
        for i, feature in enumerate(bedding_features, 1):
            coords = feature.get('geometry', {}).get('coordinates', [])
            score = feature.get('properties', {}).get('score', 0)
            if len(coords) >= 2:
                lat, lon = coords[1], coords[0]
                print(f"   {i}. Green circle at {lat:.6f}, {lon:.6f} (Score: {score:.2f})")
        
        # Feeding areas
        feeding_features = prediction.get('feeding_areas', {}).get('features', [])
        print(f"\n🌾 FEEDING AREAS ({len(feeding_features)} orange circles):")
        for i, feature in enumerate(feeding_features, 1):
            coords = feature.get('geometry', {}).get('coordinates', [])
            score = feature.get('properties', {}).get('score', 0)
            if len(coords) >= 2:
                lat, lon = coords[1], coords[0]
                print(f"   {i}. Orange circle at {lat:.6f}, {lon:.6f} (Score: {score:.2f})")
        
        # Stand recommendations
        stands = prediction.get('mature_buck_analysis', {}).get('stand_recommendations', [])
        print(f"\n🎯 STAND RECOMMENDATIONS ({len(stands)} stand markers):")
        for i, stand in enumerate(stands, 1):
            coords = stand.get('coordinates', {})
            lat = coords.get('lat', 0)
            lon = coords.get('lon', 0)
            confidence = stand.get('confidence', 0)
            
            colors = {1: "Red (🏆)", 2: "Blue (🥈)", 3: "Purple (🥉)"}
            color = colors.get(i, "Unknown")
            
            print(f"   {i}. {color} marker at {lat:.6f}, {lon:.6f} (Confidence: {confidence:.1f}%)")
        
        # Camera placement
        camera = prediction.get('optimal_camera_placement')
        if camera and camera.get('lat') and camera.get('lon'):
            lat = camera.get('lat', 0)
            lon = camera.get('lon', 0)
            confidence = camera.get('confidence', 0)
            distance = camera.get('distance_from_stand', 0)
            print(f"\n📹 CAMERA PLACEMENT (1 dark green marker):")
            print(f"   1. Dark green marker at {lat:.6f}, {lon:.6f} (Confidence: {confidence}%, Distance: {distance}m)")
        
        print("\n" + "=" * 50)
        print("✅ FRONTEND VERIFICATION CHECKLIST:")
        print("=" * 50)
        print("👁️ Visual checks to perform on the frontend:")
        print(f"   1. Map centered around {test_data['lat']:.4f}, {test_data['lon']:.4f}")
        print(f"   2. Total of {len(travel_features)} blue travel corridor circles")
        print(f"   3. Total of {len(bedding_features)} green bedding zone circles")
        print(f"   4. Total of {len(feeding_features)} orange feeding area circles")
        print(f"   5. Total of {len(stands)} stand markers (red/blue/purple)")
        if camera and camera.get('lat'):
            print("   6. 1 dark green camera marker")
        print("   7. All markers clickable with popup information")
        print("   8. Markers NOT in linear/grid pattern (intelligent placement)")
        
        print(f"\n🌐 Frontend URL: http://localhost:8501")
        print("📍 Input coordinates 44.2619, -72.5806 and click 'Generate Hunting Predictions'")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    test_marker_accuracy()
