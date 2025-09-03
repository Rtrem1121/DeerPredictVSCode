#!/usr/bin/env python3
"""
Test enhanced multi-tier bedding zone generation
Testing the hierarchical search system for multiple bedding zones
"""

import sys
import json
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

def test_multi_tier_bedding_zones():
    """Test multi-tier bedding zone generation with hierarchical fallback"""
    print("🛏️ TESTING ENHANCED MULTI-TIER BEDDING ZONE GENERATION")
    print("=" * 70)
    
    # Use the problematic Vermont coordinates that previously only generated 1 bedding zone
    test_lat = 43.3106
    test_lon = -73.2306
    
    print(f"📍 Test Coordinates: {test_lat:.4f}, {test_lon:.4f}")
    print("🎯 Testing scenario: Should generate 2-3 bedding zones for mature buck movement patterns")
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
        
        print(f"   Primary Location Aspect: {primary_aspect}°")
        print(f"   Primary Location Slope: {primary_slope:.1f}°")
        print(f"   Aspect Suitable for Bedding: {135 <= primary_aspect <= 225}")
        print(f"   Slope Suitable for Bedding: {primary_slope <= 30}")
        print()
        
        # Test enhanced bedding zone generation
        print("🛏️ GENERATING ENHANCED BEDDING ZONES WITH MULTI-TIER SEARCH...")
        bedding_result = predictor.generate_enhanced_bedding_zones(
            test_lat, test_lon, gee_data, osm_data, weather_data
        )
        
        print()
        print("📊 MULTI-TIER BEDDING ZONE ANALYSIS:")
        print("=" * 50)
        
        bedding_features = bedding_result.get('features', [])
        search_method = bedding_result.get('properties', {}).get('search_method')
        
        print(f"🛏️ BEDDING ZONES GENERATED:")
        print(f"   Total Bedding Zones: {len(bedding_features)}")
        print(f"   Search Method: {search_method or 'standard'}")
        print(f"   Fallback Activated: {'✅ YES' if search_method == 'alternative_site_search' else '❌ NO'}")
        print()
        
        if len(bedding_features) >= 2:
            print("✅ MATURE BUCK REQUIREMENT MET: Multiple bedding zones generated")
        else:
            print("⚠️  MATURE BUCK REQUIREMENT UNMET: Only 1 bedding zone (need 2-3)")
        
        print()
        print("🦌 INDIVIDUAL BEDDING ZONE ANALYSIS:")
        print("-" * 50)
        
        for i, feature in enumerate(bedding_features):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [0, 0])
            
            print(f"🛏️ Bedding Zone {i+1}:")
            print(f"   Location: {coords[1]:.4f}, {coords[0]:.4f}")
            print(f"   Type: {props.get('bedding_type', 'standard')}")
            print(f"   Score: {props.get('score', 0):.1f}%")
            print(f"   Confidence: {props.get('confidence', 0):.1f}")
            print(f"   Aspect: {props.get('aspect', 'N/A')}° ({'optimal' if props.get('aspect') and 135 <= props.get('aspect') <= 225 else 'suboptimal'})")
            print(f"   Slope: {props.get('slope', 'N/A')}°")
            if 'distance_from_primary' in props:
                print(f"   Distance from Primary: {props.get('distance_from_primary', 0)}m")
            if 'search_tier' in props:
                print(f"   Search Tier: {props.get('search_tier', 'N/A')}")
            if 'aspect_criteria' in props:
                print(f"   Aspect Criteria: {props.get('aspect_criteria', 'N/A')}")
            print(f"   Description: {props.get('description', 'N/A')}")
            print()
        
        # Analyze bedding zone diversity
        if 'bedding_diversity' in bedding_result.get('properties', {}):
            diversity = bedding_result['properties']['bedding_diversity']
            print("🎯 BEDDING ZONE DIVERSITY ANALYSIS:")
            print(f"   Zone Types: {', '.join(diversity.get('zone_types', []))}")
            print(f"   Distance Range: {diversity.get('distance_range_m', {}).get('min', 0)}-{diversity.get('distance_range_m', {}).get('max', 0)}m")
            print(f"   Aspect Range: {diversity.get('aspect_range_deg', {}).get('min', 0):.0f}°-{diversity.get('aspect_range_deg', {}).get('max', 0):.0f}°")
            print(f"   Thermal Diversity: {diversity.get('thermal_diversity', 'unknown')}")
            print()
        
        # Movement pattern analysis
        print("🦌 MATURE BUCK MOVEMENT PATTERN VALIDATION:")
        print("-" * 45)
        
        distances = [f.get('properties', {}).get('distance_from_primary', 0) for f in bedding_features if f.get('properties', {}).get('distance_from_primary')]
        aspects = [f.get('properties', {}).get('aspect') for f in bedding_features if f.get('properties', {}).get('aspect')]
        bedding_types = [f.get('properties', {}).get('bedding_type', 'standard') for f in bedding_features]
        
        # Check biological requirements
        multiple_zones = len(bedding_features) >= 2
        distance_appropriate = not distances or (min(distances) >= 100 and max(distances) <= 800)  # 100-800m range is ideal
        thermal_diversity = not aspects or (max(aspects) - min(aspects) >= 20)  # At least 20° aspect difference
        
        print(f"✅ Multiple Bedding Zones: {'YES' if multiple_zones else 'NO'} ({len(bedding_features)} zones)")
        print(f"✅ Appropriate Distances: {'YES' if distance_appropriate else 'NO'} ({min(distances) if distances else 0}-{max(distances) if distances else 0}m)")
        print(f"✅ Thermal Diversity: {'YES' if thermal_diversity else 'NO'} ({max(aspects) - min(aspects) if len(aspects) > 1 else 0:.0f}° spread)")
        print(f"✅ Zone Type Diversity: {'YES' if len(set(bedding_types)) > 1 else 'NO'} ({len(set(bedding_types))} types)")
        
        # Overall biological accuracy
        requirements_met = sum([multiple_zones, distance_appropriate, thermal_diversity])
        biological_grade = "A" if requirements_met >= 3 else "B" if requirements_met >= 2 else "C"
        
        print()
        print(f"🏆 BIOLOGICAL ACCURACY GRADE: {biological_grade}")
        print(f"   Requirements Met: {requirements_met}/3")
        
        if requirements_met >= 3:
            print("🦌 EXCELLENT: System provides optimal bedding diversity for mature whitetail bucks!")
        elif requirements_met >= 2:
            print("🦌 GOOD: System provides adequate bedding options with room for improvement")
        else:
            print("⚠️  NEEDS IMPROVEMENT: System lacks sufficient bedding diversity for mature bucks")
        
        return bedding_result
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_multi_tier_bedding_zones()
