#!/usr/bin/env python3
"""
Test feeding area aspect fallback mechanism
Testing the scenario where primary location has poor aspect for feeding
"""

import sys
import json
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

def test_feeding_aspect_fallback():
    """Test feeding area aspect fallback with problematic coordinates"""
    print("🌾 TESTING FEEDING AREA ASPECT FALLBACK MECHANISM")
    print("=" * 70)
    
    # Vermont coordinates that previously showed aspect issues
    test_lat = 44.3106
    test_lon = -72.8092
    
    print(f"📍 Test Coordinates: {test_lat:.4f}, {test_lon:.4f}")
    print("🎯 Testing scenario: Primary location with poor aspect for feeding")
    print()
    
    try:
        # Initialize enhanced predictor
        predictor = EnhancedBeddingZonePredictor()
        
        # Get terrain data for primary location
        print("🔍 GETTING TERRAIN DATA FOR PRIMARY LOCATION...")
        gee_data = predictor.get_dynamic_gee_data_enhanced(test_lat, test_lon)
        osm_data = predictor.get_osm_road_proximity(test_lat, test_lon)
        weather_data = predictor.get_enhanced_weather_with_trends(test_lat, test_lon)
        
        print(f"   Primary Location Aspect: {gee_data.get('aspect', 'N/A')}°")
        print(f"   Primary Location Slope: {gee_data.get('slope', 'N/A')}°")
        print(f"   Aspect Suitable for Feeding: {135 <= gee_data.get('aspect', 0) <= 225}")
        print()
        
        # Test feeding area generation with aspect fallback
        print("🌾 GENERATING ENHANCED FEEDING AREAS WITH FALLBACK...")
        feeding_result = predictor.generate_enhanced_feeding_areas(
            test_lat, test_lon, gee_data, osm_data, weather_data
        )
        
        # Analyze results
        print(f"✅ FEEDING AREA GENERATION COMPLETED")
        print(f"   Total Features Generated: {len(feeding_result.get('features', []))}")
        print(f"   Marker Type: {feeding_result.get('properties', {}).get('marker_type', 'unknown')}")
        print()
        
        # Examine each feeding area
        print("📊 FEEDING AREA ANALYSIS:")
        print("-" * 50)
        
        for i, feature in enumerate(feeding_result.get('features', [])):
            props = feature.get('properties', {})
            coords = feature.get('geometry', {}).get('coordinates', [0, 0])
            
            print(f"🌾 Feeding Area {i+1}:")
            print(f"   Location: {coords[1]:.4f}, {coords[0]:.4f}")
            print(f"   Type: {props.get('feeding_type', 'standard')}")
            print(f"   Score: {props.get('score', 0):.1f}%")
            print(f"   Aspect: {props.get('aspect', 'N/A')}°")
            print(f"   Slope: {props.get('slope', 'N/A')}°")
            print(f"   Description: {props.get('description', 'N/A')}")
            if 'distance_from_primary' in props:
                print(f"   Distance from Primary: {props.get('distance_from_primary', 0)}m")
            if 'search_reason' in props:
                print(f"   Search Reason: {props.get('search_reason', 'N/A')}")
            print()
        
        # Check for aspect improvement
        primary_aspect = gee_data.get('aspect', 0)
        feeding_aspects = [f.get('properties', {}).get('aspect') for f in feeding_result.get('features', [])]
        
        print("🎯 ASPECT FALLBACK ANALYSIS:")
        print(f"   Primary Location Aspect: {primary_aspect:.1f}°")
        print(f"   Primary Aspect Suitable: {135 <= primary_aspect <= 225}")
        print(f"   Generated Feeding Aspects: {[f'{a:.1f}°' if a else 'N/A' for a in feeding_aspects]}")
        
        # Check if any feeding areas have better aspects
        improved_aspects = [a for a in feeding_aspects if a and 135 <= a <= 225]
        if improved_aspects:
            print(f"   ✅ FALLBACK SUCCESS: {len(improved_aspects)} feeding areas with optimal south-facing aspects")
        else:
            print(f"   ⚠️  FALLBACK STATUS: No optimal south-facing feeding areas found")
        
        print()
        
        # Check properties for fallback indicators
        search_method = feeding_result.get('properties', {}).get('search_method')
        if search_method == 'alternative_feeding_search':
            print("✅ FALLBACK MECHANISM ACTIVATED: Alternative feeding sites generated")
        else:
            print("ℹ️  STANDARD GENERATION: Primary location used (no fallback needed)")
        
        return feeding_result
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_feeding_aspect_fallback()
