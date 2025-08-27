#!/usr/bin/env python3
"""
Direct test of enhanced_accuracy.py to debug hardcoded values
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from enhanced_accuracy import enhanced_terrain_analysis
from terrain_feature_mapper import TerrainFeatureMapper

def test_enhanced_accuracy_direct():
    """Test enhanced_accuracy.py directly with known coordinates"""
    
    # Test coordinates from user
    lat, lon = 44.074565, -72.647567
    
    print("DIRECT ENHANCED ACCURACY TEST")
    print("=" * 60)
    print(f"Coordinates: {lat}, {lon}")
    print()
    
    # Get terrain features
    # Create basic terrain features for testing
    terrain_features = {
        'elevation': 400.0,
        'slope': 8.5,
        'cover_density': 0.75,
        'water_proximity': 350.0,
        'terrain_ruggedness': 0.6
    }
    
    mapper = TerrainFeatureMapper()
    enhanced_features = mapper.map_terrain_features(terrain_features, lat, lon)
    
    print("ENHANCED TERRAIN FEATURES:")
    for key, value in enhanced_features.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")
    print()
    
    # Call enhanced_terrain_analysis directly
    scores = enhanced_terrain_analysis(enhanced_features, lat, lon)
    
    print("ENHANCED TERRAIN ANALYSIS RESULTS:")
    for key, value in scores.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")
    
    # Check specific calculations
    road_distance = enhanced_features.get('nearest_road_distance', 1000.0)
    road_distance_yards = road_distance * 1.094
    print(f"\nROAD DISTANCE DEBUG:")
    print(f"  Road distance (m): {road_distance:.1f}")
    print(f"  Road distance (yards): {road_distance_yards:.1f}")
    
    # Check pressure resistance components
    escape_cover = enhanced_features.get('escape_cover_density', 0)
    hunter_access = enhanced_features.get('hunter_accessibility', 0.7)
    wetland_prox = enhanced_features.get('wetland_proximity', 1000)
    cliff_prox = enhanced_features.get('cliff_proximity', 1000)
    visibility = enhanced_features.get('visibility_limitation', 0.5)
    
    print(f"\nPRESSURE RESISTANCE COMPONENTS:")
    print(f"  Escape cover density: {escape_cover:.1f}%")
    print(f"  Hunter accessibility: {hunter_access:.3f}")
    print(f"  Wetland proximity: {wetland_prox:.1f}m")
    print(f"  Cliff proximity: {cliff_prox:.1f}m")
    print(f"  Visibility limitation: {visibility:.3f}")

if __name__ == "__main__":
    test_enhanced_accuracy_direct()
