#!/usr/bin/env python3
"""
Comprehensive test: Verify both bedding zones and feeding areas have aspect fallback
"""

import sys
import json
from enhanced_bedding_zone_predictor import EnhancedBeddingZonePredictor

def test_symmetrical_aspect_fallback():
    """Test that both bedding and feeding areas have symmetric aspect fallback"""
    print("🦌 COMPREHENSIVE SYMMETRICAL ASPECT FALLBACK TEST")
    print("=" * 70)
    
    # Vermont coordinates that previously showed aspect issues
    test_lat = 44.3106
    test_lon = -72.8092
    
    print(f"📍 Test Coordinates: {test_lat:.4f}, {test_lon:.4f}")
    print("🎯 Testing both bedding zones and feeding areas for aspect fallback symmetry")
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
        print(f"   Aspect Suitable for Habitat: {135 <= primary_aspect <= 225}")
        print(f"   Slope Suitable for Bedding: {primary_slope <= 30}")
        print()
        
        # Test bedding zones
        print("🛏️ GENERATING ENHANCED BEDDING ZONES...")
        bedding_result = predictor.generate_enhanced_bedding_zones(
            test_lat, test_lon, gee_data, osm_data, weather_data
        )
        
        # Test feeding areas
        print("🌾 GENERATING ENHANCED FEEDING AREAS...")
        feeding_result = predictor.generate_enhanced_feeding_areas(
            test_lat, test_lon, gee_data, osm_data, weather_data
        )
        
        print()
        print("📊 SYMMETRICAL FALLBACK ANALYSIS:")
        print("=" * 50)
        
        # Analyze bedding zones
        bedding_features = bedding_result.get('features', [])
        bedding_search_method = bedding_result.get('properties', {}).get('search_method')
        bedding_aspects = [f.get('properties', {}).get('aspect') for f in bedding_features]
        bedding_fallback_used = bedding_search_method == 'alternative_site_search'
        
        print(f"🛏️ BEDDING ZONES:")
        print(f"   Total Generated: {len(bedding_features)}")
        print(f"   Fallback Activated: {'✅ YES' if bedding_fallback_used else '❌ NO'}")
        print(f"   Aspects Generated: {[f'{a:.1f}°' if a else 'N/A' for a in bedding_aspects]}")
        print(f"   South-Facing Count: {len([a for a in bedding_aspects if a and 135 <= a <= 225])}")
        
        # Analyze feeding areas
        feeding_features = feeding_result.get('features', [])
        feeding_search_method = feeding_result.get('properties', {}).get('search_method')
        feeding_aspects = [f.get('properties', {}).get('aspect') for f in feeding_features]
        feeding_fallback_used = feeding_search_method == 'alternative_feeding_search'
        
        print(f"🌾 FEEDING AREAS:")
        print(f"   Total Generated: {len(feeding_features)}")
        print(f"   Fallback Activated: {'✅ YES' if feeding_fallback_used else '❌ NO'}")
        print(f"   Aspects Generated: {[f'{a:.1f}°' if a else 'N/A' for a in feeding_aspects]}")
        print(f"   South-Facing Count: {len([a for a in feeding_aspects if a and 135 <= a <= 225])}")
        
        print()
        print("🎯 SYMMETRY VERIFICATION:")
        print("-" * 30)
        
        # Check if both systems show consistent behavior
        both_activated = bedding_fallback_used and feeding_fallback_used
        both_deactivated = not bedding_fallback_used and not feeding_fallback_used
        symmetrical = both_activated or both_deactivated
        
        if both_activated:
            print("✅ SYMMETRICAL SUCCESS: Both bedding and feeding areas activated fallback mechanisms")
            print("   🦌 Biological accuracy maintained across all habitat components")
        elif both_deactivated:
            print("✅ SYMMETRICAL SUCCESS: Neither system needed fallback (primary location suitable)")
            print("   🦌 Primary location has optimal aspects for both bedding and feeding")
        else:
            print("⚠️  ASYMMETRICAL BEHAVIOR DETECTED:")
            print(f"   Bedding Fallback: {'✅ Active' if bedding_fallback_used else '❌ Inactive'}")
            print(f"   Feeding Fallback: {'✅ Active' if feeding_fallback_used else '❌ Inactive'}")
        
        # Count total south-facing sites generated
        total_south_facing = len([a for a in bedding_aspects + feeding_aspects if a and 135 <= a <= 225])
        total_sites = len(bedding_features) + len(feeding_features)
        
        print()
        print(f"📈 OVERALL RESULTS:")
        print(f"   Total Habitat Sites: {total_sites}")
        print(f"   South-Facing Sites: {total_south_facing}")
        print(f"   Biological Accuracy: {(total_south_facing/total_sites*100):.1f}% optimal aspects")
        
        if total_south_facing == total_sites:
            print("🏆 PERFECT BIOLOGICAL ACCURACY: All sites have optimal south-facing aspects!")
        elif total_south_facing >= total_sites * 0.8:
            print("✅ EXCELLENT BIOLOGICAL ACCURACY: >80% sites have optimal aspects")
        else:
            print("⚠️  Room for improvement in aspect optimization")
        
        return {
            'bedding_result': bedding_result,
            'feeding_result': feeding_result,
            'symmetrical': symmetrical,
            'biological_accuracy': total_south_facing/total_sites*100
        }
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_symmetrical_aspect_fallback()
