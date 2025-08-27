#!/usr/bin/env python3
"""
Test to determine which terrain scoring path is being taken
"""
import sys
import os
sys.path.append('backend')

from backend.enhanced_accuracy import enhanced_terrain_analysis

def test_enhanced_scoring():
    """Test if enhanced_accuracy.py is working"""
    lat, lon = 44.074565, -72.647567
    
    # Test terrain features (sample data)
    terrain_features = {
        'elevation': 487.0,
        'slope': 15.0,
        'aspect': 180.0,
        'cover_density': 0.75,
        'terrain_ruggedness': 0.5,
        'water_proximity': 300.0,
        'road_distance': 1500.0,
        'escape_cover_density': 51.8,  # From our enhanced calculation
        'hunter_accessibility': 0.51,
        'wetland_proximity': 914.0,
        'cliff_proximity': 1972.0,
        'visibility_limitation': 0.36,
        'nearest_road_distance': 1454.0  # Converted to meters
    }
    
    print("Testing Enhanced Terrain Scoring:")
    print("="*50)
    
    try:
        scores = enhanced_terrain_analysis(terrain_features, lat, lon)
        
        print("✅ Enhanced scoring WORKS!")
        print(f"Results:")
        print(f"  Bedding Suitability: {scores.get('bedding_suitability', 'N/A'):.1f}%")
        print(f"  Escape Route Quality: {scores.get('escape_route_quality', 'N/A'):.1f}%")
        print(f"  Isolation Score: {scores.get('isolation_score', 'N/A'):.1f}%")
        print(f"  Pressure Resistance: {scores.get('pressure_resistance', 'N/A'):.1f}%")
        print(f"  Overall Suitability: {scores.get('overall_suitability', 'N/A'):.1f}%")
        
        # Check if these match our expected values
        isolation = scores.get('isolation_score', 0)
        pressure = scores.get('pressure_resistance', 0)
        
        print(f"\nAnalysis:")
        if isolation == 95.0:
            print("  Isolation: Expected 95.0 (correct for this location)")
        else:
            print(f"  Isolation: Got {isolation:.1f}, expected 95.0")
            
        if pressure == 0.0:
            print("  Pressure: Expected 0.0 based on terrain features")
        elif pressure == 60.0:
            print("  Pressure: Still getting 60.0 (hardcoded value!)")
        else:
            print(f"  Pressure: Got {pressure:.1f}")
            
        return True
        
    except Exception as e:
        print(f"❌ Enhanced scoring FAILED: {e}")
        print("This means the system falls back to standard analysis")
        return False

if __name__ == "__main__":
    test_enhanced_scoring()
