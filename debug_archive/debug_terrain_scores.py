#!/usr/bin/env python3
"""
Debug script to test terrain scores calculation
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.ml_mature_buck_predictor import get_mature_buck_predictor
import traceback

def test_terrain_scores():
    """Test terrain scores with sample data"""
    print("Testing terrain scores calculation...")
    
    # Sample terrain features (similar to what would come from actual analysis)
    terrain_features = {
        'elevation': 1200,
        'slope': 15,
        'aspect': 180,
        'cover_density': 0.75,
        'terrain_ruggedness': 0.5,
        'water_proximity': 300,
        'road_distance': 1000
    }
    
    lat, lon = 44.0, -72.0  # Vermont coordinates
    
    try:
        print("Getting buck predictor...")
        buck_predictor = get_mature_buck_predictor()
        
        print("Analyzing terrain...")
        scores = buck_predictor.analyze_mature_buck_terrain(terrain_features, lat, lon)
        
        print("Results:")
        print(f"Bedding Suitability: {scores.get('bedding_suitability', 'N/A')}")
        print(f"Escape Route Quality: {scores.get('escape_route_quality', 'N/A')}")
        print(f"Isolation Score: {scores.get('isolation_score', 'N/A')}")
        print(f"Pressure Resistance: {scores.get('pressure_resistance', 'N/A')}")
        print(f"Overall Suitability: {scores.get('overall_suitability', 'N/A')}")
        
        # Test with different terrain
        print("\n" + "="*50)
        print("Testing with different terrain...")
        
        terrain_features2 = {
            'elevation': 800,
            'slope': 8,
            'aspect': 90,
            'cover_density': 0.9,
            'terrain_ruggedness': 0.3,
            'water_proximity': 150,
            'road_distance': 500
        }
        
        scores2 = buck_predictor.analyze_mature_buck_terrain(terrain_features2, lat, lon)
        
        print("Results 2:")
        print(f"Bedding Suitability: {scores2.get('bedding_suitability', 'N/A')}")
        print(f"Escape Route Quality: {scores2.get('escape_route_quality', 'N/A')}")
        print(f"Isolation Score: {scores2.get('isolation_score', 'N/A')}")
        print(f"Pressure Resistance: {scores2.get('pressure_resistance', 'N/A')}")
        print(f"Overall Suitability: {scores2.get('overall_suitability', 'N/A')}")
        
        # Check if scores are different
        print("\n" + "="*50)
        print("Comparison:")
        if scores.get('isolation_score') != scores2.get('isolation_score'):
            print("✅ Isolation scores are different (good!)")
        else:
            print("❌ Isolation scores are the same (bug!)")
            
        if scores.get('pressure_resistance') != scores2.get('pressure_resistance'):
            print("✅ Pressure resistance scores are different (good!)")
        else:
            print("❌ Pressure resistance scores are the same (bug!)")
            
    except Exception as e:
        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_terrain_scores()
