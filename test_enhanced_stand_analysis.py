#!/usr/bin/env python3
"""
Quick Implementation Test - Enhanced Stand #1 Analysis
Tests the specific components that were flagged in validation
"""

import requests
import json

def test_enhanced_stand_analysis():
    """Test the enhanced Stand #1 analysis specifically"""
    
    # Test Stand #1 coordinates
    response = requests.post(
        "http://localhost:8000/predict",
        json={
            "lat": 44.2619,
            "lon": -72.5806,
            "date_time": "2025-11-15T06:00:00",
            "season": "rut",
            "include_camera_placement": True
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print("🎯 TESTING ENHANCED STAND #1 ANALYSIS")
        print("=" * 50)
        
        # Test terrain features
        terrain = data.get("terrain_features", {})
        print(f"\\n📊 TERRAIN FEATURES:")
        print(f"   Elevation: {terrain.get('elevation', 'missing')} feet")
        print(f"   Slope: {terrain.get('slope', 'missing')}°")
        print(f"   Canopy Closure: {terrain.get('canopy_closure', 'missing')}%")
        print(f"   Water Proximity: {terrain.get('water_proximity', 'missing')}m")
        print(f"   Ag Proximity: {terrain.get('ag_proximity', 'missing')}m")
        
        # Test mature buck analysis
        buck_analysis = data.get("mature_buck_analysis", {})
        print(f"\\n🦌 MATURE BUCK ANALYSIS:")
        print(f"   Viable Location: {buck_analysis.get('viable_location', 'missing')}")
        print(f"   Movement Confidence: {buck_analysis.get('movement_confidence', 'missing')}%")
        
        # Test bedding zones for deer approach calculations
        bedding_zones = data.get("bedding_zones", [])
        print(f"\\n🏠 BEDDING ZONES: {len(bedding_zones)} found")
        if bedding_zones:
            first_bedding = bedding_zones[0]
            bedding_lat = first_bedding.get("lat", 0)
            bedding_lon = first_bedding.get("lon", 0)
            print(f"   First bedding zone: {bedding_lat:.4f}, {bedding_lon:.4f}")
            
            # Calculate deer approach bearing (what frontend does)
            import math
            stand_lat, stand_lon = 44.2619, -72.5806
            lat_diff = bedding_lat - stand_lat
            lon_diff = bedding_lon - stand_lon
            bearing = math.degrees(math.atan2(lon_diff, lat_diff))
            if bearing < 0:
                bearing += 360
                
            print(f"   Calculated bearing: {bearing:.1f}°")
            
            # Convert to compass direction
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            compass_index = int((bearing + 11.25) / 22.5) % 16
            compass_dir = directions[compass_index]
            print(f"   Compass direction: {compass_dir}")
            
            # Calculate deer approach bearing for wind calculations
            deer_approach_bearing = (bearing + 180) % 360
            optimal_wind_1 = (deer_approach_bearing + 90) % 360
            optimal_wind_2 = (deer_approach_bearing - 90) % 360
            
            wind_dir_1 = directions[int((optimal_wind_1 + 11.25) / 22.5) % 16]
            wind_dir_2 = directions[int((optimal_wind_2 + 11.25) / 22.5) % 16]
            
            print(f"   Optimal wind directions: {wind_dir_1} or {wind_dir_2}")
        
        # Test camera placement
        camera_placement = data.get("camera_placement", {})
        print(f"\\n📹 CAMERA PLACEMENT:")
        if camera_placement:
            optimal_camera = camera_placement.get("optimal_camera", {})
            print(f"   Camera coordinates: {optimal_camera.get('lat', 'missing'):.4f}, {optimal_camera.get('lon', 'missing'):.4f}")
            print(f"   Confidence score: {optimal_camera.get('confidence_score', 'missing')}%")
            print(f"   Distance from stand: {optimal_camera.get('distance_from_target_meters', 'missing')}m")
            
            strategy = camera_placement.get("placement_strategy", {})
            if strategy:
                print(f"   Strategic reasoning: Available")
            else:
                print(f"   Strategic reasoning: Missing")
        else:
            print(f"   ❌ Camera placement missing from response")
        
        # Overall assessment
        print(f"\\n🎯 ASSESSMENT:")
        issues = []
        
        if terrain.get("elevation", 0) == 0:
            issues.append("Missing terrain elevation data")
        
        if buck_analysis.get("movement_confidence", 0) == 0:
            issues.append("Low mature buck movement confidence")
            
        if len(bedding_zones) == 0:
            issues.append("No bedding zones for deer approach calculations")
            
        if not camera_placement:
            issues.append("Missing camera placement integration")
        
        if len(issues) == 0:
            print("   ✅ All components working correctly!")
        else:
            print("   ⚠️ Issues found:")
            for issue in issues:
                print(f"      - {issue}")
                
    else:
        print(f"❌ API request failed: {response.status_code}")

if __name__ == "__main__":
    test_enhanced_stand_analysis()
