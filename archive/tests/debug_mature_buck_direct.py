#!/usr/bin/env python3
"""
Test mature buck predictor directly to see exactly what values it returns
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_mature_buck_predictor_direct():
    """Test the mature buck predictor directly"""
    from mature_buck_predictor import get_mature_buck_predictor
    from terrain_feature_mapper import TerrainFeatureMapper
    
    # Test coordinates
    lat, lon = 44.074565, -72.647567
    
    print("DIRECT MATURE BUCK PREDICTOR TEST")
    print("=" * 60)
    print(f"Coordinates: {lat}, {lon}")
    print()
    
    # Get terrain features
    basic_features = {
        'elevation': 400.0,
        'slope': 8.5,
        'cover_density': 0.75,
        'water_proximity': 350.0,
        'terrain_ruggedness': 0.6
    }
    
    mapper = TerrainFeatureMapper()
    enhanced_features = mapper.map_terrain_features(basic_features, lat, lon)
    
    # Get mature buck predictor
    buck_predictor = get_mature_buck_predictor()
    
    # Analyze terrain
    scores = buck_predictor.analyze_mature_buck_terrain(enhanced_features, lat, lon)
    
    print("MATURE BUCK PREDICTOR RESULTS:")
    for key, value in scores.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")
    
    print()
    print("SPECIFIC VALUES:")
    print(f"  Isolation Score: {scores.get('isolation_score', 'N/A'):.1f}")
    print(f"  Pressure Resistance: {scores.get('pressure_resistance', 'N/A'):.1f}")

if __name__ == "__main__":
    test_mature_buck_predictor_direct()
