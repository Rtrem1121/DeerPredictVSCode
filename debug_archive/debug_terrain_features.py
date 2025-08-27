#!/usr/bin/env python3
"""
Debug terrain features to see what data is being passed to scoring functions
"""
import requests
import json

def debug_terrain_features():
    """Check what terrain features are being calculated"""
    backend_url = "http://localhost:8000"
    
    # Test different locations
    test_locations = [
        {"name": "Mountain", "lat": 44.0708, "lon": -72.8429},
        {"name": "Valley", "lat": 44.0500, "lon": -72.8000},
        {"name": "Ridge", "lat": 44.1000, "lon": -72.9000}
    ]
    
    for location in test_locations:
        print(f"\n{'='*60}")
        print(f"Testing: {location['name']} ({location['lat']}, {location['lon']})")
        print("="*60)
        
        try:
            # Make terrain features request
            response = requests.get(
                f"{backend_url}/terrain-features", 
                params={"lat": location["lat"], "lon": location["lon"]},
                timeout=15
            )
            
            if response.status_code == 200:
                features = response.json()
                
                print("Key terrain features that affect isolation/pressure scores:")
                print(f"  nearest_road_distance: {features.get('nearest_road_distance', 'N/A')}")
                print(f"  nearest_building_distance: {features.get('nearest_building_distance', 'N/A')}")
                print(f"  trail_density: {features.get('trail_density', 'N/A')}")
                print(f"  escape_cover_density: {features.get('escape_cover_density', 'N/A')}")
                print(f"  hunter_accessibility: {features.get('hunter_accessibility', 'N/A')}")
                print(f"  wetland_proximity: {features.get('wetland_proximity', 'N/A')}")
                print(f"  cliff_proximity: {features.get('cliff_proximity', 'N/A')}")
                print(f"  visibility_limitation: {features.get('visibility_limitation', 'N/A')}")
                
                # Calculate what the scores should be manually
                road_dist = features.get('nearest_road_distance', 1000.0)
                print(f"\nManual score calculation:")
                print(f"  Road distance: {road_dist} yards")
                
                # Distance scoring thresholds (from distance_scorer.py)
                road_impact_range = 500.0  # Default value
                if road_dist >= road_impact_range:
                    expected_road_score = 95.0
                elif road_dist >= road_impact_range * 0.7:  # >= 350
                    expected_road_score = 70.0 + (road_dist / road_impact_range * 25.0)
                elif road_dist >= road_impact_range * 0.3:  # >= 150  
                    expected_road_score = 40.0 + (road_dist / (road_impact_range * 0.7) * 30.0)
                else:
                    expected_road_score = 10.0 + (road_dist / (road_impact_range * 0.3) * 30.0)
                    
                print(f"  Expected road impact score: {expected_road_score:.1f}")
                
            else:
                print(f"❌ Error getting terrain features: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_terrain_features()
