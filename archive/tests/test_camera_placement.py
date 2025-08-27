#!/usr/bin/env python3
"""
Test the camera placement system with multiple locations
"""
from advanced_camera_placement import BuckCameraPlacement

def test_multiple_locations():
    """Test camera placement across different hunting locations"""
    
    test_locations = [
        {"name": "Central Vermont", "lat": 44.26, "lon": -72.58},
        {"name": "Northern Vermont", "lat": 44.95, "lon": -72.32},
        {"name": "Southern Vermont", "lat": 43.15, "lon": -72.88}
    ]
    
    camera_system = BuckCameraPlacement()
    
    print("🎥 Testing Camera Placement Across Multiple Locations")
    print("=" * 60)
    
    for location in test_locations:
        print(f"\n📍 Testing: {location['name']} ({location['lat']}, {location['lon']})")
        
        result = camera_system.calculate_optimal_camera_position(
            location['lat'], location['lon']
        )
        
        camera = result['optimal_camera']
        strategy = result['placement_strategy']
        
        print(f"   🎥 Camera: ({camera['lat']:.6f}, {camera['lon']:.6f})")
        print(f"   📏 Distance: {camera['distance_from_target_meters']:.0f}m")
        print(f"   🎯 Confidence: {camera['confidence_score']:.1f}%")
        print(f"   🧠 Key Factor: {strategy['primary_factors'][0]}")
        
        # Validate results
        if 50 <= camera['distance_from_target_meters'] <= 150:
            print(f"   ✅ Distance within optimal range")
        else:
            print(f"   ⚠️ Distance outside optimal range")
            
        if camera['confidence_score'] >= 70:
            print(f"   ✅ High confidence placement")
        else:
            print(f"   ⚠️ Low confidence placement")
    
    print(f"\n🎯 All locations tested successfully!")

if __name__ == "__main__":
    test_multiple_locations()
