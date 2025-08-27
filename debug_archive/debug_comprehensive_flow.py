#!/usr/bin/env python3
"""
Create a comprehensive test that checks terrain scores at every step
"""
import requests
import json
import sys
import os

# Add backend to path for direct testing
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def comprehensive_terrain_debugging():
    """Test terrain scores through the complete pipeline"""
    
    # Test coordinates
    lat, lon = 44.074565, -72.647567
    
    print("COMPREHENSIVE TERRAIN SCORE DEBUGGING")
    print("=" * 70)
    print(f"Coordinates: {lat}, {lon}")
    print()
    
    # 1. Test enhanced_accuracy.py directly
    print("1. ENHANCED_ACCURACY.PY DIRECT TEST:")
    print("-" * 40)
    try:
        from enhanced_accuracy import enhanced_terrain_analysis
        from terrain_feature_mapper import TerrainFeatureMapper
        
        basic_features = {
            'elevation': 400.0,
            'slope': 8.5,
            'cover_density': 0.75,
            'water_proximity': 350.0,
            'terrain_ruggedness': 0.6
        }
        
        mapper = TerrainFeatureMapper()
        enhanced_features = mapper.map_terrain_features(basic_features, lat, lon)
        scores = enhanced_terrain_analysis(enhanced_features, lat, lon)
        
        print(f"  Isolation Score: {scores.get('isolation_score', 'N/A'):.1f}")
        print(f"  Pressure Resistance: {scores.get('pressure_resistance', 'N/A'):.1f}")
        
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # 2. Test mature buck predictor
    print("2. MATURE BUCK PREDICTOR TEST:")
    print("-" * 40)
    try:
        from mature_buck_predictor import get_mature_buck_predictor
        
        buck_predictor = get_mature_buck_predictor()
        scores = buck_predictor.analyze_mature_buck_terrain(enhanced_features, lat, lon)
        
        print(f"  Isolation Score: {scores.get('isolation_score', 'N/A'):.1f}")
        print(f"  Pressure Resistance: {scores.get('pressure_resistance', 'N/A'):.1f}")
        
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    
    # 3. Test API endpoint
    print("3. API ENDPOINT TEST:")
    print("-" * 40)
    try:
        test_request = {
            "name": "Debug Test Location",
            "lat": lat,
            "lon": lon,
            "date_time": "2024-10-15T06:00:00",
            "season": "early_season",
            "weather": {"temperature": 45, "wind_speed": 8, "wind_direction": 190}
        }
        
        response = requests.post('http://localhost:8000/predict', 
                               json=test_request,
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            mature_buck_data = data.get('mature_buck_analysis', {})
            terrain_scores = mature_buck_data.get('terrain_scores', {})
            
            print(f"  Isolation Score: {terrain_scores.get('isolation_score', 'N/A'):.1f}")
            print(f"  Pressure Resistance: {terrain_scores.get('pressure_resistance', 'N/A'):.1f}")
            
            # Check if there are any other sources of pressure resistance
            markers = mature_buck_data.get('opportunity_markers', [])
            if markers:
                marker = markers[0]
                print(f"  Marker Pressure Resistance: {marker.get('pressure_resistance', 'N/A'):.1f}")
            
        else:
            print(f"  API Error: {response.status_code}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    print()
    print("ANALYSIS:")
    print("-" * 40)
    print("If all three tests return the same values, the system is working correctly.")
    print("If API returns different values, there's post-processing happening.")

if __name__ == "__main__":
    comprehensive_terrain_debugging()
