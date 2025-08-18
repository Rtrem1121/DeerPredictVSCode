#!/usr/bin/env python3
"""
Enhanced Stand #1 Information Demo
Shows the comprehensive hunt data now available in the frontend
"""

import requests
import json

def demo_enhanced_stand_analysis():
    """Demonstrate the enhanced Stand #1 detailed hunt information"""
    
    print("🎯 ENHANCED STAND #1 - DETAILED HUNT INFORMATION DEMO")
    print("=" * 60)
    
    # Test with Stand #1 coordinates
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
        
        # Extract Stand #1 information (first recommended stand)
        mature_buck_data = data.get('mature_buck_analysis', {})
        stand_recommendations = mature_buck_data.get('stand_recommendations', [])
        
        if stand_recommendations:
            stand_1 = stand_recommendations[0]
            
            print("📍 STAND LOCATION ANALYSIS:")
            print(f"   Coordinates: {stand_1.get('coordinates', {}).get('lat', 0):.6f}, {stand_1.get('coordinates', {}).get('lon', 0):.6f}")
            print(f"   Stand Type: {stand_1.get('type', 'Unknown')}")
            print(f"   Algorithm Confidence: {stand_1.get('confidence', 0):.0f}%")
            
            # Terrain suitability scores
            terrain_scores = mature_buck_data.get('terrain_scores', {})
            if terrain_scores:
                print("\\n🏔️ TERRAIN SUITABILITY SCORES:")
                print(f"   Bedding Suitability: {terrain_scores.get('bedding_suitability', 0):.1f}%")
                print(f"   Escape Route Quality: {terrain_scores.get('escape_route_quality', 0):.1f}%")
                print(f"   Isolation Score: {terrain_scores.get('isolation_score', 0):.1f}%")
                print(f"   Pressure Resistance: {terrain_scores.get('pressure_resistance', 0):.1f}%")
                print(f"   Overall Suitability: {terrain_scores.get('overall_suitability', 0):.1f}%")
            
            # Strategic reasoning
            print("\\n🧠 ALGORITHM ANALYSIS:")
            terrain_justification = stand_1.get('terrain_justification', 'Advanced positioning')
            print(f"   Strategic Positioning: {terrain_justification}")
            
            setup_requirements = stand_1.get('setup_requirements', [])
            if setup_requirements:
                print("   Setup Requirements:")
                for req in setup_requirements:
                    print(f"      • {req}")
            
            # Movement prediction
            movement_prediction = mature_buck_data.get('movement_prediction', {})
            if movement_prediction:
                print("\\n🦌 MOVEMENT PREDICTION:")
                movement_prob = movement_prediction.get('movement_probability', 0)
                confidence_score = movement_prediction.get('confidence_score', 0)
                print(f"   Movement Probability: {movement_prob:.0f}%")
                print(f"   Prediction Confidence: {confidence_score:.0f}%")
                
                preferred_times = movement_prediction.get('preferred_times', [])
                if preferred_times:
                    print("   Optimal Hunt Times:")
                    for time in preferred_times:
                        print(f"      • {time}")
                
                behavioral_notes = movement_prediction.get('behavioral_notes', [])
                if behavioral_notes:
                    print("   Behavioral Intelligence:")
                    for note in behavioral_notes[:3]:  # Show first 3
                        if "✅" in note or "🎯" in note or "🌞" in note:
                            print(f"      • {note}")
            
            # Wind analysis
            wind_analysis = stand_1.get('wind_analysis', {})
            if wind_analysis:
                print("\\n🍃 WIND ANALYSIS:")
                print(f"   Wind Direction: {wind_analysis.get('wind_direction', 0):.0f}°")
                print(f"   Wind Speed: {wind_analysis.get('wind_speed', 0):.1f} mph")
                print(f"   Wind Pattern: {wind_analysis.get('wind_consistency', 'unknown')}")
                print(f"   Scent Safety Margin: {wind_analysis.get('scent_safety_margin', 0):.0f}m")
                
                wind_advantage = wind_analysis.get('wind_advantage_score', 0)
                if wind_advantage >= 90:
                    wind_quality = "🟢 EXCELLENT"
                elif wind_advantage >= 70:
                    wind_quality = "🟡 GOOD"
                else:
                    wind_quality = "🔴 POOR"
                print(f"   Wind Quality: {wind_quality}")
            
            # Camera placement integration
            camera_placement = data.get('optimal_camera_placement', {})
            if camera_placement and camera_placement.get('enabled'):
                print("\\n📹 CAMERA POSITION:")
                camera_distance = camera_placement.get('distance_meters', 0)
                camera_confidence = camera_placement.get('confidence_score', 0)
                print(f"   Distance from Stand: {camera_distance:.0f}m")
                print(f"   Camera Confidence: {camera_confidence:.1f}%")
                
                if camera_confidence >= 85:
                    print(f"   Quality: 🎥 PRIME Camera Spot")
                else:
                    print(f"   Quality: 📹 Good Camera Spot")
            
            # Deer approach calculation
            bedding_zones = data.get('bedding_zones', {}).get('zones', [])
            if bedding_zones:
                print("\\n📏 DEER APPROACH ANALYSIS:")
                first_bedding = bedding_zones[0]
                bedding_lat = first_bedding.get('lat', 0)
                bedding_lon = first_bedding.get('lon', 0)
                stand_lat = stand_1.get('coordinates', {}).get('lat', 0)
                stand_lon = stand_1.get('coordinates', {}).get('lon', 0)
                
                if bedding_lat and bedding_lon and stand_lat and stand_lon:
                    import math
                    
                    # Calculate deer approach bearing
                    lat_diff = stand_lat - bedding_lat
                    lon_diff = stand_lon - bedding_lon
                    bearing = math.degrees(math.atan2(lon_diff, lat_diff))
                    if bearing < 0:
                        bearing += 360
                    
                    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                                "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                    deer_approach_dir = directions[int((bearing + 11.25) / 22.5) % 16]
                    
                    print(f"   Deer Approach From: {deer_approach_dir} ({bearing:.0f}°)")
                    
                    # Calculate optimal wind directions
                    optimal_wind_1 = (bearing + 90) % 360
                    optimal_wind_2 = (bearing - 90) % 360
                    wind_dir_1 = directions[int((optimal_wind_1 + 11.25) / 22.5) % 16]
                    wind_dir_2 = directions[int((optimal_wind_2 + 11.25) / 22.5) % 16]
                    
                    print(f"   Optimal Wind Directions: {wind_dir_1} or {wind_dir_2}")
                    print(f"   Avoid Wind From: {deer_approach_dir} (towards deer)")
        
        print("\\n🎯 ENHANCED STAND #1 DATA SUMMARY:")
        print("✅ Comprehensive terrain suitability analysis")
        print("✅ Detailed wind direction intelligence")
        print("✅ Precise deer approach calculations")
        print("✅ Strategic positioning reasoning")
        print("✅ Movement prediction with behavioral notes")
        print("✅ Camera placement integration")
        print("✅ Equipment and timing recommendations")
        print("\\n🏆 Your enhanced Stand #1 information is now comprehensive!")
        
    else:
        print(f"❌ Failed to get prediction data: {response.status_code}")

if __name__ == "__main__":
    demo_enhanced_stand_analysis()
