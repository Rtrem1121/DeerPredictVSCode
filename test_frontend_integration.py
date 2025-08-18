#!/usr/bin/env python3
"""
Frontend Integration Demo for Single Camera Placement
Shows how the camera placement integrates with the current map interface
"""
import requests
import json

def test_frontend_integration():
    """Test how camera placement would integrate with frontend"""
    
    print("🖥️ Frontend Integration Demo - Single Optimal Camera Placement")
    print("=" * 70)
    
    # Simulate user clicking on map at these coordinates
    user_click_lat = 44.26
    user_click_lon = -72.58
    
    print(f"👆 User clicks on map at: ({user_click_lat}, {user_click_lon})")
    print("🔄 System calculates optimal camera placement...")
    
    # Call our standalone camera system (simulating the API call)
    from advanced_camera_placement import BuckCameraPlacement
    camera_system = BuckCameraPlacement()
    result = camera_system.calculate_optimal_camera_position(user_click_lat, user_click_lon)
    
    # Extract the single camera placement
    camera = result["optimal_camera"]
    
    print(f"\n📍 SINGLE CAMERA PLACEMENT RESULT:")
    print(f"   🎥 Optimal Position: ({camera['lat']:.6f}, {camera['lon']:.6f})")
    print(f"   📏 Distance from target: {camera['distance_from_target_meters']:.0f} meters")
    print(f"   🎯 Confidence Score: {camera['confidence_score']:.1f}%")
    
    # Show how this would appear on the frontend map
    print(f"\n🗺️ MAP DISPLAY:")
    print(f"   📌 RED PIN: Target location ({user_click_lat}, {user_click_lon})")
    print(f"   📷 CAMERA ICON: Optimal placement ({camera['lat']:.6f}, {camera['lon']:.6f})")
    print(f"   📏 DISTANCE LINE: {camera['distance_from_target_meters']:.0f}m connection")
    
    # Show strategy explanation for user
    strategy = result["placement_strategy"]
    print(f"\n💡 USER EXPLANATION:")
    print(f"   Why this location: {strategy['primary_factors'][0]}")
    print(f"   Best monitoring times: {', '.join(strategy['optimal_times'])}")
    print(f"   Expected detection range: {strategy['expected_detection_range']}")
    
    # Frontend JSON structure for map integration
    frontend_data = {
        "target_marker": {
            "lat": user_click_lat,
            "lon": user_click_lon,
            "icon": "target_pin",
            "color": "red",
            "label": "Hunting Target"
        },
        "camera_marker": {
            "lat": camera['lat'],
            "lon": camera['lon'], 
            "icon": "camera",
            "color": "green",
            "label": f"Optimal Camera ({camera['confidence_score']:.0f}% confidence)"
        },
        "connection_line": {
            "from": [user_click_lat, user_click_lon],
            "to": [camera['lat'], camera['lon']],
            "distance_text": f"{camera['distance_from_target_meters']:.0f}m",
            "color": "blue",
            "style": "dashed"
        },
        "info_panel": {
            "title": "Camera Placement Analysis",
            "confidence": f"{camera['confidence_score']:.1f}%",
            "distance": f"{camera['distance_from_target_meters']:.0f} meters",
            "reasoning": strategy['primary_factors'][0],
            "optimal_times": strategy['optimal_times']
        }
    }
    
    print(f"\n🔧 FRONTEND INTEGRATION DATA:")
    print(json.dumps(frontend_data, indent=2))
    
    return frontend_data

def simulate_different_locations():
    """Simulate clicking different locations to see varied placements"""
    
    print(f"\n🎯 Testing Different Target Locations:")
    print("=" * 50)
    
    test_locations = [
        {"name": "Forest Edge", "lat": 44.26, "lon": -72.58},
        {"name": "Open Field", "lat": 44.95, "lon": -72.32}, 
        {"name": "Valley Bottom", "lat": 43.15, "lon": -72.88}
    ]
    
    from advanced_camera_placement import BuckCameraPlacement
    camera_system = BuckCameraPlacement()
    
    for location in test_locations:
        print(f"\n📍 {location['name']}: ({location['lat']}, {location['lon']})")
        
        result = camera_system.calculate_optimal_camera_position(
            location['lat'], location['lon']
        )
        
        camera = result["optimal_camera"]
        print(f"   🎥 Camera: {camera['distance_from_target_meters']:.0f}m away, {camera['confidence_score']:.0f}% confidence")
        print(f"   💭 Strategy: {result['placement_strategy']['primary_factors'][0]}")

if __name__ == "__main__":
    # Test main integration
    frontend_data = test_frontend_integration()
    
    # Test multiple locations
    simulate_different_locations()
    
    print(f"\n✅ Frontend integration testing complete!")
    print(f"📋 Ready for integration into main application")
