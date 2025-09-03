#!/usr/bin/env python3
"""
Test the NEW problem coordinates with only 1 bedding zone generated
"""

import sys
import json
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

def test_new_problem_coordinates():
    """Test the coordinates from the NEW problem report"""
    print("🚨 TESTING NEW PROBLEM COORDINATES")
    print("=" * 60)
    
    # Coordinates from the NEW problem report 
    test_lat = 43.3140
    test_lon = -73.2306
    
    print(f"📍 New Problem Coordinates: {test_lat:.4f}, {test_lon:.4f}")
    print("🚨 User reported:")
    print("   • Only 1 alternative bedding zone generated (alternative_bedding_0)")
    print("   • Incorrect slope rejection: 24.0° rejected despite being within 3°-30° range")
    print("   • Should generate 2-3 bedding zones for mature buck movement")
    print()
    
    try:
        predictor = EnhancedBeddingZonePredictor()
        
        # Get terrain data first to check slope issue
        print("🔍 CHECKING PRIMARY LOCATION TERRAIN DATA...")
        gee_data = predictor.get_dynamic_gee_data_enhanced(test_lat, test_lon)
        osm_data = predictor.get_osm_road_proximity(test_lat, test_lon)
        weather_data = predictor.get_enhanced_weather_with_trends(test_lat, test_lon)
        
        primary_aspect = gee_data.get('aspect', 0)
        primary_slope = gee_data.get('slope', 0)
        
        print(f"   Primary Location Aspect: {primary_aspect}°")
        print(f"   Primary Location Slope: {primary_slope:.1f}°")
        print(f"   Slope within 3°-30° range: {3 <= primary_slope <= 30}")
        print(f"   Aspect suitable (135°-225°): {135 <= primary_aspect <= 225}")
        print()
        
        # Check if slope rejection is happening incorrectly
        if 3 <= primary_slope <= 30:
            print("⚠️  SLOPE ISSUE CONFIRMED: Slope is within acceptable range but may be rejected")
        
        # Run full bedding zone generation
        print("🛏️ GENERATING BEDDING ZONES...")
        bedding_result = predictor.generate_enhanced_bedding_zones(
            test_lat, test_lon, gee_data, osm_data, weather_data
        )
        
        print("✅ BEDDING ZONE GENERATION COMPLETED")
        print()
        
        # Analyze results
        bedding_features = bedding_result.get('features', [])
        search_method = bedding_result.get('properties', {}).get('search_method')
        rejection_reason = bedding_result.get('properties', {}).get('primary_rejection_reason')
        
        print("📊 BEDDING ZONE ANALYSIS:")
        print("=" * 40)
        print(f"Total Bedding Zones: {len(bedding_features)}")
        print(f"Expected: 2-3 zones")
        print(f"User Reported: Only 1 zone")
        print(f"Search Method: {search_method or 'standard'}")
        print(f"Rejection Reason: {rejection_reason or 'N/A'}")
        print()
        
        # Check for the specific issues mentioned
        if len(bedding_features) == 1:
            print("🚨 CONFIRMED: Only 1 bedding zone generated (matches user report)")
        elif len(bedding_features) >= 2:
            print("✅ FIXED: Multiple bedding zones now generated")
        else:
            print("❌ WORSE: No bedding zones generated")
        
        # Check slope rejection issue
        if rejection_reason and "Slope" in rejection_reason and "24" in rejection_reason:
            print("🚨 CONFIRMED: Incorrect slope rejection detected")
            print(f"   Rejection says: {rejection_reason}")
            print(f"   Actual slope: {primary_slope:.2f}° (within 3°-30° range)")
        
        print()
        print("🛏️ INDIVIDUAL BEDDING ZONE DETAILS:")
        print("-" * 40)
        
        for i, feature in enumerate(bedding_features):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [0, 0])
            
            print(f"Bedding Zone {i+1}:")
            print(f"   ID: {props.get('id', 'N/A')}")
            print(f"   Location: {coords[1]:.4f}, {coords[0]:.4f}")
            print(f"   Type: {props.get('bedding_type', 'unknown')}")
            print(f"   Score: {props.get('score', 0):.1f}%")
            print(f"   Aspect: {props.get('aspect', 'N/A')}°")
            print(f"   Slope: {props.get('slope', 'N/A')}°")
            if 'distance_from_primary' in props:
                print(f"   Distance from Primary: {props.get('distance_from_primary', 0)}m")
            print()
        
        # Problem diagnosis
        print("🎯 PROBLEM DIAGNOSIS:")
        print("-" * 30)
        
        if len(bedding_features) == 1:
            print("❌ Issue 1: Only 1 bedding zone generated (need 2-3)")
            print("   🦌 Mature bucks need multiple bedding options for dynamic behavior")
        else:
            print("✅ Issue 1: Multiple bedding zones generated")
        
        if rejection_reason and "24" in rejection_reason and primary_slope <= 30:
            print("❌ Issue 2: Incorrect slope rejection detected")
            print(f"   Slope {primary_slope:.1f}° incorrectly rejected (should be accepted)")
        else:
            print("✅ Issue 2: No incorrect slope rejection")
        
        return bedding_result
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_new_problem_coordinates()
