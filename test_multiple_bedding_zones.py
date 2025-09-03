#!/usr/bin/env python3
"""
Test enhanced multiple bedding zone generation
Testing the fix for generating only 1 alternative bedding zone instead of 2-3
"""

import sys
import json
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

def test_multiple_bedding_zones():
    """Test multiple bedding zone generation for mature whitetail buck behavior"""
    print("🦌 TESTING MULTIPLE BEDDING ZONE GENERATION")
    print("=" * 70)
    
    # Vermont coordinates with problematic northwest-facing aspect (310.22°)
    test_lat = 43.3139
    test_lon = -73.2306
    
    print(f"📍 Test Coordinates: {test_lat:.4f}, {test_lon:.4f}")
    print("🎯 Testing scenario: Primary location with northwest-facing aspect requiring fallback")
    print("🦌 Expected: 2-3 bedding zones (primary, secondary, escape) for mature buck behavior")
    print()
    
    try:
        # Initialize enhanced predictor
        predictor = EnhancedBeddingZonePredictor()
        
        # Get terrain data for primary location
        print("🔍 GETTING TERRAIN DATA FOR PRIMARY LOCATION...")
        gee_data = predictor.get_dynamic_gee_data_enhanced(test_lat, test_lon)
        osm_data = predictor.get_osm_road_proximity(test_lat, test_lon)
        weather_data = predictor.get_enhanced_weather_with_trends(test_lat, test_lon)
        
        primary_aspect = gee_data.get('aspect', 0)
        primary_slope = gee_data.get('slope', 0)
        
        print(f"   Primary Location Aspect: {primary_aspect}° (target: 310.22° northwest-facing)")
        print(f"   Primary Location Slope: {primary_slope:.1f}°")
        print(f"   Aspect Suitable for Bedding: {135 <= primary_aspect <= 225} (need south-facing)")
        print(f"   Slope Suitable for Bedding: {primary_slope <= 30}")
        print()
        
        # Test bedding zone generation
        print("🛏️ GENERATING ENHANCED BEDDING ZONES...")
        bedding_result = predictor.generate_enhanced_bedding_zones(
            test_lat, test_lon, gee_data, osm_data, weather_data
        )
        
        print()
        print("📊 BEDDING ZONE ANALYSIS:")
        print("=" * 50)
        
        # Analyze results
        bedding_features = bedding_result.get('features', [])
        total_zones = len(bedding_features)
        search_method = bedding_result.get('properties', {}).get('search_method', 'standard')
        
        print(f"✅ BEDDING ZONE GENERATION COMPLETED")
        print(f"   Total Bedding Zones Generated: {total_zones}")
        print(f"   Search Method: {search_method}")
        print(f"   Expected for Mature Bucks: 2-3 zones (primary, secondary, escape)")
        print()
        
        # Examine each bedding zone
        bedding_types = set()
        aspects = []
        slopes = []
        
        for i, feature in enumerate(bedding_features):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [0, 0])
            
            bedding_type = props.get('bedding_type', 'unknown')
            bedding_types.add(bedding_type)
            aspect = props.get('aspect', 0)
            slope = props.get('slope', 0)
            aspects.append(aspect)
            slopes.append(slope)
            
            print(f"🛏️ Bedding Zone {i+1}:")
            print(f"   Location: {coords[1]:.4f}, {coords[0]:.4f}")
            print(f"   Type: {bedding_type}")
            print(f"   Score: {props.get('score', 0):.1f}")
            print(f"   Aspect: {aspect:.1f}° ({'south-facing' if 135 <= aspect <= 225 else 'other'})")
            print(f"   Slope: {slope:.1f}°")
            print(f"   Description: {props.get('description', 'N/A')}")
            if 'distance_from_primary' in props:
                print(f"   Distance from Primary: {props.get('distance_from_primary', 0)}m")
            if 'biological_purpose' in props:
                print(f"   Biological Purpose: {props.get('biological_purpose', 'N/A')}")
            print()
        
        print("🎯 MATURE BUCK BEDDING BEHAVIOR ANALYSIS:")
        print("-" * 50)
        
        # Check for biological accuracy
        required_types = {'primary', 'secondary', 'escape'}
        found_base_types = {bt.split('_')[-1] for bt in bedding_types if '_' in bt}
        
        print(f"   Bedding Zone Types Generated: {list(bedding_types)}")
        print(f"   Base Types Found: {list(found_base_types)}")
        print(f"   Required Types: {list(required_types)}")
        
        # Evaluate completeness
        has_primary = any('primary' in bt for bt in bedding_types)
        has_secondary = any('secondary' in bt for bt in bedding_types)
        has_escape = any('escape' in bt for bt in bedding_types)
        
        print()
        print(f"📋 BEDDING ZONE COMPLETENESS:")
        print(f"   Primary Bedding Zone: {'✅ Present' if has_primary else '❌ Missing'}")
        print(f"   Secondary Bedding Zone: {'✅ Present' if has_secondary else '❌ Missing'}")
        print(f"   Escape Bedding Zone: {'✅ Present' if has_escape else '❌ Missing'}")
        
        complete_set = has_primary and has_secondary and has_escape
        if complete_set:
            print(f"   🏆 COMPLETE SET: All 3 bedding zone types present!")
        else:
            print(f"   ⚠️  INCOMPLETE: Missing bedding zone types for mature buck behavior")
        
        # Aspect quality check
        south_facing_count = len([a for a in aspects if 135 <= a <= 225])
        aspect_quality = south_facing_count / total_zones if total_zones > 0 else 0
        
        print()
        print(f"📈 BIOLOGICAL QUALITY METRICS:")
        print(f"   Total Bedding Zones: {total_zones}")
        print(f"   South-Facing Zones: {south_facing_count}")
        print(f"   Aspect Quality: {aspect_quality*100:.1f}% optimal")
        print(f"   Average Slope: {sum(slopes)/len(slopes):.1f}°" if slopes else "N/A")
        
        # Overall assessment
        if total_zones >= 2 and complete_set and aspect_quality >= 0.8:
            print(f"🏆 EXCELLENT: Perfect bedding zone generation for mature whitetail buck behavior!")
        elif total_zones >= 2 and aspect_quality >= 0.6:
            print(f"✅ GOOD: Adequate bedding zones generated with room for improvement")
        elif total_zones >= 2:
            print(f"⚠️  PARTIAL: Multiple zones generated but aspect quality needs improvement")
        else:
            print(f"❌ POOR: Insufficient bedding zones for mature buck dynamic behavior")
        
        print()
        print("🔍 DETAILED RESULTS:")
        print(f"   Search Method: {search_method}")
        print(f"   Primary Rejection Reason: {bedding_result.get('properties', {}).get('primary_rejection_reason', 'N/A')}")
        print(f"   Enhancement Version: {bedding_result.get('properties', {}).get('enhancement_version', 'N/A')}")
        
        return bedding_result
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_multiple_bedding_zones()
