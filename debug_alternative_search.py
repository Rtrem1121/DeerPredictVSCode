#!/usr/bin/env python3
"""
Debug the alternative bedding site search to see why it's failing
"""

import sys
import json
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

def debug_alternative_search():
    """Debug why alternative bedding site search is failing"""
    print("🔍 DEBUGGING ALTERNATIVE BEDDING SITE SEARCH")
    print("=" * 60)
    
    # Vermont coordinates with problematic northwest-facing aspect (310.22°)
    test_lat = 43.3139
    test_lon = -73.2306
    
    print(f"📍 Test Coordinates: {test_lat:.4f}, {test_lon:.4f}")
    print()
    
    try:
        # Initialize enhanced predictor
        predictor = EnhancedBeddingZonePredictor()
        
        # Get terrain data for primary location
        print("🔍 PRIMARY LOCATION DATA:")
        gee_data = predictor.get_dynamic_gee_data_enhanced(test_lat, test_lon)
        osm_data = predictor.get_osm_road_proximity(test_lat, test_lon)
        weather_data = predictor.get_enhanced_weather_with_trends(test_lat, test_lon)
        
        print(f"   Aspect: {gee_data.get('aspect')}°")
        print(f"   Slope: {gee_data.get('slope')}°")
        print(f"   Canopy: {gee_data.get('canopy_coverage')}")
        print(f"   Road Distance: {osm_data.get('nearest_road_distance_m')}m")
        print()
        
        # Test individual search points manually
        print("🔍 TESTING INDIVIDUAL SEARCH POINTS:")
        print("-" * 40)
        
        # Search offsets from the alternative search method
        search_offsets = [
            (0.0009, 0.0012),   # ~100m NE  
            (-0.0009, 0.0012),  # ~100m NW
            (0.0009, -0.0012),  # ~100m SE
            (-0.0009, -0.0012), # ~100m SW
            (0.0000, 0.0018),   # ~200m N
            (0.0000, -0.0018),  # ~200m S
            (0.0018, 0.0000),   # ~200m E
            (-0.0018, 0.0000),  # ~200m W
        ]
        
        suitable_count = 0
        max_slope_limit = 30
        
        for i, (lat_offset, lon_offset) in enumerate(search_offsets):
            search_lat = test_lat + lat_offset
            search_lon = test_lon + lon_offset
            
            try:
                # Get terrain data for this location
                search_gee_data = predictor.get_dynamic_gee_data_enhanced(search_lat, search_lon)
                
                search_slope = search_gee_data.get("slope", 90)
                search_aspect = search_gee_data.get("aspect", 0)
                
                # Check slope suitability
                slope_suitable = search_slope <= max_slope_limit
                
                # Check aspect suitability (south-facing)
                aspect_suitable = (search_aspect is not None and 
                                 isinstance(search_aspect, (int, float)) and 
                                 135 <= search_aspect <= 225)
                
                print(f"   Point {i+1}: {search_lat:.4f}, {search_lon:.4f}")
                print(f"     Slope: {search_slope:.1f}° ({'✅ OK' if slope_suitable else '❌ STEEP'} - need ≤{max_slope_limit}°)")
                print(f"     Aspect: {search_aspect:.1f}° ({'✅ SOUTH' if aspect_suitable else '❌ OTHER'} - need 135°-225°)")
                
                if slope_suitable and aspect_suitable:
                    print(f"     🎯 POTENTIALLY SUITABLE - checking full criteria...")
                    
                    # Evaluate full suitability
                    suitability = predictor.evaluate_bedding_suitability(search_gee_data, osm_data, weather_data)
                    
                    print(f"     Full Suitability Score: {suitability['overall_score']:.1f}%")
                    print(f"     Meets Criteria: {'✅ YES' if suitability['meets_criteria'] else '❌ NO'}")
                    
                    if suitability["meets_criteria"]:
                        suitable_count += 1
                        print(f"     ✅ SUITABLE SITE FOUND! (Total: {suitable_count})")
                    else:
                        print(f"     ❌ Failed other criteria")
                        criteria = suitability.get('criteria', {})
                        print(f"       Canopy: {criteria.get('canopy_coverage', 0):.1%}")
                        print(f"       Road Distance: {criteria.get('road_distance', 0):.0f}m")
                else:
                    print(f"     ❌ Basic criteria failed")
                
                print()
                
            except Exception as e:
                print(f"     ❌ Error checking point {i+1}: {e}")
                print()
        
        print(f"🎯 SEARCH SUMMARY:")
        print(f"   Points Checked: {len(search_offsets)}")
        print(f"   Suitable Sites Found: {suitable_count}")
        print(f"   Success Rate: {suitable_count/len(search_offsets)*100:.1f}%")
        
        if suitable_count == 0:
            print(f"   🚫 NO SUITABLE SITES - This explains the fallback failure")
            print(f"   💡 Potential Solutions:")
            print(f"     - Expand search radius")
            print(f"     - Relax aspect requirements slightly")
            print(f"     - Lower suitability thresholds for alternatives")
        else:
            print(f"   ✅ SUITABLE SITES AVAILABLE - Issue may be in search method")
        
    except Exception as e:
        print(f"❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_alternative_search()
